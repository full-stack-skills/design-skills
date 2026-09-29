---
name: ui-design-preview
description: Build runnable local UI previews with synchronized page/theme switching and fixed device viewports. Use for interactive prototype previews, Phone/Pad comparisons, independent side-by-side review, and portable preview delivery.
license: Apache-2.0
---

# UI Design Preview

本技能独立负责预览与对比。`ui-design-visual`继续负责页面制作，`ui-design-review`负责正式设计审查；不要为预览任务重新生成已确认页面。

## When to use

为已有页面建立可点击的本地对照台：同步切换同一场景，检查 Phone/Pad 的布局差异，比较浅深主题，或交付可复制运行的评审附件。不要用一张桌面截图缩小后冒充移动布局。页面制作、视觉批准和生产运行验收分别记录。

## How to use · Workflow

### Step 1：确认输入

读取当前任务的页面ID、已确认设计、视口、主题、源文件及输出位置。保护已有修改；已有规格继续作为事实源，不建立另一份产品需求。范围明确时直接执行，只有缺失页面或互相冲突的合同才询问。
### Step 2：复制完整示例

将本技能 [完整应用](assets/device-preview/review.html) 所在的 `assets/device-preview` 目录整体复制到目标输出目录；不要只拷贝评审壳，不依赖兄弟技能或原仓库。保持所有相对路径，替换项目品牌时保留来源记录。按需读取 [运行与适配合同](references/preview-method.md)。
### Step 3：映射同一场景

在副本的 `review.js` 维护页面目录和设备尺寸，在页面侧实现场景与主题适配器。默认例子是 Phone 390×884、Pad 768×1024；Desktop 1280×1024仅在用户要求且有对应页面时添加。保持iframe逻辑视口不变，只缩放外层展示。
### Step 4：启动与实际操作

在复制目录执行 `python3 serve.py --port 8872`，打开打印的回环地址。使用统一页面、前后按钮、主题、各端快捷选择；再点击界面内导航和“链接地址/压缩文件”等选项卡确认联动；关闭同步分别查看，重新开启跟随最近操作端。刷新验证URL恢复，重载单端验证最新选择能回放。
### Step 5：验证与修正

在已具备 Playwright/Chrome 的环境执行 `python3 verify_review.py` 和 `python3 verify_ui.py`。前者自启临时服务并检查评审联动，后者覆盖完整案例业务交互。实际接入新项目后，替换案例选择器和断言，再运行，不能沿用旧例的通过结果。浏览器/依赖缺失时报告未验证，不静默安装。
### Step 6：交付

给出预览入口、完整目录、页面/设备映射、输入来源版本、实际截图和检查结果；列出缺失场景、错误资源和未接入能力。截图与可点击演示不能证明原生应用或真实后台能力已完成。

## 操作合同

| 操作 | 预期结果 |
|---|---|
| 顶部选择页面/主题、前后切页 | 一次切换全部设备 |
| 同步开启时使用单端快捷选择 | 传播到另一端，并更新全部选择器 |
| 点击任一端内部导航、导入方式、添加/获取模型入口 | 另一端进入同一场景，布局各自适配 |
| 关闭同步后选择单端 | 另一端维持页面和主题 |
| 重新开启同步 | 采用最近操作端的页面和主题 |
| 刷新或某端晚加载 | 按URL和当前选择恢复，不回放过时值 |
| 页面适配器缺失 | 显示失败，修复后重载；不能显示已同步 |

同步包括评审场景/主题及白名单中的内部导航、弹窗开关和选项卡。通过页面适配器报告语义状态，禁止重放任意点击。输入、密钥、保存、导入、网络请求和删除绝不转发到其他设备。URL只存场景、主题、联动状态，不存业务数据。示例包含模拟模型获取与来源草稿导入，须保留演示说明。

## Validation checklist

- [ ] 完整目录复制到项目外临时目录后，页面和本地SVG均能加载，无404和脚本错误。
- [ ] 全局和单端联动、独立对照、重新同步、URL恢复及慢载/重载均按合同执行。
- [ ] iframe逻辑宽度与指定设备一致，窄评审窗口仅改变展示比例，无页面横向溢出。
- [ ] 模型列表、手填/获取模型、技能/智能体/插件导入的演示范围没有被说成真实服务。
- [ ] 实际对照截图、执行日志和已知缺口均可追溯；未修改已确认基线。

## 不适用与边界

本技能只对照已有可信HTML或交互原型，不负责凭空补设计、远程生成、上线发布或真实模型/包安装。输入只有截图时仅做视觉评审；需要行为验收必须有可运行页面。没有源文件或来源映射时报告缺失项，不把自带案例包装成用户项目结果。

## Gotchas

1. **逻辑尺寸被缩放替换**：检查iframe内的innerWidth；CSS transform只作用于外层显示，不能把390改成可用容器宽度。
2. **迟到页面覆盖新选择**：load事件读取当前期望状态，快速切三页后最后一页仍须生效。
3. **两端布局不同被误判**：同一场景在手机逐级返回、Pad主从分栏是合理差异；比较语义和可达操作，不要求像素相同。
4. **任意广播用户操作**：只广播已登记的页面、主题、弹窗与选项卡状态，不能复制输入、提交或凭据；每个新内部入口都需适配和实际点击验证。
5. **示例验证冒充实际验证**：接入新页面后更换断言并重新运行；保留Stitch来源ID，不伪造远端回执。
6. **单技能安装后缺文件**：完整复制本技能内部资源，用项目外临时目录检查；不得指向兄弟技能的资产。

## Best Practices

仅运行可信本地原型。现有示例使用同源iframe直接调用，服务器只监听127.0.0.1；端口占用时换端口，不杀未知服务。跨源页面不可通过关闭浏览器安全策略接入；若确需消息桥，显式验证origin、source、协议版本和数据白名单。静态截图只能比较视觉，不能验证交互。单端404、缺失资源或适配器失败先修复来源映射，不盲目重新生成界面。

## Output contract

交付 `preview_url`、`source_directory`、场景/设备/主题清单、源版本或SHA256、截图、实际执行检查、失败/跳过项和下一步。检查未执行记为 `NOT_VERIFIED`；完整代码存在不等于完成验收。原型修改与生产实现分别记录。

## References

- [运行、适配和故障恢复](references/preview-method.md)
- [完整应用说明](assets/device-preview/README.md)
- [来源与代码校验说明](assets/device-preview/SOURCE.md)
- [场景联动浏览器回归](assets/device-preview/verify_review.py)
- [模型及导入完整交互回归](assets/device-preview/verify_ui.py)

## Examples

- [正常预览与独立对照](examples/synchronized-review.md)
- [只有截图与来源缺失](examples/missing-input.md)
- [慢载与适配器恢复](examples/load-recovery.md)

## Keywords

UI preview, synchronized preview, device comparison, responsive review, 交互预览, 同步切页, 多设备对照, 手机, 平板, 主题对比
