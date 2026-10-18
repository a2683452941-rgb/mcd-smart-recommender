#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦智选 · 饮食推荐引擎（确定性可运行版）

基于 mcd-mcp `list-nutrition-foods` 返回的营养结构（能量/蛋白/脂肪/碳水/钠/钙），
按用户目标（减脂/增肌/控糖/均衡）做筛选与评分，并给出组合建议。
规则阈值见仓库 references/nutrition_rules.md。

用法:
  python recommend.py --goal muscle_gain --scene lunch --avoid 猪,辣 --top 10
  python recommend.py --goal fat_loss
  python recommend.py --goal low_sugar --scene afternoon

注意: 本脚本为离线演示引擎，真实餐品/价格/供应以 mcd-mcp 实时返回为准。
"""

import argparse

# 数据集: (名称, 热量kcal, 蛋白g, 脂肪g, 碳水g, 钠mg, 钙mg)
# 取自 mcd-mcp list-nutrition-foods 的结构化样本（数值为真实量级，用于演示）。
NUTRITION = [
    ("猪柳麦满分", 308, 16, 16, 24, 781, 213),
    ("猪柳蛋麦满分", 387, 23, 21, 25, 846, 243),
    ("烟肉蛋麦满分", 260, 16, 10, 24, 483, 238),
    ("火腿扒麦满分", 261, 14, 12, 24, 608, 131),
    ("中薯条", 289, 4, 12, 38, 165, 18),
    ("大薯条", 379, 6, 16, 50, 216, 23),
    ("小薯条", 210, 3, 9, 28, 120, 13),
    ("圆筒冰淇淋", 93, 2, 3, 14, 36, 77),
    ("麦乐鸡5块", 213, 12, 12, 13, 422, 9),
    ("麦辣鸡翅-2块", 224, 13, 15, 9, 537, 13),
    ("吉士汉堡包", 294, 16, 12, 30, 673, 144),
    ("双层吉士汉堡", 429, 27, 22, 31, 1017, 232),
    ("麦香鸡", 369, 15, 17, 39, 731, 73),
    ("麦香鱼", 325, 16, 13, 35, 556, 99),
    ("麦辣鸡腿汉堡", 485, 24, 24, 42, 1208, 154),
    ("板烧鸡腿堡", 391, 23, 17, 35, 1041, 93),
    ("巨无霸", 513, 27, 26, 42, 961, 171),
    ("培根蔬萃双层牛堡", 442, 24, 23, 34, 728, 73),
    ("可乐中杯", 147, 0, 0, 36, 0, 10),
    ("可乐大杯", 224, 0, 0, 55, 15, 15),
    ("无糖可口可乐中杯", 0, 0, 0, 1, 35, 0),
    ("雪碧中杯", 105, 0, 0, 26, 29, 0),
    ("大杯鲜萃咖啡", 13, 1, 0, 0, 3, 8),
    ("小杯鲜萃咖啡", 15, 1, 3, 2, 6, 6),
    ("锡兰红茶", 2, 0, 0, 0, 5, 5),
    ("纯牛奶（盒装）", 129, 7, 7, 10, 73, 231),
    ("麦旋酷阳光橙", 228, 1, 2, 50, 77, 52),
    ("脆薯饼", 146, 1, 9, 14, 311, 7),
    ("脆香油条", 202, 5, 12, 19, 230, 18),
    ("100%苹果汁", 88, 0, 0, 21, 0, 0),
    ("汉堡包", 248, 13, 8, 29, 492, 61),
    ("麦乐鸡4块", 170, 10, 10, 11, 337, 7),
    ("苹果片", 32, 0, 0, 7, 0, 18),
    ("不素之霸双层牛堡", 493, 28, 27, 34, 1012, 75),
    ("双层深海鳕鱼堡", 485, 28, 21, 46, 917, 147),
    ("儿童鱼排堡", 269, 15, 6, 36, 442, 58),
    ("培根安格斯厚牛堡", 707, 34, 44, 43, 1037, 161),
    ("芝士安格斯厚牛堡", 696, 32, 44, 43, 897, 150),
    ("皮蛋鸡肉粥", 133, 6, 3, 20, 611, 20),
    ("雪菜脆笋鸡肉粥", 120, 4, 2, 22, 552, 14),
    ("麦麦脆汁鸡-琵琶腿", 328, 21, 20, 16, 905, 24),
    ("麦麦脆汁鸡-带骨里脊", 332, 22, 18, 16, 812, 25),
    ("奥利奥麦旋风", 266, 5, 9, 40, 116, 185),
    ("草莓新地", 245, 4, 6, 43, 84, 158),
    ("香芋派", 232, 2, 12, 28, 159, 7),
    ("菠萝派", 221, 2, 11, 27, 147, 5),
    ("德式图林根香肠", 87, 5, 6, 2, 293, 5),
    ("优品豆浆大杯", 202, 8, 4, 33, 43, 21),
    ("优品豆浆小杯", 151, 6, 3, 25, 32, 15),
    ("玉米杯大杯", 87, 4, 1, 12, 2, 10),
    ("玉米杯小杯", 53, 2, 1, 7, 1, 6),
    ("柠檬拉明顿", 121, 2, 7, 12, 35, 17),
    ("薄皮焦香V翅", 192, 17, 11, 6, 594, 15),
    ("麦麦趣鸡球", 266, 17, 13, 19, 789, 13),
]

SCENE_MAP = {
    "breakfast": ["麦满分", "粥", "豆浆", "鲜萃", "油条", "薯饼"],
    "lunch": ["汉堡", "薯条", "可乐", "鸡", "鱼", "堡"],
    "afternoon": ["麦旋风", "新地", "派", "玉米杯", "麦乐鸡", "鸡球"],
    "dinner": ["汉堡", "堡", "粥", "鸡", "鱼"],
    "night": ["汉堡", "粥", "红茶", "咖啡"],
    "post_workout": ["汉堡", "鸡", "鱼", "堡", "可乐"],
}


def passes_avoid(name, avoid):
    if not avoid:
        return True
    return not any(k in name for k in avoid)


def is_dessert(name):
    return any(k in name for k in ["新地", "雪冰", "麦旋风", "派", "汁", "拉明顿"])


def score(item, goal):
    name, kcal, protein, fat, carb, sodium, calcium = item
    s = 0
    if goal == "fat_loss":
        if protein >= 20:
            s += 40
        elif protein >= 12:
            s += 20
        s += 30 if kcal <= 400 else max(0, 30 - (kcal - 400) // 20)
        s += 15 if sodium <= 700 else max(0, 15 - (sodium - 700) // 100)
    elif goal == "muscle_gain":
        if protein >= 25:
            s += 40
        elif protein >= 18:
            s += 25
        s += 30 if kcal >= 400 else max(0, 30 - (400 - kcal) // 20)
        s += 10 if sodium <= 1000 else 0
    elif goal == "low_sugar":
        if is_dessert(name):
            s -= 30
        if any(k in name for k in ["无糖", "红茶", "鲜萃", "咖啡", "苹果片", "玉米杯"]):
            s += 25
        s += 15 if protein >= 10 else 0
        s += 10 if sodium <= 800 else 0
    elif goal == "children":
        if any(k in name for k in ["辣", "带骨", "麦辣", "香辣", "椒", "辣翅"]):
            return 0
        if sodium <= 500:
            s += 30
        elif sodium <= 800:
            s += 15
        else:
            s -= 10
        if 8 <= protein <= 22:
            s += 25
        if 150 <= kcal <= 350:
            s += 20
        if any(k in name for k in ["鱼排", "麦乐鸡", "玉米杯", "苹果片",
                                   "纯牛奶", "豆浆", "小薯条", "汉堡包",
                                   "麦香鱼", "粥", "麦满分"]):
            s += 15
    elif goal == "office":
        if 12 <= protein <= 30:
            s += 20
        if 300 <= kcal <= 500:
            s += 20
        if sodium <= 900:
            s += 10
        if any(k in name for k in ["麦满分", "粥", "汉堡", "板烧",
                                   "吉士", "咖啡", "豆浆", "薯条"]):
            s += 15
        if kcal > 600:
            s -= 10
    else:  # balanced
        if 10 <= protein <= 30:
            s += 25
        if 300 <= kcal <= 600:
            s += 25
        s += 15 if sodium <= 800 else 0
    return max(0, s)


def recommend(goal, scene, avoid, top):
    items = [i for i in NUTRITION if passes_avoid(i[0], avoid)]
    scored = [(score(i, goal), i) for i in items]
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [i for _, i in scored if _ > 0][:top]
    return picked


def is_drink(name):
    return any(k in name for k in ["可乐", "雪碧", "咖啡", "红茶", "豆浆", "汁", "牛奶", "奶铁", "奶"])


def build_combo(picked):
    drinks = [i for i in picked if is_drink(i[0])]
    mains = [i for i in picked
             if any(k in i[0] for k in ["堡", "麦满分", "粥", "鸡", "鱼", "汉堡", "卷"])
             and not is_drink(i[0])]
    sides = [i for i in picked
             if any(k in i[0] for k in ["薯条", "玉米杯", "苹果片", "麦乐鸡", "鸡球", "派", "新地", "麦旋风"])
             and not is_drink(i[0])]
    main = mains[0] if mains else next((i for i in picked if not is_drink(i[0])), None)
    side = sides[0] if sides else None
    drink = drinks[0] if drinks else None
    seen, combo = set(), []
    for x in [main, side, drink]:
        if x and x[0] not in seen:
            seen.add(x[0])
            combo.append(x)
    return combo


def fmt(item):
    name, kcal, protein, fat, carb, sodium, calcium = item
    return f"{name:12s} {kcal:>4}kcal  蛋白{protein:>2}g  脂肪{fat:>2}g  碳水{carb:>2}g  钠{sodium:>4}mg"


def main():
    ap = argparse.ArgumentParser(description="麦麦智选 饮食推荐引擎")
    ap.add_argument("--goal", default="balanced",
                    choices=["fat_loss", "muscle_gain", "low_sugar",
                             "balanced", "children", "office"])
    ap.add_argument("--scene", default=None,
                    choices=list(SCENE_MAP.keys()))
    ap.add_argument("--avoid", default="", help="忌口关键词，逗号分隔，如 猪,辣,鱼")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    avoid = [a.strip() for a in args.avoid.split(",") if a.strip()]
    goal_cn = {"fat_loss": "减脂", "muscle_gain": "增肌",
               "low_sugar": "控糖", "balanced": "均衡",
               "children": "儿童家庭", "office": "上班族快手"}[args.goal]

    picked = recommend(args.goal, args.scene, avoid, args.top)
    # 场景加权
    if args.scene:
        kw = SCENE_MAP[args.scene]
        picked.sort(key=lambda i: sum(k in i[0] for k in kw), reverse=True)

    print(f"=== 麦麦智选 · {goal_cn}推荐 (场景:{args.scene or '不限'}) ===")
    if avoid:
        print(f"已剔除忌口: {', '.join(avoid)}")
    print(f"\n[Top {len(picked)} 推荐餐品]")
    for i in picked:
        print(" " + fmt(i))

    print("\n[示例组合]")
    combo = build_combo(picked)
    tot_k, tot_p = 0, 0
    for i in combo:
        print(" + " + fmt(i))
        tot_k += i[1]
        tot_p += i[2]
    if combo:
        print(f"  -> 合计约 {tot_k}kcal, 蛋白 {tot_p}g（组合价为演示估算，实际以 mcd-mcp calculate-price 为准）")
    print("\n* 仅供参考，不构成专业营养建议；实际餐品/价格以官方实时结果为准。")


if __name__ == "__main__":
    main()
