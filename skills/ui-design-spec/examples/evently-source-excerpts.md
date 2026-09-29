# Evently 原成果摘录

采集日期：2026-09-29。以下为工作区原文片段，保留原 ID。来源为当时的本地文件（可能含未提交修改），不是某个发布版本，也不是运行验收。片段外的状态、批准和最新规则须回到项目核对。导航文件开头另有视觉规则被用户后续选择取代的声明；本摘录仅用于导航结构教学，不能据此套用历史视觉约束。

## P06 功能规格

来源：`docs/specs/2026-09-04-nianhuileme-tenant-console-p01-p15-functional-spec.md`，行 90–101。

完整来源文件 SHA256：`a2d1d23fb2ba90076cee587975bd43ea97e4b78e4be47845c80747adac2402de`。

````markdown
### P06 Participant Import / 导入参与人员

- **Scope / Context：** Event。
- **进入方式：** P05“导入人员”；属于全屏或大尺寸向导。
- **核心用户：** Organizer、具备 Manage Participants 权限的成员。
- **核心问题：** 如何安全导入 Excel/CSV，并在写入前解决字段、重复与冲突？
- **固定步骤：** ①上传文件；②字段映射；③数据校验；④问题处理与确认导入。
- **必须展示：** 文件信息与解析结果；源列到 Evently 字段映射；必填字段；有效、重复、缺失、格式错误、未知部门、桌位冲突等校验摘要；逐条问题与处理策略；最终新增/更新/跳过数量。
- **主要操作：** 下载模板、重新上传、保存映射模板、合并/覆盖/跳过、修正数据、确认导入、下载错误报告。
- **关键状态：** 不支持格式；文件过大；编码异常；完全无有效行；提交时数据已变化；导入事务失败并整体回滚。正式名单不允许“部分成功”；可修复行与被跳过行只属于 Commit 前的 Preview 结果。
- **规则：** 必须两阶段 Preview → Commit；不能上传后立即写库；批量导入应幂等并有 Audit。
- **上下游：** 成功返回 P05，并可继续 P10/P11 排座。
````

## P06 Surface Registry

来源：`docs/specs/interfaces/tenant-console/REGISTRY.md`，行 235–264。

完整来源文件 SHA256：`07814a3b5a0e1d15edd318d5623e700527bd051ea964956e25d23d22ce140dff`。

````markdown
# P06 导入参与人员

### Wizard

- `P06-01` 上传文件。
- `P06-02` 字段映射。
- `P06-03` 数据校验。
- `P06-04` 问题处理 / 确认导入。
- `P06-05` 导入结果。

### Actions

- `P06-A01` 下载模板。
- `P06-A02` 重新上传。
- `P06-A03` 保存字段映射模板。
- `P06-A04` 合并 / 覆盖 / 跳过冲突策略。
- `P06-A05` 逐条修正。
- `P06-A06` 确认 Commit。
- `P06-A07` 下载错误报告。

### Errors

- `P06-E01` 文件格式不支持。
- `P06-E02` 文件过大。
- `P06-E03` 编码/解析异常。
- `P06-E04` 无有效行。
- `P06-E05` Commit 时数据版本变化。
- `P06-E06` 导入事务失败 / 已回滚。

---
````

## 导航与页面归属

来源：`docs/specs/interfaces/tenant-console/NAVIGATION.md`，行 10–105。

完整来源文件 SHA256：`d68894a6ec3e6ed0b0cb80123b91ef8026ec7dd2cc10280c6413a16113a0a303`。

````markdown
## 1. Global Header

固定包含：

```text
年会了么 Brand
Tenant Switcher
Event Switcher
Global Search
WorkBuddy
Notifications
Help
Current Account
```

当 Event 未选择时，不显示 Event 日期、场地、LIVE 状态等 Event Runtime 信息。

---

## 2. 左侧菜单唯一命名

以下名称冻结，后续任何设计图不得自行改写、缩写或替换：

```text
工作台

活动管理

人员 / 签到

流程 / 节目

奖项 / 抽奖

席位 / 座位

物料 / 大屏

互动 / 游戏

现场执行（LIVE）
├── 现场导演台
├── 大屏控制
└── 设备管理

数据中心
├── 数据报表
└── 数据大屏

设置中心
├── 基础设置
├── 权限管理
└── 系统设置
```

### 禁止出现的漂移命名

后续设计不得擅自改为：

```text
人员管理
桌位 / 座位
设备与节点管理
大屏与素材
现场控制
报告中心
企业设置
系统管理
```

除非未来产品规格正式修改 Frozen Navigation。

---

## 3. P 系列归属

| 菜单 | 主功能 |
|---|---|
| 工作台 | P01 企业工作台 |
| 活动管理 | P02 全部活动、P03 创建活动、P04 活动总览及 Event 生命周期动作 |
| 人员 / 签到 | P05–P09 |
| 席位 / 座位 | P10–P11 |
| 流程 / 节目 | P12–P15 |
| 奖项 / 抽奖 | P16–P19、P38 领奖核销 |
| 互动 / 游戏 | P20–P26 |
| 物料 / 大屏 | P27–P30 |
| 现场导演台 | P31、P32、P33、P37、P40 的 LIVE 运行控制面 |
| 大屏控制 | Scene 输出/现场投放相关运行 Surface，主要关联 P27/P29/P32/P33 |
| 设备管理 | P34–P36、P37 的 Node 管理与健康入口 |
| 数据报表 | P41 活动报告、相关导出/对比 Surface |
| 数据大屏 | 现场/经营数据展示与投屏入口，关联 P37/P41；若形成独立主页面需新增 Registry ID |
| 基础设置 | P43 活动基础设置与 Tenant 基础信息入口 |
| 权限管理 | P44 企业成员与 Event Role / MCP Scope |
| 系统设置 | P45–P47 商业、集成、部署与 License |

说明：Registry 页面编号和左侧菜单不是一一对应。详情页、向导、Modal、Drawer 不新增左侧菜单项。
````

## 设计任务目标

来源：`docs/superpowers/tasks/interface-design/tenant-console/P02/P02-A11.md`，行 8–12。

完整来源文件 SHA256：`7b6e395ee6c067dd64ca4525518ab259546158c20e4c26bb6ccd450bfc914654`。

````markdown
## 1. Task Goal

只完成一个 Registry Surface：**P02-A11「Create Rehearsal Session」**。

父功能：`P02` — 全部活动
````

## 设计任务业务内容

来源：`docs/superpowers/tasks/interface-design/tenant-console/P02/P02-A11.md`，行 65–69。

完整来源文件 SHA256：`7b6e395ee6c067dd64ca4525518ab259546158c20e4c26bb6ccd450bfc914654`。

````markdown
## 5. Required Business Content

> Create Rehearsal Session：Session 名称/计划时间/使用 Snapshot/确认

不得用通用 Dashboard 卡片替代上述业务合同；字段、状态、主动作和交互层必须从这条合同展开。
````

## 设计任务的上下文与布局合同

来源：`docs/superpowers/tasks/interface-design/tenant-console/P02/P02-A11.md`，行 23–31。

完整来源文件 SHA256：`7b6e395ee6c067dd64ca4525518ab259546158c20e4c26bb6ccd450bfc914654`。

````markdown
## 3. Design Contract V2

- **Scope / Context:** Tenant Scope；Event Switcher 显示“选择活动”，不要绑定具体 Event
- **Selected Navigation:** 活动管理
- **Layout Archetype:** Lifecycle Management List
- **First-screen Question:** 第一屏回答：哪些活动处于当前生命周期，是否需要现在处理？
- **Composition:** 稳定 8 生命周期 Tab + 5–6 个紧凑 KPI + 高密度活动列表/表格 + 可选窄右栏；融合已确认两张 P02-05 参考：A 的年会品牌/礼盒丝带/右侧最终检查，B 的表格密度/栅格/对齐与留白。
- **Surface Presentation:** 真实来源页/本端已批准 Shell 代表性页面上下文 + 当前 Type 指定的唯一交互层；保留 Actor、目标、影响与取消/恢复路径。
- **Business Contract:** Create Rehearsal Session：Session 名称/计划时间/使用 Snapshot/确认
````
