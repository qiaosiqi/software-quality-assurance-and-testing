"""siqi 实验全局配置。值直接改这里。

唯一例外：HEADLESS 额外认一个环境变量 SQA_HEADLESS——
快速 demo 会给子进程注入 SQA_HEADLESS=1 让浏览器后台跑（避免 4 人并行时窗口互相抢焦点）。
默认（不设该变量）仍为 False，与原行为一致，实时测试不受影响。
"""
import os

BASE_URL = "http://automationexercise.com"

DEFAULT_TIMEOUT_MS = 10_000

NAV_TIMEOUT_MS = 30_000

HEADLESS = os.environ.get("SQA_HEADLESS") == "1"

SLOW_MO_MS = 200
