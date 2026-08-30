#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动同步脚本：监听当前文件夹，文件变化后自动 git add / commit / push。
用法：
    python3 auto_sync.py            # 前台运行
    nohup python3 auto_sync.py &    # 后台常驻运行
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------- 样式 ----------
# ANSI 颜色（输出不是终端时自动降级为纯文本）
IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
if IS_TTY:
    BOLD, DIM = "\033[1m", "\033[2m"
    CYAN, GREEN, YELLOW, RED, MAGENTA = (
        "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[35m",
    )
    RESET = "\033[0m"
else:
    BOLD = DIM = CYAN = GREEN = YELLOW = RED = MAGENTA = RESET = ""

def ts():
    """当前时间戳（用于日志前缀）。"""
    return datetime.now().strftime("%H:%M:%S")

def log(msg, color=""):
    """打印一行带时间戳的日志。"""
    print(f"{DIM}{ts()}{RESET} {color}{msg}{RESET}")

def ok(msg):
    log(f"✔ {msg}", GREEN)

def warn(msg):
    log(f"⚠ {msg}", YELLOW)

def err(msg):
    log(f"✘ {msg}", RED)

def info(msg):
    log(f"• {msg}", CYAN)

# ---------- 配置 ----------
# 忽略的目录/文件，避免把缓存也提交上去
IGNORE = {".git", "__pycache__", ".DS_Store", "sync.py"}
# 防抖时间（秒）：文件连续变化时，等安静下来再提交
DEBOUNCE = 3.0
# 提交说明
COMMIT_MSG = "auto-sync: update files"

_last_sync = 0.0


def run(cmd):
    """在项目根目录执行命令，返回成功与否。"""
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True, text=True)
    if result.stdout.strip():
        print(f"{DIM}{result.stdout.strip()}{RESET}")
    if result.stderr.strip():
        print(f"{RED}{result.stderr.strip()}{RESET}")
    return result.returncode == 0


def sync():
    """把改动推送到远程。"""
    global _last_sync
    if time.time() - _last_sync < DEBOUNCE:
        return
    _last_sync = time.time()

    print()
    info("开始同步到 GitHub")
    # 1. 暂存所有改动
    if not run(["git", "add", "-A"]):
        err("git add 失败")
        return
    # 2. 有改动才提交
    status = subprocess.run(["git", "status", "--porcelain"],
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True, text=True).stdout.strip()
    if not status:
        info("无改动，跳过提交")
        return
    if not run(["git", "commit", "-m", COMMIT_MSG]):
        err("git commit 失败")
        return
    ok("已提交到本地")
    # 3. 推送到远程；若远程有新提交，先拉取合并再重试
    for attempt in range(3):
        if run(["git", "push"]):
            ok("已同步到 GitHub")
            return
        warn(f"远程有新提交，拉取合并后重试 ({attempt + 1}/3)...")
        run(["git", "pull", "--rebase", "origin", "main"])
    err("git push 多次失败（请检查网络/凭据，改动已保存在本地提交中）")


class Handler(FileSystemEventHandler):
    def on_any_event(self, event):
        # 忽略目录本身和忽略列表
        if event.is_directory:
            return
        if any(seg in IGNORE for seg in event.src_path.split(os.sep)):
            return
        info(f"检测到变化: {os.path.basename(event.src_path)}")
        sync()


if __name__ == "__main__":
    watch_dir = os.path.dirname(os.path.abspath(__file__))
    # 启动横幅（边框随内容自适应）
    title = "Auto-Sync  本地 ⇄ GitHub 自动同步"
    line1 = f"监听目录: {watch_dir}"
    width = max(len(title), len(line1)) + 4
    top = "╔" + "═" * width + "╗"
    mid = "║" + " " * width + "║"
    bottom = "╚" + "═" * width + "╝"
    print()
    print(f"{CYAN}{top}{RESET}")
    print(f"{CYAN}║{RESET} {BOLD}{title:<{width - 1}}{RESET}║")
    print(f"{CYAN}║{RESET} {DIM}{line1:<{width - 1}}{RESET}║")
    print(f"{CYAN}{bottom}{RESET}")
    print(f"{DIM}按 Ctrl+C 停止运行{RESET}")
    print()
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        info("已停止")
    observer.join()
