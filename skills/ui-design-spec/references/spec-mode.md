# Product Design — spec 模式

把分散需求整理为**功能完整、交互走得通、每页结构明确、任务可以交接**的设计计划。固定按“范围与依据 → 功能详规 → 导航与逐页结构 → 用户流程 → Surface → 任务 → 审阅”整理；不能以几张界面拼图或通用表格宣布完整产品设计完成。

## When to use this skill

- 用户要求完整功能清单、详细功能设计计划、界面结构或交互流程及后续任务。
- 需要组织全产品文档，或接续已有页面与规格。
- 页面已经很多，但缺少稳定入口、返回、状态、异常或功能到任务的映射。

只解释/审查时保持只读；明确要求整理文档才写入指定项目。行为与导航的专业职责见 [职责与交接](responsibility-contract.md)，已有完整章节直接复用，只补缺口；本模式可独立完成全产品文档整理，不要求安装其它技能或启动设计运行器。纯视觉执行、业务实现、安装、发布不由本技能自动授权。

## How to use this skill

1. **恢复现状。** 确认路径、指令、Git 状态、现有规格/任务及已确认决定。建立范围内模块覆盖记录，保留已有 ID 与修改。同一变更只有一个规格事实源；不得自行初始化 SDD 或新增第二套任务状态。
2. **核对目标项目。** 阅读本轮范围内的需求、导航、页面、操作和原任务源，建立模块覆盖表。逐条展开跨页链、异常分支和任务依赖；已有规格足够时核实后复用，只补缺口。
3. **应用固定合同。** 阅读 [交付合同](delivery-contract.md)与 [工作法](design-workflow.md)。新项目使用标准目录；已有项目登记职责映射并补缺口，保留人工文件，不强制改名。业务专属文件、屏数、颜色、视口、技术栈和批准状态不得照搬。
4. **先功能后界面。** 功能总表必须对应逐模块/逐页详规：角色、Scope、核心问题、入口、真实字段、规则、权限、操作、状态、结果与验收。详规用 [模板](../assets/specification-template.md)。仅有功能名/优先级不合格。
5. **明确页面结构。** 每个主页面及结构不同的子页写从上到下/从左到右的业务分区、字段、主次动作、固定/滚动区和状态变化；固定导航、上下文、来源和返回。详情/向导不是天然一级菜单。用 Mermaid 表达导航、旅程与必要状态机。
6. **逐操作走通。** 每条主链配操作表：起点、前提、输入、权限、写入时机、进行中、成功/失败去向、取消/返回、数据保留。不要把计划执行顺序当用户流程；未知结果不能冒充失败可重试，普通只读动作不强加审批。
7. **登记并拆任务。** 区分稳定视图、动作、状态、错误、结果与全局面，保持真实父页。任务明确输入、依赖、阶段、责任角色、范围、产物、验收及验证；设计任务写首屏问题、业务字段、父页/允许变化区域与动作去向。现有 OpenSpec/Spec Kit 任务继续使用原事实源。
8. **审阅并验证。** 执行 [审阅清单](review-checklist.md)，分别确认功能完整、流程闭环、界面结构和任务覆盖。运行下述结构检查；有未决阻断就报告不完整，不自动提升 Approved 或勾选实现。

## Validation

解析 `<skill>` 为当前实际安装目录。只读、Python 标准库，无安装依赖：

```bash
python3 <skill>/scripts/validate_functional_design.py <project>/docs/functional-design --require-task-coverage --require-methodology
python3 <skill>/scripts/generate_design_maps.py <project>/docs/functional-design --write
python3 <skill>/scripts/generate_design_maps.py <project>/docs/functional-design --check
```

如果现有文件名称不同，使用 `--document-map <mapping.json>`，格式见交付合同。现有 registry schema 不同则使用项目校验器并记录等价检查结果，不静默重写为第二套登记。

新完整包同时遵守[六项交付合同](methodology-contract.md)。关系投影放在现有 Registry，派生设计地图只生成引用表；校验菜单归属、动作失败去向、父母版依赖、冻结/可变边界及唯一输出。已有项目按等价合同补缺口，不另立 task/approval 状态。

新完整包按 [任务覆盖合同](task-coverage.md)生成派生索引；原始历史快照可不带 --require-task-coverage 检查，不改写示例。脚本检查必需文件、逐页存在、ID 唯一、操作来源/目标/返回、Registry 行、本地链接，以及任务索引对 Registry 的覆盖、任务源定位和依赖无环。**不判断语义质量、全产品范围是否遗漏、任务依赖的业务合理性、视觉批准或运行结果**；这些必须在 STATUS/评审记录提供实际依据。旧 `validate_delivery.py` 仅校验历史 00–06 教学包，不适用于标准包。

## Best Practices

- 以已有用户决定和规格为准，不能靠文件更晚、标题“最终”或截图美观覆盖权威。
- 总表用于索引，pages/ 用于交接；不能只写“Header + Sidebar + Content”。
- 原始快照保留 Draft 和未知项。新项目需要自己的来源、决策、批准与验证。
- 多端一致性按用户要求定义；要求视觉/交互一致时，组件框架差异不构成放宽理由。
- 功能文档、视觉设计、人工批准、实现、运行验收分别记录；借鉴目录不复制示例的审批制度。

## Output contract

交付位置、范围覆盖、唯一规格/任务源、功能/流程/页面/任务入口、未决项、实际验证和下一步。全量任务只有范围内各模块都满足内容深度及覆盖要求，才能报告文档整理完成。

## Keywords

functional design, feature catalog, page specification, interface structure, user flow, screen registry, task planning, 功能设计, 功能清单, 交互流程, 界面结构, 产品计划
