#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日项目想法日志生成脚本。

- 属于《基于 STM32 与云端协同的阳光伴学助手》项目。
- 每天由 GitHub Actions 定时调用（也可本地手动运行，标准库即可，无第三方依赖）。
- 在同一天的第一次运行时，生成 `daily-ideas/YYYY-MM-DD.md` 并提交；
  同一天重复运行不会重复生成（幂等），保证“每天至多一次提交”。
- 日期按北京时间（UTC + 8）计算。
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 北京时间 = UTC + 8
BJ_TZ = timezone(timedelta(hours=8))

ROOT = Path(__file__).resolve().parents[2]  # 仓库根目录
IDEAS_DIR = ROOT / "daily-ideas"  # 想法日志目录
PROJECT = "基于 STM32 与云端协同的阳光伴学助手"


def now_bj() -> datetime:
    return datetime.now(BJ_TZ)


def git(*args: str, cwd: Path = ROOT) -> str:
    """运行 git 命令并返回 stdout（去除首尾空白）。"""
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git 命令执行失败")
    return proc.stdout.strip()


def today_commits(date: datetime.date) -> str:
    """列出当天推送到 main 的提交；没有则返回“无”。"""
    day = date.strftime("%Y-%m-%d")
    since = f"{day} 00:00:00 +0800"
    until = f"{day} 23:59:59 +0800"
    lines = git(
        "log", "--since", since, "--until", until,
        "--pretty=format:%h|%an|%s", "--date-order", "--",
    ).splitlines()
    if not lines:
        return "（当天暂未推送到 main 的提交）"
    return "\n".join(
        f"- `{line.split('|', 2)[0]}` {line.split('|', 2)[2]} — {line.split('|', 2)[1]}"
        for line in lines
    )


def main() -> int:
    IDEAS_DIR.mkdir(parents=True, exist_ok=True)
    today = now_bj().date()
    target = IDEAS_DIR / f"{today.isoformat()}.md"

    # 幂等：同一天已生成过则不再生成（保证每天至多一次提交）
    if target.exists():
        print(f"[skip] 今日想法日志已存在：{target.name}")
        return 0

    content = f"""# {today.isoformat()} · 项目想法日志

> 本文件由 GitHub Actions **每日自动生成并提交**（也可手动触发）。
> 用于逐日记录对《{PROJECT}》的想法与进展，方便日后回顾。

## 💡 今日想法

<!-- 把今天对项目的想法写在这里：想到了什么、踩了什么坑、下一步要做什么。
     若为自动生成且暂无人工想法，可保留为“暂无”。 -->

- 暂无新增想法

## 🔄 今日仓库动态

{today_commits(today)}

---
<sub>自动生成时间：{now_bj().strftime("%Y-%m-%d %H:%M:%S")}（北京时间） · 生成脚本：`.github/scripts/daily_idea.py`</sub>
"""
    target.write_text(content, encoding="utf-8")
    print(f"[ok] 已生成：{target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
