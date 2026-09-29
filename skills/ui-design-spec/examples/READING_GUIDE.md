# 完整范例与局部范例怎么读

## 主要范例：Agent Browser 全产品文档包

从 [README](agent-browser/docs/functional-design/README.md) 开始，再看 [功能清单](agent-browser/docs/functional-design/FUNCTION-CATALOG.md)、[导航](agent-browser/docs/functional-design/NAVIGATION.md)、[界面结构](agent-browser/docs/functional-design/UI-STRUCTURE.md)、[交互流程](agent-browser/docs/functional-design/USER-FLOWS.md)、[Registry](agent-browser/docs/functional-design/SCREEN-REGISTRY.md)。

以职位链学习连续产品体验：J01 搜索→J02 保存/对比→J03 申请草稿→G03 具体确认→任务/成果。逐项查 [J01](agent-browser/docs/functional-design/pages/J01.md)、[J02](agent-browser/docs/functional-design/pages/J02.md)、[J03](agent-browser/docs/functional-design/pages/J03.md)、[全局合同](agent-browser/docs/functional-design/GLOBAL-SURFACES.md)、[P11 任务](agent-browser/docs/functional-design/pages/P11.md)、[P12 成果](agent-browser/docs/functional-design/pages/P12.md)，以原流程的条件与去向为准，不把本句简写当成固定顺序。

最后读 [实施计划](agent-browser/docs/functional-design/MASTER-PLAN.md)、[设计执行](agent-browser/docs/functional-design/DESIGN-EXECUTION.md)、[状态](agent-browser/docs/functional-design/STATUS.md)，学习如何分开文档、视觉、批准、实现和运行验收。所有 24 份 pages 合同均在包内；按目标业务加载相关条目。

### 完整程度与来源边界

- 全量拷入当时 `docs/functional-design` 的 36 个文件，另外附 1 份上游 [product-spec](agent-browser/docs/product-spec.md)，共 37 个原文件；不是重新编写的缩略例子。
- [provenance.json](agent-browser/provenance.json) 记录源 HEAD、工作区属性及每文件 SHA256。采集于 2026-09-29，来源含尚未提交的文档；快照不是发布版。
- 原字节保留，内部文档链接可以离线阅读。原文提到的仓库级校验命令、源码、工具版本等是历史上下文；当前技能用下方命令检查本快照。
- “完整范例”指完整文档目录和贯通关系，并不意味着全部业务细节已批准。当前 Draft、未验收和未运行状态保留。
- 部分页面的字段/分区仍较简短，取消/失败有共用措辞；新项目必须依技能模板按动作细化，不能直接复制为通过的语义评审。真实图稿、目标产品技术栈与业务运行也不因读到范例就成为事实。

## 细节范例：Evently

[原成果摘录](evently-source-excerpts.md)与[来源记录](evently-source-provenance.json)展示真实模块规格、导航、Registry 及设计任务合同。[P06 贯穿案例](evently-functional-design-walkthrough.md)展开字段、Preview/Commit、失败恢复和任务说明；[P02 案例](evently-pattern.md)与[原 Registry](evently-p02-source.md)提供另一业务链。

此前 Evently 示例是“原文摘录 + 单模块完整链路”的教学案例，**不是 Evently 全产品目录快照**。其 00–06 为教学章节顺序；映射到当前标准文件即可，不要求另造一份 00–06 文档包。以 Agent Browser 学全产品组织，以 Evently 学每个模块应展开到什么深度。

## 历史格式：Agent Buddy 小范围教学包

[Agent Buddy 单功能包](agent-buddy-install-plan/00-scope-and-sources.md)及[接续示例](continuation.md)保留旧 product-interface-spec 草稿的七文档 + delivery.json 形式，仅用于旧格式和任务追踪教学。1 功能、3 Surface、1 旅程、2 任务映射不代表完整产品，也不代表满足本技能的全产品深度。

## 本地验证

在技能目录执行：

```bash
python3 scripts/validate_functional_design.py examples/agent-browser/docs/functional-design
python3 scripts/validate_delivery.py examples/agent-buddy-install-plan --require-ready
python3 -m unittest discover -s scripts -p 'test_*.py'
```

这些证明结构与校验行为，不证明新项目产品正确、获得批准或任何智能体都会自动遵循。未执行跨模型真实任务评测，不复制历史审阅 pass。
