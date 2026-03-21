## ADDED Requirements

### Requirement: 行程脉络图（Journey Map Strip）
页面 SHALL 在 Day 1 时间轴结束后展示一个水平可滚动的「行程脉络图」，每天一个小卡片，展示 Day N + 城市名 + 主题词 + 锁定状态。

#### Scenario: 脉络图展示所有天
- **WHEN** 用户看完 Day 1 时间轴
- **THEN** 页面显示水平滚动的脉络图，包含完整 N 天（Day 1 已解锁，Day 2+ 显示 🔒）

#### Scenario: 脉络图移动端横向滚动
- **WHEN** 设备宽度不足以容纳全部天卡片
- **THEN** 脉络图可水平滑动，不溢出父容器

### Requirement: 亮点预告卡（Highlight Preview Cards）
页面 SHALL 在脉络图之后展示 2–3 张「亮点预告卡」，每张聚焦后续某天最值得期待的场景。

#### Scenario: 亮点预告卡展示
- **WHEN** 用户滚动至亮点预告区
- **THEN** 呈现 2–3 张卡片，每张包含：大 emoji 视觉焦点、主标题（「第 N 天 · 城市」）、一句情感描述、锁定标记

#### Scenario: 点击亮点预告卡触发付费引导
- **WHEN** 用户点击任意亮点预告卡
- **THEN** 触发 goToPricing，trigger 参数为 `highlight_card_N`

### Requirement: 节奏引导句（Rhythm Guide）
页面 SHALL 在亮点预告卡之后展示一句「你刚看完的只是开始」式引导句，并配合主 CTA。

#### Scenario: 节奏引导句展示
- **WHEN** 用户滚动至引导句区域
- **THEN** 展示引导句文案（从 `trial-day-hook.ts` 常量读取）和「解锁全部 N 天」按钮

### Requirement: 场景化 Hook 变体
`TrialDayHook` 组件 SHALL 接受 `scenario` prop（`'couple' | 'friends' | 'deep' | 'default'`），并根据场景选择对应亮点文案。

#### Scenario: 情侣场景
- **WHEN** `scenario === 'couple'`
- **THEN** 亮点预告卡显示情侣向文案（如「第 3 天 · 温泉之夜 — 泡完汤对方说这趟旅行值了」）

#### Scenario: 默认场景
- **WHEN** `scenario` 未传或为 `'default'`
- **THEN** 显示通用版本文案，适用于任意出行类型
