# -*- coding: utf-8 -*-
"""
复习提醒算法（间隔重复）
========================
这个文件是"智能刷题助手"云端最核心的部分。

它做的事情很简单：
    一道错题记下来之后，不是马上让你复习，而是隔一段时间提醒你一次。
    因为根据"遗忘曲线"，人在刚学完时忘得最快，之后忘得越来越慢。
    所以在合适的时间点提醒复习，记忆效果最好。

这套算法参考了"艾宾浩斯遗忘曲线"和"间隔重复（Spaced Repetition）"的思想，
做了简化，方便初学者理解和使用。
"""


# 复习间隔（单位：天）
# 意思是：第 1 次复习在第 1 天，第 2 次在第 3 天，第 3 次在第 7 天……
REVIEW_INTERVALS = [1, 3, 7, 15, 30]


def get_review_days(wrong_day: int, review_count: int) -> int:
    """
    计算一道错题下次该复习的日子。

    参数：
        wrong_day    : 这道题是第几天记成错题的（0 表示今天）
        review_count : 这道题已经复习过几次了

    返回：
        下次复习是第几天（相对第 0 天）
    """
    if review_count >= len(REVIEW_INTERVALS):
        # 复习次数超过了设定，就沿用最后一个间隔（30 天）
        interval = REVIEW_INTERVALS[-1]
    else:
        interval = REVIEW_INTERVALS[review_count]

    return wrong_day + interval


def is_due_to_review(wrong_day: int, review_count: int, today: int) -> bool:
    """
    判断今天要不要复习这道错题。

    参数：
        wrong_day    : 记成错题的那一天
        review_count : 已经复习过几次
        today        : 今天是第几天

    返回：
        True 表示今天该复习了，False 表示还不到时候
    """
    next_day = get_review_days(wrong_day, review_count)
    return today >= next_day


# ------------------- 下面是简单的测试代码 -------------------
# 运行方式：在软件目录下执行  python3 review_algorithm.py
# 如果看到"全部测试通过！"，说明算法没问题。

if __name__ == "__main__":
    # 测试1：第0天记的错题，第0次复习，应该第1天复习
    assert get_review_days(0, 0) == 1
    # 测试2：第0天记的错题，复习过1次后，应该第3天复习
    assert get_review_days(0, 1) == 3
    # 测试3：第2天记的错题，复习过1次后，应该第5天复习（2+3=5）
    assert get_review_days(2, 1) == 5
    # 测试4：第0天记的错题，今天第0天，还不该复习
    assert is_due_to_review(0, 0, 0) is False
    # 测试5：第0天记的错题，今天第1天，该复习了
    assert is_due_to_review(0, 0, 1) is True
    # 测试6：复习次数很多时，一直按30天间隔
    assert get_review_days(0, 10) == 30

    print("全部测试通过！复习提醒算法工作正常。")

    # 演示一下：模拟一道错题的复习安排
    print("\n--- 演示：一道错题的复习计划 ---")
    wrong_day = 0  # 假设第0天记的错题
    for count in range(6):
        day = get_review_days(wrong_day, count)
        print(f"第 {count + 1} 次复习安排在：第 {day} 天")
