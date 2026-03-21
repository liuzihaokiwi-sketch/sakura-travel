// ── User Segmentation Constants ─────────────────────────────────────────────
// 轻量差异化分流：japan_experience × play_mode 四象限

// ── 类型定义 ──────────────────────────────────────────────────────────────────

export type JapanExperience = "first_time" | "few_times" | "experienced";
export type PlayMode = "multi_city" | "single_city" | "undecided";

// ── 四条分流规则 ──────────────────────────────────────────────────────────────
// 供后端生成逻辑 / 前端预览文案注入使用

export interface SegmentationRule {
  dimension: "experience" | "play_mode";
  value: string;
  /** 调整说明（自然语言，注入 prompt 用） */
  instructions: string[];
  /** 提升权重的内容类型 */
  boost: string[];
  /** 降低权重的内容类型 */
  suppress: string[];
}

export const SEGMENTATION_RULES: SegmentationRule[] = [
  {
    dimension: "experience",
    value: "first_time",
    instructions: [
      "用户是第一次去日本，优先推荐经典、易上手、不踩坑的路线",
      "解释每个安排的理由，不要假设用户了解日本交通规则",
      "在每个关键节点加入避坑提醒",
    ],
    boost: ["classic_landmark", "easy_transport", "tourist_friendly", "pitfall_warning"],
    suppress: ["hidden_local", "complex_multi_transfer", "obscure_area"],
  },
  {
    dimension: "experience",
    value: "experienced",
    instructions: [
      "用户去过日本多次，跳过耳熟能详的景点，推荐本地化、差异化路线",
      "假设用户了解基本常识（Suica、JR Pass 等），不需要重复解释",
      "优先推荐当地人才知道的街区、市场、小馆子",
    ],
    boost: ["local_area", "hidden_gem", "non_tourist", "neighborhood_walk"],
    suppress: ["classic_landmark", "tourist_trap", "overcrowded_spot"],
  },
  {
    dimension: "play_mode",
    value: "multi_city",
    instructions: [
      "用户想多城顺玩，优化城市间的顺路衔接，减少回头路",
      "每个城市停留天数不宜过长，以广度换时效",
      "交通方案优先选大巴/新干线直连，避免折返",
    ],
    boost: ["inter_city_efficiency", "shinkansen_route", "city_hub"],
    suppress: ["single_area_deep_dive", "multi_day_same_area"],
  },
  {
    dimension: "play_mode",
    value: "single_city",
    instructions: [
      "用户想一地深玩，在单一城市内安排更丰富的层次",
      "可以按区域分天，同一个区域的不同面貌（白天/夜晚/早市）都可以排进去",
      "不需要安排跨城行程，把交通成本节省下来换成更多本地体验",
    ],
    boost: ["neighborhood_depth", "same_city_variety", "local_market", "evening_experience"],
    suppress: ["cross_city_transit", "day_trip_to_other_city"],
  },
];

// ── 四种交付语气模板 ──────────────────────────────────────────────────────────
// 供文案生成时注入 prompt 前缀，体现用户差异感

export interface DeliveryTone {
  key: string;
  label: string;
  promptPrefix: string;
  example: string;
}

export const DELIVERY_TONE: DeliveryTone[] = [
  {
    key: "first_time",
    label: "首次去日本",
    promptPrefix:
      '用户是第一次去日本。用引导式语气写行程说明，解释每个安排背后的原因，多用"这里建议你……"、"这样安排是因为……"等句式。',
    example:
      "浅草寺建议你在上午 10 点前到，这个时间段游客还不多，而且正面拍雷门的光线最好。仲见世通的商品价格偏高，不建议在这里买纪念品，旁边小巷的价格会便宜很多。",
  },
  {
    key: "experienced",
    label: "去过多次的熟客",
    promptPrefix:
      '用户去过日本多次，对基础常识已很熟悉。语气简洁直接，省略显而易见的解释，重点说「这次和上次不同的地方」和「本地人才知道的选择」。',
    example:
      "这次绕开上野公园，推荐你试试谷中银座——昭和老街感很强，游客少，路边有几家本地人开的甜品店值得进去坐坐。交通直接搭日暮里线，10 分钟到。",
  },
  {
    key: "multi_city",
    label: "多城顺玩",
    promptPrefix:
      "用户想多城顺玩。语气注重效率和节奏感，每段说明要体现「这样顺路省时」的逻辑，说清楚城市间怎么接驳最合算。",
    example:
      "东京 → 京都走东海道新干线，约 2h15min，直接在京都站出发。建议在京都住 2 晚，第三天傍晚直接从京都乘新干线去大阪，酒店定在大阪站附近，第二天一早逛道顿堀不用赶时间。",
  },
  {
    key: "single_city",
    label: "一地深玩",
    promptPrefix:
      "用户想在一个城市深度体验。语气注重层次感和发现感，同一个地方可以从不同角度写（早上和晚上完全不同）。告诉用户「只待这一个地方，你能看到的比走马观花多很多」。",
    example:
      "锦市场早上 8 点和下午 2 点是完全不同的体验：早上是本地人买菜的时间，摊主会和你说话，可以试吃；下午变成游客区，热闹但嘈杂。我们帮你安排了两次路过，感觉会完全不一样。",
  },
];

// ── 首页 / 专题页入口短文案 ────────────────────────────────────────────────────
// 四个场景各一句，供首页 hero 区 / /rush 入口卡片使用

export const ENTRY_COPY = {
  first_time: {
    hook: "第一次去日本？",
    sub: "我们帮你排好每一天，不用查攻略，不踩坑，拿到就能出发。",
    cta: "开始定制行程 →",
  },
  experienced: {
    hook: "去过很多次了？",
    sub: "这次换个玩法——本地路线、少人排队、你还没去过的那些街区。",
    cta: "来一次不一样的 →",
  },
  multi_city: {
    hook: "想多城顺玩？",
    sub: "东京 + 京都 + 大阪，顺路走一遍，我们帮你算好最省时的接驳方式。",
    cta: "开始规划路线 →",
  },
  single_city: {
    hook: "想一地深玩？",
    sub: "只去一个城市，把它玩透——早市、老街、夜景、本地食堂，全安排进去。",
    cta: "开始深度定制 →",
  },
} as const;
