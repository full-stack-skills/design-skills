## ADDED Requirements

### Requirement: 统一规格入口
The package SHALL expose complete functional planning through ui-design-spec spec mode and SHALL remove the standalone functional-design registration.

#### Scenario: 完整规划请求
- **WHEN** 用户要求功能清单、页面结构、交互流程与实施计划
- **THEN** spec 模式维护一套完整设计包，保留逐页合同、示例与校验，不自动启动渲染或 Harness

### Requirement: 专业职责与事实源
The skills SHALL share canonical feature/page IDs, authority versions and task references while limiting edits to each specialist's responsibility.

#### Scenario: 已有完整章节
- **WHEN** behavior 或 navigation 阶段获得已完成的规格章节
- **THEN** 核对该阶段所需内容并引用已有版本，仅补真实缺口，不生成另一套规格

### Requirement: 有界运行交接
Ui-design-spec SHALL process a Harness dispatch only within its named stage, and Harness SHALL resume the selected run without rerouting through the entrypoint.

#### Scenario: 运行内 task dispatch
- **WHEN** 已有 run 把 task 阶段交给 ui-design-spec
- **THEN** 返回该阶段的任务合同与证据，不重新选择模式、创建 run 或递归启动 Harness

### Requirement: 完整可移植示例
Ui-design-spec SHALL preserve the complete Agent Browser snapshot, focused Evently examples and read-only validators under its own skill directory.

#### Scenario: 独立技能目录
- **WHEN** 用户只安装 ui-design-spec
- **THEN** 示例内部引用和验证器可使用；没有原工作区也能阅读完整设计包，原 Draft 与验证边界不变

### Requirement: 运行兼容与审查边界
The integration SHALL preserve existing Harness profile identities and persisted run schemas, and SHALL keep guard findings separate from product decisions.

#### Scenario: 恢复已有设计运行
- **WHEN** 恢复持有原 profile stage plan 的 run
- **THEN** 继续原调度和证据门禁，不因技能入口合并自动迁移或批准产物

### Requirement: 六技能统一命名与旧运行兼容
The package SHALL register the six approved ui-design-* names and resolve historical handler names at execution boundaries without rewriting saved plans or journal history.

#### Scenario: 新建运行
- **WHEN** 使用新内置 profile 创建运行
- **THEN** 保存新的 profile 版本和 ui-design-* handler，目录、技能入口及清单一致

#### Scenario: 旧运行尚未派发
- **WHEN** 旧 stage plan 引用 product-design 或 feature-design 等旧名称
- **THEN** next-action 和新 dispatch 使用对应 ui-design-* 名称，原 stage plan 与既有日志不变

#### Scenario: 旧运行已派发
- **WHEN** 恢复已有旧名称的活动 dispatch
- **THEN** 返回可执行的新 handler 并保留 dispatch ID，查询不改写存储，完成仍使用同一 dispatch

### Requirement: 主题与连续性独立入口
The package SHALL additionally register ui-design-theme and ui-design-continuity as independent skills, preserving their theme assets and continuity responsibilities. Active references and affected Harness profiles SHALL use the registered names.

#### Scenario: 主题与连续性技能发现
- **WHEN** 用户选择主题或继续已有界面
- **THEN** 分别使用 ui-design-theme 或 ui-design-continuity，入口名称与目录和注册一致，技能正文不包含旧名称映射表

#### Scenario: 连续性阶段调度
- **WHEN** 新 profile 或已有运行需要执行连续性阶段
- **THEN** 派发到 ui-design-continuity，保留既有运行的记录与身份

### Requirement: 首次设计与连续性预检
The continuity stage SHALL produce pre-render constraints in initial, inherit or correction mode. Initial mode SHALL explicitly record the absence of an approved visual baseline without inventing approval. Candidate comparison SHALL occur after rendering in review. Evidence SHALL retain existing pass/fail/unknown/needs-decision statuses; not-applicable SHALL NOT be used as an unsupported stage status.

#### Scenario: 首次生成页面
- **WHEN** 首次设计没有获批视觉基线
- **THEN** continuity 返回 initial 模式约束、已确认产品事实与待探索视觉范围；完成预检可返回 pass，但不代表视觉或产品批准

### Requirement: 主题交接和视觉授权
The skills SHALL share theme identity, version, source, maturity and allowed changes. Existing theme choices SHALL be reused. Capability fallback SHALL preserve required decisions and approval gates. Visual outputs SHALL NOT contain unsolicited promotional watermarks.

#### Scenario: 已指定主题继续页面
- **WHEN** 用户要求在已有主题上继续
- **THEN** 引用原主题版本，不重新选择，不因模型或工具能力跳过必要确认

### Requirement: 任务索引校验
New full-product planning SHALL include a derived task coverage index referencing the canonical task source without duplicating execution status. A read-only validator SHALL reject missing coverage, unknown references, duplicate task IDs, missing source markers and cyclic dependencies. Historical source snapshots SHALL remain unchanged.

#### Scenario: 功能未被任务承接
- **WHEN** 声明的功能或 Surface 没有对应任务
- **THEN** 校验报告缺口，不提升完成状态
