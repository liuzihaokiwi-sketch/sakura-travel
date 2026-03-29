// ── Mobile-First UX Spec Constants ──────────────────────────────────────────
// 本项目移动端设计规范，供开发/设计验收时引用

// ── 11 条总规范 ───────────────────────────────────────────────────────────────

export const MOBILE_RULES = [
  {
    id: "B1",
    name: "首屏原则",
    rule: "任何页面手机首屏必须在 3 秒内让用户看懂：这是什么 / 能帮我做什么 / 下一步做什么",
    forbidden: ["首屏放地图", "首屏放对比表", "首屏超过 3 个 CTA"],
  },
  {
    id: "B2",
    name: "触摸目标",
    rule: "所有可点击元素最小 44×44px。按钮 h-11+，列表项 gap-3+",
    tailwind: ["h-11", "h-12", "min-h-[44px]"],
  },
  {
    id: "B3",
    name: "单列优先",
    rule: "手机端默认单列。2 列仅用于：图片展示卡、价格简要对比。禁止 grid-cols-3 在 < sm",
    forbidden: ["grid-cols-3（无 sm: 前缀）", "grid-cols-4（无 md: 前缀）"],
  },
  {
    id: "B4",
    name: "禁止主容器横向滚动",
    rule: "主内容区禁止横向溢出。表格、对比表必须改为手机友好交互（Accordion / 标签切换）",
    allowed: ["overflow-x-auto（内部容器如 CityTabs、JourneyMapStrip）"],
  },
  {
    id: "B5",
    name: "CTA 规则",
    rule: "主 CTA 全宽 w-full + rounded-full + h-12。每屏最多 1 主 CTA + 1 次级链接。FloatingCTA 文案 ≤ 12 字",
    tailwind: ["w-full", "rounded-full", "h-12"],
  },
  {
    id: "B6",
    name: "文字密度",
    rule: "正文 text-sm + leading-relaxed。单段落 ≤ 4 行（约 80 字）。超过必须折叠或截断",
    tailwind: ["text-sm", "leading-relaxed", "line-clamp-3", "line-clamp-4"],
  },
  {
    id: "B7",
    name: "延迟加载",
    rule: "Leaflet 地图、大图 banner、Satori 卡片、PDF 导出必须用 next/dynamic 延迟加载，预留骨架占位",
    required: ["next/dynamic", "loading placeholder with fixed height"],
  },
  {
    id: "B8",
    name: "CLS 防护",
    rule: "所有图片必须指定 width/height 或用 aspect-ratio 容器。骨架占位尺寸与真实内容一致",
    tailwind: ["aspect-video", "aspect-square", "aspect-[4/3]"],
  },
  {
    id: "B9",
    name: "抽屉/弹层规则",
    rule: "详情信息用 bottom sheet（手机）/ right slideover（桌面）。底部弹层必须 rounded-t-2xl + max-h-[85vh] + overflow-y-auto",
    tailwind: ["fixed bottom-0", "rounded-t-2xl", "max-h-[85vh]", "overflow-y-auto"],
  },
  {
    id: "B10",
    name: "表单规则",
    rule: "问卷每屏一题。选项最小 h-14 + text-base。能选择就不打字",
    tailwind: ["h-14", "text-base"],
  },
  {
    id: "B11",
    name: "安全区",
    rule: "所有 FloatingCTA / BottomSheet 必须用 pb-safe（padding-bottom: env(safe-area-inset-bottom)）",
    tailwind: ["pb-safe"],
  },
] as const;

// ── 选项网格规则 ───────────────────────────────────────────────────────────────

export const GRID_RULES = {
  /** 根据选项数量返回 Tailwind grid 类名 */
  forOptions: (count: number): string => {
    if (count <= 3) return "grid-cols-1";
    return "grid-cols-2"; // 4 个及以上，最多 2 列
  },
  /** 图片展示卡（SpotCard 等）固定 2 列 */
  forImageCards: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4",
  /** 价格卡 */
  forPricingCards: "grid-cols-1 md:grid-cols-3",
} as const;

// ── Breakpoints ────────────────────────────────────────────────────────────────

export const BREAKPOINTS = {
  sm: 640,   // 手机横屏 / 小平板
  md: 768,   // 平板 / 对比表切换点
  lg: 1024,  // 桌面
  xl: 1280,
} as const;

// ── 验收清单 ───────────────────────────────────────────────────────────────────

export const ACCEPTANCE_CHECKLIST = [
  {
    id: "AC-01",
    page: "全站",
    check: "Chrome DevTools 375px：主容器无横向滚动条",
    priority: "P0",
  },
  {
    id: "AC-02",
    page: "全站",
    check: "所有按钮高度 ≥ 44px（可用 DevTools 测量）",
    priority: "P0",
  },
  {
    id: "AC-03",
    page: "/pricing",
    check: "手机端对比表显示为 Accordion，不出现横向滚动",
    priority: "P0",
  },
  {
    id: "AC-04",
    page: "/order",
    check: "3 选项题目单列显示，选项高度 ≥ 56px",
    priority: "P0",
  },
  {
    id: "AC-05",
    page: "/preview",
    check: "TrialDayHook 亮点卡在 375px 下单列显示",
    priority: "P0",
  },
  {
    id: "AC-06",
    page: "/",
    check: "首页首屏只显示一条场景短句（375px），Hero 文字不溢出",
    priority: "P0",
  },
  {
    id: "AC-07",
    page: "/rush",
    check: "SpotCard 图片在 375px 下高度 ≥ 144px，景点名不截断",
    priority: "P1",
  },
  {
    id: "AC-08",
    page: "/plan/[id]",
    check: "天数 Tab（7 天）可横向滑动，不溢出父容器",
    priority: "P1",
  },
  {
    id: "AC-09",
    page: "/preview + /plan/[id]",
    check: "iPhone Safari：FloatingCTA 不被 Home 条遮挡（pb-safe 生效）",
    priority: "P1",
  },
  {
    id: "AC-10",
    page: "/rush",
    check: "SakuraMap 不在首屏加载（IntersectionObserver 触发）",
    priority: "P1",
  },
  {
    id: "AC-11",
    page: "全站",
    check: "首屏 LCP ≤ 2.5s（Chrome Lighthouse Mobile 模拟测速）",
    priority: "P1",
  },
  {
    id: "AC-12",
    page: "/custom",
    check: '手机端"提交修改"按钮固定底部，不被键盘遮挡',
    priority: "P1",
  },
] as const;

// ── 各页面手机端关键改动记录 ──────────────────────────────────────────────────

export const PAGE_MOBILE_SUMMARY = {
  home: "Hero 场景短句手机端只显示一条；PainPoints 单列；FinalCTA flex-col",
  rush: "SpotCard h-36 sm:h-40；CityTabs overflow-x-auto；SpotDetailDrawer bottom sheet",
  quiz: "选项网格 ≤3→cols-1，4+→cols-2；每题一屏；自动跳转",
  preview: "TrialDayHook cols-1 sm:cols-2；FloatingCTA pb-safe；StayTimeCTA pb-safe",
  pricing: "价格卡 md:grid-cols-3（手机单列）；对比表 Accordion（手机）/ table（桌面）",
  plan: "px-4 md:px-6；天数 Tab overflow-x-auto；PDF 说明折叠",
  custom: "固定底部操作区；全宽候选卡片",
} as const;
