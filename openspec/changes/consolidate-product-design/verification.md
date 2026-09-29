# 六技能整合验证（2026-09-29）

## 已完成

正式入口为 ui-design-spec、ui-design-feature、ui-design-nav、ui-design-harness、ui-design-visual、ui-design-review。functional-design 内容归入 ui-design-spec；旧独立入口移除。包仍为 15 个技能，保留其他辅助技能。目录、frontmatter、manifest、双语目录、CI 和 eval 路径同步。

原六个已跟踪目录共 231 个文件均在新目录找到对应路径；完整示例和来源快照保留。Agent Browser 为完整产品组织范例，Evently 为摘录与模块细化范例。规格、专业章节、运行状态和审查分别确定责任与唯一事实源。

## 已执行证据

| 检查 | 结果 |
| --- | --- |
| Harness 全量 unittest discover | 126 项通过 |
| 规格两个校验器 unittest discover | 30 项通过，含 Agent Browser 快照清单与 SHA256 校验 |
| 完整 Agent Browser 设计包结构校验 | valid=true |
| Agent Buddy 历史小包 --require-ready | valid=true；仅旧格式结构教学 |
| scripts/lint_skills.py | 15 skills，0 errors |
| skill-creator quick_validate | 六个入口全部通过 |
| 活跃规格/功能/导航/Harness/审查文档相对链接 | 58 个路径存在；不含示例和第三方视觉文档 |
| openspec validate consolidate-product-design --strict --no-interactive | 通过 |
| git diff --check | 通过 |

新增兼容测试先出现三个目标失败，再在实现后四项通过：新 profile、新派发的旧计划、已派发的旧记录、未知自定义 handler。全量回归涵盖这些测试。旧记录保持原字节；执行边界解析正式技能名，既有 dispatch ID 保持不变。新 profile 使用递增版本，既有 profile ID、stage plan 和 schema 保留。

旧名称残留已检查：历史 handler 映射/兼容测试、来源说明、上游 URL、第三方 demo 和稳定服务标识属于保留范围；活跃调度使用新名。新增规格包及当前变更扫描未发现本机绝对路径。

## 边界与后续

- 结构测试不等于产品语义完整、用户批准或真实运行验收。评测场景已补齐，尚未执行跨模型真实任务评测，不能保证任何模型必然遵守。
- Agent Browser 打包快照散列有效；原项目工作区此后已有变化，不能把快照说成实时镜像。
- 未安装到宿主，未运行远端 CI，未提交、推送或发布。
- 当前 change 保留待审阅状态；不自动同步/归档历史规格，不触碰来源项目。

## 追加：主题与连续性统一命名

按用户确认新增 ui-design-theme、ui-design-continuity 两个正式独立名称，现为八个 ui-design-* 技能；包内总数仍为 15。目录、注册、入口、README、eval 和活跃调用已同步；技能正文不加入名称迁移说明。主题原有 13 个已跟踪文件与连续性 5 个文件迁移完整，资源内容核对通过。

新增连续性调度测试先因旧 handler 返回而失败，调整后 Harness 全量 127 项通过。两入口 quick_validate 通过，包 lint 为 15 skills / 0 errors，diff 空白检查通过。受影响 profile 版本递增，历史名称解析保留，旧运行记录不改写。未安装、提交、推送或运行远端 CI。

## 八技能闭环优化验证

- continuity 改为 initial/inherit/correction 生成前约束；initial 明确没有获批视觉基线，pass 只表示预检完成。已有 runtime 状态集不变，移除文档中无法执行的 not-applicable 跳过约定。
- 主题身份/版本/来源/成熟度接入 task、continuity、visual 和 review；已有选择不重复询问。候选差异检查只在生成后的 review 进行，问题通过调用方回到受影响职责并重查。
- visual 入口缩为按任务加载的指南；详细工作法下沉 references。移除按模型品牌降级、跳过必要确认、默认推广水印，修复动画案例断链；同步导出指南与章节规范。
- 新完整包增加派生 task-coverage.json 和 --require-task-coverage。检查任务覆盖、重复 ID、未知引用、原任务行定位、依赖成环和 Registry Surface 对齐；不复制执行状态。
- 实际验证：Harness 128 项通过，规格校验 42 项通过；八个入口 quick_validate 通过；lint 15 skills / 0 errors；当前非示例 Markdown 相对链接 88 项、零断链；OpenSpec strict 和 diff 空白检查通过。来源快照 SHA256 测试仍通过。
- 首次设计测试使用临时存储和合成上游证据，只证明预检派发/完成后可进入 candidate 而不进入批准状态，不证明任何模型能自动产生正确的约束或完成真实视觉任务。
- 任务索引只能证明声明范围内部一致；真实业务范围、任务语义和依赖合理性仍须审阅。模型行为场景已补充但未执行跨模型评测。没有安装、提交、推送或运行远端 CI。

## 提交前暂存检查

纳入全部新文件后，cached diff 空白检查发现历史范例中的尾部空行和 Evently 原文的 Markdown 双空格换行；保留这些来源内容，不为格式归一化改写原文快照。新增视觉工作法的尾部空行已清理。此前 diff 检查通过仅覆盖当时已跟踪差异，不代表全部未跟踪新文件无空白提示。暂存新增行的本机绝对路径、私钥头和 GitHub token 模式扫描无命中；该扫描不等价于完整秘密审计。

## Git 分发修复验证

原发布存在 12 个开发技能文件（4 个去重名称）和 16 个未跟踪的必要 JSON 资源。修复根目录及视觉技能内的忽略规则，取消 .agents/.kimi-code/.zcode 的开发 skills 跟踪，保留本地文件；原 OpenSpec specs/tasks 不受影响。保留工作区现有 Stitch handler 名称更新。

新增 scripts/check_distribution.py 与 CI 检查；修复前检查失败，修复后暂存清单为 15 个正式入口。通过 git checkout-index 导出临时干净副本，分发检查和 lint 通过，Harness 128 项、规格 42 项测试通过。使用本机已有 Skills CLI 1.7.0 执行 add <clean-copy> --list，实际返回 Found 15 skills，包含八个 ui-design-*，不包含 OpenSpec 技能。只列出，没有执行安装。

这次证据来自 Git 待分发文件，不借用主工作区被忽略的资源；未执行真实视觉生产或跨模型评测。
