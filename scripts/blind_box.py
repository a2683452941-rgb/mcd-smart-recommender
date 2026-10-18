#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦智选 · 盲盒随机推荐（摇一摇）

在你设定的目标/忌口/场景下，从饮食引擎筛出的候选里"随机摇"一份组合。
适合纠结星人：给约束但不想自己选时用。

用法:
  python blind_box.py --goal muscle_gain --scene lunch --avoid 猪,辣
  python blind_box.py --goal low_sugar --scene afternoon --seed 42

实现: 复用 scripts/recommend.py 的 NUTRITION / recommend() / build_combo()，
先按真实规则筛分，再在 Top 候选里随机成组，保证"随机但不离谱"。
"""

import argparse
import random

from recommend import NUTRITION, SCENE_MAP, recommend, build_combo, fmt, is_drink


def shake(goal, scene, avoid, pool, seed):
    if seed is not None:
        random.seed(seed)
    candidates = recommend(goal, scene, avoid, pool)
    # 主/副/饮 分桶，分别从桶里随机取，增加"摇"的惊喜感
    mains = [i for i in candidates
             if any(k in i[0] for k in ["堡", "麦满分", "粥", "鸡", "鱼", "汉堡", "卷"])
             and not is_drink(i[0])]
    sides = [i for i in candidates
             if any(k in i[0] for k in ["薯条", "玉米杯", "苹果片", "麦乐鸡", "鸡球", "派", "新地", "麦旋风"])
             and not is_drink(i[0])]
    drinks = [i for i in candidates if is_drink(i[0])]

    picks = []
    for bucket in (mains, sides, drinks):
        if bucket:
            picks.append(random.choice(bucket))
    # 若某桶为空，从候选补一个不重复的
    for i in candidates:
        if len(picks) >= 3:
            break
        if i[0] not in [p[0] for p in picks]:
            picks.append(i)
    return picks[:3]


def main():
    ap = argparse.ArgumentParser(description="麦麦智选 盲盒随机推荐")
    ap.add_argument("--goal", default="balanced",
                    choices=["fat_loss", "muscle_gain", "low_sugar",
                             "balanced", "children", "office"])
    ap.add_argument("--scene", default=None, choices=list(SCENE_MAP.keys()))
    ap.add_argument("--avoid", default="", help="忌口关键词，逗号分隔")
    ap.add_argument("--pool", type=int, default=12, help="候选池大小（越大越随机）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（可复现演示）")
    args = ap.parse_args()

    avoid = [a.strip() for a in args.avoid.split(",") if a.strip()]
    goal_cn = {"fat_loss": "减脂", "muscle_gain": "增肌", "low_sugar": "控糖",
               "balanced": "均衡", "children": "儿童家庭", "office": "上班族快手"}[args.goal]

    combo = shake(args.goal, args.scene, avoid, args.pool, args.seed)

    print("🎲 === 麦麦智选 · 摇一摇 (%s%s) ===" % (goal_cn, "·" + args.scene if args.scene else ""))
    if avoid:
        print("已剔除忌口: %s" % ", ".join(avoid))
    print("\n今天替你随机摇到:")
    tot_k = tot_p = 0
    for i in combo:
        print(" 🎁 " + fmt(i))
        tot_k += i[1]
        tot_p += i[2]
    if combo:
        print("\n -> 合计约 %dkcal, 蛋白 %dg（组合价为演示估算，实际以 mcd-mcp calculate-price 为准）" % (tot_k, tot_p))
    print("\n* 仅供参考，不构成专业建议；实际餐品/价格以官方实时为准。")


if __name__ == "__main__":
    main()
