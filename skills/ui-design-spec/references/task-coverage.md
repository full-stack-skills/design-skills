# 任务覆盖索引

新建完整功能设计包必须提供 `task-coverage.json`。它是原任务源的派生引用，不保存 checked/status/done/completed，不创建第二个计划。已有外部任务系统先提供本地只读导出并引用其原 ID；记录导出时间与原链接，由审查核实新鲜度。历史示例快照不改写。

```json
{
  "schema_version": 1,
  "features": ["F01"],
  "surfaces": ["P01-01", "P01-E01"],
  "tasks": [
    {"id": "T01", "source": "MASTER-PLAN.md", "marker": "## T01 页面与失败恢复",
     "feature_ids": ["F01"], "surface_ids": ["P01-01", "P01-E01"], "depends_on": []}
  ]
}
```

这是索引形状示例，不是完整产品。features 必须与功能清单的在范围 ID 对齐，surfaces 必须包含 registry 的全部视图、动作、状态、错误、结果及全局面。task ID 保留原 ID；source 相对索引文件，可指向原 OpenSpec tasks；marker 必须逐行精确且唯一匹配实际任务行/标题。多个任务可覆盖同一功能或 Surface；依赖引用任务 ID 且不得成环。

```bash
python3 <skill>/scripts/validate_functional_design.py <package> --require-task-coverage
python3 <skill>/scripts/validate_task_coverage.py <package>/task-coverage.json
```

独立脚本核验声明范围覆盖、引用、定位和依赖；完整包检查另对照 registry 的 Surface 集合。两者都不证明业务范围完整、文字内容深度、任务依赖的业务合理性或批准。语义审查必须对照功能清单与真实来源确认 features 没有遗漏，并核实任务内容与映射一致。
