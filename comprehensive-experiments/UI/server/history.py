"""历史记录持久化：读写 server/history.json。

存储结构是一个 JSON 数组，每项一条测试运行记录。
读写都走 _LOCK 加锁，避免并发写损坏。
超过 MAX_ENTRIES 自动裁剪保留最近的。
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from server.adapters.base import TestResult

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"
MAX_ENTRIES = 1000
_LOCK = threading.Lock()

# 合法的测试类别
CATEGORIES = {"unit", "integration", "data", "performance"}


def _read_all() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_all(entries: list[dict]) -> None:
    HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append(category: str, case_name: str, case_id: str, result: TestResult) -> dict:
    """append 一条历史记录，返回入库后的完整条目（含 id）。"""
    if category not in CATEGORIES:
        raise ValueError(f"非法 category={category}，需为 {CATEGORIES}")

    entry = {
        "id": _gen_id(),
        "started_at": result.started_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "category": category,
        "case_name": case_name,
        "case_id": case_id,
        "owner": result.owner,
        "params": result.params,
        "success": result.success,
        "passed": result.passed,
        "failed": result.failed,
        "skipped": result.skipped,
        "duration_sec": result.duration_sec,
        "report_path": result.report_path,
        "extra": result.extra,
        "raw_output": result.raw_output,
    }

    with _LOCK:
        entries = _read_all()
        entries.append(entry)
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
        _write_all(entries)

    return entry


def query(
    from_: Optional[str] = None,
    to: Optional[str] = None,
    category: Optional[str] = None,
    owner: Optional[str] = None,
) -> list[dict]:
    """按时间/类别/成员筛选；返回按 started_at 倒序的列表。"""
    with _LOCK:
        entries = _read_all()

    def _ok(e: dict) -> bool:
        if category and e.get("category") != category:
            return False
        if owner and e.get("owner") != owner:
            return False
        if from_ and e.get("started_at", "") < from_:
            return False
        if to and e.get("started_at", "") > to:
            return False
        return True

    filtered = [e for e in entries if _ok(e)]
    filtered.sort(key=lambda e: e.get("started_at", ""), reverse=True)
    return filtered


def stats() -> dict:
    with _LOCK:
        entries = _read_all()
    by_cat: dict[str, int] = {}
    for e in entries:
        c = e.get("category", "unknown")
        by_cat[c] = by_cat.get(c, 0) + 1
    return {"total": len(entries), "by_category": by_cat}


def _gen_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
