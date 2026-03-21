## 1. 内容常量层（其他任务依赖）

- [x] 1.1 新建 `web/lib/content/trial-day-hook.ts` — 导出 `HOOK_CONTENT`：脉络图 Days 数组、亮点预告卡数组（default/couple/friends/deep 四个变体）、节奏引导句文案
- [x] 1.2 更新 `web/lib/content/pricing.ts` — 新增 `FREE_TIER_COPY`（一日体验版名称、tagline、includes、CTA）和 `COMPARE_ROWS`（三列对比表全量文案常量，供 pricing/page.tsx import）

## 2. 核心新组件

- [x] 2.1 新建 `web/components/pricing/TrialDayHook.tsx` — 接受 `{ days: PreviewDay[]; totalDays: number; price: number; planId?: string; scenario?: Scenario }` props，渲染：行程脉络图 Strip + 亮点预告卡（2–3 张）+ 节奏引导句 + 解锁 CTA 按钮（依赖 1.1）

## 3. Preview 页集成

- [x] 3.1 更新 `web/app/preview/[id]/page.tsx` — Header 副标题改为「完整体验第 1 天 · 精确到分钟的时间线、拍摄指南、避坑提醒」（依赖 1.1）
- [x] 3.2 更新 `web/app/preview/[id]/page.tsx` — 在 `<PreviewTimeline>` 之后、`<InlineCTA>` 之前插入 `<TrialDayHook>`，传入 `days`、`totalDays`、`price`、`planId`（依赖 2.1）
- [x] 3.3 更新 `web/app/preview/[id]/page.tsx` — `InlineCTA`（after timeline）文案改为「你刚看完的，只是这趟行程的第一天」+ 节奏副文案（依赖无）

## 4. 定价页文案更新

- [x] 4.1 更新 `web/app/pricing/page.tsx` — free tier 的 `name`/`tagline`/`includes`/`cta` 从 `FREE_TIER_COPY` 常量读取（依赖 1.2）
- [x] 4.2 更新 `web/app/pricing/page.tsx` — `compare_rows` 数组替换为从 `COMPARE_ROWS` 常量读取，确保三列文案符合 spec（依赖 1.2）

## 5. 质量验收

- [x] 5.1 访问 `/preview/demo`，验证：页面结构顺序正确（Timeline → TrialDayHook → InlineCTA → DayTeaser → TrustModule）（代码审查确认）
- [x] 5.2 访问 `/pricing`，验证：free 卡文案已更新，对比表三列无弱化词（「一日体验版」+「完整体验第 1 天，不是摘要」；compare_rows 无「部分」「摘要」「简版」）
- [x] 5.3 移动端（375px）验证：脉络图 Strip 可横向滚动，不溢出；亮点预告卡 grid-cols-2 在 375px 正常堆叠