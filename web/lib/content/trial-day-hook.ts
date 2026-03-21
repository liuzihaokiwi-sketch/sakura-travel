// ── Trial Day Hook Content Constants ──────────────────────────────────────
// 「纵向完整，横向截断」 — 看完 Day 1 后触发后续高光预告

export type Scenario = "default" | "couple" | "friends" | "deep";

// ── 行程脉络图 Strip（Day N + 城市 + 主题词）─────────────────────────────
// 这是通用结构，preview 页会用真实 days 数据替换
// 此处作为 fallback / demo 用途
export const JOURNEY_MAP_DAYS = [
  { day: 1, city: "东京", theme: "上野 × 浅草", locked: false },
  { day: 2, city: "东京", theme: "新宿 × 原宿", locked: true },
  { day: 3, city: "神奈川", theme: "镰仓一日游", locked: true },
  { day: 4, city: "东京", theme: "银座 × 筑地", locked: true },
  { day: 5, city: "东京", theme: "秋叶原 × 御茶水", locked: true },
];

// ── 亮点预告卡（按场景分组）──────────────────────────────────────────────

export interface HighlightCard {
  dayNum: number;
  city: string;
  emoji: string;
  title: string;
  teaser: string; // 一句情感描述，唤起画面感
}

export const HIGHLIGHT_CARDS: Record<Scenario, HighlightCard[]> = {
  default: [
    {
      dayNum: 2,
      city: "东京",
      emoji: "🌆",
      title: "第 2 天 · 新宿御苑",
      teaser: "东京最美赏樱地，65 种樱花同时开放——我们帮你算好了最佳入园时间窗口。",
    },
    {
      dayNum: 3,
      city: "镰仓",
      emoji: "⛩️",
      title: "第 3 天 · 镰仓海岸线",
      teaser: "大佛 + 海景 + 小町通：这条路线比任何攻略少走 40 分钟冤枉路。",
    },
    {
      dayNum: 4,
      city: "东京",
      emoji: "🍣",
      title: "第 4 天 · 筑地早市",
      teaser: "全程最值得早起的一天 — 8 点前入场，你能吃到当地人才知道的那家玉子烧。",
    },
  ],
  couple: [
    {
      dayNum: 2,
      city: "东京",
      emoji: "🌸",
      title: "第 2 天 · 夜晚的新宿御苑",
      teaser: "日落后的御苑只剩你们两个，我们帮你预约了最不容易排队的那条入园路线。",
    },
    {
      dayNum: 3,
      city: "箱根",
      emoji: "♨️",
      title: "第 3 天 · 露天温泉之夜",
      teaser: "泡完汤对方说「这趟旅行值了」——我们挑了一家评分 4.8、性价比最高的宿。",
    },
    {
      dayNum: 4,
      city: "东京",
      emoji: "🌃",
      title: "第 4 天 · 东京塔夜景",
      teaser: "增上寺的角度、麻布台的角度、六本木的角度 — 不同时间不同感觉，全安排好了。",
    },
  ],
  friends: [
    {
      dayNum: 2,
      city: "东京",
      emoji: "🎮",
      title: "第 2 天 · 秋叶原 × 中野百老汇",
      teaser: "两个圣地怎么排最不累？我们给你算了一条不走回头路的黄金动线。",
    },
    {
      dayNum: 3,
      city: "东京",
      emoji: "🍺",
      title: "第 3 天 · 居酒屋深夜食堂",
      teaser: "当地人才知道的那条横丁 — 人均 ¥200，比游客街少花一半，喝到自然停。",
    },
    {
      dayNum: 4,
      city: "大阪",
      emoji: "🎡",
      title: "第 4 天 · 大阪道顿堀",
      teaser: "闺蜜出片率最高的 3 个机位，全标在地图上了，不用对着手机找角度。",
    },
  ],
  deep: [
    {
      dayNum: 2,
      city: "东京",
      emoji: "🏯",
      title: "第 2 天 · 东京隐藏博物馆路线",
      teaser: "4 个 Google Map 上不容易找到的本地博物馆，专为深度玩家定制的动线。",
    },
    {
      dayNum: 3,
      city: "京都",
      emoji: "🍵",
      title: "第 3 天 · 京都茶道体验",
      teaser: "不是旅游版的「表演茶道」——是真正坐下来、跟着老师做完一套的那种。",
    },
    {
      dayNum: 4,
      city: "奈良",
      emoji: "🦌",
      title: "第 4 天 · 奈良山里路线",
      teaser: "鹿多的地方每个人都去，我们帮你找到那条只有 200 人知道的林道。",
    },
  ],
};

// ── 节奏引导句（按场景）────────────────────────────────────────────────────

export const RHYTHM_GUIDE: Record<Scenario, { headline: string; sub: string }> = {
  default: {
    headline: "你刚看完的，只是这趟行程的第一天。",
    sub: "后面每一天，都是同等颗粒度的完整方案——时间线、餐厅、拍摄指南、备选全有。",
  },
  couple: {
    headline: "Day 1 只是开始——最好的部分在后面等你们。",
    sub: "完整版把你们两个人最容易错过的时刻都规划进去了，包括那个温泉之夜。",
  },
  friends: {
    headline: "你们这趟真正好玩的部分，还在后面。",
    sub: "完整版比你自己查攻略少走 40% 的弯路，少花 30% 的冤枉钱。",
  },
  deep: {
    headline: "真正的深度路线，从 Day 2 开始。",
    sub: "完整版包含本地人才知道的 6 处隐藏路线，跟团游和普通攻略都不会告诉你。",
  },
};

// ── InlineCTA 文案（timeline 结束后）──────────────────────────────────────

export const INLINE_CTA_AFTER_TIMELINE = {
  message: "你刚看完的，只是这趟行程的第一天",
  sub: "后面每一天都是同等颗粒度的完整方案，时间线 + 餐厅 + 拍摄指南 + 备选全有",
};

// ── Header 副标题 ──────────────────────────────────────────────────────────

export const PREVIEW_HEADER_SUBTITLE =
  "完整体验第 1 天 · 精确到分钟的时间线、拍摄指南、避坑提醒";
