## Why

`/preview/[id]` 页面已有基础骨架（SpotCard、DayTeaser、LockedModule、45s 弹窗），但体验版的「产品定位」仍不清晰：对比表中 `free` 列显得苍白、后续几天的 DayTeaser 缺乏情感勾引力、体验版结束后没有系统性的"后续亮点预告区"，导致用户看完 Day 1 之后不知道为什么要解锁——转化路径断层。现在定价体系已稳定（free / standard / premium），是最好的时机把体验版「产品力」补完。MVP 优先级：高（直接影响主漏斗转化率）。

## What Changes

- **体验版产品定位文案**：明确「纵向完整，横向截断」——Day 1 完整可执行，Day 2+ 锁定，但配高光预告
- **后续高光预告区（HighlightHookSection）**：Day 1 时间轴结束后、FloatingCTA 之前，插入全新模块：
  - 行程全局脉络图（每天城市/主题，一行看完）
  - 2–3 张「亮点预告卡」（聚焦后续某天最值得期待的场景）
  - 「第 N 天你会最喜欢」节奏引导句
- **InlineCTA 文案升级**：「你刚看完的只是开始…」节奏引导，替换当前通用话术
- **对比表三列重写**：
  - `free`：「完整体验第 1 天」——不是摘要，是真实颗粒度
  - `standard`：「全程都像这一天一样细」——完整 N 天 × 相同密度
  - `premium`：「在完整攻略基础上，更深服务」——比价系统+人工陪同答疑
- **定价页 free 卡文案升级**：CTA 改为「先免费看一天」，副标题「体验真实颗粒度，再决定」

## Capabilities

### New Capabilities
- `trial-day-hook`: 后续高光预告区组件及内容规范（脉络图 + 亮点预告卡 + 节奏引导句 + 情侣/闺蜜/深玩等场景化变体文案）

### Modified Capabilities
- `pricing-copy`: 对比表三列文案重写；free 卡定位文案、tagline、CTA 重写
- `preview-soft-engine`: PreviewPage 页面结构——插入 HighlightHookSection；InlineCTA 文案升级；Header 副标题升级

## Impact

- `web/app/preview/[id]/page.tsx` — 插入 `<HighlightHookSection>` 组件；InlineCTA / Header 文案更新
- `web/components/pricing/TrialDayHook.tsx` — 新建，后续亮点区组件
- `web/lib/content/pricing.ts` — 新增 free 卡定位常量、对比表文案常量、hook 区文案常量
- `web/app/pricing/page.tsx`（server 侧 data）— 对比表三列文案更新
- 无新 API、无新依赖、无 breaking changes
