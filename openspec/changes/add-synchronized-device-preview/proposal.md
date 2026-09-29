## Why

用户认可 AgentScope Phone/Pad 交互评审效果，要求快速切换联动，并将完整代码与方法直接收录到两个设计技能仓库。

## What Changes

- 新增独立技能 `ui-design-preview`，提供按需预览说明与完整、自包含的参考应用。
- 评审器默认同步页面/主题，支持前后切换、单端解锁、URL恢复、加载后应用最新选择。
- 保留实际设备逻辑视口；CSS缩放仅用于外层展示，不改变断点。
- 附带运行脚本、浏览器回归与代码来源散列，验证单技能复制即可运行。

## Capabilities

### New Capabilities
- `synchronized-device-preview`: 本地多设备场景联动评审及完整可携带示例。

### Modified Capabilities
无。

## Impact

只修改目标技能、对应目录说明与本变更；技能注册数量从15增加到16，不调用远程Stitch，不安装、发布或提交推送。源原型的实际实现依据其已有设计文档，本仓规格只管理技能资源的分发和使用合同。
