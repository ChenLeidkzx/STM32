# -*- coding: utf-8 -*-
"""阳光伴学助手云端服务。"""

import hashlib
import os
import sqlite3
import uuid

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "sunshine-study-assistant-secret-key"


def get_db_connection():
    """创建数据库连接。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化用户和会话表，并兼容旧版数据库结构。"""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "role" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_user_by_username(username):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return dict(row) if row else None


def create_user(username, password, role="user"):
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role),
        )
        conn.commit()
        return cursor.lastrowid


def create_session(user_id):
    token = uuid.uuid4().hex
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, token) VALUES (?, ?)",
            (user_id, token),
        )
        conn.commit()
    return token


def get_user_from_token(token):
    if not token:
        return None
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def get_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.args.get("token") or request.headers.get("X-Token")


def require_login():
    """要求用户必须登录，否则返回 (None, error_response)。"""
    token = get_token_from_request()
    user = get_user_from_token(token)
    if user is None:
        return None, (jsonify({"error": "未登录或 token 无效"}), 401)
    return user, None


def row_to_log(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@app.route("/")
def index():
    """返回云端状态页面。"""
    return render_template("index.html")


@app.route("/health")
def health():
    """返回服务器健康状态。"""
    with get_db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return jsonify({
        "ok": True,
        "service": "sunshine-study-assistant",
        "user_count": count,
    })


@app.route("/register", methods=["POST"])
def register():
    """注册新用户。支持传入 role，可由管理员创建管理员账号。"""
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    requested_role = (payload.get("role") or "user").strip().lower()

    if not username or not password:
        return jsonify({"error": "username 和 password 不能为空"}), 400
    if len(username) < 3 or len(password) < 6:
        return jsonify({"error": "username 至少 3 位，password 至少 6 位"}), 400
    if requested_role not in {"user", "admin"}:
        return jsonify({"error": "role 只能是 user 或 admin"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "用户名已存在"}), 409

    user_id = create_user(username, password, role=requested_role)
    token = create_session(user_id)

    return jsonify({
        "message": "注册成功",
        "token": token,
        "user": {"id": user_id, "username": username, "role": requested_role},
    }), 201


@app.route("/login", methods=["POST"])
def login():
    """登录并返回用户 token。"""
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    user = get_user_by_username(username)
    if not user or user["password_hash"] != hash_password(password):
        return jsonify({"error": "用户名或密码错误"}), 401

    token = create_session(user["id"])
    return jsonify({
        "message": "登录成功",
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
    })


@app.route("/logout", methods=["POST"])
def logout():
    """注销当前登录的 token。"""
    token = get_token_from_request()
    if not token:
        return jsonify({"error": "缺少 token"}), 401

    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()

    return jsonify({"message": "已退出登录"})


@app.route("/me")
def get_current_user():
    """获取当前登录用户信息。"""
    token = get_token_from_request()
    user = get_user_from_token(token)
    if user is None:
        return jsonify({"error": "未登录或 token 无效"}), 401
    return jsonify({"user": user})


@app.route("/users")
def list_users():
    """返回当前登录用户可见的用户列表。"""
    user, error = require_login()
    if error is not None:
        return error

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, created_at FROM users ORDER BY id ASC"
        ).fetchall()

    return jsonify({
        "user": user,
        "users": [
            {"id": row["id"], "username": row["username"], "created_at": row["created_at"]}
            for row in rows
        ],
    })


@app.route("/admin/users")
def admin_list_users():
    """返回所有用户数据，仅管理员可访问。"""
    user, error = require_login()
    if error is not None:
        return error

    if user.get("role") != "admin":
        return jsonify({"error": "只有管理员才能访问所有用户数据"}), 403

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY id ASC"
        ).fetchall()

    return jsonify({
        "admin": user,
        "total_users": len(rows),
        "users": [
            {"id": row["id"], "username": row["username"], "role": row["role"], "created_at": row["created_at"]}
            for row in rows
        ],
    })


@app.route("/study/add", methods=["POST"])
def add_study_log():
    """添加当前用户的学习记录。"""
    user, error = require_login()
    if error is not None:
        return error

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()

    if not title or not content:
        return jsonify({"error": "title 和 content 不能为空"}), 400

    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO study_logs (user_id, title, content) VALUES (?, ?, ?)",
            (user["id"], title, content),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, user_id, title, content, created_at, updated_at FROM study_logs WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return jsonify({
        "message": "学习记录已保存",
        "log": row_to_log(row),
    }), 201


@app.route("/study/list", methods=["GET"])
def list_study_logs():
    """返回当前用户的学习记录列表。"""
    user, error = require_login()
    if error is not None:
        return error

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, user_id, title, content, created_at, updated_at FROM study_logs WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()

    return jsonify({
        "user": user,
        "logs": [row_to_log(row) for row in rows],
    })


@app.route("/study/<int:log_id>", methods=["GET", "PUT", "DELETE"])
def study_log_detail(log_id):
    """查看、更新或删除当前用户自己的学习记录。"""
    user, error = require_login()
    if error is not None:
        return error

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, user_id, title, content, created_at, updated_at FROM study_logs WHERE id = ? AND user_id = ?",
            (log_id, user["id"]),
        ).fetchone()

        if row is None:
            return jsonify({"error": "记录不存在或不属于当前用户"}), 404

        if request.method == "GET":
            return jsonify({"log": row_to_log(row)})

        if request.method == "DELETE":
            conn.execute("DELETE FROM study_logs WHERE id = ?", (log_id,))
            conn.commit()
            return jsonify({"message": "学习记录已删除", "id": log_id})

        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or row["title"]).strip()
        content = (payload.get("content") or row["content"]).strip()
        if not title or not content:
            return jsonify({"error": "title 和 content 不能为空"}), 400

        conn.execute(
            "UPDATE study_logs SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, content, log_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT id, user_id, title, content, created_at, updated_at FROM study_logs WHERE id = ?",
            (log_id,),
        ).fetchone()
        return jsonify({"message": "学习记录已更新", "log": row_to_log(updated)})


# 在 users 表创建之前，确保 study_logs 表存在
with get_db_connection() as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()


init_db()


if __name__ == "__main__":
    print("云端服务启动！本地访问 http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000, debug=False)
