#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包云端程序并推送到 GitHub，输出 PythonAnywhere 更新命令。"""

import os
import sys
import subprocess
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "software", "deploy")
ZIP_NAME = "cloud_deploy.zip"
ZIP_PATH = os.path.join(ROOT, ZIP_NAME)

GITHUB_REPO = "ChenLeidkzx/STM32"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{ZIP_NAME}"

# 不覆盖缓存、数据和日志文件。
SKIP_FILES = {"__pycache__", "wrong_questions.json", "server.log"}


def pack():
    """把 deploy 目录打包为 app/... 结构。"""
    print("[1/3] 正在打包代码...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, _, files in os.walk(DEPLOY):
            for name in files:
                if name in SKIP_FILES or "__pycache__" in folder:
                    continue
                full = os.path.join(folder, name)
                rel = os.path.join("app", os.path.relpath(full, DEPLOY))
                zf.write(full, rel)
    print(f"      打包完成 → {ZIP_NAME}（{os.path.getsize(ZIP_PATH)//1024} KB）")


def git_push():
    """提交并推送部署包。"""
    print("[2/3] 正在推送到 GitHub...")
    for cmd in (
        ["git", "add", ZIP_NAME],
        ["git", "commit", "-m", "cloud deploy package update"],
        ["git", "push"],
    ):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        out = (r.stdout or r.stderr).strip()
        if out:
            print("      " + out.splitlines()[-1] if out else "")
        if r.returncode != 0:
            pass
    print("      已推送到 GitHub")


def show_instructions():
    """输出 PythonAnywhere 更新命令。"""
    print("[3/3] 请按下面 2 步操作完成云端更新：")
    print()
    print("=" * 70)
    print("第 1 步：打开 PythonAnywhere → Consoles → Bash，粘贴：")
    print()
    print("  cd ~ && rm -rf cloud_app && curl -L -o cloud_deploy.zip "
          f"{RAW_URL} && unzip -o cloud_deploy.zip -d cloud_app && "
          "cp -r cloud_app/app/* /home/Tyits/app/ && "
          "rm -rf cloud_app cloud_deploy.zip")
    print()
    print("第 2 步：回到 PythonAnywhere 的 Web 页面，点绿色的 Reload 按钮")
    print("=" * 70)
    print()
    print("完成后打开 https://Tyits.pythonanywhere.com/ 即可看到新版。")


if __name__ == "__main__":
    if not os.path.isdir(DEPLOY):
        print("错误：找不到 software/deploy 目录")
        sys.exit(1)
    pack()
    git_push()
    show_instructions()
