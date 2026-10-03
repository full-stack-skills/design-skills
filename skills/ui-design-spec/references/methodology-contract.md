# 功能设计方法：六项交付合同

本合同适用于全产品或明确的功能范围。沿用目标项目的菜单、编号、主题、视口与规格权威；布局与交互取决于使用者、业务对象和任务目标。已有完整合同核实后复用，详细步骤见[设计工作流](design-workflow.md)。

## 六项产物与验收

| 要求 | 权威内容/派生索引 | 出口条件 |
| --- | --- | --- |
| 菜单与功能地图 | NAVIGATION、FUNCTION-CATALOG；menus/features/objects | 菜单唯一名称、层级、默认页；页面、对象、功能及上下游可追踪；详情与 Tab 保持局部归属 |
| 逐页设计规格 | pages、UI-STRUCTURE；page_details | 使用者、核心问题、布局、真实字段、主次动作、权限、正常/异常状态有具体说明 |
| 子页面与交互面 | SCREEN-REGISTRY、GLOBAL-SURFACES；surface_details | Tab、详情、创建/编辑、抽屉、确认、结果、错误、空态逐项登记；不适用写理由；浮层绑定真实来源页 |
| 交互流程 | USER-FLOWS、逐页操作合同；transitions | 动作区分导航/命令/局部切换；来源、前提、权限、状态变化、成功、失败、取消、恢复闭环 |
| 独立设计任务 | 原任务源、task-coverage；design_units | 每个设计单元稳定 ID，任务定位、母版、冻结/可变区域、产物、验收、父依赖明确；可单独交接 |
| 生成与校验 | registry、派生 DESIGN-MAP.generated | 同 ID 串联菜单→功能→页面→Surface→流程→任务→资产；生成可重复，来源变更能检出过期 |

完整性按本轮声明范围核对，数量从源计算。机器通过只证明声明之间的结构一致；还要审查未登记功能、字段真实性、布局是否回答业务问题、恢复是否可执行、实际画面是否遵守冻结区域。母版引用存在不代表它已获批。视觉产物与原任务批准状态由既有 delivery/Harness 管理。

## 在现有 Registry 中扩展，不新建权威

新增 `registry.json.methodology`，`schema_version: 1`。这是原规格和任务的关系投影，保持原 ID。任务仍使用 [task-coverage.json](task-coverage.md) 的 ID/源定位，不在关系索引存执行状态。每个 `source`/`source_ref` 应精确定位权威章节；脚本检验引用 ID，人工核实原文与投影。普通字段不得填写“参见 Registry”等循环引用。

source/source_ref 使用包根相对本地文件，可附 `#章节`；外部权威用实际相对路径，不写自然语言文件描述。生成地图记录 Registry、任务索引和所有声明来源文件的 SHA256；这些文件变化会使 --check 失败。指纹证明来源变化，不能证明新投影正确反映原文；重生成前必须核实内容。未登记的来源不在自动新鲜度检查范围内。

| 集合 | 必需字段与关系 |
| --- | --- |
| objects | id、name、owner、source；区分谁保存配置、谁产生运行事实 |
| features | id、page_ids、object_ids、upstream_ids、downstream_ids、source；ID 集合等于 task-coverage.features；无上下游用空列表 |
| menus | id、label、parent_id、page_ids、default_page_id、feature_ids、object_ids；顶层 parent_id=null；纯分组 page_ids=[]/default=null；默认页属于本菜单 |
| page_details | page_id、menu_id、actors、permissions、object_ids、feature_ids、core_question、layout_archetype、source；覆盖现有 pages 全集合；非菜单页 menu_id=null 并写 non_menu_reason |
| surface_details | surface_id、kind、parent_surface_id、source；覆盖 Registry 所有 views/actions/states/errors/results/globals；根面 parent=null，局部页与浮层绑定父面 |
| transitions | id、action_id、kind、source、success、failure、cancel、precondition、permission、state_change、recovery、source_ref；每个已登记 action 至少一项；source/success/cancel 与原 action 一致 |
| design_units | id、task_id、surface_ids、mode、parent_unit_id、baseline_ref、frozen_regions、allowed_regions、acceptance、outputs、source；覆盖全部 Surface，可以多个面共享一个有明确验收的设计单元 |

所有 `*_ids`、actors、permissions、区域、acceptance、outputs 使用字符串列表。单值 ID、描述、源定位使用字符串，只有明确允许无父/无母版/无菜单时使用 null。surface kind：screen/tab/detail/create/edit/drawer/dialog/confirmation/result/error/empty/loading/readonly/conflict/state/action/global。transition kind：navigation/command/local。无业务写入的 state_change 应明确写“只改变局部选中项，不写业务数据”；失败仍要定义恢复，不能凭空制造确认框。

`cancel` 可沿用既有 `return_surface`，任务必须说明实际返回与焦点恢复。会跳转到结果面的动作需要登记结果面；就地成功可指向原 Surface，并在合同里写明反馈与变化。加载/只读等适用性在逐页合同审查，不强行按固定数量建图。

## 设计单元与母版

| mode | 用途 | 绑定要求 |
| --- | --- | --- |
| NEW_SCREEN | 建立独立页面/初始母版 | 初次可 parent=null、baseline=null；外壳约束仍要显式列出 |
| EDIT_PARENT | 父图基础上修改局部页面/状态 | parent_unit_id + baseline_ref，继承父任务依赖 |
| OVERLAY_PARENT | 来源页上画抽屉/弹窗/确认 | 同上，写明保留的背景与允许改变区域 |
| ACTION_HIGHLIGHT | 父面上突出动作、状态变化 | 同上，避免把每个按钮画成新整页 |

冻结与允许变化列表不得重叠；区域边界、变更预算、校验方法写入任务原文。`baseline_ref` 绑定资产身份/版本；实际执行前再核验批准证据、hash、尺寸及当前版本。跨任务父子必须在 task-coverage.depends_on 包含父任务，同任务内的顺序写在原合同。父级与 Surface 依赖不得成环。

`outputs` 是计划产物路径，相对包根；必须唯一、不能跨目录逃逸、不能靠 Windows 路径大小写制造重复。共享母版用 baseline_ref，不让不同设计单元覆盖同一输出。资产是否存在、内容是否正确、是否获批仍用 [交付合同](delivery-contract.md) 检验。

## 从业务决定布局，再生成

任务先写第一屏要回答的问题，再选择布局：列表定位、对象详情、工作台、编辑表单、向导、监控、配置或画布。记录为何选该布局，真实字段与阅读顺序、主次操作、滚动/固定区、空/错时替换区域。换功能保留项目外壳，业务区按问题变化。

1. 补齐权威正文，再把上述关系投影到 registry 与 task-coverage。
2. 运行严格结构校验，先修引用、遗漏、依赖与边界错误。
3. 生成派生地图；生成器只写 DESIGN-MAP.generated.md，不改正文、任务状态或批准记录。
4. 检查地图与正文同 ID、同菜单、同去向；检查实际设计资产与设计单元合同。
5. 修改权威后重建投影并生成，运行 --check；汇总文档、视觉候选、批准、实现、运行验收各自证据。

```bash
python3 <skill>/scripts/validate_functional_design.py <package> --require-task-coverage --require-methodology
python3 <skill>/scripts/generate_design_maps.py <package> --write
python3 <skill>/scripts/generate_design_maps.py <package> --check
```

已有文件名用两脚本的 `--document-map <json>` 映射，保留原章节与 ID。历史快照按旧命令校验，不反写来源；新完整包使用双严格开关。需要纳入已有项目时按缺口渐进补齐，未经核实不批量重编 ID/任务。执行命令记录实际使用的 Python 路径；Windows 可使用 `python -X utf8`，避免系统默认编码影响中文。
