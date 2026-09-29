## Context

原技能草稿已经具备全产品示例和结构校验，但功能、导航、文档与运行编排的触发范围存在重叠。用户批准以 ui-design-spec 统一入口，以 feature/navigation 为专业职责，以 Harness 为流程运行器，以 renderer/guard 为生成与审查。

## Goals / Non-Goals

目标：统一入口、固定文档交付、共享 ID/版本/任务源、无循环路由、保留实例与测试。
非目标：修改既有运行 schema、自动提升批准状态、合并全部专业技能、安装/发布、替代真实业务验收。

## Decisions

1. 资源直接迁入 ui-design-spec 的 references/assets/examples/scripts；不保留第二个可发现的 functional-design SKILL.md 或 manifest 项。原说明转为内部 spec-mode.md。
2. spec 模式维护全产品文档组织；ui-design-feature 负责行为章节，ui-design-nav 负责导航章节。已有完整合同先核对并引用，仅补实际缺口；单独安装 ui-design-spec 时按内置模板完成，不能因缺少可选专业技能而自动安装或伪称调用。
3. execution 只决定一次工作范围与 profile，然后交给 Harness；运行内 dispatch 到 ui-design-spec 时，仅处理 packet 指定的 baseline 或 task 阶段，不重进总入口、不建第二个 run。
4. 保留 product-to-ui 各阶段职责与 evidence_stage，更新新 profile 的 handler 名称及版本：behavior/navigation 阶段可以验证并引用已完成的 spec 章节，不强制重写。TASK_READY 引用原任务，不复制执行状态。已有 run 的 stage plan 不迁移。
5. Guard 对比同一输入版本并报告，不改需求；Huashu 只生成当前单元，不能把视觉探索当功能/导航重新设计。
6. 原 change 更名 consolidate-product-design，保留初始验证的历史事实，不同时维护两个同义 change。

## Validation

迁移前后范例 SHA256、技能引用、包注册、30 项原校验测试、包 lint、技能格式、Harness 回归和 profile smoke、OpenSpec strict validate。语义走查区分纯规格、单功能、导航修复、既有 run 恢复和有界 dispatch；未运行跨模型前向评测不得宣称已验证自动路由行为。

## Risks / Trade-offs

- 旧本地 draft 仍可能被人工引用：文档明确正式入口 ui-design-spec spec；不安装旧草稿。
- 自包含模式允许缺少可选专业技能：职责合同统一，但不宣称实际调用了不可用技能。
- 这次改变的是技能执行指令；单测通过不证明任意 LLM 都能遵循所有边界。

## 命名决策更新

用户确认六个 ui-design-* 名称，以正式名称统一入口和新运行的 handler。保留 profile ID、runtime schema 与既有 stage plan/dispatch/journal 原值；新增只读名称解析，next-action 和 dispatch 返回可执行的新 handler。新 profile 版本递增，旧运行不迁移。源码文件 design_harness.py 继续保留，避免无意义变更 Python 模块/API。第三方 URL、署名和完整来源快照不做批量替换。
