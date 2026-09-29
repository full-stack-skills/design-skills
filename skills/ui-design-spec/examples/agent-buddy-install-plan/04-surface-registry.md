# F07 页面与交互详规

以下为从原 B06 摘录继续细化的教学设计。字段顺序对应合同；并非产品实现证据。

## B06

- **feature_ids**：F07
- **preconditions**：来源与目标已选择；允许预览
- **context**：当前来源、目标和范围，不跨目标沿用计划
- **user_question**：计划是否有效，准备写入哪些内容？
- **required_information**：计划 ID、版本、目标、差异、风险、备份引用
- **secondary_actions**：返回选择并保留草稿
- **fields_and_validation**：来源/目标/范围必需；摘要由系统生成且只读；变更后旧计划失效
- **permission**：检查读取目标权限；预览不具有写盘权限
- **return_behavior**：回来源/目标选择，保留草稿，改变输入后重算
- **accessibility**：差异可键盘滚动，禁用继续时说明原因，关闭异常后恢复焦点
- **data_contract**：目标 InstallPlan 用例；API 名称尚未在本样例核定
- **visual_dependency**：沿用既有 B06 父页，双端信息结构一致；不决定全局导航争议
- **acceptance**：显示真实计划内容；过期时禁用继续，重算后替换计划标识
- **id**：B06
- **kind**：page
- **parent_id**：顶级页面
- **entry**：原来源/目标流程进入安装向导
- **layout**：步骤栏、输入摘要和计划工作区
- **primary_action**：进入计划预览
- **success**：B06-03
- **failure**：输入缺失时保留草稿并返回选择

## B06-03

- **feature_ids**：F07
- **preconditions**：来源与目标已选择；允许预览
- **context**：当前来源、目标和范围，不跨目标沿用计划
- **user_question**：计划是否有效，准备写入哪些内容？
- **required_information**：计划 ID、版本、目标、差异、风险、备份引用
- **secondary_actions**：返回选择并保留草稿
- **fields_and_validation**：来源/目标/范围必需；摘要由系统生成且只读；变更后旧计划失效
- **permission**：检查读取目标权限；预览不具有写盘权限
- **return_behavior**：回来源/目标选择，保留草稿，改变输入后重算
- **accessibility**：差异可键盘滚动，禁用继续时说明原因，关闭异常后恢复焦点
- **data_contract**：目标 InstallPlan 用例；API 名称尚未在本样例核定
- **visual_dependency**：沿用既有 B06 父页，双端信息结构一致；不决定全局导航争议
- **acceptance**：显示真实计划内容；过期时禁用继续，重算后替换计划标识
- **id**：B06-03
- **kind**：subview
- **parent_id**：B06
- **entry**：输入通过后生成冻结计划
- **layout**：页头计划标识；左侧文件差异；右侧风险/权限/备份；底部继续/返回
- **primary_action**：校验并审阅计划
- **success**：有效预览交给原审批流程；此样例不执行审批
- **failure**：B06-E01 展示具体变化对象

## B06-E01

- **feature_ids**：F07
- **preconditions**：来源与目标已选择；允许预览
- **context**：当前来源、目标和范围，不跨目标沿用计划
- **user_question**：计划是否有效，准备写入哪些内容？
- **required_information**：计划 ID、版本、目标、差异、风险、备份引用
- **secondary_actions**：返回选择并保留草稿
- **fields_and_validation**：来源/目标/范围必需；摘要由系统生成且只读；变更后旧计划失效
- **permission**：检查读取目标权限；预览不具有写盘权限
- **return_behavior**：回来源/目标选择，保留草稿，改变输入后重算
- **accessibility**：差异可键盘滚动，禁用继续时说明原因，关闭异常后恢复焦点
- **data_contract**：目标 InstallPlan 用例；API 名称尚未在本样例核定
- **visual_dependency**：沿用既有 B06 父页，双端信息结构一致；不决定全局导航争议
- **acceptance**：显示真实计划内容；过期时禁用继续，重算后替换计划标识
- **id**：B06-E01
- **kind**：error
- **parent_id**：B06
- **entry**：检测来源/文件/目标摘要变化
- **layout**：保留差异，顶部失效原因，突出重新预览，禁用继续
- **primary_action**：重新预览
- **success**：B06-03 展示新计划与摘要
- **failure**：保留失效标识，可返回选择

