"""快速测试 demo 编排。

需求：
- 4 个成员的测试**并行**跑（每人 1 单元 + 1 集成 + 5 条数据组合，不跑性能）；
- 全程 **headless 后台**跑，避免 4 个可见浏览器互相抢焦点；
- 前端用 4 个进度框展示实时进度（步进 + 已用秒 + 日志尾巴）；
- 产物落到独立目录 outputs/quick-demo/<时间戳>/，并生成合并分析报告。

实现要点：
- 整批一次性持有 server.runlock.RUN_LOCK，跑完才释放——和"实时测试"页天然互斥，
  不会和手动运行打架。
- 用 ThreadPoolExecutor 4 路并行，每个 worker 串行跑自己 3 步；单步异常被兜住，
  只标红自己那一步/那个框，不拖垮其他成员。
- headless 通过给子进程注入环境变量 SQA_HEADLESS=1 实现（不污染 uvicorn 主进程
  的环境），zhiyi 则通过接口参数 headless=True -> -Dheadless=true。
- 接口层是阻塞式、一次性返回，没有细粒度流式进度，所以"实时进度"用
  "3 个离散步骤的步进 + 已用秒 + 每步小结" 来体现，零侵入接口。
"""
from __future__ import annotations

import shutil
import threading
import time
import traceback
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Optional

from server.adapters import ADAPTERS, OWNER_DISPLAY, get_adapter
from server.runlock import RUN_LOCK

UI_ROOT = Path(__file__).resolve().parent.parent
COMP_ROOT = UI_ROOT.parent
OUTPUT_ROOT = COMP_ROOT / "outputs" / "quick-demo"

# 进度框 / 报告里的成员顺序（与前端 OWNER_ORDER 一致）
OWNER_ORDER = ["siqi", "zhiyi", "yusheng", "xupeng"]

# 每个成员 demo 的 1 单元 + 1 集成 的具体选择（数据组合统一取各自前 N 条）
DEMO_PLAN: dict[str, dict] = {
    "siqi":    {"unit": "product_list", "integration": {"depth": 3}},
    "zhiyi":   {"unit": "register",     "integration": {"depth": 4, "path": 1}},
    "yusheng": {"unit": "cart_add",     "integration": {"depth": 5, "path": 1}},
    "xupeng":  {"unit": "contact",      "integration": {"depth": 5, "path": 1}},
}
DATA_LIMIT = 5
STEP_TOTAL = 3
MAX_WORKERS = 4


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class _OwnerState:
    """单个成员在一批 demo 中的运行状态（线程间共享，读写都在 DemoRunner 锁内）。"""

    def __init__(self, owner: str, display: str, available: bool):
        self.owner = owner
        self.display = display
        self.available = available
        self.state = "pending" if available else "skipped"   # pending|running|passed|failed|error|skipped
        self.step_done = 0
        self.step_total = STEP_TOTAL
        self.current_label = "等待开始" if available else "成员 adapter 不可用，已跳过"
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.passed = 0
        self.failed = 0
        self.steps: list[dict] = []          # [{name, success, passed, failed, duration}]
        self.log_tail: deque[str] = deque(maxlen=24)
        self.report_url: Optional[str] = None

    def snapshot(self) -> dict:
        now = time.time()
        if self.started_at is None:
            elapsed = 0.0
        elif self.finished_at is None:
            elapsed = now - self.started_at
        else:
            elapsed = self.finished_at - self.started_at
        return {
            "owner": self.owner,
            "display": self.display,
            "available": self.available,
            "state": self.state,
            "step_done": self.step_done,
            "step_total": self.step_total,
            "current_label": self.current_label,
            "elapsed_sec": round(elapsed, 1),
            "passed": self.passed,
            "failed": self.failed,
            "steps": list(self.steps),
            "log_tail": list(self.log_tail),
            "report_url": self.report_url,
        }


class DemoRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.status = "idle"                 # idle|running|done
        self.run_id: Optional[str] = None
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.out_dir: Optional[Path] = None
        self.report_url: Optional[str] = None
        self.owners: dict[str, _OwnerState] = {}

    # ---------- 对外快照 ----------
    def status_snapshot(self) -> dict:
        with self._lock:
            now = time.time()
            if self.started_at is None:
                elapsed = 0.0
            elif self.finished_at is None:
                elapsed = now - self.started_at
            else:
                elapsed = self.finished_at - self.started_at
            return {
                "status": self.status,
                "run_id": self.run_id,
                "started_at": (
                    datetime.fromtimestamp(self.started_at).isoformat(timespec="seconds")
                    if self.started_at else None
                ),
                "elapsed_sec": round(elapsed, 1),
                "report_url": self.report_url,
                "owners": [self.owners[o].snapshot() for o in OWNER_ORDER if o in self.owners],
            }

    # ---------- 启动 ----------
    def start(self) -> dict:
        with self._lock:
            if self.status == "running":
                return {"ok": False, "reason": "已有一批快速 demo 正在运行"}
            # 抢全局锁；抢不到说明实时测试正在跑
            if not RUN_LOCK.acquire(blocking=False):
                return {"ok": False, "reason": "实时测试正在运行，请等待其结束后再启动 demo"}

            run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.run_id = run_id
            self.status = "running"
            self.started_at = time.time()
            self.finished_at = None
            self.out_dir = OUTPUT_ROOT / run_id
            self.report_url = None
            self.owners = {
                o: _OwnerState(o, OWNER_DISPLAY[o], get_adapter(o).available)
                for o in OWNER_ORDER
            }

        # 后台线程跑整批，跑完释放锁。锁已在上面拿到。
        t = threading.Thread(target=self._run_batch, name=f"demo-{run_id}", daemon=True)
        t.start()
        return {"ok": True, "run_id": run_id}

    # ---------- 批次主流程（后台线程）----------
    def _run_batch(self) -> None:
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            available = [o for o in OWNER_ORDER if self.owners[o].available]
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                futures = [ex.submit(self._run_owner, o) for o in available]
                for f in futures:
                    f.result()   # 异常已在 _run_owner 内吞掉，这里不会抛
            # 跳过的成员留个说明文件
            for o in OWNER_ORDER:
                st = self.owners[o]
                if not st.available:
                    (self.out_dir / f"{o}.log").write_text(
                        f"{st.display} ({o}) 的 adapter 不可用，已跳过。\n",
                        encoding="utf-8",
                    )
            report_url = self._generate_report()
            with self._lock:
                self.report_url = report_url
        except Exception:
            # 极端情况下整批崩了也要把状态收尾，避免前端一直转圈
            with self._lock:
                for st in self.owners.values():
                    if st.state in ("pending", "running"):
                        st.state = "error"
                        st.current_label = "批次异常终止"
        finally:
            with self._lock:
                self.status = "done"
                self.finished_at = time.time()
            try:
                RUN_LOCK.release()
            except RuntimeError:
                pass

    # ---------- 单个成员 3 步 ----------
    def _run_owner(self, owner: str) -> None:
        adapter = get_adapter(owner)
        plan = DEMO_PLAN[owner]
        with self._lock:
            st = self.owners[owner]
            st.state = "running"
            st.started_at = time.time()
            st.current_label = "准备中…"

        any_failed = False
        any_error = False
        full_log: list[str] = []

        # 数据组合前 5 条 id（pytest 成员用 select_ids，zhiyi 用 limit；接口各自忽略不认识的参数）
        try:
            data_ids = [c["id"] for c in adapter.list_data_cases()[:DATA_LIMIT]]
        except Exception:
            data_ids = []

        steps = [
            ("单元测试", lambda: adapter.run_unit(module=plan["unit"], headless=True)),
            ("集成测试", lambda: adapter.run_integration(**plan["integration"], headless=True)),
            (f"数据组合(前{DATA_LIMIT}条)",
             lambda: adapter.run_data_combination(
                 select_ids=data_ids, limit=DATA_LIMIT, headless=True)),
        ]

        for name, fn in steps:
            with self._lock:
                self.owners[owner].current_label = f"正在跑：{name}"
            try:
                result = fn()
                ok = bool(getattr(result, "success", False))
                p = int(getattr(result, "passed", 0) or 0)
                f = int(getattr(result, "failed", 0) or 0)
                dur = float(getattr(result, "duration_sec", 0.0) or 0.0)
                raw = getattr(result, "raw_output", "") or ""
                rpath = getattr(result, "report_path", None)
                if not ok or f > 0:
                    any_failed = True
                full_log.append(f"\n{'='*60}\n[{name}] success={ok} passed={p} failed={f} "
                                 f"({dur:.1f}s)\n{'='*60}\n{raw}")
                copied = self._copy_report(owner, name, rpath)
                with self._lock:
                    s = self.owners[owner]
                    s.step_done += 1
                    s.passed += p
                    s.failed += f
                    s.steps.append({"name": name, "success": ok, "passed": p,
                                    "failed": f, "duration": round(dur, 1)})
                    s.log_tail.append(f"[{name}] {'✅' if ok else '❌'} 通过{p} 失败{f} · {dur:.1f}s")
                    if copied and s.report_url is None:
                        s.report_url = copied
            except Exception as e:                       # noqa: BLE001 单步容错
                any_error = True
                tb = traceback.format_exc()
                full_log.append(f"\n{'='*60}\n[{name}] 运行异常: {e}\n{'='*60}\n{tb}")
                with self._lock:
                    s = self.owners[owner]
                    s.step_done += 1
                    s.steps.append({"name": name, "success": False, "passed": 0,
                                    "failed": 0, "duration": 0.0, "error": str(e)})
                    s.log_tail.append(f"[{name}] ⚠️ 异常：{e}")

        # 落整段日志
        try:
            (self.out_dir / f"{owner}.log").write_text("\n".join(full_log), encoding="utf-8")
        except Exception:
            pass

        with self._lock:
            s = self.owners[owner]
            s.finished_at = time.time()
            s.state = "error" if any_error else ("failed" if any_failed else "passed")
            s.current_label = {"error": "运行出错", "failed": "完成（有失败用例）",
                               "passed": "全部通过"}[s.state]

    # ---------- 把成员报告拷进 demo 目录 ----------
    def _copy_report(self, owner: str, step_name: str, report_path: Optional[str]) -> Optional[str]:
        """把单步报告拷到 out_dir/<owner>/ 下，返回前端可访问的 URL（拷不到返回 None）。"""
        if not report_path:
            return None
        src = Path(report_path)
        if not src.exists():
            return None
        owner_dir = self.out_dir / owner
        owner_dir.mkdir(parents=True, exist_ok=True)
        # 文件名里去掉中文/括号，避免 URL 编码麻烦
        slug = (step_name.replace("（", "_").replace("）", "")
                .replace("(", "_").replace(")", "").replace("前", "").replace("条", ""))
        try:
            if src.is_file():
                dst = owner_dir / f"{slug}_{src.name}"
                shutil.copy2(src, dst)
                return f"/outputs/quick-demo/{self.run_id}/{owner}/{dst.name}"
            if src.is_dir():
                dst = owner_dir / slug
                shutil.copytree(src, dst, dirs_exist_ok=True)
                # 优先指向 index.html / emailable-report.html
                for cand in ("index.html", "emailable-report.html"):
                    if (dst / cand).exists():
                        return f"/outputs/quick-demo/{self.run_id}/{owner}/{slug}/{cand}"
                return f"/outputs/quick-demo/{self.run_id}/{owner}/{slug}/"
        except Exception:
            return None
        return None

    # ---------- 生成合并分析报告 ----------
    def _generate_report(self) -> Optional[str]:
        try:
            snaps = [self.owners[o].snapshot() for o in OWNER_ORDER if o in self.owners]
            ts_human = datetime.fromtimestamp(self.started_at).strftime("%Y-%m-%d %H:%M:%S")
            total_pass = sum(s["passed"] for s in snaps)
            total_fail = sum(s["failed"] for s in snaps)
            md = _render_markdown(self.run_id, ts_human, snaps, total_pass, total_fail)
            (self.out_dir / "report.md").write_text(md, encoding="utf-8")
            html = _render_html(self.run_id, ts_human, snaps, total_pass, total_fail)
            (self.out_dir / "index.html").write_text(html, encoding="utf-8")
            return f"/outputs/quick-demo/{self.run_id}/index.html"
        except Exception:
            return None


# ============================================================
# 报告渲染（纯函数，方便单测）
# ============================================================

_STATE_CN = {"passed": "全部通过", "failed": "有失败用例", "error": "运行出错",
             "skipped": "已跳过", "running": "运行中", "pending": "等待"}


def _render_markdown(run_id: str, ts_human: str, snaps: list[dict],
                     total_pass: int, total_fail: int) -> str:
    lines = [
        "# 快速测试 demo — 分析报告",
        "",
        f"- 批次编号：`{run_id}`",
        f"- 执行时间：{ts_human}",
        "- 被测站点：http://automationexercise.com/",
        "- 执行方式：4 人并行 · headless 后台 · 每人 1 单元 + 1 集成 + "
        f"{DATA_LIMIT} 条数据组合（不含性能）",
        f"- 总体结果：**通过 {total_pass} / 失败 {total_fail}**",
        "",
        "## 成员汇总",
        "",
        "| 成员 | 状态 | 单元 | 集成 | 数据组合 | 通过/失败 | 耗时 |",
        "|---|---|---|---|---|---|---|",
    ]

    def step_cell(snap: dict, idx: int) -> str:
        if idx >= len(snap["steps"]):
            return "—"
        s = snap["steps"][idx]
        mark = "✅" if s["success"] else "❌"
        return f"{mark} {s['passed']}/{s['passed'] + s['failed']}"

    for s in snaps:
        lines.append(
            f"| {s['display']} | {_STATE_CN.get(s['state'], s['state'])} "
            f"| {step_cell(s, 0)} | {step_cell(s, 1)} | {step_cell(s, 2)} "
            f"| {s['passed']}/{s['passed'] + s['failed']} | {s['elapsed_sec']}s |"
        )

    lines += ["", "## 各成员明细", ""]
    for s in snaps:
        lines.append(f"### {s['display']}（{s['owner']}）— {_STATE_CN.get(s['state'], s['state'])}")
        lines.append("")
        if s["state"] == "skipped":
            lines += ["> adapter 不可用，本批次已跳过。", ""]
            continue
        for st in s["steps"]:
            mark = "✅" if st["success"] else "❌"
            extra = f"，异常：{st['error']}" if st.get("error") else ""
            lines.append(f"- {mark} **{st['name']}** — 通过 {st['passed']} / 失败 "
                         f"{st['failed']}（{st['duration']}s）{extra}")
        lines.append(f"- 原始日志：`{s['owner']}.log`")
        lines.append("")
    return "\n".join(lines)


def _render_html(run_id: str, ts_human: str, snaps: list[dict],
                 total_pass: int, total_fail: int) -> str:
    def badge(state: str) -> str:
        color = {"passed": "#137333", "failed": "#c5221f", "error": "#b06000",
                 "skipped": "#5f6368"}.get(state, "#5f6368")
        return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:10px;font-size:12px;">{_STATE_CN.get(state, state)}</span>'

    rows = []
    for s in snaps:
        steps_html = []
        for st in s["steps"]:
            mark = "✅" if st["success"] else "❌"
            steps_html.append(
                f"<li>{mark} {escape(st['name'])} — 通过 {st['passed']} / 失败 {st['failed']}"
                f"（{st['duration']}s）</li>")
        report_link = (f'<a href="{escape(s["report_url"])}" target="_blank">查看报告</a>'
                       if s.get("report_url") else "—")
        rows.append(f"""
        <tr>
          <td><strong>{escape(s['display'])}</strong><br><span style="color:#888;font-size:12px;">{escape(s['owner'])}</span></td>
          <td>{badge(s['state'])}</td>
          <td>{s['passed']}/{s['passed'] + s['failed']}</td>
          <td>{s['elapsed_sec']}s</td>
          <td><ul style="margin:0;padding-left:18px;">{''.join(steps_html) or '—'}</ul></td>
          <td>{report_link}</td>
        </tr>""")

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>快速测试 demo 报告 · {escape(run_id)}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; margin: 32px; color: #202124; background:#f8f9fa; }}
  h1 {{ font-size: 22px; }}
  .meta {{ color:#5f6368; font-size:14px; line-height:1.8; margin-bottom:20px; }}
  table {{ border-collapse: collapse; width: 100%; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
  th, td {{ border-bottom: 1px solid #eee; padding: 12px; text-align: left; vertical-align: top; font-size:14px; }}
  th {{ background:#f1f3f4; }}
  .total {{ font-size:16px; margin:12px 0; }}
</style></head>
<body>
  <h1>快速测试 demo — 分析报告</h1>
  <div class="meta">
    批次编号：<code>{escape(run_id)}</code><br>
    执行时间：{escape(ts_human)}<br>
    被测站点：http://automationexercise.com/<br>
    执行方式：4 人并行 · headless 后台 · 每人 1 单元 + 1 集成 + {DATA_LIMIT} 条数据组合（不含性能）
  </div>
  <div class="total">总体结果：<strong style="color:#137333;">通过 {total_pass}</strong> · <strong style="color:#c5221f;">失败 {total_fail}</strong></div>
  <table>
    <thead><tr><th>成员</th><th>状态</th><th>通过/失败</th><th>耗时</th><th>步骤明细</th><th>报告</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body></html>"""


# 进程级单例
RUNNER = DemoRunner()


def start() -> dict:
    return RUNNER.start()


def status() -> dict:
    return RUNNER.status_snapshot()
