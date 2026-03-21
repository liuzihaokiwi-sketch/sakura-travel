## ADDED Requirements

### Requirement: PDF 轻水印渲染
PDF 渲染层 SHALL 在每页页脚右下角添加轻水印，包含订单号和「仅供本人使用」字样。水印 MUST 为淡灰色小字（opacity ≤ 0.15），不遮挡正文内容。

#### Scenario: 标准版 PDF 包含水印
- **WHEN** renderer 为 ¥248 标准版订单生成 PDF
- **THEN** PDF 每页页脚右下角显示 `订单号: {order_id_short} · 仅供本人使用`，字号 8px，颜色 rgba(0,0,0,0.12)

#### Scenario: HTML 预览也显示水印
- **WHEN** renderer 为任意订单生成 HTML 预览
- **THEN** HTML 底部包含相同水印样式（CSS `position: fixed; bottom: 12px; right: 18px`）

#### Scenario: 免费预览不含订单号水印
- **WHEN** renderer 为免费体验版生成预览 HTML
- **THEN** 水印文案为 `体验版 · 完整版请联系规划师` 而非订单号

### Requirement: 水印数据传递
renderer 的 `_build_render_context` SHALL 接收 `order_id` 参数并传入模板 context，模板使用 `{{ watermark_text }}` 渲染。

#### Scenario: order_id 传入渲染器
- **WHEN** `render_html(session, plan_id, order_id="abc123")` 被调用
- **THEN** 模板 context 包含 `watermark_text = "订单号: abc123 · 仅供本人使用"`

#### Scenario: order_id 缺失时的 fallback
- **WHEN** `render_html(session, plan_id)` 不传 order_id
- **THEN** 模板 context 包含 `watermark_text = "专属定制行程"`