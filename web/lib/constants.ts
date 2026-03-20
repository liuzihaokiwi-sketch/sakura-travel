// ── WeChat ──────────────────────────────────────────────────────────────────
export const WECHAT_ID = "Kiwi_iloveu_O-o";
export const WECHAT_NOTE = "樱花";

// ── Data Authority Stats ────────────────────────────────────────────────────
export const STATS = {
  dataSources: { value: "4", label: "大数据源", detail: "JMA · JMC · Weathernews · 地方官方" },
  jmaCities: { value: "58", label: "个观测城市", detail: "日本气象厅 JMA 官方" },
  spots: { value: "240+", label: "赏樱景点", detail: "5 大城市全覆盖" },
  dailyUpdates: { value: "3", label: "次/天更新", detail: "08:30 · 11:30 · 17:30" },
  userReports: { value: "200万+", label: "用户报告", detail: "Weathernews 众包实况" },
  historyYears: { value: "10", label: "年历史验证", detail: "准确度逐年分析" },
  confidenceScore: { value: "0-100", label: "置信度评分", detail: "多源融合算法" },
} as const;

// ── Service Advantages (12 items from real project data) ────────────────────
export const ADVANTAGES = [
  {
    icon: "🇯🇵",
    title: "旅居日本 · 人工验证",
    pain: "AI推荐的餐厅已倒闭、景点在维修",
    solution: "我们实际住在日本，每条路线亲自走过",
    highlight: "旅居日本",
  },
  {
    icon: "🗺️",
    title: "8条精品路线 · 3-8天",
    pain: "千篇一律的模板行程",
    solution: "东京/关西/联程，3-8天按需定制",
    highlight: "8条路线",
  },
  {
    icon: "👥",
    title: "4种场景适配",
    pain: "不分情侣出行还是带娃出行",
    solution: "情侣/家庭/独旅/闺蜜，自动调整推荐权重",
    highlight: "4种场景",
  },
  {
    icon: "🎯",
    title: "9维偏好匹配",
    pain: "只问你想去哪就完了",
    solution: "购物/美食/温泉/自然/文化/动漫/亲子/夜生活/出片",
    highlight: "9维问卷",
  },
  {
    icon: "🍣",
    title: "Tabelog 严选 · 3.5+",
    pain: "只有名字没评价、评分虚高",
    solution: "最高4.68分，含招牌菜/人均/预约指引",
    highlight: "Tabelog 3.5+",
  },
  {
    icon: "📊",
    title: "12维智能评分",
    pain: "随便推荐几个景点",
    solution: "Google + Tabelog + Booking 三平台数据融合",
    highlight: "12维评分",
  },
  {
    icon: "📖",
    title: "16套杂志级PDF",
    pain: "Word文档级别的攻略",
    solution: "可打印旅行杂志排版，含每日时间轴",
    highlight: "16套模板",
  },
  {
    icon: "🕸️",
    title: "11个数据爬虫",
    pain: "只看一个平台的信息",
    solution: "Google Flights/Booking/Tabelog/携程/Agoda 全覆盖",
    highlight: "11个爬虫",
  },
  {
    icon: "🎪",
    title: "55+ 活动祭典",
    pain: "不知道当地有什么活动",
    solution: "夜樱/花火/市集/祭典全覆盖，含时间地点门票",
    highlight: "55+活动",
  },
  {
    icon: "🗾",
    title: "143个目的地",
    pain: "只推荐东京大阪",
    solution: "JNTO 日本国家旅游局官方目的地数据",
    highlight: "143个",
  },
  {
    icon: "🚃",
    title: "顺路串联 · 不走回头路",
    pain: "景点之间来回跑",
    solution: "按区域聚合景点，交通卡 Pass 最省方案自动计算",
    highlight: "顺路串联",
  },
  {
    icon: "📸",
    title: "出片保证",
    pain: "和网红拍的一模一样",
    solution: "最佳时段 + 小众机位 + 错峰路线",
    highlight: "小众机位",
  },
] as const;

// ── Process Steps ───────────────────────────────────────────────────────────
export const PROCESS_STEPS = [
  { num: 1, title: "加微信", detail: "备注「樱花」即可" },
  { num: 2, title: "告知需求", detail: "日期 · 城市 · 人数 · 偏好" },
  { num: 3, title: "免费获取1天攻略", detail: "景点 + 餐厅 + 交通全包" },
  { num: 4, title: "满意再付费", detail: "不满意不收费" },
] as const;

// ── Trust Indicators ────────────────────────────────────────────────────────
export const TRUST_ITEMS = [
  "🔒 不满意不收费",
  "🌸 已服务 200+",
  "🎁 首次免费体验",
] as const;

// ── City config ─────────────────────────────────────────────────────────────
export const CITIES = [
  { code: "tokyo", nameCn: "东京", nameJa: "東京", spotCount: 73 },
  { code: "kyoto", nameCn: "京都", nameJa: "京都", spotCount: 63 },
  { code: "osaka", nameCn: "大阪", nameJa: "大阪", spotCount: 28 },
  { code: "aichi", nameCn: "爱知", nameJa: "愛知", spotCount: 47 },
  { code: "hiroshima", nameCn: "广岛", nameJa: "広島", spotCount: 29 },
] as const;
