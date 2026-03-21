## MODIFIED Requirements

### Requirement: Preview 页 Header 副标题
Header 副标题 SHALL 传达「完整体验一天」的价值，而非单纯描述「免费预览」。

#### Scenario: Header 副标题展示
- **WHEN** 用户打开 `/preview/[id]`
- **THEN** 副标题显示「完整体验第 1 天 · 精确到分钟的时间线、拍摄指南、避坑提醒」，而非「免费预览精选 Day 1」

### Requirement: InlineCTA 文案（after timeline）
Day 1 时间轴结束后插入的 InlineCTA，文案 SHALL 使用节奏引导式而非通用促销式。

#### Scenario: InlineCTA 文案
- **WHEN** InlineCTA 在 Day 1 时间轴结束后渲染
- **THEN** 主文案为「你刚看完的，只是这趟行程的第一天」，副文案强调「后面每一天都是同等颗粒度的完整方案」

### Requirement: TrialDayHook 插入位置
`TrialDayHook` 组件 SHALL 插入 `PreviewTimeline` 之后、`InlineCTA`（after timeline）之前，确保用户刚结束 Day 1 阅读时即看到后续高光预告。

#### Scenario: Hook 插入位置正确
- **WHEN** 页面渲染完成
- **THEN** 页面结构顺序为：Day 1 Header → PreviewTimeline → TrialDayHook → InlineCTA → DayTeaser 列表 → TrustModule → WechatFallback → FloatingCTA
