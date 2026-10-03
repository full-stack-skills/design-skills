# Design relationship maps (generated)

Source: registry.json methodology. Read-only projection; approval and runtime evidence remain separate.
Registry SHA256: f240e9d138cd6dd5e3cc4ab8dec72dea9f7e90b3eb90548b9cdeb89e182850a1

Task index SHA256: cb98e40bd4204431adbe0d9264c1aefabfb5db2f5bc495e286a2c663544aba07

## Source fingerprints

| Source | SHA256 |
| --- | --- |
| FUNCTION-CATALOG.md | 2549ad3e53834a81f3de22dfb8ff5dff0aa85a3607085c7fdb7dd19e7c9517a3 |
| MASTER-PLAN.md | c96b3b72cd4c6a9192abbe0bc2f24bf84b5723cb52abf2c6dceaea70faf32410 |
| SCREEN-REGISTRY.md | cca108cf94e42092e78d49980ea84bfd60c53f62017b5af95ddb17761f3cde96 |
| USER-FLOWS.md | 721a3794adf2560ef0a019111ccd973df77be13f45903303319382a3327a6dfa |
| pages/P01.md | 337c9588a0249ea49c75c501b900eb19e50abb6b187fd87fdf0d51c3f30152eb |

## Business objects

| id | name | owner | source |
| --- | --- | --- | --- |
| O01 | Order | 订单服务 | pages/P01.md |
| O02 | ExportJob | 导出服务 | pages/P01.md |

## Features and dependencies

| id | page_ids | object_ids | upstream_ids | downstream_ids | source |
| --- | --- | --- | --- | --- | --- |
| F01 | P01 | O01, O02 |  |  | FUNCTION-CATALOG.md |

## Menus

| id | label | parent_id | default_page_id | page_ids | feature_ids | object_ids |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | 订单 | — | P01 | P01 | F01 | O01, O02 |

## Page specifications

| page_id | menu_id | actors | permissions | feature_ids | object_ids | core_question | layout_archetype | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | M01 | 订单分析员 | 订单读取, 订单导出 | F01 | O01, O02 | 找到哪些订单、要导出哪个范围？ | 过滤列表与范围抽屉 | pages/P01.md |

## Interaction surfaces

| surface_id | kind | parent_surface_id | source |
| --- | --- | --- | --- |
| P01-01 | screen | — | SCREEN-REGISTRY.md |
| P01-02 | drawer | P01-01 | SCREEN-REGISTRY.md |
| P01-A01 | action | P01-01 | SCREEN-REGISTRY.md |
| P01-A02 | action | P01-02 | SCREEN-REGISTRY.md |
| P01-E01 | error | P01-02 | SCREEN-REGISTRY.md |
| P01-R01 | result | P01-01 | SCREEN-REGISTRY.md |
| P01-S01 | loading | P01-02 | SCREEN-REGISTRY.md |

## Transitions

| id | action_id | kind | source | precondition | permission | state_change | success | failure | cancel | recovery | source_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FLOW01 | P01-A01 | local | P01-01 | 订单读取权限且列表已加载 | 订单读取 | 只打开范围抽屉，不生成文件 | P01-02 | P01-E01 | P01-01 | 保留列表筛选，刷新权限后重开 | USER-FLOWS.md |
| FLOW02 | P01-A02 | command | P01-02 | 导出权限、范围有效、无重复提交 | 订单导出 | 创建导出任务；确认完成后展示结果 | P01-R01 | P01-E01 | P01-02 | 保留范围；超时进入 P01-S01 先查询请求状态，核实未创建后才能重试 | USER-FLOWS.md |

## Design units

| id | task_id | surface_ids | mode | parent_unit_id | baseline_ref | frozen_regions | allowed_regions | acceptance | outputs | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DU01 | T01 | P01-01 | NEW_SCREEN | — | — | 导航, 页面外壳 | 订单列表业务区 | 显示订单号、状态、金额和更新时间；空列表保留筛选入口；返回保持组织与筛选, 冻结导航和外壳保持一致 | assets/DU01-P01-01.png | MASTER-PLAN.md#T01 |
| DU02 | T02 | P01-02 | OVERLAY_PARENT | DU01 | planned:DU01@v1; approval pending | 导航, 页面外壳 | 导出范围业务区 | 范围不可跨组织；抽屉打开不重排底图；取消保留列表位置并恢复导出按钮焦点, 冻结导航和外壳保持一致 | assets/DU02-P01-02.png | MASTER-PLAN.md#T02 |
| DU03 | T03 | P01-A01 | ACTION_HIGHLIGHT | DU01 | planned:DU01@v1; approval pending | 导航, 页面外壳 | 打开导出业务区 | 具备读取权限才能打开；打开/取消不创建导出任务；无权限显示原因和返回入口, 冻结导航和外壳保持一致 | assets/DU03-P01-A01.png | MASTER-PLAN.md#T03 |
| DU04 | T04 | P01-A02 | ACTION_HIGHLIGHT | DU02 | planned:DU02@v1; approval pending | 导航, 页面外壳 | 提交导出业务区 | 具备导出权限且范围有效才能提交；进行中禁止重复触发；确认完成后才进入结果面, 冻结导航和外壳保持一致 | assets/DU04-P01-A02.png | MASTER-PLAN.md#T04 |
| DU05 | T05 | P01-S01 | EDIT_PARENT | DU02 | planned:DU02@v1; approval pending | 导航, 页面外壳 | 处理与结果核对业务区 | 展示请求标识和当前任务状态；超时标为结果未知；先核对状态再决定继续等待或重试, 冻结导航和外壳保持一致 | assets/DU05-P01-S01.png | MASTER-PLAN.md#T05 |
| DU06 | T06 | P01-E01 | EDIT_PARENT | DU02 | planned:DU02@v1; approval pending | 导航, 页面外壳 | 已确认失败业务区 | 已确认失败才进入本面；显示原因并保留范围；修复入口回到原范围，不能宣称未知写入已回滚, 冻结导航和外壳保持一致 | assets/DU06-P01-E01.png | MASTER-PLAN.md#T06 |
| DU07 | T07 | P01-R01 | EDIT_PARENT | DU01 | planned:DU01@v1; approval pending | 导航, 页面外壳 | 导出结果业务区 | 显示已完成任务标识、导出范围与下载入口；下载失败保留结果并提供重新获取入口, 冻结导航和外壳保持一致 | assets/DU07-P01-R01.png | MASTER-PLAN.md#T07 |
