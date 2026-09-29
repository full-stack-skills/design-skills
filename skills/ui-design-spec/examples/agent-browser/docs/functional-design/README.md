# Agent Browser 功能设计基线 v0.2

目标是可连续使用的浏览器、内置应用平台与 Agent 工作台。不是把几张页面并列成演示。技术路线固定为 Rust + Servo + 本地/远端网页；Codex 承载智能体运行。当前为设计草案，未宣称产品已实现。

## 文档权威与阅读顺序

1. [产品规格](../product-spec.md)：FR/NFR 及边界的唯一需求事实源。
2. [功能清单](FUNCTION-CATALOG.md)：24 个页面职责与范围、入口、需求对应。
3. [导航](NAVIGATION.md)及[界面结构](UI-STRUCTURE.md)：固定布局与位置，先于单页视觉设计。
4. [页面注册表](SCREEN-REGISTRY.md)：稳定子视图、操作面、状态、错误与结果编号。
5. [交互流程](USER-FLOWS.md)及[全局合同](GLOBAL-SURFACES.md)：端到端路径；逐功能细节在 pages/。
6. [实施计划](MASTER-PLAN.md)：依赖、阶段产物、验收门禁。
7. [设计执行](DESIGN-EXECUTION.md)和[状态](STATUS.md)：单元交付，禁止把生成图当批准或实现。
8. [Codex 接入](CODEX-INTEGRATION.md)：智能体载体的责任与验证边界。

registry.json 是页面 ID、操作目标与分解数据的机器可读登记，不替代产品规格。修改必须同步清单、页面合同与注册表；运行 `python3 scripts/check_design_registry.py` 检查关系。不得另外创建同义页面编号。

## 借鉴 Evently 的方式

参考 Evently 仓库的 `docs/specs/interfaces/tenant-console/NAVIGATION.md`、`REGISTRY.md`、`docs/specs/2026-09-06-design-execution-contract.md`，以及 P11/P11-A10 单操作任务合同：先导航，再稳定视图，再操作、状态、错误和结果；先确定入口与返回，再生成独立设计单元。借鉴方法而不继承其业务、颜色和抽屉比例。Evently 仓库本轮只读。

SDD：已有文档与部分脚手架，无需新建规格体系；本轮延续 product-spec.md，阶段为功能设计细化。未安装、初始化或迁移 Spec Kit/OpenSpec。交互细化为待评审设计，不静默改变既有核心要求。
