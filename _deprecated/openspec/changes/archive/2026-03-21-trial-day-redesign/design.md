## Context

`/preview/[id]/page.tsx` 已有完整骨架（567 行）：`SpotCard`（可展开的景点卡）、`LockedModule`（模糊占位）、`DayTeaser`（其他天缩略卡）、`InlineCTA`（中插转化条）、`StayTimeCTA`（45s 停留弹窗）、`TrustModule`（深色信任区）、`WechatFallback`（微信引导）、`FloatingCTA`（悬浮底栏）。

当前缺失的是：Day 1 时间轴结束后、进入付费引导前，**没有任何"后续几天值得解锁"的具体内容预告**——用户不知道后面有什么，不知道值不值得买。此外，对比表文案（`compare_rows`）和 free 卡文案由 `pricing/page.tsx` 服务端注入，是静态常量，需要一起升级。

## Goals / Non-Goals

**Goals:**
- 新增 `TrialDayHook` 组件：行程脉络图 + 亮点预告卡 + 节奏引导句，插入 preview 页的正确位置
- 升级 `pricing.ts` 内容常量：free 卡文案、对比表三列文案、hook 区文案
- 升级 `preview/[id]/page.tsx` 中的 Header 副标题、InlineCTA 文案
- 定价页 `pricing/page.tsx` server data 中的 `compare_rows` 与 free tier 同步更新

**Non-Goals:**
- 不改 SpotCard / LockedModule / FloatingCTA 等已有组件的逻辑
- 不新增后端 API 或数据模型
- 不引入新 npm 包
- 不做 A/B 测试基础设施

## Decisions

**D1：TrialDayHook 放在哪里？**
放在 `PreviewTimeline` 之后、`InlineCTA`（中插，after timeline）之前，即用户刚看完 Day 1 时间轴、注意力最集中的那一刻。这是「纵向完整体验刚结束 → 横向截断 → 后续高光引诱」的自然节奏断点。

**D2：TrialDayHook 的数据从哪来？**
硬编码在 `web/lib/content/trial-day-hook.ts`（新文件），而非从 API 动态拉取。理由：Hook 内容是营销文案，不依赖用户个性化数据；动态化反而增加首屏风险；未来需要改文案时只动常量文件即可。

**D3：脉络图用什么实现？**
不用 Canvas / SVG 路线图，用 **水平滚动的 flex row**，每天一个小卡片（Day N + 城市 + 主题词 + 锁定图标），可在移动端横向滑动。理由：零依赖、复用已有 Tailwind，脉络清晰、信息密度够。

**D4：亮点预告卡用什么视觉？**
每张卡用大 emoji 作为视觉焦点（替代图片），加一句「为什么你会喜欢这一天」的情感描述，加一个模糊遮罩的锁定标记。不用真实图片（避免资产管理复杂度），emoji 足够唤起画面感。

**D5：对比表文案存在哪？**
`pricing/page.tsx` 已经用 server-side 静态对象注入 `compare_rows`。继续维持这个模式，同时把文案常量提取到 `web/lib/content/pricing.ts` 中统一管理，server 端直接 import。

**D6：场景化 Hook 变体（情侣/闺蜜/深玩）如何处理？**
MVP 阶段：`TrialDayHook` 接受 `scenario` prop（`'couple' | 'friends' | 'deep' | 'default'`），从 `trial-day-hook.ts` 内容常量中选取对应文案。`scenario` 由 preview 页从 `PreviewData` 的 sku 或 URL params 中读取，默认 `'default'`。

## Risks / Trade-offs

- **硬编码内容 vs. 个性化**：Hook 文案无法随用户行程动态变化。→ 可接受，Hook 的目的是激发购买欲而非提供信息，通用文案足够有效；个性化是 v2 迭代方向。
- **横向脉络图在极窄屏（< 360px）溢出**：→ 加 `overflow-x-auto` + `scrollbar-hide`，不 overflow 父容器。
- **文案常量分散在两个文件（pricing.ts + trial-day-hook.ts）**：→ 接受，trial-day-hook 内容独立，不污染 pricing 的价格/FAQ 关注点。

## Migration Plan

纯前端变更，无数据迁移：
1. 新建 `web/lib/content/trial-day-hook.ts`
2. 更新 `web/lib/content/pricing.ts`（free 卡文案、compare_rows 常量）
3. 新建 `web/components/pricing/TrialDayHook.tsx`
4. 更新 `web/app/preview/[id]/page.tsx`
5. 更新 `web/app/pricing/page.tsx`（compare_rows 数据）
6. 本地验证：`pnpm dev`，访问 `/preview/demo` 和 `/pricing`

回滚：git revert，无后端依赖，风险极低。
