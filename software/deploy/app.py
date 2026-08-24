# -*- coding: utf-8 -*-
"""
智能刷题助手 · 云端服务（Flask，部署到 PythonAnywhere 用）
===========================================================
这就是项目的"云端"：一个公网可访问的小网站。

功能：
    1. 打开浏览器看到错题列表和复习提醒（数据页面）
    2. 提供接口，让"设备"（或模拟脚本）上传错题数据
    3. 提供接口，标记错题复习

部署方法：见 software/云端部署指引_PythonAnywhere.md
本地测试：cd deploy && python3 app.py 然后访问 http://127.0.0.1:5000
"""

import os
import sys

# 让程序能找到同目录下的算法和数据文件
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, render_template, jsonify
from question_model import load_questions, add_question, review_question
from review_algorithm import is_due_to_review, get_review_days

app = Flask(__name__)

# 今天是第几天（演示用固定值；正式可改成从日期计算）
TODAY = 3


@app.route("/")
def index():
    """主页：展示错题列表和今天该复习的题"""
    questions = load_questions()
    due = [q for q in questions if is_due_to_review(
        q.wrong_day, q.review_count, TODAY)]
    return render_template("index.html",
                           questions=questions,
                           due=due,
                           today=TODAY)


@app.route("/api/upload", methods=["POST"])
def upload():
    """接口：设备上传错题数据。

    收到的 JSON 例子：
        {"subject": "数学", "content": "二次函数顶点坐标", "wrong_day": 0}
    """
    data = request.get_json()
    if not data or "subject" not in data or "content" not in data:
        return jsonify({"ok": False, "msg": "参数不对"}), 400

    q = add_question(
        subject=data["subject"],
        content=data["content"],
        wrong_day=data.get("wrong_day", TODAY),
    )
    return jsonify({"ok": True, "msg": "已记录", "id": q.id})


@app.route("/api/review/<int:qid>", methods=["POST"])
def do_review(qid):
    """接口：标记某道错题复习了一次"""
    review_question(qid)
    return jsonify({"ok": True, "msg": f"错题 {qid} 已复习"})


if __name__ == "__main__":
    print("云端服务启动！本地访问 http://127.0.0.1:8000")
    # 注意：
    # 1. 用 debug=False，否则浏览器访问会被 Flask 调试器保护拦截(403)
    # 2. 端口用 8000，避开 macOS 系统占用的 5000 端口（AirTunes 服务）
    # 3. PythonAnywhere 部署时不用 host=0.0.0.0（由平台接管），本地测试用它
    app.run(host="127.0.0.1", port=8000, debug=False)
