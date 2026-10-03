# Surface Registry

| ID | 类型 | 父面 | 名称 |
| --- | --- | --- | --- |
| P01-01 | screen | 根面 | 订单列表 |
| P01-02 | drawer | P01-01 | 导出范围 |
| P01-A01 | action | P01-01 | 打开导出 |
| P01-A02 | action | P01-02 | 提交导出 |
| P01-S01 | loading | P01-02 | 处理与结果核对 |
| P01-E01 | error | P01-02 | 已确认失败 |
| P01-R01 | result | P01-01 | 导出结果 |
