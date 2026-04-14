## MODIFIED Requirements

### Requirement: fallback 产品数据对齐三档
`products.py` 的 `_FALLBACK_PRODUCTS` SHALL 与产品文档三档定义对齐：免费体验版（¥0）、标准版（¥248）、尊享版（¥888）。旧的 ¥19.9 fallback MUST 移除。

#### Scenario: DB 为空时返回三档 fallback
- **WHEN** `GET /products` 但 product_sku 表为空
- **THEN** 返回三个 fallback 产品：basic_free (¥0), standard_248 (¥248), premium_888 (¥888)

#### Scenario: features 包含正确的 max_modifications
- **WHEN** fallback 产品被返回
- **THEN** standard_248 的 features 包含 `max_modifications: 1`，premium_888 包含 `max_modifications: 3`