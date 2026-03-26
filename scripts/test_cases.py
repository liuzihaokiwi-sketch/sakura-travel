"""
test_cases.py — 三类回归测试用例定义 (v2 — 硬断言版)

标准型: 最常见用户，验证主链稳定
约束型: 大量限制（blocker case），验证规则和约束是否传到底
边界型: 容易翻车的场景，验证 fallback 和特殊 day type
"""

# ── 用例 1：标准型 ─────────────────────────────────────────────────────────────
CASE_STANDARD = {
    "case_id": "standard",
    "case_label": "标准型 · 情侣首次关西",
    "case_desc": "最常见用户画像，验证主链路是否稳定输出",

    "duration_days": 6,
    "cities": [
        {"city_code": "kyoto", "nights": 3},
        {"city_code": "osaka", "nights": 2},
    ],
    "party_type": "couple",
    "budget_level": "mid",
    "arrival_airport": "KIX",
    "departure_airport": "KIX",
    "arrival_shape": "same_city",
    "pace": "moderate",
    "must_have_tags": ["culture", "food", "theme_park"],
    "avoid_tags": [],
    "daytrip_tolerance": "medium",
    "hotel_switch_tolerance": "medium",
    "travel_dates": {"start": "2026-04-10", "end": "2026-04-15"},

    "profile_summary": {
        "travel_portrait": "情侣 · 首次关西 · 偏美食+轻松 · 不想频繁换酒店",
        "hard_constraints": [
            "6天5晚 · 关西经典圈",
            "京都3晚 + 大阪2晚",
            "含USJ环球影城",
            "返程日需轻量安排",
        ],
        "care_about": [
            "想吃好：章鱼烧、大阪烧、抹茶甜品都想试",
            "想少折腾：不频繁换酒店",
            "想拍好看的照片：千本鸟居、竹林、清水寺",
            "适度文化体验：寺社不要太密集",
        ],
        "key_decisions": [
            "不单独住奈良，改成京都日归（减少搬行李）",
            "USJ单独成天，不与其他景点混排",
            "高分餐厅放在大阪后段（作为行程高潮）",
            "到达日只保留轻量主线（伏见稻荷/河原町散步）",
            "全程菜系不重复，午餐跟走廊、晚餐品质优先",
        ],
    },

    "assertions": {
        "min_days": 6,
        "max_days": 6,
        # ── 走廊 & 结构 ──
        "must_have_corridors": ["fushimi", "arashiyama", "higashiyama"],
        "theme_park_day_exists": True,
        # ── arrival/departure 白名单 ──
        "arrival_day_type": "arrival",
        "departure_day_type": "departure",
        "departure_day_intensity_whitelist": ["light", "balanced"],
        # ── 住宿真实性 ──
        "must_have_hotel_cities": ["kyoto", "osaka"],   # hotel.bases 必须覆盖两城
        # ── 返程日无景点 ──
        "departure_day_no_poi": True,
        # ── 餐厅城市/走廊一致性 ──
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        # ── 净化 ──
        "no_raw_keys_in_pdf": True,
        # ── 体验质量 ──
        "day_vibe_consistency": True,
    },
}

# ── 用例 2：约束型（blocker）──────────────────────────────────────────────────
CASE_CONSTRAINED = {
    "case_id": "constrained",
    "case_label": "约束型 · 三代同堂家庭 [BLOCKER]",
    "case_desc": "大量限制条件，验证规则引擎和约束传递是否生效",
    "is_blocker": True,

    "duration_days": 5,
    "cities": [
        {"city_code": "kyoto", "nights": 3},
        {"city_code": "osaka", "nights": 1},
    ],
    "party_type": "family_multi_gen",
    "budget_level": "premium",
    "arrival_airport": "KIX",
    "departure_airport": "KIX",
    "arrival_shape": "same_city",
    "pace": "relaxed",
    "must_have_tags": ["culture", "nature"],
    "avoid_tags": ["sushi", "sashimi", "raw"],
    "daytrip_tolerance": "low",
    "hotel_switch_tolerance": "low",
    "travel_dates": {"start": "2026-04-12", "end": "2026-04-16"},

    "profile_summary": {
        "travel_portrait": "三代同堂 · 带70岁老人+5岁小孩 · 偏轻松 · 高预算 · 不吃生食",
        "hard_constraints": [
            "5天4晚 · 关西经典圈",
            "京都3晚 + 大阪1晚",
            "老人腿脚不便，每天步行控制在1万步以内",
            "不吃生鱼片/寿司等生食",
            "返程航班14:00，最后一天需提前到机场",
        ],
        "care_about": [
            "老人想看寺庙和日式庭园",
            "小孩想喂鹿（奈良）",
            "不要太多台阶和爬坡",
            "每天午休时间留够",
            "晚餐品质高但不要太晚",
        ],
        "key_decisions": [
            "住京都站附近（交通便利，减少老人步行）",
            "每天只安排1-2个主景点，不贪多",
            "奈良日归但只去奈良公园（平坦），不上春日大社山路",
            "餐厅排除所有 sushi/sashimi 标签",
            "返程日只保留酒店早餐+直奔机场",
        ],
    },

    "assertions": {
        "min_days": 5,
        "max_days": 5,
        # ── 约束传递 ──
        "avoid_cuisine_enforced": ["sushi", "sashimi"],
        "departure_day_type": "departure",
        "departure_day_intensity_whitelist": ["light"],
        "departure_day_max_items": 2,
        # ── 节奏约束 ──
        "all_days_max_intensity": "balanced",
        # ── 偏好兑现 ──
        "must_not_have_day_themes": ["USJ", "环球影城"],   # 老人团不应出现 USJ
        # ── 餐厅 ──
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        # ── 净化 ──
        "no_raw_keys_in_pdf": True,
        # ── 体验质量 ──
        "day_vibe_consistency": True,
    },
}

# ── 用例 3：边界型 ─────────────────────────────────────────────────────────────
CASE_EDGE = {
    "case_id": "edge",
    "case_label": "边界型 · 单人穷游短行程",
    "case_desc": "到达晚、预算紧、天数少但想去的多，验证 fallback 和特殊 day type",

    "duration_days": 4,
    "cities": [
        {"city_code": "osaka", "nights": 3},
    ],
    "party_type": "solo",
    "budget_level": "budget",
    "arrival_airport": "KIX",
    "departure_airport": "KIX",
    "arrival_shape": "evening_only",
    "arrival_time": "20:00",
    "pace": "dense",
    "must_have_tags": ["food", "theme_park", "culture"],
    "avoid_tags": [],
    "daytrip_tolerance": "high",
    "hotel_switch_tolerance": "low",
    "travel_dates": {"start": "2026-05-01", "end": "2026-05-04"},

    "profile_summary": {
        "travel_portrait": "独行侠 · 穷游 · 高密度 · 全住大阪不换酒店",
        "hard_constraints": [
            "4天3晚 · 全住大阪难波",
            "到达航班20:00落地，第一天只有晚餐时间",
            "必须含USJ整天",
            "想去京都日归（至少半天）",
            "预算经济型，人均每餐<1500日元",
        ],
        "care_about": [
            "吃遍大阪B级美食：章鱼烧、串炸、大阪烧",
            "USJ要玩够",
            "京都至少打卡伏见稻荷",
            "拍照发社交媒体",
        ],
        "key_decisions": [
            "到达日(Day1)仅安排道顿堀夜食，不排景点",
            "Day2 USJ整天（园区内解决午餐）",
            "Day3 京都日归：伏见稻荷(早)+清水寺/岚山(午后)，晚上回大阪",
            "Day4 上午黑门市场+大阪城，下午赴机场",
            "全程控制餐饮预算，以B级美食街头小吃为主",
        ],
    },

    "assertions": {
        "min_days": 4,
        "max_days": 4,
        # ── 结构 ──
        "arrival_day_type": "arrival",
        "arrival_day_max_items": 3,          # 到达日应轻量（晚到只有夜食）
        "departure_day_type": "departure",
        "theme_park_day_exists": True,       # release blocker: USJ 必须落成独立天
        # ── 餐厅 ──
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        # ── 净化 ──
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 4：樱花季 ─────────────────────────────────────────────────────────────
# 闺蜜樱花季，7天6晚，摄影重度，要赶花期，验证季节性权重和时间窗口
CASE_SAKURA = {
    "case_id": "sakura",
    "case_label": "季节型 · 闺蜜樱花季摄影",
    "case_desc": "樱花季高峰出行，验证季节性权重、花期时间窗和预约压力",

    "duration_days": 7,
    "cities": [
        {"city_code": "kyoto", "nights": 4},
        {"city_code": "osaka", "nights": 2},
    ],
    "party_type": "friends",
    "budget_level": "mid",
    "arrival_airport": "KIX",
    "departure_airport": "KIX",
    "arrival_shape": "same_city",
    "pace": "moderate",
    "must_have_tags": ["photo", "nature", "culture"],
    "avoid_tags": [],
    "daytrip_tolerance": "medium",
    "hotel_switch_tolerance": "medium",
    "travel_dates": {"start": "2026-03-28", "end": "2026-04-03"},

    "profile_summary": {
        "travel_portrait": "闺蜜四人 · 樱花季 · 重度摄影 · 愿意早起抢光线",
        "hard_constraints": [
            "7天6晚 · 关西经典圈",
            "京都4晚 + 大阪2晚",
            "出行日期 3/28–4/3 正值关西染井吉野盛花期",
            "清水寺/醍醐寺需提前查夜间特别参拜",
            "岚山竹林建议7点前到达避开人流",
        ],
        "care_about": [
            "要拍到最好的樱花：哲学之道、中之岛、醍醐寺",
            "想体验夜樱：清水寺春季夜间特别参拜 / 圆山公园",
            "和服变装拍一整天",
            "不想全是寺庙，要穿插咖啡厅和甜品",
        ],
        "key_decisions": [
            "京都段集中走樱花名所：哲学之道→南禅寺→清水寺→岚山",
            "安排一晚夜樱（清水寺夜间参拜或圆山公园）",
            "岚山安排最早出发（7:00竹林→天龙寺→渡月桥）",
            "大阪段安排大阪城赏樱+造币局樱花通路（如开放）",
            "到达日下午河原町散步+咖啡，不硬排景点",
        ],
    },

    "assertions": {
        "min_days": 7,
        "max_days": 7,
        # ── 走廊 & 结构 ──
        "must_have_corridors": ["arashiyama", "higashiyama"],
        "arrival_day_type": "arrival",
        "departure_day_type": "departure",
        "departure_day_intensity_whitelist": ["light", "balanced"],
        # ── 餐厅 ──
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        # ── 净化 ──
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 5：小众特殊要求 ──────────────────────────────────────────────────────
# 建筑设计师，只想看建筑和庭园，不去热门景点，纯素食，验证冷门走廊和饮食过滤
CASE_NICHE = {
    "case_id": "niche",
    "case_label": "小众型 · 建筑师深度庭园线",
    "case_desc": "冷门兴趣+饮食限制+拒绝热门景点，验证长尾覆盖和约束叠加",

    "duration_days": 5,
    "cities": [
        {"city_code": "kyoto", "nights": 4},
    ],
    "party_type": "solo",
    "budget_level": "premium",
    "arrival_airport": "KIX",
    "departure_airport": "KIX",
    "arrival_shape": "same_city",
    "pace": "relaxed",
    "must_have_tags": ["architecture", "nature", "culture"],
    "avoid_tags": ["yakiniku", "ramen"],
    "daytrip_tolerance": "low",
    "hotel_switch_tolerance": "low",
    "travel_dates": {"start": "2026-11-15", "end": "2026-11-19"},

    "profile_summary": {
        "travel_portrait": "建筑设计师 · 独行 · 红叶季 · 偏庭园和现代建筑 · 不吃烧肉拉面",
        "hard_constraints": [
            "5天4晚 · 全程住京都",
            "不去清水寺/金阁寺/伏见稻荷等超热门景点",
            "不吃烧肉和拉面",
            "每天最多2个主要目的地，留足驻留时间",
            "红叶季（11月中旬）出行",
        ],
        "care_about": [
            "安藤忠雄 · 陶板名画之庭、光之教堂（大阪茨木）",
            "枯山水 · 龙安寺、大德寺、东福寺方丈庭园",
            "苔寺（西芳寺）要提前预约",
            "桂离宫（需提前在宫内厅预约）",
            "现代建筑 · 京都站大楼（原广司）、MIHO MUSEUM（贝聿铭）",
        ],
        "key_decisions": [
            "全程住京都站附近（方便去宇治/大阪郊外看建筑）",
            "不排任何超热门景点，让出时间给小众庭园",
            "餐厅以�的石料理、汤豆腐、精进料理为主",
            "红叶重点放在东福寺通天桥和永观堂（非清水寺）",
            "安排一天宇治日归：平等院+中村藤吉抹茶",
        ],
    },

    "assertions": {
        "min_days": 5,
        "max_days": 5,
        # ── 约束传递 ──
        "avoid_cuisine_enforced": ["yakiniku", "ramen"],
        "departure_day_type": "departure",
        "departure_day_intensity_whitelist": ["light"],
        # ── 节奏 ──
        "all_days_max_intensity": "balanced",
        # ── 餐厅 ──
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        # ── 净化 ──
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 6：明确 must_not_go (blocked_clusters) ───────────────────────────────
CASE_MUST_NOT_GO = {
    "case_id": "must_not_go",
    "case_label": "约束型 · 明确拒绝景点",
    "case_desc": "用户明确 blocked_clusters，验证拒绝项不出现在行程中",

    "duration_days": 5,
    "cities": [
        {"city_code": "kyoto", "nights": 2},
        {"city_code": "osaka", "nights": 2},
    ],
    "party_type": "couple",
    "budget_level": "mid",
    "pace": "moderate",
    "must_have_tags": ["food"],
    "avoid_tags": [],
    "blocked_clusters": ["kyo_fushimi_inari", "kyo_kinkakuji_kinugasa"],
    "travel_dates": {"start": "2026-05-01", "end": "2026-05-05"},

    "profile_summary": {
        "travel_portrait": "情侣 · 明确拒绝伏见稻荷和金阁寺",
        "hard_constraints": ["blocked: fushimi_inari, kinkakuji"],
        "care_about": ["不想去游客太多的经典线"],
        "key_decisions": [],
    },

    "assertions": {
        "min_days": 5, "max_days": 5,
        "must_not_have_day_themes": ["伏见稻荷", "金阁寺"],
        "no_raw_keys_in_pdf": True,
        "meal_corridor_consistency": True,
    },
}

# ── 用例 7：纯餐饮禁忌 ──────────────────────────────────────────────────────────
CASE_AVOID_CUISINE = {
    "case_id": "avoid_cuisine",
    "case_label": "约束型 · 纯餐饮禁忌",
    "case_desc": "多种餐饮禁忌叠加，验证 avoid_cuisines 贯穿",

    "duration_days": 4,
    "cities": [
        {"city_code": "osaka", "nights": 3},
    ],
    "party_type": "friends",
    "budget_level": "mid",
    "pace": "moderate",
    "must_have_tags": ["food", "nightlife"],
    "avoid_tags": ["sushi", "sashimi", "raw", "seafood"],
    "travel_dates": {"start": "2026-06-01", "end": "2026-06-04"},

    "profile_summary": {
        "travel_portrait": "朋友聚会 · 大阪美食但不吃生鲜海鲜",
        "hard_constraints": ["avoid: sushi, sashimi, raw, seafood"],
        "care_about": ["大阪地道熟食", "夜生活"],
        "key_decisions": [],
    },

    "assertions": {
        "min_days": 4, "max_days": 4,
        "avoid_cuisine_enforced": ["sushi", "sashimi", "raw", "seafood"],
        "must_not_have_cities_in_meals": ["tokyo"],
        "meal_corridor_consistency": True,
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 8：直接返回机场 ─────────────────────────────────────────────────────────
CASE_AIRPORT_RETURN = {
    "case_id": "airport_return",
    "case_label": "边界型 · 返程直奔机场",
    "case_desc": "departure_day_shape=direct_to_airport，验证返程日无 POI",

    "duration_days": 4,
    "cities": [
        {"city_code": "kyoto", "nights": 2},
        {"city_code": "osaka", "nights": 1},
    ],
    "party_type": "couple",
    "budget_level": "budget",
    "pace": "moderate",
    "must_have_tags": [],
    "avoid_tags": [],
    "departure_day_shape": "direct_to_airport",
    "travel_dates": {"start": "2026-07-01", "end": "2026-07-04"},

    "profile_summary": {
        "travel_portrait": "情侣 · 最后一天直奔机场",
        "hard_constraints": ["返程日直接去机场", "4天3晚"],
        "care_about": ["不要赶行程"],
        "key_decisions": [],
    },

    "assertions": {
        "min_days": 4, "max_days": 4,
        "departure_day_type": "departure",
        "departure_day_no_poi": True,
        "departure_day_intensity_whitelist": ["light"],
        "departure_day_max_items": 2,
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 9：USJ 主题公园专线 ─────────────────────────────────────────────────────
CASE_THEME_PARK = {
    "case_id": "theme_park",
    "case_label": "标准型 · USJ 主题公园",
    "case_desc": "必含 USJ 独立成天，验证 theme_park day 结构",

    "duration_days": 5,
    "cities": [
        {"city_code": "osaka", "nights": 3},
        {"city_code": "kyoto", "nights": 1},
    ],
    "party_type": "family_child",
    "budget_level": "mid",
    "pace": "moderate",
    "must_have_tags": ["theme_park", "food"],
    "avoid_tags": [],
    "travel_dates": {"start": "2026-08-01", "end": "2026-08-05"},

    "profile_summary": {
        "travel_portrait": "亲子家庭 · 必去 USJ",
        "hard_constraints": ["含 USJ 环球影城独立成天", "5天4晚"],
        "care_about": ["孩子开心", "不要太赶"],
        "key_decisions": [],
    },

    "assertions": {
        "min_days": 5, "max_days": 5,
        "theme_park_day_exists": True,
        "meal_corridor_consistency": True,
        "no_raw_keys_in_pdf": True,
    },
}

# ── 用例 10：老年低强度 ──────────────────────────────────────────────────────────
CASE_ELDERLY = {
    "case_id": "elderly_low",
    "case_label": "约束型 · 老年低强度",
    "case_desc": "senior + relaxed，验证 max_intensity 全天不超过 light",

    "duration_days": 5,
    "cities": [
        {"city_code": "kyoto", "nights": 4},
    ],
    "party_type": "senior",
    "budget_level": "premium",
    "pace": "relaxed",
    "must_have_tags": ["garden", "culture"],
    "avoid_tags": ["theme_park", "nightlife", "hiking"],
    "travel_dates": {"start": "2026-10-15", "end": "2026-10-19"},

    "profile_summary": {
        "travel_portrait": "老年人 · 纯京都慢游 · 庭园+文化",
        "hard_constraints": ["全天 relaxed 节奏", "禁止主题公园/夜生活/徒步"],
        "care_about": ["无障碍", "不赶时间", "高品质餐饮"],
        "key_decisions": [],
    },

    "assertions": {
        "min_days": 5, "max_days": 5,
        "all_days_max_intensity": "light",
        "must_not_have_day_themes": ["USJ", "环球", "夜游"],
        "departure_day_type": "departure",
        "departure_day_intensity_whitelist": ["light"],
        "meal_corridor_consistency": True,
        "no_raw_keys_in_pdf": True,
    },
}


ALL_CASES = [
    CASE_STANDARD, CASE_CONSTRAINED, CASE_EDGE, CASE_SAKURA, CASE_NICHE,
    CASE_MUST_NOT_GO, CASE_AVOID_CUISINE, CASE_AIRPORT_RETURN, CASE_THEME_PARK, CASE_ELDERLY,
]
