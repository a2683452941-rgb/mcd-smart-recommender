# MCP 集成说明（MCP_INTEGRATION.md）

本文件说明「麦麦智选」实际使用的麦当劳 MCP Server、调用的 Tool、调用流程与业务价值。

## 1. 使用的 MCP Server

| 项 | 值 |
|----|----|
| Server 名 | `mcd-mcp` |
| 传输协议 | Streamable HTTP（`streamablehttp`） |
| 接入地址 | `https://mcp.mcd.cn` |
| 鉴权方式 | `Authorization: Bearer <MCD_MCP_TOKEN>`（Token 在麦当劳控制台「激活」后获取） |
| 配置示例 | 见仓库 `mcp-config.example.json`（仅环境变量占位，无真实密钥） |

## 2. 实际使用的 Tool 与职责

### 饮食推荐引擎

| Tool | 用途 | 在流程中的角色 |
|------|------|----------------|
| `list-nutrition-foods` | 160 项餐品营养库（能量/蛋白/脂肪/碳水/钠/钙） | 离线筛选底座，按目标阈值打分 |
| `query-meals` | 按门店+场景拉取可点菜单 | 获取该店实际可点餐品 |
| `query-meal-detail` | 候选餐品详情 | 补全营养/规格细节 |
| `query-meal-assistance` | 官方饮食助手建议 | 增强饮食说明的专业性 |
| `calculate-price` | 组合算价 | 计算组合原价，供结合层比对 |

### 活动推荐引擎

| Tool | 用途 | 在流程中的角色 |
|------|------|----------------|
| `campaign-calendar` | 按日期活动日历 | 匹配当日进行中的活动 |
| `query-promotions` | 当前促销 | 活动层面的优惠 |
| `available-coupons` | 麦麦省可领券（已领/可领取） | 用户可叠加的券 |
| `query-store-coupons` | 门店券 | 门店级优惠 |
| `query-survey-coupon` | 问卷券 | 额外可领券 |
| `query-lottery-info` / `draw-lottery` | 抽奖活动信息 / 参与抽奖 | 活动玩法（draw 需用户确认） |
| `query-my-coupons` | 已持有券 | 直接可用的券 |

### 支撑类

| Tool | 用途 |
|------|------|
| `now-time-info` | 获取当前日期/星期，决定活动日历匹配 |
| `query-nearby-stores` / `delivery-query-stores` | 到店/外送门店查询 |
| `query-my-account` | 积分账户（可选展示） |
| `create-order` / `mall-*` / `party-*` | 下单/商城/派对（可选，须经用户确认） |

## 3. 调用流程

```
用户画像(目标/场景/忌口/预算/取餐方式)
   │
   ├─ now-time-info → query-nearby-stores(delivery-query-stores)   [时间+门店]
   │
   ├─ 饮食推荐引擎
   │     list-nutrition-foods → query-meals → (筛选/评分) → query-meal-detail
   │     → calculate-price(原价)
   │
   ├─ 活动推荐引擎（并行）
   │     campaign-calendar + query-promotions + available-coupons
   │     + query-store-coupons + query-survey-coupon + query-lottery-info
   │     + query-my-coupons
   │
   ├─ 结合层：餐品×券/活动 交叉匹配 → calculate-price(到手价) → 最划算组合
   │
   └─ 输出方案卡（餐品+营养表+可享优惠+到手价+取餐信息+免责声明）
```

## 4. 业务价值

- **个性化**：把「吃什么」从泛套餐升级为按健身/控糖目标定制，解决「想吃麦当劳又怕不健康」的痛点。
- **省钱闭环**：不是孤立推优惠，而是把券/活动精准叠加到用户真正会点的餐品上，给出到手价与节省金额，提升转化与获得感。
- **双引擎可独立运行也可融合**：饮食引擎与活动引擎解耦，便于扩展更多场景（儿童/家庭、上班族快手等）。
- **合规安全**：写操作（下单、领券、抽奖）全部走用户确认；Token 仅以环境变量占位，无密钥泄露风险。
