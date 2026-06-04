"""全局运行锁（从 main.py 抽出，供 main.py 和 demo.py 共享同一把锁）。

同一时刻只允许一个测试 / 一批 demo 在跑，避免 Playwright / Selenium / Locust
资源冲突。这把锁是整个后端进程唯一的实例——main.py 的实时测试 endpoint 和
demo.py 的快速 demo 编排都从这里 import，互相之间天然互斥。
"""
from __future__ import annotations

import threading

# 进程级唯一的运行锁
RUN_LOCK = threading.Lock()
