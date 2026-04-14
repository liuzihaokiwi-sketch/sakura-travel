## MODIFIED Requirements

### Requirement: 精调次数校验
`modifications.py` SHALL 从 `product_sku.features.max_modifications` 动态读取最大精调次数，而非使用硬编码 map。当 features 中无此字段时，MUST fallback 到默认值：`standard_248=1, premium_888=3, basic_free=0`。

#### Scenario: SKU features 包含 max_modifications
- **WHEN** 用户提交精调请求，订单关联的 SKU features 为 `{"max_modifications": 3}`
- **THEN** 系统允许最多 3 次精调，第 4 次返回 403

#### Scenario: SKU features 无 max_modifications 字段
- **WHEN** 用户提交精调请求，订单关联的 SKU features 不含 `max_modifications`
- **THEN** 系统使用 fallback map（standard_248=1, premium_888=3）

#### Scenario: 精调次数用完后的提示
- **WHEN** 用户精调次数已用完
- **THEN** 返回 403，消息包含当前已用次数和上限，并引导升级

### Requirement: 精调次数读取解耦
`_count_modifications` 和最大次数获取逻辑 SHALL 通过统一函数 `get_max_modifications(sku_id, db)` 封装，供 API 和前端接口复用。

#### Scenario: 获取 max_modifications
- **WHEN** 调用 `get_max_modifications("standard_248", db)`
- **THEN** 返回 SKU features 中的 `max_modifications` 值，或 fallback 值 1