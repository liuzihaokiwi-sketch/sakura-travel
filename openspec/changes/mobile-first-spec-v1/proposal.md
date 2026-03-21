## Why

本项目的流量几乎全部来自小红书、微信朋友圈、朋友转发——用户打开链接的设备是手机的概率超过 85%。但当前所有页面的主要 breakpoint 设计仍以 `md:` 为基准，手机端是"能用但未被认真设计"的状态。具体问题：

- `page.tsx` 首页 Hero 区在手机端堆了 5 层信息，场景化入口短句太长（> 45 字/行），在 375px 下超出气泡
- `/rush` SpotCard 是 `grid-cols-2`，在 360px 设备上图片只有 160px 高，照片基本看不清
- `/pricing` 对比表是标准 HTML table，手机端需要横向滚动，没有任何固定列
- `/preview` FloatingCTA 的 `inset-x-4` 在 iPhone SE 下几乎撑满屏幕但按钮文字过长换行
- `/quiz` 选项在 5 个以上时用 `grid-cols-3`，每个格子只有 ~100px，选项文字截断

不解决这些问题，从小红书跳转进来的用户有很大概率因为"看不清/点不到/读不完"而离开，不会付费。现在产品已经足够成熟，是时候把移动端做成真正的主战场。

## What Changes

- **全站移动端规范文档**：制定 11 项总规范，约束所有页面的移动端行为
- **首页**：Hero 信息层级收紧、场景入口改为 2 行紧凑版、PainPoints 改单列、SolutionFeatures 改 2 列 → 1 列降级
- **`/rush`**：SpotCard 手机端改 2 列最小高度保证、城市 Tab 改横滑不换行、底部 SpotDetailDrawer 改 bottom sheet 85vh
- **`/quiz`**：多选项（> 4 个）改换行单列、进度条固定顶部、微信号输入改更大触摸区
- **`/preview`**：FloatingCTA 文案缩短、TrialDayHook 亮点卡手机端改 1 列叠加
- **`/pricing`**：对比表改 Accordion 折叠（手机端不显示 table）、价格卡从 3 列改全宽堆叠
- **`/custom` 自助微调**：候选项从三栏布局改 bottom sheet + 滑动选择
- **`/plan/[id]`**：旅中页 DayTimeline 改支持"只看接下来 2 小时"快速视图

## Capabilities

### New Capabilities
- `mobile-ux-spec`: 全站移动端 UX 规范（交互模式选用规则、CTA 设计规则、重组件加载策略）

### Modified Capabilities
- `conversion-funnel`: 首页、价格页、预览页的手机端信息层级与 CTA
- `questionnaire-system`: /quiz 手机端选项布局和进度逻辑
- `preview-soft-engine`: /preview FloatingCTA 文案、TrialDayHook 列数
- `pricing-copy`: /pricing 手机端对比表交互方式

## Impact

- 所有改动均为纯前端样式/布局调整，零后端改动
- 主要改动文件：`web/app/page.tsx`、`web/app/rush/RushClient.tsx`、`web/app/quiz/page.tsx`、`web/app/preview/[id]/page.tsx`、`web/app/pricing/PricingClient.tsx`、`web/app/custom/page.tsx`、`web/app/plan/[id]/page.tsx`
- 新增文件：`web/lib/content/mobile-spec.ts`（规范常量，供验收 checklist 引用）
