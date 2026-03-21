## Why

docs-human（产品真相源）与代码实现之间存在多处关键偏差：精调次数前后端矛盾、订单状态机不一致、PDF 水印声明了但未实现、自助微调 API 引用不存在的表、攻略生成缺少总纲/条件页结构、product_sku 旧架构与新三档产品不匹配。这些偏差会导致用户看到的承诺与实际功能脱节，影响信任和转化。MVP 优先级：**P0**（阻塞正式交付）。

本变更在产品价位梯度中的作用：确保 ¥0 免费体验版 → ¥248 标准版 → ¥888 尊享版三档产品的前后端、数据库、文档完全对齐，是所有后续功能开发的前提。

## What Changes

- **修复** 后端 `modifications.py` 精调次数硬编码，改为从 SKU features 读取（¥248=1次、¥888=3次）
- **修复** 订单状态机：统一 `docs-human/05-delivery-workflow.md` 与 `orders.py` 的状态定义
- **新增** PDF 水印渲染：在 `renderer.py` 和 Jinja2 模板中实现轻水印（订单号 + 仅供本人使用）
- **修复** `self_adjustment.py` 引用不存在的表（`plan_slots`, `entities` 等），改为使用 ORM 模型
- **重构** `products.py` fallback 数据，与三档定价对齐（¥0/¥248/¥888）
- **新增** 攻略生成结构增强：总纲页概念 + 条件页触发占位
- **标记** 前端多处精调次数硬编码（首页/价格页/交付页/升级页）— 前端页面后续单独处理

## Capabilities

### New Capabilities
- `pdf-watermark-impl`: PDF 渲染层实现轻水印，含订单号 + 使用声明，页脚角落淡灰色小字
- `itinerary-structure-enhance`: 攻略生成结构增强——总纲页骨架 + 条件页触发占位（为后续完整实现做基础）

### Modified Capabilities
- `modification-system`: 精调次数从硬编码改为 SKU features 驱动，对齐文档定义（¥248=1次、¥888=3次）
- `product-config-source`: product_sku fallback 与 API 响应对齐三档产品定义
- `swap-soft-engine`: self_adjustment.py ORM 迁移，修复引用不存在表的 500 错误

## Impact

- **后端文件**：`app/api/modifications.py`, `app/api/products.py`, `app/api/self_adjustment.py`, `app/domains/rendering/renderer.py`
- **模板文件**：`templates/itinerary_default.html`, `templates/magazine/base.html.j2`
- **前端文件**（标记但不在此变更修改）：`web/app/page.tsx`, `web/app/pricing/page.tsx`, `web/app/plan/[id]/page.tsx`, `web/app/plan/[id]/upgrade/page.tsx`
- **数据库**：可能需要 alembic migration 为 `plan_swap_logs` 等缺失表补建
- **文档**：`docs-human/05-delivery-workflow.md`, `docs-human/06-ops-and-customer-service.md` 已直接修复