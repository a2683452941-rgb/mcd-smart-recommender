---
name: mcd-smart-recommender
description: >-
  Use this skill when a user wants a McDonald's recommendation that combines
  personalized diet guidance with activity/coupon savings, built on the mcd-mcp
  server. It filters items/combos by goal (fat-loss / muscle-gain / low-sugar /
  balanced / children / office), then layers coupons and campaigns, and outputs a
  plan with nutrition table and final price. It also supports creative scenarios:
  points-rescue + lottery loop, kids birthday-party booking, travel landing,
  late-night / mood ordering, and a blind-box random picker.
  Trigger when the user mentions: 麦当劳推荐, 麦麦吃什么, 健身期麦当劳, 减脂套餐,
  增肌点单, 控糖点单, 麦当劳优惠, 麦门省钱, 营养搭配, 麦当劳怎么点划算,
  儿童家庭点单, 带娃吃麦当劳, 宝宝吃什么, 上班族快手, 工作日午餐, 早餐吃什么,
  积分过期, 积分抽奖, 麦金喜, 生日派对, 亲子派对, 麦当劳派对, 出差吃麦当劳,
  旅游落地, 深夜宵夜, 夜宵, 今天好累, 想提神, 盲盒, 摇一摇, 随便推荐.
agent_created: true
---

# 麦麦智选 · 智能饮食 × 活动推荐 Skill

## 概述

本技能把「吃什么（饮食）」和「怎么买最划算（活动）」打通，基于麦当劳官方
`mcd-mcp` 能力，输出一份**带营养表和到手价**的个性化方案，而不是孤立地推套餐或推优惠。

核心差异点在于「结合层」：把饮食引擎筛出的餐品，自动匹配当前可领/可用的券与活动，
用 `calculate-price` 验证叠加后的到手价，给出「最划算组合」。

在基础双引擎之上，本技能还提供一系列**创意情景**（详见 `references/creative_scenarios.md`）：
积分急救 → 抽奖 → 券叠加闭环、亲子派对真实建单、出差旅游落地、深夜/情绪场景、盲盒摇一摇。

## 何时使用

- 用户想基于麦当劳 MCP 做点单/搭配推荐，且希望兼顾饮食目标与省钱。
- 用户表达健身减脂、增肌、控糖、健康饮食等目标，或询问「麦当劳吃什么不长胖 /
  健身怎么点 / 有什么优惠能叠加」。
- 用户想办亲子派对、处理将过期积分、出差落地找店、深夜/情绪化点单，或"随便推荐一份"。
- 用户想要一份包含营养信息和优惠信息的可执行方案。

## 基础工作流程（双引擎 + 结合层）

按以下顺序调用 `mcd-mcp` 工具。所有只读探测优先，下单/领券类动作必须经用户确认。

### Step 1 — 收集用户画像

向用户确认（缺失则给默认值并说明）：
- **目标**：`fat_loss`(减脂) / `muscle_gain`(增肌) / `low_sugar`(控糖) / `balanced`(均衡) / `children`(儿童家庭) / `office`(上班族快手)
- **场景**：早餐 / 午餐 / 下午茶 / 晚餐 / 夜宵(night) / 正餐
- **情景叠加层（可选）**：`mood`(治愈/提神) / `travel`(出差落地) / `blind_box`(摇一摇) —— 见下方「创意情景分支」
- **忌口**：过敏源、宗教、口味（如不要辣、不要猪肉）
- **预算** 与 **取餐方式**：到店自取(beType=1) / 麦乐送(beType=2) / 得来速(beType=5) / 团餐(beType=6)

### Step 2 — 时间与门店

- 调用 `now-time-info` 确定当前日期/星期，用于匹配当日活动日历；其小时字段可触发「深夜宵夜」分支（≥21 点）。
- 调用 `query-nearby-stores`（到店: beType=1, searchType=2, city, keyword；得来速: beType=5）
  返回门店列表，引导用户选择 `storeCode`（得来速/外送还需 `beCode`）。
- 麦乐送场景改用 `delivery-query-stores` + `delivery-create-address`/`delivery-query-addresses`。

### Step 3 — 饮食推荐引擎（核心）

1. 调用 `list-nutrition-foods` 获取营养库（160 项，含能量/蛋白/脂肪/碳水/钠/钙）。
   该结果可本地缓存，作为离线筛选底座（见 `scripts/recommend.py`）。
2. 调用 `query-meals`（storeCode, orderType, beType，得来速/外送补 beCode）拉取该店可点菜单。
3. 依据 `references/nutrition_rules.md` 的阈值，对营养库×菜单做筛选与评分：
   - `fat_loss`：高蛋白(≥20g) + 低热量(≤400kcal) + 低钠(≤700mg)
   - `muscle_gain`：高蛋白(≥25g) + 热量充足(≥400kcal)
   - `low_sugar`：低糖/无糖（优先无糖可乐、美式；规避高糖新地/雪冰）
   - `children`：蛋白 8-22g、热量 150-350kcal、钠 ≤ 500mg，自动排除辣/带骨
   - `office`：蛋白 12-30g、热量 300-500kcal、钠 ≤ 900mg，性价比优先
   - 按场景映射（早餐→麦满分/粥；下午茶→麦旋风/派；夜宵→主食）
   - 剔除用户忌口，输出 Top 候选餐品与组合。
4. 对候选组合调用 `query-meal-detail` 补全细节，必要时引用 `query-meal-assistance`（官方饮食助手）。
5. 调用 `calculate-price` 计算组合原价。

### Step 4 — 活动推荐引擎

并行/依次调用，收集可叠加的省钱机会：
- `campaign-calendar`：按日期匹配正在进行的活动
- `query-promotions`：当前促销（仅企业团餐 beType=6）
- `available-coupons`：麦麦省可领券（已领/可领取）
- `query-store-coupons`：门店券
- `query-survey-coupon`：问卷券（需用户提供 orderId）
- `query-lottery-info` / `draw-lottery`：抽奖活动（draw **必须**用户确认）
- `query-my-coupons`：已持有券

### Step 5 — 结合层 · 省钱匹配

- 将 Step 3 的餐品组合，与 Step 4 的券/活动做交叉匹配，筛选可叠加项。
- 注意 `available-coupons` 只返回券名，**无 couponCode**；要把券传到 `calculate-price` 需经券详情取 `couponCode` 后二次算价（标准动作）。
- 用 `calculate-price` 验证叠加后的到手价，计算「省了多少」。
- 输出**最优组合**（营养达标 + 到手价最低），并标注每一张券的领取/使用路径。

### Step 6 — 输出方案卡

以清晰结构输出：
1. 推荐餐品组合 + 营养表（热量/蛋白/脂肪/碳水/钠）
2. 当前可享优惠（券名 + 状态 + 怎么领）
3. 叠加后到手价 vs 原价（省 ¥X）
4. 取餐方式与该门店信息
5. 免责声明：仅供参考，不构成专业建议；以官方实时结果为准

---

## 创意情景分支

下列情景在基础流程之上叠加，**完整字段/入参见 `references/creative_scenarios.md`**。

### ① 积分急救 → 抽奖 → 券叠加闭环（旗舰）

把"抽奖"变成"省钱方案"的一环，用真实的过期积分做钩子。
1. `query-my-account` → 读 `availablePoint` / `currentMouthExpirePoint` / `nextMouthExpirePoint`。
2. 本地决策引擎 `scripts/integral_rescue.py` → 判断是否建议抽奖 / 尽快消耗。
3. `query-lottery-info` → 展示 `drawDecision.nextConsumption`（消耗积分/次数）与奖池；**严禁**根据 `availableTimes` 自行推断能否抽。
4. **向用户展示消耗与剩余，获得明确确认后**才调用 `draw-lottery`（严禁自动抽、试抽、连续抽）。
5. 中奖券（如「麦辣鸡腿汉堡5折券」）回到**结合层**（Step 5），与饮食引擎餐品重新组合 → `calculate-price` 实算到手价。
- 真实锚点（2026-10-17 实测）：可用 43.2 / 本月将过期 13.5；「周六麦金喜」24 积分/次，奖池含积分霸王餐、麦辣鸡腿堡5折券等 19+ 项。

### ② 亲子派对策划（真实建单，备选旗舰）

唯一"真的帮你建单/预约"的能力，演示冲击力最强；**建单是真实交易，必须逐步确认**。
1. `mall-points-products`（`catRuleIds=1>6>20` 生日类 / `1>6>21` 主题类）→ 取 `spuId`。
2. `query-party-city(spuId)` → 取城市 `code` + 经纬度。
3. `query-party-store(code, lat, long, spuId)` → 取可办门店 `storeCode`。
4. `query-party-store-date(storeCode)` → 取可约日期 `dateStr`。
5. `query-party-store-session(storeCode, dateStr)` → 取场次 `id/timeStart/timeEnd/leftNum`。
6. `mall-product-detail(spuId)` → 取 `skuId`，确认 `shopId=5`。
7. `party-order-create(...)` → 每步完成后**等用户明确选择**，最后引导用户说"创建订单"再下单。
- 组合：派对套餐可叠加 `children` 目标出"儿童友好餐品建议"。
- 真实锚点（2026-10-17 实测）：生日类 spuId `8516`（一起开心鸭尊享版，¥138，shopId=5）；上海 `code=310100` → 最近门店「黄浦华旭国际大厦餐厅」`1450713`（415m，营业中）。

### ③ 出差旅游落地推荐（必做）

1. `now-time-info` 或用户告知目的地 → `query-nearby-stores(keyword=目的地, city=目的地)` 取最近 `storeCode`。
2. `query-meals(storeCode)` 当期在售餐品与价格。
3. `campaign-calendar` 当期活动（如 9.9 元早餐两件套、龙焰鸡腿堡新品）做话题钩子。
4. 饮食引擎按目标筛餐 → `calculate-price` 算价。

### ④ 情绪治愈 / 提神决策（必做）

- **治愈系**（累/emo/犒劳/开心）：麦旋风、新地、派、玉米杯、麦乐鸡（分享）；允许适度"放纵"但仍标注热量。
- **提神系**（困/加班/早起/考试）：美式/鲜萃咖啡、无糖可乐、麦满分高蛋白早餐。
- 触发词：累、困、加班、犒劳、开心、学不进去、早起。

### ⑤ 深夜宵夜场景（必做）

`now-time-info` 小时 ≥ 21 → 主推热食（粥、汉堡、热红茶/咖啡），**规避冰饮与大份甜品**；偏向低负担组合（合计 ≤ 600kcal）。`SCENE_MAP["night"]` 已含 汉堡/粥/红茶/咖啡。

### ⑨ 盲盒随机推荐 · 摇一摇（顺手做）

用户给约束但不想自己选时：`scripts/blind_box.py` 复用 `recommend.py` 的 `NUTRITION`/`recommend()`，
按目标筛分后在 Top 候选里**分桶随机**（主/副/饮各取其一），保证"随机但不离谱"。
用法：`python scripts/blind_box.py --goal muscle_gain --scene lunch --avoid 猪,辣 [--seed N]`。

---

## 关键规则摘要

详细阈值、场景映射与组合搭配价规则见 `references/nutrition_rules.md`。
组合搭配价规则（企业团餐/搭配参考，来自 `query-meals`）：
20 元以下→小食；20-30→汉堡+小食或汉堡+饮料；30-40→汉堡+薯条/小食+饮料；
40-50→汉堡+薯条+小食+饮料；50 以上→丰富组合优先不重复小食。

## 示例对话

**例1（基础双引擎）**
用户：我是增肌期，今天午餐想吃点高蛋白的，附近有店吗？顺便看有什么优惠。
→ Step2 查门店 → Step3 按 muscle_gain 筛高蛋白组合并算原价
→ Step4 拉可领券/活动 → Step5 叠加算到手价 → Step6 输出方案卡。

**例2（积分急救旗舰）**
用户：我积分是不是快过期了？
→ query-my-account（本月将过期 13.5）→ integral_rescue.py 诊断建议抽奖
→ query-lottery-info 展示消耗 24 分/次 + 奖池 → 用户确认 → draw-lottery
→ 中奖券回结合层 × 增肌午餐 → calculate-price 实算到手价。

**例3（亲子派对）**
用户：想给孩子办个麦当劳生日派对，上海能办吗？
→ mall-points-products(生日类) 取 spuId 8516 → query-party-city 取 310100
→ query-party-store 取 1450713 → 引导选日期/场次 → 逐步确认 → party-order-create。

**例4（盲盒）**
用户：增肌午餐，帮我随便摇一份，别太辣。
→ blind_box.py --goal muscle_gain --scene lunch --avoid 辣 → 随机但合规的组合。

## 注意事项

- 仅使用环境变量占位符承载 Token，绝不在输出或文件中泄露真实 Token/密钥。
- 写操作必须经用户显式确认：`create-order`、`auto-bind-coupons`、`draw-lottery`、`party-order-create`。
- `draw-lottery` 约束：必须先展示 `query-lottery-info` 的 `drawDecision.nextConsumption` 与剩余，获明确确认；严禁试抽/自动抽/连续抽；频次限制以服务端返回为准。
- `party-order-create` 约束：仅 `shopId=5` 可建；每步完成后等用户选择，不得跳步；最后引导"创建订单"再下单。
- 输出须含免责声明：非官方产品，不构成医疗/营养专业建议。
- 餐品、价格、供应状态以 `mcd-mcp` 实时返回为准。
