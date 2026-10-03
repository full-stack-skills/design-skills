# 完整功能设计交付合同

新项目默认 `docs/functional-design/`，按文档职责组织。固定的是文档职责与深度；已有项目保留命名及事实源，在 README 登记映射，不能因文件名不同就重做规格。

## 标准目录与职责

```text
docs/functional-design/
  README.md
  FUNCTION-CATALOG.md
  NAVIGATION.md
  UI-STRUCTURE.md
  USER-FLOWS.md
  SCREEN-REGISTRY.md
  GLOBAL-SURFACES.md
  pages/<稳定功能或页面ID>.md
  MASTER-PLAN.md
  DESIGN-EXECUTION.md
  STATUS.md
  registry.json
  task-coverage.json
  DESIGN-MAP.generated.md
```

| 文件 | 必须包含 |
| --- | --- |
| README | 产品目标、范围、用户/对象、来源与冲突、唯一规格/任务源、阅读顺序、模块覆盖及职责映射 |
| FUNCTION-CATALOG | 全量功能索引：ID、职责/业务价值、角色/范围、入口、需求对应、阶段、逐页合同入口；功能不能因尚无页面而消失 |
| NAVIGATION | 全局/业务/页内层级、固定名称、默认落点、路由、选中态、上下文切换、深链与返回 |
| UI-STRUCTURE | 全局外壳、稳定分区、布局与交互共性、目标平台/尺寸、滚动、焦点、输入与状态；不得把某业务私有布局当全局规则 |
| pages/ID | 每模块详规：目的/用户/Scope/入口返回、逐视图结构、真实信息字段及校验、操作转换、状态异常结果、验收与设计依赖 |
| USER-FLOWS | 全部核心旅程：Mermaid 主链与分支、起止状态、上下文、取消/失败/恢复；操作表可精确引用 pages |
| SCREEN-REGISTRY | 全部稳定视图、动作、状态、错误、结果、全局面：ID、父项、承载方式、业务内容及去向 |
| GLOBAL-SURFACES | 外壳、搜索、切换、通知等真正共用交互；入口、字段、权限、效果、失败、返回、验收；不适用写业务理由 |
| MASTER-PLAN | 工作包、依赖、阶段、责任角色、输入/产物、退出条件、验收/失败注入，以及设计单元执行说明或精确引用；已有任务只作规划映射 |
| DESIGN-EXECUTION | 外壳→父页→子视图→动作→异常结果的依赖；每单元输入/输出、冻结区/可变区、主次操作、验收及真实批准约定 |
| STATUS | 分列文档、视觉、批准、实现、运行验收；当前缺口/待决、实际检查证据、下一项任务；不复制另一套任务勾选状态 |
| registry.json | 页面与全局面、稳定 ID、字段、动作来源/目标/返回、状态的机器索引；不替代正式需求与任务 |

项目特有的架构/集成文件按需追加，不要求生成无实际用途的附加文档。无需生成旧 00–06 + delivery.json 的重复文档；旧包只用于兼容教学。

上表规定完整包的职责。单模块可沿用现有单文件承载同等内容；模糊想法交付假设明确的草案，局部修改只交目标与差值及受影响映射。裁剪规则见[通用设计编制规则](design-authoring.md)，不扩大用户请求，也不宣称裁剪交付通过完整包脚本。

新完整包按[六项交付合同](methodology-contract.md)在 Registry 增补关系投影，派生 task-coverage 与 DESIGN-MAP；历史来源保持原字节，不回填。地图生成不覆盖正文、任务或审批。菜单/页面双向映射、失败恢复目标、父母版绑定、冻结边界和输出唯一性通过双严格开关校验；视觉和语义仍单独审阅。

## 逐项内容深度

遵循 [工作法](design-workflow.md)的十项模块展开。功能清单必须能追到逐页/模块合同；每页必须有真实内容区、输入字段、动作和返回；每个主要动作必须有明确的业务变化、异常恢复和去向。共同规则集中定义并引用，差异不能被“同上”隐藏。只填目录、模块名、通用页面骨架、同一句失败提示均不合格。

编号保持目标项目语义，不固定页面数量，不机械给每项操作新增整页图。页面与任务数量从目标项目范围计算。

## 任务与状态只有一个事实源

已有 OpenSpec/Spec Kit/其它任务源时，MASTER-PLAN 写规划、依赖、原定位和验收映射，不复制执行复选框。没有原任务源且已授权规划时，MASTER-PLAN 可作为任务源，不需初始化 CLI。

任务说明必须给出输入、依赖、范围、责任角色、业务字段、主次动作、异常与结果、产物、验收和验证。设计任务还须给出父页与允许变化区域。每项功能/Surface 均有任务承接；依赖无环；待决项明确影响哪项工作。新增完整包使用 [任务覆盖索引](task-coverage.md)校验声明范围、源定位和依赖无环；原任务状态仍只从原源读取。范围本身是否遗漏真实业务、依赖是否合理，仍由语义审阅核实。

## 机器索引与检查

标准 registry 结构如下：

- `version`、`status` 记录文档版本和真实状态；结构校验不修改它们。
- `pages[]`：`id/name/scope/nav/phase/purpose/entry/layout/fields/validation/state/error/result/requirements` 为具体非空文字。
- `views[]`：可用字符串列表（生成原示例式 ID `P01-01`）或 `{id, name}` 显式保留项目 ID。
- `actions[]`：`id/name/precondition/effect/source/target/cancel`；source/target 引用已登记 Surface，cancel 为具体 ID 或 `return_surface`。后者必须在页面合同中解释真实来源上下文。
- 状态默认 ID 为父 ID 的 `S01/E01/R01`；不同编号可用 `state_id/error_id/result_id`。更复杂既有状态登记不必压缩成这三个字段，沿用原 schema 与原校验器。
- `globals[]`：`id/name/entry/presentation/layout/effect/fields/failure/target`；默认 Surface 为 `<id>-01`，可用 `surface_id` 指定。

这是简单项目可直接使用的索引形态，不能据此把多种不同错误合并为同一个通用错误。复杂项目使用现行模型并补等价关系检查；不得为运行脚本删减业务状态。

文件映射示例（键是逻辑名称，值相对 PACKAGE；可保留项目既有目录）：

```json
{
  "FUNCTION-CATALOG.md": "features.md",
  "pages": "screens",
  "MASTER-PLAN.md": "plan.md"
}
```

新标准包：`python3 <skill>/scripts/validate_functional_design.py PACKAGE [--document-map mapping.json]`。
旧教学包：仅使用 `validate_delivery.py` 并参考 [旧合同](legacy-delivery-contract.md)。两种示例不强制相互转换。

## 完成门槛

结构检查通过 + 范围内所有模块的功能/流程/结构/任务语义审阅有具体证据 + 未决项及影响明确。影响交付的 blocker 未解决时只能交付部分成果并说明阻断，不宣称完整。脚本通过不是设计批准、跨模型稳定遵循证明或业务运行证据。
