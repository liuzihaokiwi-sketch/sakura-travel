## ADDED Requirements

### Requirement: 用户分层维度定义
系统 SHALL 用两个维度对用户分层：`japan_experience`（首次 / 熟客）× `play_mode`（多城 / 一地）。

#### Scenario: 四个象限覆盖完整
- **WHEN** 系统读取用户的 `japan_experience` 和 `play_mode`
- **THEN** 能匹配到以下四个象限之一：首次+多城 / 首次+一地 / 熟客+多城 / 熟客+一地

### Requirement: 分流推荐规则常量
`web/lib/content/segmentation.ts` SHALL 导出 `SEGMENTATION_RULES`，包含四条规则，每条规则说明该象限下的权重调整方向。

#### Scenario: 首次去日本用户规则
- **WHEN** `japan_experience` 为 `first_time`
- **THEN** 规则指向：提升经典景点权重、降低冷门地权重、启用"避坑优先"模式

#### Scenario: 熟客用户规则
- **WHEN** `japan_experience` 为 `experienced`
- **THEN** 规则指向：降低已广泛打卡景点权重、提升本地化 / 隐藏地 / 非游客区权重

#### Scenario: 多城顺玩规则
- **WHEN** `play_mode` 为 `multi_city`
- **THEN** 规则指向：优化跨城衔接顺序、优先选顺路目的地、控制单城停留天数

#### Scenario: 一地深玩规则
- **WHEN** `play_mode` 为 `single_city`
- **THEN** 规则指向：降低跨城行程、增加单城不同区域深度、允许同城多次往返

### Requirement: 四种语气模板常量
`web/lib/content/segmentation.ts` SHALL 导出 `DELIVERY_TONE`，四种语气各一段短模板，供文案生成时注入 prompt 前缀。

#### Scenario: 首次用户语气
- **WHEN** 生成首次用户的交付文案
- **THEN** 使用引导式、解释多、带"为什么这样安排"的语气

#### Scenario: 熟客语气
- **WHEN** 生成熟客用户的交付文案
- **THEN** 使用简洁、直接、少废话、假设对方已知基础常识的语气
