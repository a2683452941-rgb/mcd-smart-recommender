#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦智选 · 积分急救决策引擎（确定性可运行版）

输入用户积分账户快照 + 抽奖活动信息，输出"本月将过期积分如何最优消耗"的
决策建议。该脚本是 SKILL 中「积分急救 → 抽奖 → 券叠加」闭环的本地决策大脑，
真实数据来自 mcd-mcp 的 query-my-account 与 query-lottery-info。

用法:
  python integral_rescue.py --available 43.2 --expire-now 13.5 --expire-next 0 \
      --draw-point 24 --prizes "积分霸王餐,麦辣鸡腿汉堡5折券,下单立减3元券"

  # 也可直接读一段 JSON 快照
  echo '{"available":43.2,"expire_now":13.5,"draw_point":24,"prizes":[...]}' \
      | python integral_rescue.py --json -

注意: 本脚本只做决策建议，不调用任何 MCP；真实抽奖需经 query-lottery-info
展示消耗并由用户确认后，再由 WorkBuddy 调用 draw-lottery。
"""

import argparse
import json
import sys


def parse_args():
    ap = argparse.ArgumentParser(description="麦麦智选 积分急救决策引擎")
    ap.add_argument("--available", type=float, default=0.0, help="可用积分")
    ap.add_argument("--expire-now", type=float, default=0.0, help="本月将过期积分")
    ap.add_argument("--expire-next", type=float, default=0.0, help="下月将过期积分")
    ap.add_argument("--draw-point", type=float, default=0.0, help="单次抽奖消耗积分")
    ap.add_argument("--prizes", default="", help="奖池名称，逗号分隔")
    ap.add_argument("--json", default=None,
                    help="从文件或 '-' 读取 JSON 快照 {available,expire_now,...}")
    return ap.parse_args()


def load_snapshot(args):
    if args.json:
        raw = sys.stdin.read() if args.json == "-" else open(args.json, encoding="utf-8").read()
        d = json.loads(raw)
        return {
            "available": float(d.get("available", 0)),
            "expire_now": float(d.get("expire_now", 0)),
            "expire_next": float(d.get("expire_next", 0)),
            "draw_point": float(d.get("draw_point", 0)),
            "prizes": d.get("prizes", []),
        }
    prizes = [p.strip() for p in args.prizes.split(",") if p.strip()]
    return {
        "available": args.available,
        "expire_now": args.expire_now,
        "expire_next": args.expire_next,
        "draw_point": args.draw_point,
        "prizes": prizes,
    }


# 粗略估算一张券的"到手价值"，仅用于决策排序，非官方口径
def estimate_coupon_value(name):
    n = name
    if "霸王餐" in n:
        return 30.0
    if "折" in n:  # 5折/4折/6折 等
        return 8.0
    if "立减" in n:
        m = ""
        for ch in n:
            if ch.isdigit():
                m += ch
        return float(m) if m else 3.0
    if "会员积分" in n:
        return 1.0
    if "卡" in n or "券" in n:
        return 3.0
    return 2.0


def decide(snap):
    available = snap["available"]
    expire_now = snap["expire_now"]
    expire_next = snap["expire_next"]
    draw_point = snap["draw_point"]
    prizes = snap["prizes"]

    urgent = expire_now > 0
    lottery_ok = draw_point > 0 and available >= draw_point

    # 抽奖预期：取奖池里价值最高的几张作为"期望值"上界参考
    ranked = sorted(prizes, key=estimate_coupon_value, reverse=True) if prizes else []
    top_value = estimate_coupon_value(ranked[0]) if ranked else 0.0

    options = []
    if lottery_ok:
        options.append({
            "action": "lottery",
            "title": "积分抽奖（消耗 %g 积分/次）" % draw_point,
            "detail": "奖池含 %d 项，最高价值参考约 ¥%.1f（如%s）；"
                      "适合用「将过期积分」去搏一把，不亏本。" % (
                          len(prizes), top_value, ranked[0] if ranked else "优惠券"),
            "cost_point": draw_point,
            "expected_value": top_value,
        })
    if expire_now > 0:
        options.append({
            "action": "spend_soon",
            "title": "月底前尽快消耗将过期积分（%g 分）" % expire_now,
            "detail": "可通过点餐攒/用积分，或在积分商城兑换实物/券，避免清零。",
            "cost_point": expire_now,
            "expected_value": 0.0,
        })
    options.append({
        "action": "hold",
        "title": "保留积分",
        "detail": "若无可过期积分且无意抽奖，可累积用于麦金卡/学期卡等大额兑换。",
        "cost_point": 0.0,
        "expected_value": 0.0,
    })

    # 推荐优先级：将过期且能抽奖 -> 直接抽；将过期不能抽 -> 尽快消耗；否则按需
    if urgent and lottery_ok:
        recommended = "lottery"
        reason = "你本月有 %g 积分将过期，且可用积分足够抽一次（%g 分），" \
                 "用将过期积分抽奖最划算：不花『干净积分』还能搏优惠券。" % (expire_now, draw_point)
    elif urgent:
        recommended = "spend_soon"
        reason = "你本月有 %g 积分将过期，但可用积分不足一次抽奖（需 %g 分），" \
                 "建议月底前通过点餐/积分商城尽快消耗。" % (expire_now, draw_point)
    else:
        recommended = "hold"
        reason = "当前无可过期积分，可按需保留或参与抽奖娱乐。"

    return {
        "urgent": urgent,
        "expire_now": expire_now,
        "expire_next": expire_next,
        "available": available,
        "lottery_ok": lottery_ok,
        "recommended": recommended,
        "reason": reason,
        "options": options,
    }


def main():
    args = parse_args()
    snap = load_snapshot(args)
    result = decide(snap)

    print("=== 麦麦智选 · 积分急救诊断 ===")
    print("可用积分: %g | 本月将过期: %g | 下月将过期: %g | 抽奖消耗: %g/次"
          % (result["available"], result["expire_now"],
             result["expire_next"], snap["draw_point"]))
    print("\n[诊断]")
    print(" " + result["reason"])
    print("\n[可选动作]")
    for o in result["options"]:
        print(" - %s：%s" % (o["title"], o["detail"]))
    print("\n[建议] 优先执行 → %s" % result["recommended"])
    print("* 仅供参考；真实抽奖须由 query-lottery-info 展示消耗并经你确认后执行。")

    # 同时输出机器可读 JSON，便于 Skill 解析
    print("\n---JSON---")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
