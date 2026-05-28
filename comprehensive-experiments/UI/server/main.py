"""综合实验 GUI 后端入口。

Step 1 范围：
- FastAPI app 起来
- /health 健康检查
- 挂载前端静态文件 (/static) 和 siqi 报告目录 (/reports/siqi)
- 根路径 / 直接返回 web/index.html

后续 step 在这里继续加 endpoint。
"""
from __future__ import annotations

import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from server import history
from server.adapters import (
    ADAPTERS, MODULE_META, MODULE_OWNER, OWNER_DISPLAY, get_adapter,
)
from server.adapters import integration_catalog as ic

# 全局运行锁：同一时刻只允许一个测试在跑（避免 Playwright / Locust 资源冲突）
_RUN_LOCK = threading.Lock()

# 路径常量
UI_ROOT = Path(__file__).resolve().parent.parent          # comprehensive-experiments/UI
WEB_DIR = UI_ROOT / "web"
COMP_ROOT = UI_ROOT.parent                                 # comprehensive-experiments

# 4 成员的测试报告根目录（按 owner 索引）。
# 注意 zhiyi 是 Java/Maven 工程，报告在 surefire-reports/ 而不是 reports/ 下。
REPORT_DIRS: dict[str, Path] = {
    "siqi":    COMP_ROOT / "siqi" / "reports",
    "xupeng":  COMP_ROOT / "xupeng" / "reports",
    "yusheng": COMP_ROOT / "yusheng" / "reports",
    "zhiyi":   COMP_ROOT / "zhiyi" / "automationexercise-selenium-testng" / "target" / "surefire-reports",
}

# 报告目录在成员跑过测试前可能不存在，提前 mkdir 避免 StaticFiles 挂载失败
for _d in REPORT_DIRS.values():
    _d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="综合实验 GUI", version="0.1.0")

# 启动时打印关键 Python 路径，方便诊断"用错环境"问题。
# 注意：纯 ASCII，避免在 Windows cmd (gbk) 下 print emoji/中文导致 UnicodeEncodeError。
def _print_python_diagnostic() -> None:
    from server.adapters.siqi import _siqi as _siqi_mod  # 局部 import 避免循环
    print("[diagnostic] uvicorn sys.executable =", sys.executable)
    print("[diagnostic] siqi subprocess PYTHON =", _siqi_mod.PYTHON)
    if Path(sys.executable).resolve() != Path(_siqi_mod.PYTHON).resolve():
        print("[diagnostic] note: uvicorn and siqi subprocess use DIFFERENT pythons "
              "-- adapter has pinned siqi to UI/.venv to defend against miniconda etc. "
              "Usually fine; verify via /health.")

_print_python_diagnostic()


@app.get("/health")
def health() -> dict:
    from server.adapters.siqi import _siqi as _siqi_mod
    return {
        "ok": True,
        "service": "ui-backend",
        "version": "0.1.0",
        "uvicorn_python": sys.executable,
        "siqi_subprocess_python": _siqi_mod.PYTHON,
    }


@app.get("/api/monitor")
def api_monitor() -> dict:
    """首页监控小窗：探测 SUT 连通性 + 列出 adapter 可用性 + 自身存活。

    SUT 探测放在服务端做（不在浏览器里）是为了：
    1) 绕开 CORS —— automationexercise.com 不一定带跨域头；
    2) 给到真实的 server→server RTT，比浏览器 fetch 的数字更接近测试运行时的链路质量。

    handler 用同步 def，FastAPI 会把它放到 threadpool 跑，3s 超时不会阻塞事件循环。
    """
    sut: dict = {"ok": False, "latency_ms": None, "status_code": None, "error": None}
    try:
        t0 = time.perf_counter()
        r = requests.head(
            "https://automationexercise.com/",
            timeout=3,
            allow_redirects=True,
            headers={"User-Agent": "sqa-ui-monitor/1.0"},
        )
        sut["latency_ms"] = int((time.perf_counter() - t0) * 1000)
        sut["status_code"] = r.status_code
        sut["ok"] = 200 <= r.status_code < 400
    except requests.RequestException as e:
        sut["error"] = type(e).__name__

    adapters = {
        owner_id: {
            "available": adapter.available,
            "display": OWNER_DISPLAY[owner_id],
        }
        for owner_id, adapter in ADAPTERS.items()
    }

    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "sut": sut,
        "backend": {"ok": True, "version": "0.1.0"},
        "adapters": adapters,
        "running": _RUN_LOCK.locked(),
    }


@app.get("/api/meta")
def api_meta() -> dict:
    """前端首次加载用：12 模块 + 4 成员状态 + 各成员默认参数。"""
    modules = []
    for m in MODULE_META:
        owner = MODULE_OWNER[m["id"]]
        adapter = get_adapter(owner)
        modules.append({
            **m,
            "owner": owner,
            "owner_display": OWNER_DISPLAY[owner],
            "available": adapter.available,
        })

    owners = []
    for owner_id, adapter in ADAPTERS.items():
        owners.append({
            "id": owner_id,
            "display": OWNER_DISPLAY[owner_id],
            "available": adapter.available,
            "modules": adapter.list_modules(),
            "default_params": adapter.get_default_params() if adapter.available else {},
            "test_cases": adapter.list_test_cases() if adapter.available else {},
        })

    return {"modules": modules, "owners": owners}


# ============================================================
# 跑测试 endpoint
# ============================================================

class RunUnitBody(BaseModel):
    module: str                          # 12 模块之一的 id（如 "search"）
    keyword: Optional[str] = None
    product_index: Optional[int] = None


def _ensure_lock() -> None:
    """获取全局运行锁；获取不到说明已有测试在跑。"""
    if not _RUN_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="已有测试在运行，请等待结束")


def _make_report_url(owner: Optional[str], abs_path: Optional[str]) -> Optional[str]:
    """把 adapter 返回的绝对报告路径转成前端可用的 /reports/{owner}/... URL。

    - 文件路径：转成相对 REPORT_DIRS[owner] 的 URL
    - 目录路径（如 zhiyi 的 surefire-reports）：返回 /reports/{owner}/，由 StaticFiles html=True 兜底找 index.html
    - 不在 owner 报告目录下（理论不该出现）：返回 None，前端不显示链接
    """
    if not owner or not abs_path:
        return None
    base = REPORT_DIRS.get(owner)
    if base is None:
        return None
    try:
        abs_resolved = Path(abs_path).resolve()
        base_resolved = base.resolve()
    except OSError:
        return None
    try:
        rel = abs_resolved.relative_to(base_resolved)
    except ValueError:
        # 不在 base 下，可能是 zhiyi 把 surefire-reports 目录本身作为 report_path 返回
        if abs_resolved == base_resolved:
            return f"/reports/{owner}/"
        return None
    rel_str = rel.as_posix()
    if not rel_str or rel_str == ".":
        return f"/reports/{owner}/"
    return f"/reports/{owner}/{rel_str}"


def _enrich(entry: dict) -> dict:
    """给历史 entry 注入前端友好字段（目前是 report_url）。"""
    entry["report_url"] = _make_report_url(entry.get("owner"), entry.get("report_path"))
    return entry


def _case_meta_for_module(module_id: str) -> tuple[str, str]:
    """根据 module id 查中文名 + case_id，用于历史记录展示。"""
    for m in MODULE_META:
        if m["id"] == module_id:
            return m["name"], f"TC-{module_id}-01"
    return module_id, f"TC-{module_id}-01"


@app.post("/api/run/unit")
def api_run_unit(body: RunUnitBody) -> dict:
    if body.module not in MODULE_OWNER:
        raise HTTPException(400, f"未知模块 id: {body.module}")

    owner = MODULE_OWNER[body.module]
    adapter = get_adapter(owner)
    if not adapter.available:
        raise HTTPException(503, f"成员 {owner} 的 adapter 尚未实现")

    _ensure_lock()
    try:
        kwargs: dict = {}
        if body.keyword is not None:
            kwargs["keyword"] = body.keyword
        if body.product_index is not None:
            kwargs["product_index"] = body.product_index
        result = adapter.run_unit(module=body.module, **kwargs)
    finally:
        _RUN_LOCK.release()

    case_name, case_id = _case_meta_for_module(body.module)
    entry = history.append("unit", case_name, case_id, result)
    return {"ok": True, "entry": _enrich(entry)}


# ============================================================
# 历史记录查询
# ============================================================

@app.get("/api/history")
def api_history(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
    category: Optional[str] = None,
    owner: Optional[str] = None,
) -> dict:
    entries = history.query(from_=from_, to=to, category=category, owner=owner)
    return {"total": len(entries), "entries": [_enrich(e) for e in entries]}


@app.get("/api/history/stats")
def api_history_stats() -> dict:
    return history.stats()


# ============================================================
# 集成测试
# ============================================================

@app.get("/api/integration/catalog")
def api_integration_catalog() -> dict:
    """前端缓存白名单用，本地匹配槽位组合。"""
    return {"available": ic.list_available()}


class RunIntegrationBody(BaseModel):
    slots: list[Optional[str]]            # 长度 5；元素是模块 id 或 None
    keyword: Optional[str] = None
    product_index: Optional[int] = None


@app.post("/api/run/integration")
def api_run_integration(body: RunIntegrationBody) -> dict:
    if len(body.slots) != 5:
        raise HTTPException(400, "slots 必须是 5 长度")

    entry_meta = ic.lookup(body.slots)
    if entry_meta is None:
        return {
            "ok": False,
            "reason": "该组合暂未实现",
            "available": ic.list_available(),
        }

    owner, method_name, base_kwargs = entry_meta["runner"]
    adapter = get_adapter(owner)
    if not adapter.available:
        raise HTTPException(503, f"成员 {owner} 的 adapter 尚未实现")

    kwargs = dict(base_kwargs)
    if body.keyword is not None:
        kwargs["keyword"] = body.keyword
    if body.product_index is not None:
        kwargs["product_index"] = body.product_index

    _ensure_lock()
    try:
        method = getattr(adapter, method_name)
        result = method(**kwargs)
    finally:
        _RUN_LOCK.release()

    case_name = entry_meta["label"]
    case_id = f"TC-Integration-Depth{entry_meta['depth']}-01"
    record = history.append("integration", case_name, case_id, result)
    return {"ok": True, "matched": entry_meta, "entry": _enrich(record)}


# ============================================================
# 数据组合测试
# ============================================================

@app.get("/api/data/cases/{owner}")
def api_data_cases(owner: str) -> dict:
    """返回某成员数据组合测试的"待跑"表格行。"""
    adapter = get_adapter(owner)
    if not adapter.available:
        return {"available": False, "cases": []}
    return {"available": True, "cases": adapter.list_data_cases()}


class RunDataBody(BaseModel):
    owner: str
    regenerate: bool = False


@app.post("/api/run/data")
def api_run_data(body: RunDataBody) -> dict:
    adapter = get_adapter(body.owner)
    if not adapter.available:
        raise HTTPException(503, f"成员 {body.owner} 的 adapter 尚未实现")

    _ensure_lock()
    try:
        result = adapter.run_data_combination(regenerate=body.regenerate)
    finally:
        _RUN_LOCK.release()

    record = history.append("data", "数据组合测试", "TC-DataCombination", result)
    return {"ok": True, "entry": _enrich(record)}


# ============================================================
# 性能测试（参数完全透传给 adapter）
# ============================================================

class RunPerfBody(BaseModel):
    owner: str
    # 其余字段不固定结构 —— 不同 adapter 可能要不同参数
    # 用 model_config 允许额外字段，跑时按字典透传
    model_config = {"extra": "allow"}


@app.post("/api/run/performance")
def api_run_performance(body: RunPerfBody) -> dict:
    adapter = get_adapter(body.owner)
    if not adapter.available:
        raise HTTPException(503, f"成员 {body.owner} 的 adapter 尚未实现")

    # 把 body 拆成 owner + 其它 kwargs
    kwargs = body.model_dump(exclude={"owner"})
    # 类型修正：pydantic 把数字字符串保留为 string；adapter 期望 int 的字段手工 cast
    for k in ("users", "spawn_rate", "requests_per_thread"):
        if k in kwargs and kwargs[k] is not None:
            try:
                kwargs[k] = int(kwargs[k])
            except (TypeError, ValueError):
                raise HTTPException(400, f"参数 {k} 必须是整数")

    _ensure_lock()
    try:
        result = adapter.run_performance(**kwargs)
    finally:
        _RUN_LOCK.release()

    case_name = f"性能测试[{body.owner}]"
    record = history.append("performance", case_name, "TC-Performance-01", result)
    return {"ok": True, "entry": _enrich(record)}


@app.get("/")
def root() -> FileResponse:
    index = WEB_DIR / "index.html"
    if not index.exists():
        return JSONResponse(
            {"error": "web/index.html 不存在；请检查 UI 目录结构"},
            status_code=500,
        )
    return FileResponse(index)


# 前端静态资源（CSS/JS/图片）
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")

# 4 成员测试报告挂载。
# html=True：访问目录时自动找 index.html（zhiyi 的 surefire-reports 自带 index.html / emailable-report.html）。
for _owner, _dir in REPORT_DIRS.items():
    app.mount(
        f"/reports/{_owner}",
        StaticFiles(directory=_dir, html=True),
        name=f"reports-{_owner}",
    )
