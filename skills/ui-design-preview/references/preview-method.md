# 同步预览运行与适配

## 独立运行

复制本技能 `assets/device-preview` 全目录到目标位置，在目录内运行：

```sh
python3 serve.py --port 8872
```

打开 `http://127.0.0.1:8872/review.html?section=models`。关闭终端服务即可停止。无需构建、数据库、模型密钥、CDN、原仓库或另一个技能。`file://` 不作为同源iframe评审入口。

验证需已有 Python Playwright 和可启动的 Chrome/Chromium。`CHROME_PATH` 可指定浏览器；不自动下载或安装依赖。

```sh
python3 verify_review.py
python3 verify_ui.py
```

两个脚本默认自己启动随机空闲端口并在结束时关闭。复核已运行入口可用 `verify_review.py --url <评审页URL>`，应用回归可用环境变量 `DEMO_URL` 指定原型入口。`--screenshot` 给出评审截图保存位置；完整交互回归写入 `review/`。测试使用独立浏览器上下文，不读取个人浏览器账号或凭据。

## 文件职责

| 文件 | 内容 |
|---|---|
| review.html / review.css / review.js | 对照台、设备框、统一状态、URL、iframe适配 |
| preview-bridge.js | 内部导航白名单、读取视图状态与应用对端状态 |
| index.html / app.js / styles.css | 完整响应式工作区、场景入口及基础样式 |
| models.js / models.css | 供应商管理、手填和模拟获取模型 |
| settings.js / settings.css | 设置分类与能力配置 |
| imports.js / imports.css | 链接/ZIP来源草稿导入 |
| product.js | 工作、任务、文件等演示场景 |
| assets/agentscope-logo.svg | 案例品牌原始矢量资源 |
| serve.py / verify_review.py / verify_ui.py | 启动、评审器回归、案例业务交互回归 |

## 接入别的交互项目

1. 先列出页面ID、设备、主题和实际文件/路由。场景必须语义一致；缺失对应页标记缺口，不能拿其他页面替代。
2. 复制完整参考后，在副本修改 `review.js` 的 `pages` 和 `targets`，将iframe入口指向自己的同源页面。
3. 当前案例适配器为 `window.previewRoute(pageId)` 和 `window.dispatch('theme-'+theme, null)`。前者清除旧弹窗及未完成演示请求，后者设置主题。可以在本地页面添加轻量包装函数，或替换 `applyTarget` 调用为已有应用API；不要把这些名字强加给生产代码。
4. 保持 `ready`/load处理：载入前只更新期望状态，load后读取最新状态，不能捕获旧参数。当前例子重新路由会清理未提交的临时场景状态，应提前说明，不联动真实写入。
5. 为新场景增加实际内容/标题断言、独立主题、慢载和失败检查。原型按钮可点不代表后端可用。

## 接入不同设备的静态HTML

原样提供的可运行案例是交互应用，不是任意HTML自动转换器。静态HTML按 `sceneId → device → theme → localFile` 建立白名单映射；修改副本的加载适配器以载入选定本地文件。仅在目标URL变化时改src，load后验证期望URL和页面身份，避免load处理中反复导航；需要时用递增版本号忽略旧响应。静态文件未提供深色版时禁用该主题，不能声称切换成功。截图作为独立视觉证据展示，不冒充可点击HTML。

## URL与恢复

- `page`、`theme`、`sync`、`last` 保存全局和最近操作端；`sync=0` 时另保存 `phone`、`pad`、`phoneTheme`、`padTheme`。
- `section=models` 为原入口兼容参数；显式有效 `page` 优先。
- 未知页面/主题回退到已注册默认值，不拼接任意URL，不读取URL中的业务凭据。
- 默认同步快捷控制及已接入的内部导航/弹窗/选项卡，不同步表单内容、保存、导入、删除；开启独立模式后顶部控制仍可统一选择两端。
- URL恢复页面与主题；内部临时子状态只在当前评审会话中联动，不写入URL。

## 验收场景与错误恢复

正常路径：两端供应商配置 → 获取模型 → 三种导入弹窗 → 设置，页面语义一致而布局分别响应实际视口。独立路径：Phone导入技能/浅色，Pad供应商配置/深色，刷新保持，再开启同步采用最近端。

资源错误：核对本地相对路径和文件是否全部复制；404不能计入通过。适配器错误：修复API与加载顺序，然后只重载受影响端。视口异常：检查iframe width/height，不用容器宽度覆写逻辑尺寸。浏览器依赖缺失：仍交付源码与启动方法，记录浏览器验证 `NOT_VERIFIED`。端口占用：另选空闲端口。请求用户要访问外部生产页面时先确认已有授权，不复制身份信息到示例。

复用时保留来源清单，修改后重新生成本次文件SHA256，不能把初始校验和当成更新后的证明。截图包含源页面、主题、设备、时间与验证范围，发现差异回到对应页面制作步骤，不自行扩大产品需求。

## 内部点击联动适配

案例在应用事件处理器之后加载 `preview-bridge.js`。`readPreviewView()`仅导出白名单内的页面身份、主题、弹窗及选项卡；`onPreviewChange(view)`将状态通知评审器；评审器通过`applyPreviewView(view)`更新另一端，并记录最近操作端。应用对端状态不能再回发通知，避免循环。仅监听导航类操作，输入、提交与删除不能触发广播。新项目需实现相同语义的适配器，不能仅复制外部选择器就声称内部联动完成。

验收至少实际点击：Pad压缩文件→Phone选项卡选中；Phone关闭导入→Pad关闭；进入供应商→双方同一配置；添加/获取模型→双方相应弹窗。另在Phone填写、确认添加模型，验证Pad表单及模型列表未收到该内容。
