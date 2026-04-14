# Mobile UX Spec

## Requirements

### Requirement: 触摸目标最小尺寸
系统内所有可点击元素 SHALL 满足最小 44×44px 触摸目标。

#### Scenario: 按钮触摸区合规
- **WHEN** 用户在手机端点击任意按钮
- **THEN** 按钮高度不低于 44px（`h-11`），宽度根据内容，但不低于 44px

### Requirement: 禁止手机端主容器横向滚动
任何页面的主容器 SHALL 不出现横向溢出。

#### Scenario: 对比表手机端无横向滚动
- **WHEN** 用户在手机端（< 768px）访问 /pricing
- **THEN** 页面无横向滚动条，对比表改为 Accordion 展示

#### Scenario: /rush Tab 区域内部可横滑
- **WHEN** 用户在手机端滑动城市 Tab
- **THEN** Tab 容器内部横向滑动正常，但父容器不溢出

### Requirement: FloatingCTA 安全区适配
所有固定在底部的 CTA / Bottom Sheet SHALL 预留 iOS Home 条安全区。

#### Scenario: iPhone 底部安全区
- **WHEN** 用户在 iPhone X+ 设备访问任何带 FloatingCTA 的页面
- **THEN** 按钮不被 Home 条遮挡，底部有 `env(safe-area-inset-bottom)` padding

### Requirement: 手机端单列/双列布局规则
手机端（< 640px）SHALL 遵循以下列数规则：
- 3 个及以下选项：`grid-cols-1`
- 4 个选项：`grid-cols-2`
- 5 个及以上选项：`grid-cols-2`
- 图片卡片（SpotCard 等）：`grid-cols-2`
- 禁止 `grid-cols-3` 在 `< sm` 断点出现

#### Scenario: /quiz 3选项题目
- **WHEN** 题目有 3 个选项（如 japan_experience）
- **THEN** 选项呈单列垂直排列，每项高度 ≥ 56px

#### Scenario: /quiz 5+选项题目
- **WHEN** 题目有超过 4 个选项（如 style 题）
- **THEN** 选项呈双列排列，不出现三列

### Requirement: /pricing 手机端对比表改 Accordion
手机端 SHALL 不显示横向滚动表格，改为原生 `<details>/<summary>` Accordion。

#### Scenario: Accordion 展示对比信息
- **WHEN** 用户在手机端查看对比表
- **THEN** 每个维度是一个可展开的 `<details>`，`<summary>` 显示维度名，展开后显示 free/standard/premium 三列值

### Requirement: TrialDayHook 手机端单列
TrialDayHook 亮点预告卡 SHALL 在手机端改为单列，在 sm 断点及以上改为双列。

#### Scenario: 375px 设备卡片单列
- **WHEN** 用户在 375px 宽度设备查看 /preview 页
- **THEN** 亮点预告卡垂直堆叠，每张占满内容区宽度
