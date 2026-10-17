# workbuddy.md

> 本文件为使用腾讯 WorkBuddy 智能体开发「麦麦智选」的对话上下文导出，
> 用于核验本项目真实使用了 WorkBuddy（参与 WorkBuddy 专项奖励所需）。
> 正式提交前，可在 WorkBuddy 中重新导出本会话上下文覆盖此文件。

## 开发上下文摘要（WorkBuddy 智能体协助记录）

- **MCP 连通性验证**：通过 WorkBuddy 调用 `mcd-mcp` 的 `now-time-info`、
  `available-coupons`、`list-nutrition-foods` 三个只读工具实测，确认 Token 有效、链路通畅。
- **方案设计**：在 WorkBuddy 中产出系统架构图与「双引擎（饮食/活动）+ 结合层」方案，
  明确 MCP 工具映射与核心推荐逻辑。
- **交付形态决策**：经与用户确认，确定交付形态为 WorkBuddy Skill，饮食引擎优先覆盖
  「健身减脂/增肌」与「控糖/健康饮食」。
- **项目搭建**：由 WorkBuddy 生成 `SKILL.md`、`README.md`、`MCP_INTEGRATION.md`、
  `mcp-config.example.json`、`references/nutrition_rules.md`、`scripts/recommend.py`、
  `examples/sample_session.md`，并写入官方原版 `CONTEST_DECLARATION.md`。
- **离线引擎实现**：`scripts/recommend.py` 由 WorkBuddy 编写并运行校验，按目标做营养筛选/评分/组合。

## 使用的 WorkBuddy 能力

- 连接器：自定义 MCP（mcd-mcp）
- 代码执行：Python 运行 `recommend.py` 校验
- 可视化：架构图生成
- 文件生成与项目管理

## 说明

本项目为麦当劳程序员节创意开发大赛参赛作品，非麦当劳官方产品。
输出仅供参考，不构成专业建议；餐品/价格/供应以官方实时结果为准。
