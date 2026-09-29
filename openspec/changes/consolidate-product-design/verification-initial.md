# 本次验证记录

日期：2026-09-29。对应 add-functional-design-skill；只读参考 Agent Browser 与 Evently，不修改它们的内容或状态。

## 已执行

- 新结构校验测试先因 validate_functional_design 缺失而失败；实现后新旧测试合计 30 项通过。
- `python3 -m unittest discover -s skills/functional-design/scripts -p 'test_*.py'`：30/30。覆盖缺页面/计划、未知动作目标、重复 ID、取消合同、缺 Registry 行、坏数据、清单遗漏、显式视图 ID、已有文件名映射、断链和快照完整性。
- `validate_functional_design.py` 对完整 Agent Browser 快照通过：24 份页面合同、8 个全局单元、194 个注册 Surface，原 Draft 状态不变。
- 旧 `validate_delivery.py --require-ready` 对 Agent Buddy 教学包通过，仅证明其旧结构合同。
- skill-creator quick_validate：通过；包级 `scripts/lint_skills.py`：16 skills / 0 errors。
- 79 个技能内部 Markdown 链接存在；37 个 Agent Browser 原文件与来源工作区 SHA256 一致；机器私有绝对路径扫描通过。
- `openspec validate add-functional-design-skill --strict --no-interactive`：通过。
- `git diff --check`：通过。

## 语义审阅结论

完整目录采用 Agent Browser，Evently 保持局部细节范例；原始快照不改写为审批通过。标准合同覆盖功能、页面结构、用户流程、全局交互、任务与独立状态。product-design 的文档规划入口在 Harness 分流之前，单功能/导航技能职责保留。旧 00–06 合同明确标注兼容用途，不要求新项目产出重复文档。

新校验器的文档声明与实际边界一致：任务依赖/全量业务覆盖、详细文案质量和审批仍需语义审查，脚本没有假装验证这些事项。CI 工作流已接入测试和范例结构检查，尚未在远端执行。

## 尚未执行

没有全局安装、发布、提交或推送；没有跨模型/独立会话的真实任务前向评测；没有视觉生成、真实浏览器功能验证。OpenSpec change 保留未归档。本次验证针对技能源码、引用与结构检查行为，不宣称任何 LLM 一定遵守全部内容。

离线 TRACE 基础分：4.4。评分器未识别编号中文工作流（报告 step_count=0），该启发式分数仅留作检查记录，不是行为通过率，也不为抬分添加无关章节。
