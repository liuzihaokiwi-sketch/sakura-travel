## Context

当前各页面已有响应式类名，但设计基准是桌面端——手机端是"缩小版"而非"为手机设计版"。核心差异：桌面端容忍信息密度高、多列布局、滚动表格；手机端需要每屏一个核心决策点、单手操作、最小滚动跳出率。本 change 通过规范文档 + 代码改动双管齐下，系统性地把手机端做成主战场。

---

## A. 为什么本项目必须 Mobile-First

1. **流量入口决定一切**：小红书/微信分享链接 85%+ 在手机端打开，首屏体验直接决定跳出率
2. **付费决策在手机上完成**：用户不会回到电脑上付款，手机端转化路径必须完整
3. **情绪驱动内容**："想去日本"这个欲望在刷手机时被激发，必须即时满足
4. **竞品也是手机端**：用户对比的是其他攻略 App，而非网页版工具

---

## B. 全站移动端总规范（11 条）

**B1 首屏原则**：任何页面的手机首屏必须在 3 秒内让用户看懂"这是什么/能帮我做什么/下一步做什么"。禁止首屏放地图、对比表、超过 3 个 CTA。

**B2 触摸目标**：所有可点击元素最小 44×44px。按钮高度不低于 `h-11`（44px）。列表项间距不低于 `gap-3`。

**B3 单列优先**：手机端默认单列布局。2 列仅用于：图片展示卡（SpotCard）、价格简要对比。禁止手机端出现 3+ 列。

**B4 禁止横向滚动**：主内容区禁止横向滚动（对比表、Tab 等容器内部可以，但主容器不可以）。所有超宽组件（地图、表格）必须在手机端改交互方式。

**B5 CTA 规则**：主 CTA 全宽 `w-full` + `rounded-full` + 高度 `h-12`。每屏最多 1 个主 CTA + 1 个次级链接。FloatingCTA 文案不超过 12 字。

**B6 文字密度**：手机端正文 `text-sm`（14px）+ `leading-relaxed`。单段落不超过 4 行（约 80 字）。超过 4 行必须折叠或截断。

**B7 延迟加载**：地图（Leaflet）、大图 banner、Satori 卡片生成、PDF 导出按钮必须延迟加载。用 `next/dynamic` + `loading` placeholder 预留尺寸。

**B8 CLS 防护**：所有图片必须指定 `width`/`height` 或使用 `aspect-ratio` 容器。骨架占位必须与真实内容尺寸一致。

**B9 抽屉/弹层规则**：详情信息用 bottom sheet（`fixed bottom-0`，`rounded-t-2xl`，`max-h-[85vh]`，`overflow-y-auto`）。桌面端同组件改 right slideover（`fixed right-0`，`w-[400px]`，`h-full`）。

**B10 表单规则**：问卷每屏一题（或最多相关联的两题）。选项最小 `h-14` + `text-base`。打字输入能不做就不做，能选择就不打字。

**B11 安全区**：所有 FloatingCTA / BottomSheet 必须使用 `pb-safe`（`padding-bottom: env(safe-area-inset-bottom)`）防止 iPhone Home 条遮挡。

---

## C. 各页面移动端设计决策

### C1 首页 (`/`)

**现状问题**：场景化短句气泡在 375px 下文字超出 → 改为 `text-[11px]`，且只显示一行（不展示第二条）；`sm:grid-cols-2 lg:grid-cols-4` 的 SolutionFeatures 在 375px 是 1 列 4 张，太长 → 改为 `grid-cols-2` 手机端 2 列。

**改动决策**：
- Hero 场景短句：手机端只保留 `first_time` 一条，`experienced` 隐藏（`hidden sm:inline`）
- PainPoints：从 `sm:grid-cols-2` 改 `grid-cols-1`，单列更有力
- Solution Features：保持 `grid-cols-2`，但移除 icon 区多余 padding
- 首页 FinalCTA 区：`flex-col` + `gap-3` 已正确，保持不变

### C2 /rush 页

**现状问题**：SpotCard `grid-cols-2 md:grid-cols-3 lg:grid-cols-4`，手机端图片高度仅 `h-32`（128px），照片约 160px 宽，看不清 → 改 `h-36`，并保持 2 列不变（1 列太稀疏）；SpotDetailDrawer 桌面右侧 slideover 已实现，但手机端没有 `max-md:` 覆盖为 bottom sheet → 已在代码里有 `max-md:top-auto max-md:rounded-t-2xl max-md:max-w-full max-md:h-[85vh]`，这是对的，需确认 `overflow-y-auto` 正确。

**改动决策**：
- SpotCard 图片高度：`h-32 sm:h-36` 改 `h-36 sm:h-40`
- 地图 section：`mapInView`（IntersectionObserver）已实现，不需要额外改
- 转化区场景短句：手机端 `flex-wrap` 可能导致两条都换行占 3 行 → 改每条最多 1 行，超长用 `line-clamp-1`

### C3 /quiz 页

**现状问题**：当 `q.options.length <= 4` 时用 `grid-cols-2`，超过 4 个用 `grid-cols-3`。新增两道题后，`japan_experience`（3 个）用 `grid-cols-2`（不对称），`play_mode`（3 个）同样 → 3 个选项必须用 `grid-cols-1`（垂直列表），避免不对称空格。`style` 题可能有多个选项超过 4 个，`grid-cols-3` 在 375px 下每格约 108px，文字必然换行截断 → 超过 4 个一律改 `grid-cols-2`（最大），禁用 `grid-cols-3`。

**改动决策**：
- 选项网格规则：`<= 2个` → `grid-cols-1`；`3个` → `grid-cols-1`；`4个` → `grid-cols-2`；`> 4个` → `grid-cols-2`
- 进度条：已有 `w-full` bar，保持不变
- 微信号输入框：`py-4`（已有），触摸区足够

### C4 /preview 页

**现状问题**：`StayTimeCTA`（45s 弹窗）`fixed inset-x-4 bottom-24` → 需加 `pb-safe` 防 Home 条遮挡；TrialDayHook 亮点卡 `grid-cols-2`，在 375px 下每张约 168px 宽，emoji 3xl + 文案两行 + 锁定句勉强够但很挤 → 375px 下改 `grid-cols-1`（加 `sm:grid-cols-2`）。

**改动决策**：
- TrialDayHook：`grid-cols-1 sm:grid-cols-2`
- FloatingCTA 文案：`解锁完整行程 · ¥248` → 已有但需确认不超过 12 字（当前 OK）
- `StayTimeCTA`：加 `pb-safe`

### C5 /pricing 页

**现状问题**：价格卡已有 `md:grid-cols-3` → 手机端单列堆叠，这是对的；但对比表 `COMPARE_ROWS` 有 10 行，在手机端是宽表格，必须横向滚动 → 手机端改 Accordion，每行是一个 `<details>`，展示 label + 三列值。

**改动决策**：
- 手机端 `< md`：隐藏 table，改为 Accordion 列表（`<details>`/`<summary>`）
- 桌面端 `md+`：保留 table 不变
- 实现方式：在 `PricingClient.tsx` 中加 `block md:hidden`（accordion）和 `hidden md:block`（table）两套渲染

### C6 /custom 页 (自助微调)

**现状问题**：当前是 `hidden lg:flex` 的三栏布局——手机端（`< lg`）只能看到中间面板，侧边栏完全不显示。右侧"行程预览"面板在手机端完全不可见 → 手机端改为：主内容区全屏，"确认修改"改固定底部条（`fixed bottom-0`），左侧上下文信息改 top sheet 或折叠。

**改动决策**：
- 固定底部操作区：`fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-stone-100 pb-safe`，放"接受修改"按钮
- 候选列表：改为全宽卡片列表，每张占满屏幕宽度

### C7 /plan/[id] 页 (旅中/攻略页)

**现状问题**：DayTimeline 有 `grid-cols-7`（7 天 Tab），在手机端每格约 46px，文字"Day 1"勉强能放 → 可以保持，但需加 `overflow-x-auto`；攻略详情 `max-w-3xl` + `px-6` 在 375px 下内边距太大（每侧 24px）→ 改 `px-4`；PDF 说明折叠块（`<details>`）已是正确的，不需要改。

**改动决策**：
- `px-6` 改 `px-4 md:px-6`
- 天数 Tab 容器加 `overflow-x-auto scrollbar-hide`
- 操作按钮 `grid-cols-2` 已是正确的

---

## D. 性能决策

- `SakuraMap`：已用 `next/dynamic` + `useInView`，正确，无需改
- `TrialDayHook`：纯 React 组件，无额外依赖，无需延迟加载
- 图片：`<img loading="lazy">` 已在 SpotCard 中（`loading="lazy"`），正确
- `PricingClient`：Accordion 版本无额外 bundle，正确
- Core Web Vitals 重点监控页面：`/`（首页 LCP）、`/rush`（地图 CLS）、`/pricing`（表格 CLS）

---

## E. 实现优先级

**P0（直接影响转化）**：
1. `/pricing` 手机端 Accordion 对比表
2. `/quiz` 选项网格规则修正（3 选项用 `grid-cols-1`）
3. `/preview` TrialDayHook 改 `grid-cols-1 sm:grid-cols-2`
4. 首页场景短句手机端只显示一条

**P1（体验提升）**：
5. `/rush` SpotCard 图片高度调整
6. `/plan/[id]` px 调整 + 天数 Tab 横滑
7. `/custom` 固定底部操作区
8. 全站 FloatingCTA pb-safe 修复

**P2（完善）**：
9. `mobile-spec.ts` 规范常量文件
10. 验收 checklist 页面

---

## F. 不做的事

- 不新增任何页面或路由
- 不改后端 API
- 不引入新 npm 包（Accordion 用原生 `<details>`，bottom sheet 用 Tailwind `fixed`）
- 不做 A/B 测试基础设施
- 不重写已经正确的组件（`SpotDetailDrawer` 的 bottom sheet 实现已正确）
