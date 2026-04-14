## ADDED Requirements

### Requirement: 6 屏页面结构与首屏渲染

/rush 页面 SHALL 包含 6 个逻辑屏，按以下顺序从上到下排列：Hero → 排行榜 → 时间轴 → 地图 → 信任条 → 转化层。首屏（Hero + 排行榜部分）MUST 在 2 秒内完成 LCP。第四屏（地图）MUST 延迟加载，不阻塞首屏。

#### Scenario: 用户首次访问 /rush
- **WHEN** 用户打开 /rush 页面
- **THEN** 首屏显示 Hero 区域（标题 + 实时状态摘要 + 双 CTA）+ 排行榜第一排景点卡片，LCP < 2s

#### Scenario: 用户滚动到地图区域
- **WHEN** 用户滚动至第四屏（地图区域）进入视口
- **THEN** 系统通过 IntersectionObserver 触发 Leaflet 动态加载，显示 loading 占位符后渲染地图

#### Scenario: ISR 热更新
- **WHEN** 数据文件（sakura_rush_scores.json / weathernews_all_spots.json）被爬虫更新
- **THEN** Vercel ISR 在 revalidate 周期（30 分钟）后自动更新页面内容，无需手动重新部署

---

### Requirement: Hero 区域实时状态摘要

Hero 区域 MUST 显示当前全国花期的实时摘要。摘要 SHALL 自动从数据中提取各城市的花期阶段，生成如「东京已满开 · 京都三分咲 · 大阪本周冲」的一行文本。

#### Scenario: 有满开城市
- **WHEN** 数据中有 ≥1 个城市存在满开景点
- **THEN** Hero 实时状态条显示满开城市名 + 「已满开」标签，并突出显示

#### Scenario: 全部城市未开
- **WHEN** 所有城市景点均未开花
- **THEN** Hero 实时状态条显示「花期尚未开始，持续追踪中」+ 预计最早开花城市和日期

---

### Requirement: 城市景点排行榜

排行榜 MUST 支持城市 Tab 切换（带 layoutId 弹簧动画）。每个城市下 MUST 显示按「能冲指数」降序排列的景点卡片网格。卡片 MUST 包含：真实照片、花期状态标签、能冲指数、夜樱/名所标签。卡片在照片缺失时 MUST 显示樱花 emoji 占位符。

#### Scenario: 切换城市 Tab
- **WHEN** 用户点击另一个城市的 Tab
- **THEN** Tab 背景以弹簧动画滑动到新 Tab，卡片网格以 fade + stagger 动画更新为新城市的景点

#### Scenario: 桌面端排行榜布局
- **WHEN** 视口宽度 ≥ 1024px
- **THEN** 排行榜显示为 4 列网格

#### Scenario: 手机端排行榜布局
- **WHEN** 视口宽度 < 640px
- **THEN** 排行榜显示为 2 列网格，城市 Tab 改为可横向滚动

#### Scenario: 景点卡片信息完整性
- **WHEN** 渲染一张景点卡片
- **THEN** 卡片 MUST 包含：排名序号、照片（或占位符）、景点名称（中文）、花期状态（満開/五分咲/等）、能冲指数分数、夜樱标签（如有）、名所百选标签（如有）

---

### Requirement: 花期时间轴城市对比

BloomTimeline 组件 SHALL 支持多城市对比模式，并排显示东京、京都、大阪的花期进度条。每条进度条 MUST 标注当前日期位置。

#### Scenario: 多城市对比视图
- **WHEN** 时间轴渲染
- **THEN** 显示 3 条并排的花期进度条（东京/京都/大阪），每条标注未开→三分咲→五分咲→满开→散落的时间节点，当前日期有垂直指示线

#### Scenario: 时间轴与排行榜联动
- **WHEN** 用户在排行榜中切换城市
- **THEN** 时间轴自动高亮对应城市的进度条
