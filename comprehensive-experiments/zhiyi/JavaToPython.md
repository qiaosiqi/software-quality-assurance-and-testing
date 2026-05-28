# Java → Python 集成方案：subprocess CLI

> 多人协作项目的Java测试模块与Python主程序集成方案
> 选型理由：解耦彻底、调试简单、故障隔离好

---

## 一、方案概述

### 背景
- 一名组员用Java编写了针对网站的测试模块：单元测试、集成测试、数据组合测试、性能测试
- 其余三人用Python开发，GUI也基于Python构建
- 需要让Python侧能够调用并使用Java侧的测试能力

### 选定方案
**subprocess + CLI + JSON**：Java模块打包成可执行jar，提供命令行入口；Python通过`subprocess`调用，参数和结果通过JSON交换。

### 核心理由
- **解耦彻底**：两侧代码完全独立，Java组员维护Java，Python组员维护Python
- **故障隔离**：子进程崩溃不影响主程序
- **调试简单**：jar可独立用命令行测试，问题定位清晰
- **适配场景**：测试任务"启动→执行→出报告"的流程天然契合，无需高频实时交互

### 已知权衡
- 每次调用启JVM约1–2秒冷启动开销（GUI点按钮触发完全可接受）
- 数据交换需手动JSON序列化（约定好schema即可）
- 不适合高频/低延迟的交互式调用

---

## 二、目录结构规划

```
project/
├── java-tests/
│   ├── src/...                       # Java测试代码（组员负责）
│   ├── pom.xml 或 build.gradle
│   └── target/test-runner.jar        # 打包产物
├── python-app/
│   ├── java_test_client.py           # subprocess封装层
│   ├── gui.py                        # GUI主程序
│   └── tests/                        # Python侧单元测试
├── docs/
│   └── json-schema.md                # 与组员共同维护的接口约定
└── README.md
```

---

## 三、接口契约（关键约定）

### CLI调用格式
```
java -jar test-runner.jar <test_type> <module_name> [params_json]
```

- `test_type`：`unit` | `integration` | `data_combo` | `perf`
- `module_name`：被测模块名称
- `params_json`：可选，传给测试的参数（JSON字符串）

### 统一返回结构
所有测试类型必须返回如下JSON结构，从stdout输出：
```json
{
  "success": true/false,
  "data": { ... },           // 成功时的测试结果
  "error": "错误信息",        // 失败时填写
  "errorType": "异常类名"     // 失败时填写
}
```

### 关键纪律（让Java组员严格遵守）
1. **stdout只输出最终JSON**，不允许夹杂任何日志或调试信息
2. **所有日志走stderr**（`System.err.println`），方便Python侧收集排查
3. **失败时exit code非0**（`System.exit(1)`），便于Python识别异常状态
4. **`data`字段内的schema**需要事先约定并写入`docs/json-schema.md`

---

## 四、推进步骤（联调清单）

按顺序执行，每步通过后再进入下一步：

### Step 1 — Java侧统一CLI入口
- 组员在Java项目中新增`Main`分发类，按`test_type`路由到对应的Runner
- 用Jackson或Gson做JSON序列化
- 打包生成可执行jar（Maven或Gradle）

### Step 2 — Java侧独立验证
- 命令行手动测试：`java -jar test-runner.jar unit login '{}'`
- 确认stdout输出是**干净的JSON**，无任何多余文本
- 确认stderr有可读的日志，便于调试

### Step 3 — Python侧最小链路打通
- 先用一个"假jar"测通流程：Java侧直接返回`{"success":true,"data":{"hello":"world"}}`
- Python侧确认能正确解析JSON、能拿到`data`字段
- 不涉及真实测试逻辑，只验证通信链路

### Step 4 — 约定JSON schema
- 与Java组员对齐每种`test_type`的`data`字段内容
- 在`docs/json-schema.md`中文档化，作为双方接口契约
- 字段调整必须双方同步

### Step 5 — Python客户端封装
- 实现`JavaTestClient`类，对外暴露`run_unit / run_integration / run_data_combo / run_perf`方法
- 内部统一处理：subprocess调用、超时控制、JSON解析、异常封装
- 返回值用`dataclass`包装，便于GUI使用

### Step 6 — 接入GUI
- GUI按钮回调中实例化`JavaTestClient`，调用对应方法
- 性能测试要异步执行（不阻塞GUI主线程）
- 错误信息和stderr日志在GUI中可查看

### Step 7 — 测试与稳定性加固
- Python侧用`pytest` + `mock`验证客户端逻辑（不依赖真实jar）
- 端到端测试：跑通至少一个真实测试用例
- 性能测试场景下验证超时机制是否生效

---

## 五、易踩的坑（提前注意）

### 编码问题
- Windows环境Java默认输出GBK
- 解决：Java侧强制UTF-8输出（`System.setOut(new PrintStream(System.out, true, "UTF-8"))`），或Python侧指定`encoding="gbk"`

### 命令行参数转义
- Python调用时**用list形式传cmd**，**禁用`shell=True`**
- 避免Windows下引号和空格的转义地狱

### stdout输出量
- 一般测试结果几KB到几MB：直接走stdout没问题
- 上百MB的大输出：改用**文件中转**（Java写临时文件，Python读完即删）

### 超时设置
- 单元/集成测试：默认300秒足够
- 性能测试：单独给600秒或更长，参数化暴露

### JVM参数
- 性能测试可能需要更大堆内存：通过`jvm_opts=["-Xmx2g"]`传入
- 启动慢可考虑后期优化（如AOT编译、GraalVM），但初期不必管

### 路径问题
- 用`pathlib.Path`处理jar路径，避免手拼字符串
- jar路径建议用项目根目录的相对路径或环境变量配置

---

## 六、后续优化方向（按需启用）

如果subprocess方案在使用中遇到瓶颈，可分阶段升级：

| 触发条件 | 升级方向 |
|---|---|
| GUI需要实时调用、冷启动延迟无法接受 | 改用JPype（Python嵌入JVM） |
| 需要远程部署/多机协作 | Java侧改造为REST API（Spring Boot/Javalin） |
| 多语言团队规模扩大、需要严格接口契约 | 改用gRPC（自动生成各语言客户端） |
| 单次输出超大或需要流式处理 | 用文件/管道流式传输，或切换为长连接服务 |

---

## 七、行动检查表（启动时打勾）

- [ ] Java组员确认愿意配合补CLI入口和JSON输出
- [ ] 确定打包工具（Maven / Gradle）和jar输出路径
- [ ] 创建`docs/json-schema.md`并填入第一版接口约定
- [ ] 跑通Step 2（Java独立CLI验证）
- [ ] 跑通Step 3（Python最小链路）
- [ ] 实现`JavaTestClient`封装
- [ ] 接入GUI并验证一个完整测试用例
- [ ] 补Python侧单元测试

---

## 八、相关参考

- 与本方案配套的代码脚手架：上一轮对话中已给出`Main.java`分发类和`JavaTestClient`封装类
- 备选方案对比（JPype、REST、gRPC等）：上一轮对话第一条回复
- 如需GUI接入示例（PyQt/Tkinter按钮回调），可后续单独生成
