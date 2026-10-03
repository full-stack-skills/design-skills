# Product Design — Pressure Scenarios

These scenarios capture orchestration failures that occur when a ui-design-spec task spans requirements, navigation, visual continuity, documentation, rendering, and verification.

## RED-01 — One giant skill reimplements everything

**Prompt**

> Design this product end to end. We already have skills for feature specifications, navigation, documentation, Stitch/Pencil, and testing.

**Observed baseline failure**

The agent writes a new monolithic workflow that duplicates feature modeling, route contracts, documentation templates, rendering instructions, and test mechanics instead of delegating to existing atomic skills.

**Expected behavior with the skill**

Act as an orchestrator. Identify the current design stage, invoke only the atomic skills required for the missing decisions, and pass stable contracts between them.

## RED-02 — “Continue” restarts discovery

**Prompt**

> The information architecture and first two pages are already approved. Continue with the next page.

**Observed baseline failure**

The agent starts over by asking for product positioning, style direction, or menu structure that is already approved.

**Expected behavior with the skill**

Recover the latest approved state, determine the next unfinished task, preserve locked decisions, and continue from the current checkpoint. Ask only when a missing decision materially blocks the next step.

## RED-03 — Visual execution starts before behavior/navigation are ready

**Prompt**

> Generate the next high-fidelity page now. The actions, permissions, and route behavior are still ambiguous.

**Observed baseline failure**

The agent jumps directly to visual generation and invents missing semantics in the prompt.

**Expected behavior with the skill**

Route unresolved behavior to `ui-design-feature` and unresolved hierarchy/route behavior to `ui-design-nav` before visual execution.

## RED-04 — Tool success is reported as product completion

**Prompt**

> Stitch rendered successfully. Mark the page done.

**Observed baseline failure**

The agent treats a rendered artifact as approved product design.

**Expected behavior with the skill**

Keep rendering, visual approval, contract approval, implementation verification, and archival as separate gates.

## GREEN acceptance

A response passes when it:
- identifies current stage and authority sources;
- reuses existing atomic skills instead of duplicating them;
- preserves approved decisions while continuing;
- refuses to silently invent missing product semantics;
- distinguishes candidate, approved design, implementation, and verified delivery;
- outputs a clear next action and handoff contract.


## RED-05 — Multi-stage execution has no run controller

**Prompt**

> The design plan is clear. Execute the remaining pages across feature checks, continuity, rendering, review, approval, and resume tomorrow if needed.

**Observed baseline failure**

The router directly sequences specialist skills in conversation but creates no persistent run, no transition state, no evidence ledger, and no deterministic resume point.

**Expected behavior with the skill ecosystem**

`ui-design-spec` identifies the stages and hands multi-step execution to `ui-design-harness`, which owns run state, evidence, reconciliation, approval gates, correction invalidation, and resume behavior.


## RED-06 — Harness selected but SOP profile is not

**Prompt**

> Continue one approved product page, batch-generate six sibling pages, and separately fix a local design issue.

**Observed baseline failure**

The router sends every request to `ui-design-harness` without selecting a task-specific SOP. The runtime then needs ad-hoc exceptions or reopens stages that should already be locked.

**Expected behavior with the skill ecosystem**

`ui-design-spec` selects the narrowest built-in profile: `existing-product-next-page` for one continued page, `page-family-batch` for shared-baseline siblings, and `design-correction` for scoped feedback. It leaves the profile's internal stage plan to `ui-design-harness`.

## SPEC-01 — 完整规划被缩减为几个页面

**Prompt**: 按完整设计合同整理业务产品，必须有功能清单、界面结构、交互流程和任务。

**Expected**: 选择 spec 模式；先盘点范围再覆盖全部在范围内的页面/共享界面与流程，按模板提供逐页合同、动作失败恢复、稳定 ID 和任务依赖。按合同展开模块与操作，不套用其它项目的业务或页面数量。不启动渲染或 Harness，不以三个示范页面结束全产品任务。

## SPEC-02 — 已有文档被复制成第二套规格

**Prompt**: 已有 OpenSpec 任务和 NAVIGATION，补齐功能设计并交给视觉阶段。

**Expected**: 保留原任务事实源和 ID，专业内容写回明确章节。核对已有导航是否足够，只补缺口。交接携带版本和验收，不复制任务执行状态；是否进入视觉执行遵循用户授权。

## SPEC-03 — 运行内 dispatch 递归启动入口

**Prompt**: Harness 给 ui-design-spec 派发 task 阶段，继续处理。

**Expected**: 只完成 packet 对应阶段；使用相同 run/dispatch 身份返回证据，不再次选择 profile、start/ensure-run 或重新发起全产品整理。

以上为评测场景与判据，尚未执行跨模型真实任务评测；不是通过记录。

## LOOP-01 — 首次页面没有视觉基线

输入：已有功能和导航合同，需要首个页面，尚无获批视觉基线。期望：主题保持实际成熟度；continuity 使用 initial 生成前约束；随后制作候选并审查。不得要求提供不存在的旧图，不伪造批准，不提交 not-applicable。

## LOOP-02 — 已指定主题且工具能力有限

输入：沿用当前主题与 Shell，只有串行工具，调整局部页面。期望：继承身份/版本，顺序执行；不重新选主题，不跳过必要决定，不添加推广水印。

## LOOP-03 — 审查发现导航漂移

输入：候选与既有导航合同不符。期望：review 返回失败证据与受影响 ID，调用方安排视觉修正或权威冲突决定；保留原 run，修正后重查，不重建需求文档。

这些是待执行的模型行为评测场景，不是模型评测通过记录。

## METHOD-01 — 六项合同与失败恢复

输入：客服客户中心已有导航与批准外壳；详情母图未批准，编辑抽屉保存后超时；需要六项规格产物，不授权渲染。期望：保留导航、完整拆出页面/状态/流程/任务；未知结果先核对；规划继续，继承视觉依赖绑定父图；不套用其它项目颜色或尺寸。实际演练及结构回归见 [methodology-validation.md](methodology-validation.md)，仅该场景有本轮证据，不提升其它场景为已通过。
