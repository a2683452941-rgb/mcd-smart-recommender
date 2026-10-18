# 麦麦智选 · 创意情景总览

> 本文件汇总「麦麦智选」所有可拓展的创意情景，作为 `SKILL.md` 工作流的详细补充。
> 优先级来自产品矩阵评估（横轴=落地成本，纵轴=吸 Star 潜力）：**左上角（低成本·高潜力）优先做**。

## 情景矩阵（速查）

| # | 情景 | 簇 | 落地成本 | 吸Star潜力 | 优先级 |
|---|------|----|---------|-----------|--------|
| ① | 积分急救 → 抽奖 → 券叠加闭环 | 游戏化 | 低 | 高 | 🔥 旗舰 |
| ② | 亲子派对策划（真实建单） | 社交 | 中 | 高 | ⭐ 备选旗舰 |
| ③ | 出差旅游落地推荐 | 时空 | 低 | 中高 | 必做 |
| ④ | 情绪治愈 / 提神决策 | 游戏化 | 低 | 中 | 必做 |
| ⑤ | 深夜宵夜场景 | 时空 | 低 | 中 | 必做 |
| ⑥ | 聚餐分摊算账 | 社交 | 中 | 中 | 应做 |
| ⑦ | 麦门日记周报 | 数据 | 高 | 中 | 暂不做 |
| ⑧ | 权益卡划算测算 | 会员 | 中 | 低中 | 暂不做 |
| ⑨ | 盲盒随机推荐（摇一摇） | 游戏化 | 极低 | 中 | 顺手做 |

---

## ① 积分急救 → 抽奖 → 券叠加闭环（旗舰）

**痛点**：用户积分悄悄过期，没人提醒；抽奖是孤立玩法，和"点什么"脱节。

**工作流**
1. `query-my-account` → 读取 `availablePoint` / `currentMouthExpirePoint` / `nextMouthExpirePoint`
2. 本地决策引擎 `scripts/integral_rescue.py` → 判断是否建议抽奖 / 尽快消耗
3. `query-lottery-info` → 展示 `drawDecision.nextConsumption`（消耗积分/次数）与奖池
4. **必须等用户明确确认** → `draw-lottery`（严禁自动抽、严禁试抽）
5. 中奖券（如「麦辣鸡腿汉堡5折券」）回到**结合层**，与饮食引擎筛出的餐品重新组合
6. `calculate-price` → 实算叠加后的到手价

**真实锚点**（2026-10-17 实测）：可用 43.2 / 本月将过期 13.5；抽奖活动「周六麦金喜」24 积分/次，奖池含积分霸王餐、麦辣鸡腿堡5折券等 19+ 项。

**差异化**：把"抽奖"从孤立玩法变成"省钱方案"的一环；用真实的过期积分做钩子，故事感强、演示顺。

---

## ② 亲子派对策划（备选旗舰，真实建单）

**痛点**：家长想给孩子办麦当劳生日/主题派对，但不知道哪些城市/门店能办、怎么下单。

**工作流（严格分步，每步等用户选择）**
1. `mall-points-products`（`catRuleIds=1>6>20` 生日类 / `1>6>21` 主题类）→ 取 `spuId`
2. `query-party-city(spuId)` → 取城市 `code` + 经纬度
3. `query-party-store(code, lat, long, spuId)` → 取可办门店 `storeCode`
4. `query-party-store-date(storeCode)` → 取可约日期 `dateStr`
5. `query-party-store-session(storeCode, dateStr)` → 取场次 `id/timeStart/timeEnd/leftNum`
6. `mall-product-detail(spuId)` → 取 `skuId`，确认 `shopId=5`
7. `party-order-create(...)` → **引导用户说"创建订单"后下单**

**真实锚点**（2026-10-17 实测）：生日类派对 spuId `8516`（一起开心鸭尊享版，¥138，shopId=5）；上海 `code=310100` → 最近门店「黄浦华旭国际大厦餐厅」`storeCode=1450713`（415m，营业中）。

**差异化**：唯一一个"真的帮你建单/预约"的能力，演示冲击力最强。**注意**：建单是真实交易，必须经用户确认且逐步进行。

**组合**：派对套餐可再叠加 `children` 目标（见 `references/nutrition_rules.md`）出"儿童友好餐品建议"。

---

## ③ 出差旅游落地推荐（必做）

**痛点**：到了陌生城市，不知道附近哪家麦当劳、有什么当地限定/当期活动。

**工作流**
1. `now-time-info` → 确定当前城市/日期（或用户告知目的地）
2. `query-nearby-stores(keyword=目的地, city=目的地)` → 取最近 `storeCode`
3. `query-meals(storeCode)` → 当期在售餐品与价格
4. `campaign-calendar` → 当期活动（如 9.9 元早餐两件套、龙焰鸡腿堡新品）
5. 饮食引擎按用户目标筛餐品 → `calculate-price` 算价

**真实锚点**：`campaign-calendar` 返回当期 9.9 元早餐两件套、蓝莓爆爆珠麦旋风上新、龙焰鸡腿堡韩式风味系列等。

---

## ④ 情绪治愈 / 提神决策（必做）

**痛点**：用户不想做理性选择，只想"今天累/开心/困"时有人替他点。

**两类分支**
- **治愈系**（累/emo/犒劳）：麦旋风、新地、派、玉米杯等轻甜慰藉 → 偏向 `low_sugar` 外的"心情价值"餐品
- **提神系**（困/加班/早起）：美式/鲜萃咖啡、无糖可乐、麦满分高蛋白早餐

**工作流**：识别情绪关键词 → 映射到餐品簇 → 结合 `now-time-info` 时段限制（如深夜不推冰饮）→ 出方案。

---

## ⑤ 深夜宵夜场景（必做）

**痛点**：22 点后想吃但怕太冰/太重。

**规则**：`now-time-info` 小时 ≥ 21 → 主推热食（粥、汉堡、热红茶/咖啡），**规避冰饮与大份甜品**；偏向低负担组合。

---

## ⑥ 聚餐分摊算账（应做）

**痛点**：多人聚餐不知道怎么点最划算、人均多少。

**工作流**：用户给人数 N + 目标 → 饮食引擎出组合 × N → `calculate-price` 算总价 → 人均 + 可用券最优（叠加 `available-coupons` / `query-store-coupons`）。

---

## ⑦ 麦门日记周报（暂不做）

本地轻量记录每次推荐选择，生成周报（营养/花费/省钱）。成本高、对吸 Star 帮助有限，作为长期迭代项。

---

## ⑧ 权益卡划算测算（暂不做）

基于 `query-my-account` 与活动数据，测算麦金卡/学期卡是否值得开。需要较复杂的回本计算，性价比低，暂缓。

---

## ⑨ 盲盒随机推荐 · 摇一摇（顺手做）

**痛点**：纠结星人给约束但不想自己选。

**实现**：`scripts/blind_box.py` 复用 `recommend.py` 的 `NUTRITION`/`recommend()`，按目标筛分后**在 Top 候选里随机成组**，保证"随机但不离谱"。极低成本、好玩、适合 GIF 演示。

**示例**
```bash
python scripts/blind_box.py --goal muscle_gain --scene lunch --avoid 猪,辣 --seed 7
```

---

## 已验证的真实 MCP 能力清单（2026-10-17 探活）

| 工具 | 状态 | 用途 |
|------|------|------|
| `query-my-account` | ✅ | 积分账户（可用/将过期） |
| `query-lottery-info` / `draw-lottery` | ✅ | 积分抽奖（含严格确认约束） |
| `mall-points-products` / `mall-product-detail` | ✅ | 积分商城商品 / spuId+skuId |
| `query-party-city` / `query-party-store` | ✅ | 派对城市与门店 |
| `campaign-calendar` | ✅ | 当期营销活动 |
| `query-nearby-stores` / `query-meals` / `calculate-price` | ✅ | 门店/菜单/算价 |
| `available-coupons` / `list-nutrition-foods` / `now-time-info` | ✅ | 券/营养库/时间 |
