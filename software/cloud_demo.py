# -*- coding: utf-8 -*-
"""
云端演示程序（主程序）
========================
把前面的"复习算法"和"错题数据"组合起来，做成一整套云端逻辑。

它能做的事：
    1. 添加一道错题（相当于设备端按了"标记错题"按键）
    2. 自动判断今天有哪些错题该复习
    3. 复习后自动安排下一次复习时间
    4. 打印出清晰的复习清单，方便演示给评委看

这个程序完全在电脑上运行，不需要任何硬件，是"云端协同"的软件核心。
"""

from question_model import load_questions, add_question, review_question
from review_algorithm import is_due_to_review, get_review_days

# 今天的"第几天"。演示时可以改成不同数字，看复习提醒怎么变化。
# 真实使用时，可以从系统日期算出（比如从项目开始日算起）。
TODAY = 3


def show_dashboard():
    """展示错题总览：一共多少题、今天哪些该复习。"""
    questions = load_questions()

    print("=" * 50)
    print(f"   智能刷题助手 · 云端控制台")
    print(f"   今天是第 {TODAY} 天")
    print("=" * 50)
    print(f"错题总数：{len(questions)} 道\n")

    # 找出今天该复习的错题
    due = [q for q in questions if is_due_to_review(
        q.wrong_day, q.review_count, TODAY)]

    if due:
        print("📌 今天该复习的错题：")
        for q in due:
            print(f"  · [{q.subject}] {q.content}")
            print(f"    （第{q.review_count + 1}次复习，安排在记错题后"
                  f" {get_review_days(q.wrong_day, q.review_count)} 天）")
    else:
        print("今天没有需要复习的错题，可以安心刷题！")

    print("=" * 50)


def demo():
    """演示一整套流程：添加错题 → 看复习提醒 → 复习 → 再看提醒变化"""
    print("第一步：模拟设备端添加 3 道错题……\n")
    add_question("数学", "二次函数顶点坐标求法", 0)   # 第0天记的
    add_question("物理", "牛顿第二定律 F=ma", 1)      # 第1天记的
    add_question("英语", "虚拟语气 if 句型", 2)       # 第2天记的

    show_dashboard()

    print("\n第二步：模拟今天复习了数学那道题……\n")
    questions = load_questions()
    if questions:
        review_question(questions[0].id)

    show_dashboard()


if __name__ == "__main__":
    demo()
