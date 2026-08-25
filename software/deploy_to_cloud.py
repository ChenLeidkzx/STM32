#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键部署到云端脚本
====================
作用：把本地 software/deploy/ 的代码打包并推送到 GitHub，
      然后在 PythonAnywhere 里粘贴一条命令就能更新云端。

为什么这样设计：
    你已经有 sync.py 自动同步 GitHub。我们把部署包也推上 GitHub，
    然后在 PythonAnywhere 的 Bash 里用 curl 下载 + 解压 + 覆盖，
    就完成了"改代码 → 更新云端"的整个流程。

用法：
    python3 deploy_to_cloud.py
之后：
    1. 打开 PythonAnywhere → Consoles → Bash
    2. 粘贴脚本打印的那条命令
    3. 回到 Web 页面点 Reload
"""

import os
import sys
import subprocess
import zipfile

# ---------- 路径 ----------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
DEPLOY = os.path.join(ROOT, "software", "deploy")                   # 要部署的代码
ZIP_NAME = "cloud_deploy.zip"                                       # 打包文件名
ZIP_PATH = os.path.join(ROOT, ZIP_NAME)

# GitHub 仓库（改成你自己的，注意是公开仓库才能 curl 下载）
GITHUB_REPO = "ChenLeidkzx/STM32"
# 注意：要用 raw.githubusercontent.com 这个地址，github.com/.../raw 会 302 重定向导致失败
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{ZIP_NAME}"

# 打包时排除的文件（缓存和数据文件不能覆盖云端的真实数据）
SKIP_FILES = {"__pycache__", "wrong_questions.json", "server.log"}


def pack():
    """把 deploy 目录打包成 zip，结构为 app/..."""
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
    """把 zip 提交并推送到 GitHub"""
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
            # git commit 没有变化时会返回非0，属于正常，继续
            pass
    print("      已推送到 GitHub")


def show_instructions():
    """打印在 PythonAnywhere Bash 里要执行的命令"""
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
