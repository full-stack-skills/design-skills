# 方法论整合证明

验证日期：2026-10-03。此文件是仓库评测证据，不是技能运行规范。标准技能继续保持产品无关。

结论：已把可复用的规格展开、信息架构冻结、Surface 拆分、操作转换、独立设计任务与依赖、生成一致性纳入通用合同和校验。没有证明未来每次生成的视觉图都符合期望，也没有完成目标产品实现。

## 原方法 → 通用规则 → 可执行证据

原文件本轮直接从本机 Evently 仓库读取，未修改。历史来源摘录仍单独保存在 evals/fixtures，不作为技能必读材料。

| 原方法中的具体约束 | 通用技能中的落点 | 已验证内容/边界 |
| --- | --- | --- |
| NAVIGATION 冻结菜单名称，详情/向导/Drawer 不新增菜单 | [工作流第三步](../../skills/ui-design-spec/references/design-workflow.md#第三步固定信息架构展开每个页面结构)、methodology.menus/page_details | 菜单双向归属、默认页存在、同级重名与父级循环校验；图中菜单是否漂移仍需视觉审查 |
| 逐页 Scope、核心用户、核心问题、字段、操作、状态、上下游 | [工作流第二步](../../skills/ui-design-spec/references/design-workflow.md#第二步先写功能总表再逐模块写详细规格)、逐页模板 | 演示提供订单字段、角色、权限、布局与状态；字段真实性和规格深度仍需语义评审 |
| Registry 区分稳定视图、Actions、Errors、Results/Global | [工作流第五步](../../skills/ui-design-spec/references/design-workflow.md#第五步用-registry-固定页面动作状态和结果)、surface_details | 演示列表、抽屉、动作、处理中、错误、结果覆盖七个 Surface；未自动生成七张图片 |
| source_surface/action_kind/preconditions/result_surface；箭头不能自动视为导航 | [六项合同 transitions](../../skills/ui-design-spec/references/methodology-contract.md)、[工作流第四步](../../skills/ui-design-spec/references/design-workflow.md#第四步走通每条业务链写操作转换表) | local 与 command 分开；成功/失败/取消引用校验；不存在的失败去向被拒绝；超时先核对而非直接重试 |
| 单 Surface 任务，真实父页、母版、Frozen Regions、Allowed Change、Shell Gate | [设计单元合同](../../skills/ui-design-spec/references/methodology-contract.md#设计单元与母版)、[任务合同](../../skills/ui-design-spec/references/design-task-contract.md) | 演示七个单 Surface 任务，各有具体验收；缺母版、修改冻结区、重复输出被拒绝；真实原图批准/hash/尺寸仍由 delivery/视觉执行核验 |
| 单一语义源、ID 集合一致、幂等生成、保留任务与批准状态 | [生成器](../../skills/ui-design-spec/scripts/generate_design_maps.py)、关系校验与源指纹 | --write/--check 均返回 0；来源变化检出 stale；只生成派生地图，不编辑原任务/批准；母版没有被伪造为批准 |

直接对照的源文件：

- [逐页功能规格](E:/workspaces/workspace-partme-ai/evently/docs/specs/2026-09-04-nianhuileme-tenant-console-p01-p15-functional-spec.md:90)
- [导航合同](E:/workspaces/workspace-partme-ai/evently/docs/specs/interfaces/tenant-console/NAVIGATION.md)
- [Surface Registry](E:/workspaces/workspace-partme-ai/evently/docs/specs/interfaces/tenant-console/REGISTRY.md)
- [执行与状态合同](E:/workspaces/workspace-partme-ai/evently/docs/specs/2026-09-06-design-execution-contract.md)
- [独立设计任务](E:/workspaces/workspace-partme-ai/evently/docs/superpowers/tasks/interface-design/tenant-console/P02/P02-A11.md)

品牌、主题色、40vw/60vw 抽屉、固定视口、PREP/LIVE 业务、项目编号与固定任务数量没有变成通用规则。设计模式与产物绑定沿用通用合同；目标项目不同 schema 使用等价检查，不强行改名。

## 可直接打开的完整演示

本轮新增合成“订单导出”规格，不复用活动业务。它证明交付合同能落到具体文档与任务，不是生产系统。

- [页面规格](proof-run-20261003-v2/package/pages/P01.md)：角色、问题、布局、字段、权限、状态与验收。
- [用户流程](proof-run-20261003-v2/package/USER-FLOWS.md)：打开范围、提交、处理中、成功、失败、未知结果核对。
- [独立任务](proof-run-20261003-v2/package/MASTER-PLAN.md)：七项任务、母版依赖、冻结/可变区域、具体退出条件。
- [实际生成的关系地图](proof-run-20261003-v2/package/DESIGN-MAP.generated.md)：菜单/功能/对象/页面/交互/任务/预期资产路径与来源指纹。
- [机器结果原件](proof-run-20261003-v2/results.json)：真实命令、退出码、stdout/stderr、故障结果。

| 实际运行 | 结果 |
| --- | --- |
| 正常合同严格校验 | errors=[] |
| 地图 --write / --check | exit_code=0 / 0 |
| 不存在的菜单默认页 | default page outside menu targets |
| 不存在的失败去向 | unknown failure target |
| 修改冻结导航 | frozen/allowed overlap |
| 继承单元没有母版 | missing baseline_ref |
| 两个单元覆盖同一输出 | duplicate output path |
| 来源正文变化而地图未重建 | stale generated design map |

独立任务拆分是本次新增演示证据；先前关系测试中的合成大范围映射不能单独证明逐项任务质量。本演示每项有不同验收条件，但仍没有完成真实资产或业务实现。已声明的 asset 路径不是已存在 PNG；planned 母版不是 Approved。

## 复现

使用 Python 3.10+，在仓库根目录选择一个尚不存在的输出目录：

```powershell
python -X utf8 evals/ui-design-spec/prove_methodology.py --output evals/ui-design-spec/proof-repeat
python -X utf8 -m unittest discover -s skills/ui-design-spec/scripts -p 'test_*.py'
```

本轮实际使用 bundled Python；实际完整命令记录在 results.json。演示脚本拒绝覆盖已有目录，故障注入使用临时副本，不破坏正常产物或原项目。完整技能回归本轮再次运行，53 项通过。

证据边界：上述结果证明规则落地和声明关系约束，不证明未经登记的业务全覆盖、画面美观、母版像素不变、生产运行或模型触发成功率。下一层效果证明需要在真实功能上完成候选画面及交互走查，再按这些合同审查。
