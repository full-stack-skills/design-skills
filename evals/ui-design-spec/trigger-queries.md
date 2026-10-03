# Trigger evaluation inputs

These are evaluation inputs, not measured model results. A complete trigger evaluation runs each query at least three times and records the selected skill, false positives/negatives and trigger rate. Keep the 12 training queries separate from the 8 validation queries; do not tune descriptions on validation results.

| ID | Split | Trigger this entrypoint? | User query |
| --- | --- | --- | --- |
| Q01 | train | yes | 把产品所有菜单、页面、流程和设计任务整理完整。 |
| Q02 | train | yes | 新的库存盘点功能需要逐页规格及异常流程。 |
| Q03 | train | yes | 已有需求文档，补齐页面字段、权限、状态和验收。 |
| Q04 | train | yes | Plan the interfaces and design tasks for this entire product. |
| Q05 | train | yes | 页面很多，但缺菜单对应关系和返回路径，帮我整理。 |
| Q06 | train | yes | 沿用批准的页面，继续下一项设计任务。 |
| Q07 | train | no | 只给页面选一套字体和配色。 |
| Q08 | train | no | 检查这个详情路由的深链和返回行为。 |
| Q09 | train | no | 审查这张候选图是否符合现有合同，不修改计划。 |
| Q10 | train | no | 修复保存 API 的空指针错误。 |
| Q11 | train | no | 把当前版本部署到测试环境。 |
| Q12 | train | no | 安装一个技能到本机。 |
| Q13 | validation | yes | 订单导出需要界面、权限、失败恢复和独立设计任务。 |
| Q14 | validation | yes | 沿用原规格和菜单，把尚未明确的交互面补出来。 |
| Q15 | validation | yes | I need a complete UI specification and task handoff for account recovery. |
| Q16 | validation | yes | 继续已有设计运行，保留批准母版和任务编号。 |
| Q17 | validation | no | 将主题的强调色替换为指定颜色。 |
| Q18 | validation | no | 只解释 URL 的查询参数如何保留筛选。 |
| Q19 | validation | no | 调试按钮点击事件为什么执行两次。 |
| Q20 | validation | no | 生成一个单独的插画文件。 |
