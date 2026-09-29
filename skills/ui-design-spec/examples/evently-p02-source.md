# Evently P02 原始成果摘录

来源：Evently `docs/specs/interfaces/tenant-console/REGISTRY.md`。2026-09-29 工作区只读摘录；原仓库存在未提交工作，本摘录不推断远端状态。

原文件 SHA-256：`07814a3b5a0e1d15edd318d5623e700527bd051ea964956e25d23d22ce140dff`。

## P02 全部活动


**Menu:** 活动管理  
**Purpose:** 管理 Tenant 下全部 Event 生命周期。

## 8 个稳定 Tab — 每个必须独立出图

- `P02-01` 全部活动：跨生命周期比较；状态、时间、负责人、准备度、异常和主要动作。
- `P02-02` 草稿：内容完整度、缺失项、最后编辑；Primary=`继续编辑`。
- `P02-03` 筹备中：准备度、阻断、待办、人员/Flow/Prize/Scene/Node 准备；Primary=`继续筹备`。
- `P02-04` 待彩排：彩排准备度、Flow/Scene/Media/Node/Output 检查、可用彩排时段；Primary=`发起彩排`。
- `P02-05` 即将开始：倒计时、最终准备度、签到/候选池/Node/Output；Primary=`进入 LIVE 准备`。
- `P02-06` 进行中：LIVE Badge、已运行时间、当前 Step、在线/签到、互动、Node/Output Health；Primary=`打开现场导演台`。
- `P02-07` 已结束：实际到场、互动、中奖、Claim、报告、图库；Primary=`查看活动报告`。
- `P02-08` 已归档：举办日期、归档人/时间、保留期限、原因、数据状态；Primary=`查看详情`。

## Actions

- `P02-A01` 创建活动 → P03-01。
- `P02-A02` 克隆活动 Modal：新名称/日期/负责人；选择复制 Flow/Program/Prize/Lottery Rule/Interaction/Scene/Theme/Media；明确不复制 Participant/Checkin/Winner/Claim/Session/Audit。
- `P02-A03` 归档活动确认：展示活动状态、未领取奖品、后台 Job、保留期限和归档影响。
- `P02-A04` 恢复活动确认：恢复后的 Event 状态、历史 Session 只读、Subscription Gate。
- `P02-A05` 删除草稿确认：仅无 Session 事实的 Draft 可删；存在事实则建议归档。
- `P02-A06` 导出活动：活动列表/基础信息/统计/准备度/执行数据/报告索引；Excel/CSV/PDF Summary。
- `P02-A07` 更多操作菜单：克隆、转交、归档、导出、删除草稿等按状态裁剪。
- `P02-A08` 转交负责人 Modal：目标成员、交接说明、未完成任务迁移。
- `P02-A09` 批量操作 Bar：批量负责人、归档、导出；危险动作逐项校验。
- `P02-A10` Rehearsal Preflight：人员/Flow/Program/Prize/Scene/Media/Node/Output 检查，Ready/Warning/Blocked/Not Enabled。
- `P02-A11` Create Rehearsal Session：Session 名称/计划时间/使用 Snapshot/确认。
- `P02-A12` LIVE Preflight：正式场完整 Gate，Blocked 项可深链修复。
- `P02-A13` Start Live Confirmation：目标 Event/Session、开始时间、当前 Node/Output、不可逆影响。
- `P02-A14` 高级筛选 Drawer：年份、类型、状态、负责人、地区、标签、异常、创建人、归档。
- `P02-A15` Quick Preview Drawer：不切 Event Context 查看活动摘要、待办、风险、最近 Session。

## States / Errors / Results

- `P02-S01` 首次加载。
- `P02-S02` 局部刷新。
- `P02-S03` 搜索无结果。
- `P02-S04` 当前 Tab 空状态。
- `P02-S05` Tenant 首个活动 Empty。
- `P02-S06` 批量选择状态。
- `P02-E01` 并发修改冲突。
- `P02-E02` 彩排阻断。
- `P02-E03` LIVE 启动阻断。
- `P02-E04` 报告生成失败。
- `P02-E05` 活动加载失败。
- `P02-E06` 无查看权限。
- `P02-E07` 无创建权限。
- `P02-E08` 套餐活动额度已满。
- `P02-E09` Subscription Grace。
- `P02-E10` Subscription Expired。
- `P02-R01` 草稿删除成功。
- `P02-R02` 活动归档成功。
- `P02-R03` 活动恢复成功。
- `P02-R04` 克隆成功并进入新 Draft。
- `P02-R05` Rehearsal Session 创建成功。
- `P02-R06` Live Session 启动成功 → P32。

---

