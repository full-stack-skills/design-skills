## Why

用户确认以 ui-design-spec 为统一入口，spec 模式提供完整功能设计包，执行模式组织后续设计。新增 functional-design 与现有功能/导航技能职责重叠，需要收敛为单一入口并消除入口与 Harness 的反复分流。

## What Changes

- 将 functional-design 的合同、模板、完整 Agent Browser 范例、Evently 案例和校验器迁入 ui-design-spec，移除独立注册。
- 定义 spec、execution 两种用户模式，以及运行内的有界 dispatch 处理；共享原规格、页面 ID 与任务事实源。
- 收窄 ui-design-feature、ui-design-nav、ui-design-harness、ui-design-visual、ui-design-review 的交接边界。
- 更新包目录、CI 路径和验证记录；保留 Harness profile ID 与持久化 run 格式；更新受影响 profile 版本和新 handler，解析历史 handler。

## Capabilities

### New Capabilities
- `product-design-spec`: ui-design-spec 的完整功能设计规格模式与有界交接。

### Modified Capabilities
- 无既有正式 capability delta；现有专业技能入口规则统一，不改变 Harness runtime schema。

## Impact

本 change 由原 add-functional-design-skill 原地更名并演进，最初验证保留在 verification-initial.md。不安装、不发布、不提交推送、不切分支；只读参考仓库。撤销 functional-design 独立入口是用户已确认的整合范围。

## 已确认命名（2026-09-29）

统一注册 ui-design-spec、ui-design-feature、ui-design-nav、ui-design-harness、ui-design-visual、ui-design-review。目录、frontmatter、manifest、调用路径同步调整。旧 handler 在运行边界解析为新名，不改写已有日志；新的内置 profile 使用新 handler 并递增版本。

## 主题与连续性命名补充

用户确认保留两个独立技能 ui-design-theme 和 ui-design-continuity，统一命名后为八个 ui-design-* 技能。同步目录、注册、使用引用、评测和受影响 profile；不向技能正文添加旧名称映射或迁移兼容说明。
