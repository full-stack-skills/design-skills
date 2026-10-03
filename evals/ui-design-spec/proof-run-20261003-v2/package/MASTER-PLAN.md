# 独立设计任务

## T01 订单列表

Surface: P01-01；模式 NEW_SCREEN；父单元 None；母版 None。
冻结：导航、页面外壳。允许：订单列表业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU01-P01-01.png。
验收：显示订单号、状态、金额和更新时间；空列表保留筛选入口；返回保持组织与筛选。原件尚未生成，母版批准前不执行继承视觉任务。

## T02 导出范围

Surface: P01-02；模式 OVERLAY_PARENT；父单元 DU01；母版 planned:DU01@v1; approval pending。
冻结：导航、页面外壳。允许：导出范围业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU02-P01-02.png。
验收：范围不可跨组织；抽屉打开不重排底图；取消保留列表位置并恢复导出按钮焦点。原件尚未生成，母版批准前不执行继承视觉任务。

## T03 打开导出

Surface: P01-A01；模式 ACTION_HIGHLIGHT；父单元 DU01；母版 planned:DU01@v1; approval pending。
冻结：导航、页面外壳。允许：打开导出业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU03-P01-A01.png。
验收：具备读取权限才能打开；打开/取消不创建导出任务；无权限显示原因和返回入口。原件尚未生成，母版批准前不执行继承视觉任务。

## T04 提交导出

Surface: P01-A02；模式 ACTION_HIGHLIGHT；父单元 DU02；母版 planned:DU02@v1; approval pending。
冻结：导航、页面外壳。允许：提交导出业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU04-P01-A02.png。
验收：具备导出权限且范围有效才能提交；进行中禁止重复触发；确认完成后才进入结果面。原件尚未生成，母版批准前不执行继承视觉任务。

## T05 处理与结果核对

Surface: P01-S01；模式 EDIT_PARENT；父单元 DU02；母版 planned:DU02@v1; approval pending。
冻结：导航、页面外壳。允许：处理与结果核对业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU05-P01-S01.png。
验收：展示请求标识和当前任务状态；超时标为结果未知；先核对状态再决定继续等待或重试。原件尚未生成，母版批准前不执行继承视觉任务。

## T06 已确认失败

Surface: P01-E01；模式 EDIT_PARENT；父单元 DU02；母版 planned:DU02@v1; approval pending。
冻结：导航、页面外壳。允许：已确认失败业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU06-P01-E01.png。
验收：已确认失败才进入本面；显示原因并保留范围；修复入口回到原范围，不能宣称未知写入已回滚。原件尚未生成，母版批准前不执行继承视觉任务。

## T07 导出结果

Surface: P01-R01；模式 EDIT_PARENT；父单元 DU01；母版 planned:DU01@v1; approval pending。
冻结：导航、页面外壳。允许：导出结果业务区。
输入：P01、USER-FLOWS、Registry 与父任务合同。交付：assets/DU07-P01-R01.png。
验收：显示已完成任务标识、导出范围与下载入口；下载失败保留结果并提供重新获取入口。原件尚未生成，母版批准前不执行继承视觉任务。
