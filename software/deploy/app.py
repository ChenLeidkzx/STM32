# -*- coding: utf-8 -*-
"""阳光伴学助手云端服务。"""

from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route("/")
def index():
    """返回云端状态页面。"""
    return render_template("index.html")


@app.route("/health")
def health():
    """返回服务器健康状态。"""
    return jsonify({"ok": True, "service": "sunshine-study-assistant"})


if __name__ == "__main__":
    print("云端服务启动！本地访问 http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000, debug=False)
