# -*- coding: utf-8 -*-
"""
错题数据模型与存储
====================
这个文件定义"一道错题"长什么样，以及怎么把它存下来。

一道错题有这些信息：
    id        ：编号，方便查找
    subject   ：科目（数学、物理……）
    content   ：题目内容或描述
    wrong_day ：记成错题的那一天
    review_count：已经复习过几次
    image     ：题目图片（存路径或链接）

我们用最简单的方式存储：一个 JSON 文件，叫 wrong_questions.json。
（JSON 是一种很常见的文本格式，Python 自带支持，不用装额外的东西。）
"""

import json
import os


class WrongQuestion:
    """一道错题"""

    def __init__(self, subject, content, wrong_day,
                 review_count=0, image="", qid=None):
        self.id = qid if qid is not None else _next_id()
        self.subject = subject
        self.content = content
        self.wrong_day = wrong_day
        self.review_count = review_count
        self.image = image

    def to_dict(self):
        """把对象转成字典（方便存成 JSON）"""
        return {
            "id": self.id,
            "subject": self.subject,
            "content": self.content,
            "wrong_day": self.wrong_day,
            "review_count": self.review_count,
            "image": self.image,
        }


# ---------- 全局编号计数器（给新错题发编号） ----------
_auto_id = 0


def _next_id():
    global _auto_id
    _auto_id += 1
    return _auto_id


# ---------- 数据文件路径 ----------
# 数据存在软件目录下的 wrong_questions.json
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "wrong_questions.json")


def load_questions():
    """从文件读取所有错题，返回 WrongQuestion 列表。文件不存在就返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 注意：文件里存的键是 "id"，但构造函数参数是 qid，这里做个转换
    result = []
    for item in data:
        result.append(WrongQuestion(
            subject=item["subject"],
            content=item["content"],
            wrong_day=item["wrong_day"],
            review_count=item["review_count"],
            image=item.get("image", ""),
            qid=item["id"],
        ))
    return result


def save_questions(questions):
    """把所有错题保存到文件。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([q.to_dict() for q in questions],
                  f, ensure_ascii=False, indent=2)


def add_question(subject, content, wrong_day, image=""):
    """新加一道错题，自动保存，返回新的错题对象。"""
    q = WrongQuestion(subject, content, wrong_day, image=image)
    questions = load_questions()
    questions.append(q)
    save_questions(questions)
    return q


def review_question(qid):
    """把某道错题标记为'复习了一次'。"""
    questions = load_questions()
    for q in questions:
        if q.id == qid:
            q.review_count += 1
            break
    save_questions(questions)


# ---------- 测试 ----------
if __name__ == "__main__":
    # 先清理可能残留的旧测试数据，避免重复
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

    # 加两道测试错题
    q1 = add_question("数学", "二次函数顶点坐标求法", 0)
    q2 = add_question("物理", "牛顿第二定律 F=ma", 0)

    print("已添加错题：")
    for q in load_questions():
        print(f"  [{q.id}] {q.subject}：{q.content}（复习{q.review_count}次）")

    # 模拟复习一次
    review_question(q1.id)
    print("\n复习 q1 之后：")
    for q in load_questions():
        print(f"  [{q.id}] {q.subject}：{q.content}（复习{q.review_count}次）")

    # 清理测试数据，避免影响正式使用
    os.remove(DATA_FILE)
    print("\n测试完成，已清理测试数据。")
