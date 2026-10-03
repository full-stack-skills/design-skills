---
name: ui-design-spec
description: Use when planning product or feature UI, filling page and interaction gaps, or continuing design tasks. Covers menu maps, page specs, flows and consistency checks. 完整功能设计、逐页规格与任务交接。
license: Apache-2.0
compatibility: Bundled validation and generation scripts require Python 3.10 or later; specification work has no renderer dependency.
---

# UI Design Specification

本技能负责把产品或功能需求整理为可交接的设计规格，并为后续设计准备同一份合同。先明确功能、页面、交互与任务，再按已授权范围交给专业技能执行；继续已有工作时保留规格、任务 ID、批准决定和运行身份。

## When to use

用户需要完整菜单与功能地图、逐页设计、子页面和交互面、成功与失败流程、独立设计任务及一致性校验时使用。也适用于补齐现有规格，或沿用已批准基线继续下一项设计。只要求解释或审查时保持只读，不因选中本技能自动启动渲染、实现、安装或发布。

## Capability Boundaries

| 用户意图 | 本技能职责或交接 |
|---|---|
| 全产品或明确功能范围的设计规格 | 使用 spec 模式，覆盖六项交付合同 |
| 继续已有设计或准备下一页 | 恢复原任务与基线，准备 scoped handoff |
| 行为规则、权限和副作用缺口 | 按需使用 `ui-design-feature`，写回原规格 |
| 路由、层级、选中态和返回缺口 | 按需使用 `ui-design-nav`，保留原导航 |
| 主题或连续性约束 | `ui-design-theme` / `ui-design-continuity` |
| 候选图或跨产物一致性审查 | `ui-design-review` |
| 持续执行、断点恢复和状态管理 | 选择 profile 后交给 `ui-design-harness` |
| 实际视觉产物 | 准备合同后交给适用 renderer，如 `ui-design-visual` |

专业职责可以由同一智能体按需承担。可选技能缺失时使用本技能内置合同，明确未完成的专业验证，不自动安装或伪称调用。

## How to use · Workflow

### Step 1：确认输入与事实源

读取项目指令、已有修改、产品端、用户、业务对象、范围、规格、导航、任务源及当前版本。登记来源冲突、未决事项和实际成熟度。已有完整内容核实后复用，只补缺口；不创建第二套任务状态，也不重新编号。

### Step 2：选择本轮模式

- **spec**：用户要求规格、规划或文档补齐。按范围交付，不要求创建 Harness run。
- **execution**：用户已要求实际设计执行。恢复基线、主题与原任务；已有 run 沿原身份接续。新运行选择 `product-to-ui`、`existing-product-next-page`、`page-family-batch`、`design-correction`、`stitch-high-fidelity-delivery` 或 `design-to-implementation`，内部状态机交由 Harness 管理。
- **Harness dispatch**：仅处理 packet 的阶段与范围。baseline 阶段绑定事实源，task 阶段组装原任务合同；沿用 run/dispatch/evidence_stage 返回，不重新路由或创建运行。

任务边界明确时直接推进，只有缺失决定会影响当前交付才询问。交接时按需读取[职责与交接合同](references/responsibility-contract.md)。

交付规模与运行模式分别判断：完整范围使用六项合同；单模块可沿用现有单文件；模糊想法交付标明假设的草案；局部修正只展开目标与差值。按请求裁剪时读取[通用设计编制规则](references/design-authoring.md)，不为补齐目录擅自扩大业务范围。

### Step 3：展开功能、页面与交互

按“范围与来源 → 功能详规 → 导航与页面结构 → 用户流程 → Surface Registry”展开。逐页明确使用者、核心问题、字段、布局理由、主次操作、权限、状态与验收。Tab、详情、创建/编辑、抽屉、确认、结果、错误与空态逐项判断适用性；每个动作给出真实来源、前置条件、业务变化、成功/失败/取消去向和恢复。

全产品请求覆盖范围内全部模块，不用几个示范页面代替完成。编写详规时使用[详细工作流](references/design-workflow.md)和[填写模板](assets/specification-template.md)。

共享外壳与组件规则集中定义，各页只展开差异；具体控件标签、数据示例与交互反馈可直接交接。逐项审查状态适用性，补齐响应式、键盘与焦点行为；事实、建议、待确认项分别标注，不把演示值当真实数据。

### Step 4：形成独立设计任务

给每个设计对象稳定 ID，绑定功能、Surface、原任务位置、来源页、父单元、母版版本、冻结/可变区域、唯一产物路径和可观察验收。初始母版可以明确不存在；继承单元执行前核实真实父资产的批准、hash、尺寸与版本。设计执行顺序与用户操作流程分别记录。

任务映射从原任务源派生，保留人工状态；同任务的执行说明直接引用，不复制第二套勾选清单。准备单元与依赖时读取[任务合同](references/design-task-contract.md)及[任务覆盖合同](references/task-coverage.md)。

### Step 5：生成、校验与修正

在现有 Registry 登记六项关系，原 schema 不同则保留它并提供等价检查证据。新标准完整包使用双严格开关；生成器只写派生地图，原文、任务状态和批准记录不由生成器编辑。

```bash
python3 <skill>/scripts/validate_functional_design.py <package> --require-task-coverage --require-methodology
python3 <skill>/scripts/generate_design_maps.py <package> --write --format json
python3 <skill>/scripts/generate_design_maps.py <package> --check --format json
```

将 `<skill>` 解析为实际安装目录。失败时修正报错所指的原文、关系或依赖，再生成并复核；来源变化导致过期时，先核实投影再重建。历史快照使用对应兼容检查，不反写来源。机器通过后按[审阅清单](references/review-checklist.md)核对语义、真实范围与实际资产。

### Step 6：交付或接续执行

默认文档落在 `docs/functional-design/`，包含范围与功能清单、导航与布局、逐页合同、流程与全局面、Registry、原任务映射、执行说明与状态。已有文件名称保持不变，登记职责映射；完整文件职责见[交付合同](references/delivery-contract.md)。

交付规格后只按已有授权继续视觉或实现。执行前传递同一版本的功能、导航、主题、夹具和任务合同；首次页面使用 initial，继承或纠偏使用 inherit/correction。单次有明确边界的工作可直接交给专业技能，持续执行由 Harness 保留运行和验证证据。

## Validation checklist

- [ ] 声明范围内的每个菜单、功能、对象和页面均有来源与对应关系。
- [ ] 每页布局、字段、主次动作、权限和正常/异常状态能直接交接。
- [ ] 适用的局部视图、交互层、结果与错误面均已登记，来源和返回明确。
- [ ] 主要动作区分导航、命令与局部切换，成功/失败/取消与恢复闭环。
- [ ] 设计单元具有稳定 ID、原任务定位、父依赖、冻结/可变边界及具体退出条件。
- [ ] 关系覆盖、依赖、输出唯一性和派生地图新鲜度通过实际检查；未运行项如实记录。
- [ ] 人工语义审查与机器结果分别有证据；规格、候选、批准、实现和运行验收分别报告。
- [ ] 交付规模符合请求；状态不适用有理由，跨端与无障碍有具体行为，局部修改没有越过冻结边界。

## 不适用与边界

单独选配色、查询路由、审查候选图、修复代码或安装技能时，使用相应专业技能。本技能不替代 renderer、生产实现或部署。标准文档目录和机器脚本不要求目标项目迁移权威来源；不得为了通过脚本删减业务状态或重写已确认决定。

## Gotchas

1. **菜单等同页面或截图**：详情、向导和抽屉保持真实归属；一个 Surface 不自动等于整页图。
2. **未知结果直接重试**：超时后先核对请求与业务状态；关闭页面不等于取消后台任务。
3. **母版引用冒充批准**：初始页可没有基线；继承视觉必须核实真实父图，不能凭引用解除依赖。
4. **结构通过冒充业务完整**：脚本检查已声明关系；遗漏需求、字段真实性和画面冻结区仍需审查。
5. **继续任务重建整个流程**：保留原版本、任务和 run/dispatch，不循环进入总入口。
6. **只填表格没有具体内容**：共同规则通过引用复用，业务差异必须展开到输入、输出、恢复和验收。

## Best Practices

一份需求权威、一份任务执行来源、同一组稳定 ID。围绕第一屏问题选择布局，继承外壳而不机械复用业务区。专业技能只补其职责范围内的缺口，审查失败回到受影响的原任务修正。按请求使用本地或外部工具，不自动安装依赖；脚本为 Python 标准库实现，`--help` 查看参数，`--check` 进行只读复核。

## Output contract

交付 mode/stage、范围覆盖、唯一规格与任务源、输入版本、产物路径、未决事项、实际验证、未验证/失败项和下一步。新完整标准包含 Registry 关系投影、task-coverage 和派生地图；已有项目交付等价映射与检查结果。Harness worker 返回对应 stage evidence；文件存在不等于批准、实现或运行完成。

## References

- [六项设计交付合同](references/methodology-contract.md)：全范围设计或关系投影时读取。
- [spec 模式](references/spec-mode.md)：建立或补齐规格包时读取。
- [详细设计工作流](references/design-workflow.md)：功能、逐页和动作深度不足时读取。
- [交付合同](references/delivery-contract.md)：确定文件职责与现有文件映射时读取。
- [填写模板](assets/specification-template.md)：编写逐页、流程和任务内容时使用。
- [通用设计编制规则](references/design-authoring.md)：裁剪交付、细化控件、跨端设计、局部修正或处理冲突/写入失败时读取。
- [设计任务合同](references/design-task-contract.md)、[任务覆盖](references/task-coverage.md)：拆分与交接任务时读取。
- [职责与交接](references/responsibility-contract.md)、[执行路由](references/workflow.md)：专业交接或运行内派发时读取。
- [审阅清单](references/review-checklist.md)：交付前或检查发现缺口时读取。

## Examples

- **规格补齐**：“补齐订单导出的页面、错误恢复和设计任务，保持原菜单。” → spec；补齐逐页与动作合同、稳定单元和任务映射，运行检查并报告未决项。
- **继续设计**：“沿用已批准页面制作编辑抽屉。” → execution；绑定父资产和版本，冻结背景，仅改变当前交互层，按既有审批规则审查。
- **只读解释**：“检查规格是否漏了取消恢复。” → 列出来源、缺口和影响；不写文件、不创建运行、不启动渲染。

## Keywords

UI design specification, feature catalog, menu map, page specification, interaction surface, user flow, design task, design handoff, 功能设计, 菜单地图, 逐页规格, 交互流程, 独立设计任务, 一致性校验
