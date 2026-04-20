# 数据流视图

> 用户视角的端到端:从填表到拿到手账本。每步配一行"这时候在干嘛"。

```
填表 → 生成方案 → 预览确认 → 选预算 → 渲染手账本 → 交付
```

| 步 | 用户在做 | 系统在做 |
|---|---|---|
| 1. 填表 | 4屏轻表单(日期/城市/人群/节奏) | 收集表单数据 |
| 2. 生成方案 | 等待 | 装配引擎生成 N 日方案 |
| 3. 预览确认 | 看方案,调城市/风格/节奏 | 应用纠偏,重新装配 |
| 4. 选预算 | 选经济/中档/高档 | 计算升降档混搭 |
| 5. 渲染手账本 | 等待 | 60 页 PDF 生成 |
| 6. 交付 | 收到纸质手账本 + 贴纸 DIY 包 | 客服发货 |

## 文档去哪找

| 阶段 | 设计/规范在哪 |
|---|---|
| 填表 | [intake/](intake/) |
| 装配 | [SCHEMA.md](SCHEMA.md) + [templates/TEMPLATE_CREATION_GUIDE.md](templates/TEMPLATE_CREATION_GUIDE.md) |
| 预览/纠偏 | [intake/](intake/) |
| 预算 | [../content/kansai/policy.json](../content/kansai/policy.json) + [templates/CONTENT_POOL_WRITING_GUIDE.md](templates/CONTENT_POOL_WRITING_GUIDE.md)(餐厅预算档一节) |
| 渲染 | [page_system/](page_system/) + [product/](product/) |
| 交付 | [ops/SERVICE_FLOW.md](ops/SERVICE_FLOW.md) |
