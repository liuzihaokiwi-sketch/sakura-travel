## MODIFIED Requirements

### Requirement: Free 卡（一日体验版）产品文案
Free 卡的名称、tagline、includes 列表、CTA 文案 SHALL 体现「完整体验第 1 天」而非「免费摘要」，不得让用户误以为体验版只是残缺内容。

#### Scenario: Free 卡名称与 tagline
- **WHEN** 用户查看定价页 free 卡
- **THEN** 显示名称「一日体验版」，tagline「完整体验第 1 天，不是摘要」

#### Scenario: Free 卡 includes 列表
- **WHEN** 用户查看 free 卡权益列表
- **THEN** 至少包含：完整 Day 1 时间线（精确到 30 分钟）、每个景点推荐理由（专业判断）、Day 1 餐厅推荐（含预约提示）、Day 1 拍摄指南、Day 1 避坑提醒、Plan B（遇雨/排队长备选）

#### Scenario: Free 卡 CTA
- **WHEN** 用户点击 free 卡 CTA
- **THEN** CTA 文字为「先免费看一天 →」，点击跳转 `/quiz`

### Requirement: 对比表三列文案
对比表中三列的 `free` / `standard` / `premium` 单元格文案 SHALL 清晰区分三档定位。

#### Scenario: Free 列文案定位
- **WHEN** 对比表渲染
- **THEN** free 列文案体现「完整 1 天」，如「Day 1 完整版（时间线+餐厅+拍摄+避坑）」，不出现「部分」「摘要」「简版」等弱化词

#### Scenario: Standard 列文案定位
- **WHEN** 对比表渲染
- **THEN** standard 列文案体现「全程都像这一天一样细」，如「全部 N 天 × 相同颗粒度」

#### Scenario: Premium 列文案定位
- **WHEN** 对比表渲染
- **THEN** premium 列文案体现「在完整攻略基础上，更深服务」，如「完整攻略 + 深度比价系统 + 微信答疑」，不把比价系统作为完整攻略唯一差异点
