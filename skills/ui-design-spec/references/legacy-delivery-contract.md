> 兼容说明：本文只用于旧 product-interface-spec 草稿的 00–06 + delivery.json 教学包。新项目使用 delivery-contract.md，不需要再生成本套文件。

# 固定交付合同 v1

本合同适用于技能的完整整理/计划模式。用户明确限制为只读审查时，按同样七阶段报告缺口，不写文件、不声称生成了合格交付包。用户要求改变合同则记录偏离与影响；不得声称按原合同验证通过。

## 固定执行顺序

0. 检查输入、权限、现行规格与原任务源。
1. 来源/用户/对象/冲突登记。
2. 功能清单。
3. 导航与页面结构。
4. 用户旅程与状态转换。
5. Screen + Interaction Surface 详规。
6. 有依赖和验收条件的计划任务。
7. 覆盖检查、语义审阅和机器验证。

阶段不能省略。不适用内容在对应字段写明“不适用：具体理由”；不能用空值、待补、TODO 或通用套话代替。缺少关键信息时记录 blocker 和影响，继续完成不受影响部分，整体标记 blocked。

## 固定文件清单

输出根目录记为 PACKAGE，默认按项目现有 docs 组织选择一个变更目录。所有完整交付固定包含以下文件，不因产品大小合并或删减；小产品缩短条目数量。

| 文件 | 固定职责与必要内容 |
| --- | --- |
| `00-scope-and-sources.md` | 范围、用户、对象、证据、现行规格事实源、冲突及决定依据 |
| `01-feature-catalog.md` | 功能总表 + 逐模块十项详规；功能 ID、目标、前提、输入输出、权限、规则、必须信息、异常恢复、优先级、成熟度、来源 |
| `02-navigation-and-layout.md` | 产品端、外壳、域、导航/路由、每页真实内容分区表或线框、上下文切换/返回、Mermaid 页面树 |
| `03-journeys-and-states.md` | 旅程 ID、入口/终点、逐操作转换表、状态机、异常/拒绝/取消/离线/冲突/恢复、Mermaid 流程 |
| `04-surface-registry.md` | 页面、子视图、动作、状态、阻断、结果、全局入口，完整 Surface 字段 |
| `05-task-plan.md` | 任务总表 + 可交接执行说明；依赖顺序、阶段、责任角色、输入、产物、验收、验证方式和正式任务源映射 |
| `06-review-report.md` | 覆盖与孤立项、未解决冲突、语义审阅依据、验证命令/结果、剩余风险、未运行证据 |
| `delivery.json` | 上述实体的机器可读索引与引用；不得维护独立实现状态 |

已有文档保留原路径、ID、确认记录和状态。新固定文件作为带定位引用的交付视图，不能复制为另一套需求事实源；详细内容可保留在原文件，固定文件必须说明本阶段结论和精确入口，不能只有一句“见其它文档”。

## 内容深度合同

必须遵循 [详细设计工作流](design-workflow.md)的逐模块、逐页面、逐操作和逐任务展开要求。范围内每个模块均有覆盖记录；同类共用规则可以集中定义并引用，差异必须写明。完整产品请求不能以一个教学切片代表全量完成。

只包含目录、总表、抽象流程或“表单/按钮/弹窗”等通用描述，即使文件与 JSON 齐全，也不能通过语义审阅。至少检查接手者能否确定业务输入输出、真实字段、动作去向、页面分区、失败恢复和任务验收。JSON v1 保持机器索引兼容；本次内容深度要求由 06 审阅报告逐模块记录实际证据，现有校验器不自动判断文字质量。

## 计划任务的唯一事实源

- 已有 OpenSpec：写入/引用当前 change 的 tasks.md；Spec Kit 或其它体系同理。本包 `05-task-plan.md` 是规划和追踪视图，不复制可勾选执行状态。
- 没有现行任务源且已授权输出计划：本包 `05-task-plan.md` 即唯一任务源，无需初始化工具。
- 已有任务不足且未获修改范围：登记缺口，不悄悄新增另一套任务；有授权时在原任务源补齐。
- 每项任务明确功能、Surface、先决任务、输入、产物、可观察验收和验证方法。责任字段是角色，不擅自指派真实同事。
- 状态只能从原任务源读取；“规划已完成”不能勾选实现任务。循环依赖、任务无产物、功能无任务、Surface 无任务均不合格。

## `delivery.json` v1 字段

字符串必须有实际内容；列表内对象遵循以下合同，关联字段不可填未定义 ID。所有 ID 在全包内唯一，保留项目已有编号，不强制迁移为示例前缀。

顶层：

- `schema_version`: 1。
- `status`: `draft`、`blocked` 或 `ready`。只有语义审阅与验证通过才能是 ready，ready 指规格交付可用，不指实现完成。
- `scope`: 对象，含 `product`、`users`、`objects`、`in_scope`、`out_of_scope`、`spec_source`，均为非空字符串。
- `sources`: 每项 `id`、`location`、`version`、`evidence_kind`、`conclusion`；证据类型为 `user_decision/spec/code/runtime/design/history`。
- `features`: 每项 `id`、`goal`、`preconditions`、`inputs`、`outputs`、`permission`、`exceptions`、`acceptance`、`priority`、`maturity`、`source_ids`。
- `surfaces`: 每项 `id`、`kind`、`parent_id`（仅顶级为空）、`feature_ids`、`entry`、`preconditions`、`context`、`user_question`、`layout`、`required_information`、`primary_action`、`secondary_actions`、`fields_and_validation`、`permission`、`success`、`failure`、`return_behavior`、`accessibility`、`data_contract`、`visual_dependency`、`acceptance`。
- Surface `kind`: `page/subview/action/state/error/result/global`。除 page/global 外必须有父节点；父关系无环。
- `journeys`: 每项 `id`、`feature_ids`、`goal`、`preconditions`、`outcome`、`steps`、`branches`。steps 每项 `surface_id`、`action`、`transition`、`permission`、`success`、`failure`。branches 对象固定键 `failure/denial/cancel/offline/conflict/interruption/recovery`，每键为实际处理说明或“不适用：具体理由”。
- `task_source`: 相对 PACKAGE 的现行本地任务文件路径；允许 `../` 引用项目已有任务文件，仅用于只读核验。
- `tasks`: 每项 `id`、`feature_ids`、`surface_ids`、`depends_on`、`phase`、`owner_role`、`inputs`、`deliverable`、`acceptance`、`verification`、`source_marker`。marker 必须能在 task_source 中唯一定位该正式任务，建议 Markdown 行完整标题或编号前缀。不得加第二套 checked/status 字段。
- `issues`: 可空；每项 `id`、`severity`（`blocker/warning`）、`description`、`impact`、`resolution`；resolution 为 `open` 或具体解决依据。ready 不允许 open blocker。
- `reviews`: 每项 `area`、`verdict`（`pass/fail/pending`）、`evidence`。area 必须完整且不重复：`source_authority/functional_closure/layout_and_navigation/interaction_and_recovery/task_plan/cross_surface_consistency`。evidence 必须指向本地文件及可选片段并说明审阅结论；不能由验证器自动生成为 pass。

机器索引包含必填语义，Markdown 是供人阅读的对应展开；两者不得各自演化。以正式规格为准修正二者。审阅报告明确“JSON 与文档一致性已审阅”的依据。

## 完成门槛

执行 `python3 <skill>/scripts/validate_delivery.py PACKAGE --require-ready`。退出非零或任一语义检查未通过时，报告具体差距，禁止宣称完整整理完成。验证器只校验结构、引用、任务映射及显式审阅状态；它无法证明文案真实、产品完整或其他智能体遵守了流程。外部编排/CI 只有显式接入此命令才具有强制阻断效果，不宣称自动安装了 CI。
