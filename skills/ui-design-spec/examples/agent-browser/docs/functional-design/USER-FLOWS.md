# 端到端交互流程

每条路径引用注册的功能。节点中无编号的文字是处理步骤，不是新页面。全局面取消返回实际来源并保留上下文。

## F01 首次进入与配置

首次启动无需配置模型就能进入本地首页。Agent 未就绪才引导配置；网站登录与模型认证分别管理。

```mermaid
flowchart LR
    Start[启动] --> Home[P01 首页]
    Home --> Local[P04 打开内置应用]
    Home --> Ask[A01 发起任务]
    Ask --> Ready{智能体可用?}
    Ready -->|否| Setup[P17 配置连接]
    Setup --> Auth[G04 用户认证]
    Auth --> Check[校验连接与能力]
    Check -->|成功| Ask
    Check -->|失败| Setup
    Ready -->|是| Task[P11 创建任务]
```

异常与恢复：配置取消返回首页；错误保留配置但不保存明文密钥；连接成功后恢复待发送内容，不自动提交。

## F02 应用打开与离线

首页快捷入口与应用中心指向同一应用记录。打开应用不等于获得所有本地能力。

```mermaid
flowchart LR
    Home[P01 首页] --> Apps[P03 应用中心]
    Apps --> Detail[P04 详情]
    Detail --> Permission{需要新能力?}
    Permission -->|是| Grant[G05 选择范围]
    Grant --> Open[打开应用标签]
    Permission -->|否| Open
    Open --> Network{联网?}
    Network -->|否| Offline[本地功能可用 / 云操作说明原因]
    Network -->|是| Online[本地与云业务]
    Online --> Work[P02 最近工作]
    Offline --> Work
```

异常与恢复：拒绝授权仍可返回详情；依赖被拒能力的按钮明确不可用；包加载失败提供重试，不能伪造空业务成功页。

## F03 浏览、登录与人工接管

用户在可见的 Servo 页面完成认证；Agent 继续使用同一受控 profile，须重新观察登录结果。

```mermaid
flowchart LR
    Address[SH01 地址栏] --> Web[P05 网页]
    Web --> Need{需要认证?}
    Need -->|是| Take[G04 人工接管]
    Take --> Verify[观察实际登录状态]
    Verify -->|成功| Resume[A01 继续任务]
    Verify -->|失败或取消| Wait[P11 等待用户]
    Need -->|否| Resume
    Resume --> Account{账号或页面变化?}
    Account -->|是| Observe[重新观察并复核权限]
    Account -->|否| Next[下一步操作]
```

异常与恢复：弹窗登录、跨域重定向、认证过期与重启恢复均需 Servo 实测；不支持的站点明确记录，不承诺任意网站可用。

## F04 Agent 执行闭环

用户目标变为可见任务。写入批准绑定具体对象、内容和账号；普通已授权只读动作不重复打断。

```mermaid
flowchart TD
    Ask[A01 目标与上下文] --> Plan[P11 步骤与范围]
    Plan --> Observe[观察 / 读取业务数据]
    Observe --> Prepare[准备动作并校验]
    Prepare --> Need{需具体确认?}
    Need -->|是| Approval[G03 确认内容与影响]
    Approval -->|取消| Paused[P11 等待或取消]
    Approval -->|批准且有效| Execute[登记意图后执行]
    Need -->|否| Execute
    Execute --> Verify[核验后置条件]
    Verify -->|未完成| Observe
    Verify -->|证据满足| Result[P12 成果]
    Verify -->|无法确定| Unknown[P11 结果未知待核对]
```

异常与恢复：过期目标、权限变化或内容变化都返回重新准备；模型文字、点击回执或 HTTP 200 不能充当业务成功证据。

## F05 职位业务完整路径

招聘是首个内置应用案例，核心浏览器与 Agent 不硬编码职位字段。

```mermaid
flowchart LR
    Search[J01 搜索职位] --> Detail[J01 阅读详情与来源]
    Detail --> Save[J02 保存候选职位]
    Save --> Compare[J02 对比职位]
    Compare --> Draft[J03 生成并编辑草稿]
    Draft --> Preview[J03 预览内容附件]
    Preview --> Confirm[G03 确认提交]
    Confirm --> Send[已授权账号执行]
    Send --> Verify{找到提交证据?}
    Verify -->|是| Done[P12 回执与来源]
    Verify -->|否| Unknown[P11 核对状态]
```

异常与恢复：搜索筛选、保存偏好不等于提交授权。站点无提交能力时保留草稿供人工使用；验证站点账号前不把演示数据当真实职位。

## F06 暂停、接管与取消

暂停阻止新的动作；正在发送的操作可能已经生效，状态必须如实表达。

```mermaid
flowchart LR
    Run[P11 运行中] --> Pause[请求暂停]
    Pause --> Drain{有在途动作?}
    Drain -->|否| Stop[已暂停]
    Drain -->|是| Check[等待回执 / 核对结果]
    Check --> Stop
    Stop --> Human[G04 人工处理]
    Human --> Refresh[重新观察与权限检查]
    Refresh --> Resume[继续任务]
    Stop --> Cancel[取消后续步骤]
    Cancel --> Result[保留已完成结果及未决事项]
```

异常与恢复：取消不撤销已提交申请；需要补偿时产生独立可审查动作。接管期间 Agent 不与用户争夺页面输入。

## F07 知识、引用与记忆

资料是原始内容，记忆是有来源和范围的可编辑事实，两者独立管理。

```mermaid
flowchart LR
    Library[P13 导入资料] --> Detail[P14 内容与来源]
    Detail --> Index{解析与索引成功?}
    Index -->|否| Retry[P14 原因与重试]
    Index -->|是| Context[G05 选择任务上下文]
    Context --> Ask[A01 基于资料回答]
    Ask --> Evidence[P12 引用证据]
    Evidence --> Propose[建议保存偏好]
    Propose --> Memory[P15 用户查看与修改]
    Memory --> Delete[删除 / 撤销使用]
    Delete --> Future[后续检索排除]
```

异常与恢复：来源被删后旧成果保留允许保留的摘要及来源失效标记；不能悄悄改旧结论。凭据不得进入资料记忆。

## F08 崩溃与未决提交恢复

恢复优先保证不重复产生外部副作用。

```mermaid
flowchart TD
    Restart[重启] --> Recovery[G07 发现恢复记录]
    Recovery --> Read[恢复标签 / 草稿 / 任务日志]
    Read --> Pending{存在未决写入?}
    Pending -->|否| Pause[P11 暂停等待继续]
    Pending -->|是| Unknown[P11 结果未知]
    Unknown --> Check[按业务证据核对]
    Check -->|确认已完成| Result[P12 回执]
    Check -->|确认未执行| Prepare[重新准备并取得必要确认]
    Check -->|仍不确定| Human[G04 人工核对]
```

异常与恢复：重启不会恢复已过期确认和旧节点句柄；恢复窗口关闭后，未决事项仍在任务中心可找到。

## F09 权限撤销与产品配置

用户可以撤销具体能力；产品默认配置不能放大用户已有授权。

```mermaid
flowchart LR
    Tools[P18 工具范围] --> Revoke[撤销能力]
    Revoke --> Gate[网关立即拒绝新调用]
    Gate --> Tasks[P11 相关任务暂停说明]
    Tasks --> Grant[G05 用户重新选择范围]
    Config[P20 产品配置] --> Preview[预览品牌 / 首页 / 预装应用]
    Preview --> Validate[配置校验]
    Validate --> Apply[应用并保留上次可用版本]
    Apply --> Home[P01 首页]
```

异常与恢复：产品配置为 V1.1；本期不会因规划该入口就创建可执行插件市场。配置失败保持上次可用版本。
