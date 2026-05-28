# AutomationExercise Selenium + TestNG 综合实验

## 1. 项目说明

测试网站：https://automationexercise.com

本项目完成：

- 2 个以上单模块测试：注册、登录、登出
- 2 组以上集成模块测试
- 1 条集成路径深度 > 3
- 1 条自定义集成路径深度 >= 4：注册 -> 登出 -> 错误登录 -> 正确登录 -> 登出
- 1 项数据组合测试：登录账号 5 类 × 密码 5 类 = 25 组
- 1 项性能测试：默认 120 并发线程
- 1 个 Swing GUI 自动化测试运行界面

## 2. 环境准备

- JDK 17 或以上
- Maven 3.8+
- Chrome / Edge / Firefox 任一浏览器

Selenium 4 自带 Selenium Manager，一般不需要手动下载 chromedriver。

## 3. 运行功能测试

```bash
mvn test -DsuiteXmlFile=src/test/resources/testng.xml \
  -DbaseUrl=https://automationexercise.com \
  -Dbrowser=chrome \
  -Dheadless=false \
  -Dusername="Selenium Student" \
  -Dpassword="Test@123456"
```

Windows 可写成一行：

```bash
mvn test -DsuiteXmlFile=src/test/resources/testng.xml -DbaseUrl=https://automationexercise.com -Dbrowser=chrome -Dheadless=false -Dusername="Selenium Student" -Dpassword="Test@123456"
```

## 4. 运行性能测试

```bash
mvn test -DsuiteXmlFile=src/test/resources/testng-performance.xml -Dperformance.threads=120 -Dperformance.requestsPerThread=2
```

## 5. 运行 GUI

```bash
mvn exec:java -Dexec.mainClass=com.example.ae.gui.TestRunnerGUI
```

## 6. 自定义深度>=4模块组合

自定义组合：

注册模块 -> 登出模块 -> 登录模块错误分支 -> 登录模块正确分支 -> 登出模块

深度为 5。测试重点是：

1. 注册后账号真实创建；
2. 登出后会话被清除；
3. 错误密码不能登录；
4. 正确密码可以重新登录；
5. 再次登出后回到登录页。


## 2026-05 稳定性修复说明

本版本针对 automationexercise.com 页面广告脚本较多、Chrome 148 环境下页面加载容易超时的问题做了修复：

1. 浏览器 PageLoadStrategy 改为 EAGER，避免一直等待广告资源加载。
2. driver.get() 增加超时后 window.stop() 处理。
3. 点击按钮时增加滚动到元素位置和 JS 点击兜底。
4. 注册成功后如果没有稳定保持登录态，会自动用刚注册的账号再登录一次。
5. 登录数据组合测试只注册一次有效账号，不再 25 组每组都重新注册。
