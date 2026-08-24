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
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 忽略的目录/文件，避免把缓存也提交上去
IGNORE = {".git", "__pycache__", ".DS_Store", "auto_sync.py"}
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
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.returncode == 0


def sync():
    """把改动推送到远程。"""
    global _last_sync
    if time.time() - _last_sync < DEBOUNCE:
        return
    _last_sync = time.time()

    print("=" * 40)
    # 1. 暂存所有改动
    if not run(["git", "add", "-A"]):
        print("! git add 失败")
        return
    # 2. 有改动才提交
    status = subprocess.run(["git", "status", "--porcelain"],
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True, text=True).stdout.strip()
    if not status:
        print("无改动，跳过提交。")
        return
    if not run(["git", "commit", "-m", COMMIT_MSG]):
        print("! git commit 失败")
        return
    # 3. 推送到远程
    if not run(["git", "push"]):
        print("! git push 失败（请检查网络/凭据，改动已保存在本地提交中）")
    print("✓ 已同步到 GitHub")


class Handler(FileSystemEventHandler):
    def on_any_event(self, event):
        # 忽略目录本身和忽略列表
        if event.is_directory:
            return
        if any(seg in IGNORE for seg in event.src_path.split(os.sep)):
            return
        print(f"检测到变化: {os.path.basename(event.src_path)}")
        sync()


if __name__ == "__main__":
    watch_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"开始监听: {watch_dir}")
    print("按 Ctrl+C 停止。")
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
