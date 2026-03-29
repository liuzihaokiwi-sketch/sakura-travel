from __future__ import annotations

"""
AI 种子数据生成器
用 Claude 直接生成日本各城市的景点/餐厅/酒店结构化数据
无需外部爬虫，立即可用，作为数据库初始种子

特点：
- 生成真实存在的知名地点（Claude 训练数据里有完整的日本旅游信息）
- 包含坐标、评分、描述、标签等完整字段
- 支持分城市、分类别批量生成
- 幂等：重复运行不会产生重复数据
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.core.ai_cache import cached_ai_call
from app.core.config import settings


def _extract_json_array(text: str) -> str:
    """
    从 AI 响应中提取并清洗 JSON 数组，带多层容错处理：
    1. 去掉 markdown code block
    2. 去掉 JSON 前后的解释文字
    3. 修复 control characters、尾部多余逗号、单引号
    4. 尝试截断修复（AI 返回被截断时补齐括号）
    """
    import json as _json

    text = text.strip()

    # 1. 去掉 markdown code block（```json ... ``` 或 ``` ... ```）
    md_match = re.search(r'```(?:json)?\s*(\[.*?)\s*```', text, re.DOTALL)
    if md_match:
        text = md_match.group(1)
    else:
        # 2. 提取第一个 '[' 到最后一个 ']' 之间的内容
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        elif start != -1:
            # 截断 JSON：没有找到闭合 ']'，尝试补齐
            text = text[start:]

    # 3. 去除 control characters（\x00-\x1f 除 \t\n\r 外）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)

    # 4. 修复尾部多余逗号（, ] 或 , }）
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # 5. 先尝试直接解析
    try:
        _json.loads(text)
        return text
    except _json.JSONDecodeError:
        pass

    # 6. 尝试截断修复：找最后一个完整对象结尾 '}' 后加 ']'
    last_obj = text.rfind('}')
    if last_obj != -1:
        candidate = text[: last_obj + 1]
        # 找到这个 '}' 前的最后一个 '{'，构成完整对象列表
        candidate = candidate.rstrip().rstrip(',') + ']'
        # 确保以 '[' 开头
        if not candidate.lstrip().startswith('['):
            candidate = '[' + candidate
        try:
            _json.loads(candidate)
            return candidate
        except _json.JSONDecodeError:
            pass

    return '[]'


def validate_entity(data: dict) -> list[str]:
    """
    校验实体数据质量，返回错误列表（空列表 = 合法）。
    检查：name_zh 非空、坐标范围、评分范围。
    """
    errors: list[str] = []
    if not data.get("name_zh"):
        errors.append("name_zh is empty")
    lat = data.get("lat")
    lng = data.get("lng")
    if lat is not None:
        try:
            lat_f = float(lat)
            if lat_f < -90 or lat_f > 90:
                errors.append(f"lat {lat_f} out of range [-90, 90]")
        except (TypeError, ValueError):
            errors.append(f"lat is not numeric: {lat!r}")
    if lng is not None:
        try:
            lng_f = float(lng)
            if lng_f < -180 or lng_f > 180:
                errors.append(f"lng {lng_f} out of range [-180, 180]")
        except (TypeError, ValueError):
            errors.append(f"lng is not numeric: {lng!r}")
    rating = data.get("google_rating") or data.get("tabelog_score")
    if rating is not None:
        try:
            r = float(rating)
            if r < 0 or r > 5:
                errors.append(f"rating {r} out of range [0, 5]")
        except (TypeError, ValueError):
            pass
    return errors


def _extract_json_object(text: str) -> str:
    """从 AI 响应中提取单个 JSON 对象"""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return '{}'


# ─────────────────────────────────────────────────────────────────────────────
# POI 生成
# ─────────────────────────────────────────────────────────────────────────────

_POI_PROMPT = """\
你是日本旅游数据库工程师。请生成 {city_zh}（{city_en}）的{category}景点数据。

要求：
1. 只生成真实存在的知名景点，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字
3. 每条数据字段完整准确

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "浅草寺",
    "name_ja": "浅草寺",
    "name_en": "Senso-ji Temple",
    "city_code": "tokyo",
    "poi_category": "temple",
    "lat": 35.7148,
    "lng": 139.7967,
    "address_ja": "東京都台東区浅草2丁目3-1",
    "address_zh": "东京都台东区浅草2-3-1",
    "google_rating": 4.6,
    "google_review_count": 120000,
    "avg_visit_minutes": 90,
    "entrance_fee_jpy": 0,
    "opening_hours": "06:00-17:00",
    "best_season": ["spring", "autumn"],
    "tags": ["temple", "history", "culture", "shopping"],
    "short_desc_zh": "东京最古老的寺庙，建于628年，供奉观音菩萨，仲见世购物街延伸至雷门。",
    "tip_zh": "早晨6点开门时人少，推荐清晨参观体验宁静氛围。"
  }}
]

城市：{city_zh}（{city_en}）
类别：{category}
生成数量：{count} 条
poi_category 值只能用：shrine / temple / castle / museum / park / onsen / garden / landmark / theme_park / tower / market / district
"""

POI_CATEGORIES = {
    "shrine":     "神社",
    "temple":     "寺庙",
    "castle":     "城堡",
    "museum":     "博物馆美术馆",
    "park":       "公园自然景点",
    "district":   "街区商业区",
    "landmark":   "地标建筑塔",
    "onsen":      "温泉",
}

# 中国城市 POI 类别
POI_CATEGORIES_CN = {
    "temple":      "寺庙古刹",
    "museum":      "博物馆纪念馆",
    "park":        "公园自然景点",
    "district":    "历史街区古镇老街",
    "landmark":    "地标建筑",
    "scenic":      "自然风光景区",
    "garden":      "园林",
    "mountain":    "名山",
}

# 中国城市所属的 city_code 集合（用于自动判断是否使用中国版 prompt）
_CN_CITIES = frozenset([
    "guangzhou", "shenzhen", "hongkong", "macau", "zhuhai", "foshan", "shunde",
    "urumqi", "yili", "altay", "burqin", "kanas", "hemu", "nalati", "sailimu",
    "chaozhou", "shantou", "meizhou", "zhaoqing", "shaoguan", "qingyuan", "jiangmen",
    "shanghai", "hangzhou", "suzhou", "nanjing", "wuxi", "wuzhen", "xitang",
    "zhoushan", "huangshan", "moganshan",
])

# 中国城市菜系
RESTAURANT_CUISINES_CN = {
    "cantonese":   "粤菜（广府菜）",
    "dimsum":      "早茶点心",
    "teochew":     "潮汕菜",
    "hakka":       "客家菜",
    "hotpot":      "火锅",
    "bbq":         "烧烤串串",
    "seafood":     "海鲜",
    "noodles":     "面食粉食",
    "snack":       "地方小吃",
    "muslim":      "清真菜/新疆菜",
}

CITY_MAP = {
    # ── 关西圈 ──
    "tokyo":         ("东京", "Tokyo"),
    "osaka":         ("大阪", "Osaka"),
    "kyoto":         ("京都", "Kyoto"),
    "nara":          ("奈良", "Nara"),
    "kobe":          ("神户", "Kobe"),
    "uji":           ("宇治", "Uji"),
    "arima_onsen":   ("有马温泉", "Arima Onsen"),
    # ── 关东/东京圈 ──
    "hakone":        ("箱根", "Hakone"),
    "kamakura":      ("镰仓", "Kamakura"),
    "yokohama":      ("横滨", "Yokohama"),
    "nikko":         ("日光", "Nikko"),
    "kawaguchiko":   ("河口湖", "Kawaguchiko"),
    "karuizawa":     ("轻井泽", "Karuizawa"),
    # ── 北海道圈 ──
    "sapporo":       ("札幌", "Sapporo"),
    "otaru":         ("小樽", "Otaru"),
    "hakodate":      ("函馆", "Hakodate"),
    "noboribetsu":   ("登别", "Noboribetsu"),
    "furano":        ("富良野", "Furano"),
    "biei":          ("美瑛", "Biei"),
    "asahikawa":     ("旭川", "Asahikawa"),
    "toya":          ("洞爷湖", "Lake Toya"),
    # ── 广府圈（广深港澳）──
    "guangzhou":     ("广州", "Guangzhou"),
    "shenzhen":      ("深圳", "Shenzhen"),
    "hongkong":      ("香港", "Hong Kong"),
    "macau":         ("澳门", "Macau"),
    "zhuhai":        ("珠海", "Zhuhai"),
    "foshan":        ("佛山", "Foshan"),
    "shunde":        ("顺德", "Shunde"),
    # ── 北疆圈 ──
    "urumqi":        ("乌鲁木齐", "Urumqi"),
    "yili":          ("伊犁", "Yili"),
    "altay":         ("阿勒泰", "Altay"),
    "burqin":        ("布尔津", "Burqin"),
    "kanas":         ("喀纳斯", "Kanas"),
    "hemu":          ("禾木", "Hemu"),
    "nalati":        ("那拉提", "Nalati"),
    "sailimu":       ("赛里木湖", "Sayram Lake"),
    # ── 广东圈（潮汕+其他）──
    "chaozhou":      ("潮州", "Chaozhou"),
    "shantou":       ("汕头", "Shantou"),
    "meizhou":       ("梅州", "Meizhou"),
    "zhaoqing":      ("肇庆", "Zhaoqing"),
    "shaoguan":      ("韶关", "Shaoguan"),
    "qingyuan":      ("清远", "Qingyuan"),
    "jiangmen":      ("江门", "Jiangmen"),
    # ── 华东圈 ──
    "shanghai":      ("上海", "Shanghai"),
    "hangzhou":      ("杭州", "Hangzhou"),
    "suzhou":        ("苏州", "Suzhou"),
    "nanjing":       ("南京", "Nanjing"),
    "wuxi":          ("无锡", "Wuxi"),
    "wuzhen":        ("乌镇", "Wuzhen"),
    "xitang":        ("西塘", "Xitang"),
    "zhoushan":      ("舟山", "Zhoushan"),
    "huangshan":     ("黄山", "Huangshan"),
    "moganshan":     ("莫干山", "Moganshan"),
    # ── 其他日本城市（保持兼容）──
    "abashiri":      ("网走", "Abashiri"),
    "fukuoka":       ("福冈", "Fukuoka"),
    "hiroshima":     ("广岛", "Hiroshima"),
    "naha":          ("那霸", "Naha"),
    "ishigaki":      ("石垣岛", "Ishigaki"),
    "miyako":        ("宫古岛", "Miyako"),
    "kerama":        ("庆良间", "Kerama"),
    "kanazawa":      ("金泽", "Kanazawa"),
    # ── 九州补充城市 ──
    "beppu":         ("别府", "Beppu"),
    "yufuin":        ("由布院", "Yufuin"),
    "nagasaki":      ("长崎", "Nagasaki"),
    "kagoshima":     ("鹿儿岛", "Kagoshima"),
    "aso":           ("阿苏", "Aso"),
    "kumamoto":      ("熊本", "Kumamoto"),
    # ── 中部补充城市 ──
    "takayama":      ("高山", "Takayama"),
    "shirakawago":   ("白川乡", "Shirakawa-go"),
    "matsumoto":     ("松本", "Matsumoto"),
}


_POI_PROMPT_CN = """\
你是中国旅游数据库工程师。请生成{city_zh}（{city_en}）的{category}景点数据。

要求：
1. 只生成真实存在的知名景点，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字
3. 每条数据字段完整准确

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "陈家祠",
    "name_en": "Chen Clan Ancestral Hall",
    "city_code": "guangzhou",
    "poi_category": "landmark",
    "lat": 23.1285,
    "lng": 113.2458,
    "address_zh": "广州市荔湾区中山七路恩龙里34号",
    "google_rating": 4.5,
    "google_review_count": 8000,
    "avg_visit_minutes": 90,
    "entrance_fee_cny": 10,
    "opening_hours": "08:30-17:30",
    "best_season": ["spring", "autumn"],
    "tags": ["history", "culture", "architecture"],
    "short_desc_zh": "清代广东七十二县陈姓合族祠堂，岭南建筑艺术巅峰之作。",
    "tip_zh": "建议早上去，光线好，游客少，适合拍照。"
  }}
]

城市：{city_zh}（{city_en}）
类别：{category}
生成数量：{count} 条
poi_category 值只能用：temple / museum / park / district / landmark / scenic / garden / mountain / market
"""


async def generate_pois(
    city_code: str,
    category: str,
    count: int = 5,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定类别的景点数据。
    自动根据 city_code 选择日本版或中国版 prompt。
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    is_cn = city_code in _CN_CITIES

    if is_cn:
        cat_zh = POI_CATEGORIES_CN.get(category, category)
        prompt = _POI_PROMPT_CN.format(
            city_zh=city_zh, city_en=city_en,
            category=cat_zh, count=count,
        )
    else:
        cat_zh = POI_CATEGORIES.get(category, category)
        prompt = _POI_PROMPT.format(
            city_zh=city_zh, city_en=city_en,
            category=cat_zh, count=count,
        )

    raw = await cached_ai_call(
        prompt=prompt,
        model=settings.ai_model,
        temperature=0.3,
        max_tokens=4000,
    )

    data = json.loads(_extract_json_array(raw or "[]"))

    for item in data:
        item["city_code"] = city_code
        if "poi_category" not in item:
            item["poi_category"] = category
        # 中国城市：将 entrance_fee_cny 转换为统一字段
        if is_cn and "entrance_fee_cny" in item:
            item["entrance_fee_jpy"] = int((item.pop("entrance_fee_cny") or 0) * 21)

    return data


# ─────────────────────────────────────────────────────────────────────────────
# 餐厅生成
# ─────────────────────────────────────────────────────────────────────────────

_RESTAURANT_PROMPT = """\
你是日本美食数据库工程师。请生成 {city_zh}（{city_en}）的{cuisine}餐厅数据。

要求：
1. 只生成真实存在的知名餐厅或代表性餐厅，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字
3. tabelog_score 范围 3.0-5.0

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "すきやばし次郎 本店",
    "name_ja": "すきやばし次郎 本店",
    "name_en": "Sukiyabashi Jiro Honten",
    "city_code": "tokyo",
    "cuisine_type": "sushi",
    "district": "银座",
    "lat": 35.6721,
    "lng": 139.7636,
    "tabelog_score": 4.2,
    "tabelog_review_count": 850,
    "price_lunch_jpy": 30000,
    "price_dinner_jpy": 40000,
    "price_tier": "luxury",
    "has_lunch": true,
    "has_dinner": true,
    "reservation_required": true,
    "tags": ["sushi", "michelin", "omakase"],
    "short_desc_zh": "米其林三星寿司名店，传奇师傅小野二郎主持，需提前数月预订。",
    "tip_zh": "需要通过酒店礼宾部预订，个人预订几乎不可能。"
  }}
]

城市：{city_zh}
菜系：{cuisine}
生成数量：{count} 条
cuisine_type 只能用：sushi / ramen / tempura / yakitori / kaiseki / izakaya / teppanyaki / udon / soba / wagyu / seafood / japanese / western / cafe
price_tier 只能用：budget / mid / premium / luxury
"""

RESTAURANT_CUISINES = {
    "sushi":    "寿司",
    "ramen":    "拉面",
    "kaiseki":  "怀石料理",
    "yakitori": "烧鸟居酒屋",
    "tempura":  "天妇罗",
    "wagyu":    "和牛烧肉",
    "udon":     "乌冬面荞麦面",
    "seafood":  "海鲜",
}


_RESTAURANT_PROMPT_CN = """\
你是中国美食数据库工程师。请生成{city_zh}（{city_en}）的{cuisine}餐厅数据。

要求：
1. 只生成真实存在的知名餐厅或老字号，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字
3. 大众点评评分范围 3.5-5.0

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "陶陶居（总店）",
    "name_en": "Taotaoju Restaurant",
    "city_code": "guangzhou",
    "cuisine_type": "cantonese",
    "district": "荔湾区",
    "lat": 23.1247,
    "lng": 113.2527,
    "dianping_score": 4.3,
    "price_lunch_cny": 80,
    "price_dinner_cny": 120,
    "price_tier": "mid",
    "has_lunch": true,
    "has_dinner": true,
    "reservation_required": false,
    "tags": ["cantonese", "dimsum", "historic", "老字号"],
    "short_desc_zh": "百年老字号粤菜名店，早茶点心和经典粤菜均出色。",
    "tip_zh": "早茶需要排队，建议9点前到；虾饺和叉烧包必点。"
  }}
]

城市：{city_zh}
菜系：{cuisine}
生成数量：{count} 条
cuisine_type 只能用：cantonese / dimsum / teochew / hakka / hotpot / bbq / seafood / noodles / snack / muslim / western / cafe
price_tier 只能用：budget / mid / premium / luxury
"""


async def generate_restaurants(
    city_code: str,
    cuisine: str,
    count: int = 5,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定菜系的餐厅数据。
    自动根据 city_code 选择日本版或中国版 prompt。
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    is_cn = city_code in _CN_CITIES

    if is_cn:
        cuisine_zh = RESTAURANT_CUISINES_CN.get(cuisine, cuisine)
        prompt = _RESTAURANT_PROMPT_CN.format(
            city_zh=city_zh, city_en=city_en,
            cuisine=cuisine_zh, count=count,
        )
    else:
        cuisine_zh = RESTAURANT_CUISINES.get(cuisine, cuisine)
        prompt = _RESTAURANT_PROMPT.format(
            city_zh=city_zh, city_en=city_en,
            cuisine=cuisine_zh, count=count,
        )

    raw = await cached_ai_call(
        prompt=prompt,
        model=settings.ai_model,
        temperature=0.3,
        max_tokens=4000,
    )

    data = json.loads(_extract_json_array(raw or "[]"))

    for item in data:
        item["city_code"] = city_code
        if "cuisine_type" not in item:
            item["cuisine_type"] = cuisine
        # 中国城市：价格转换 CNY → JPY（用于统一 DB 字段）
        if is_cn:
            for key in ("price_lunch_cny", "price_dinner_cny"):
                jpy_key = key.replace("_cny", "_jpy")
                if key in item:
                    item[jpy_key] = int((item.pop(key) or 0) * 21)
            if "dianping_score" in item:
                item["tabelog_score"] = item.pop("dianping_score")

    return data


# ─────────────────────────────────────────────────────────────────────────────
# 酒店生成
# ─────────────────────────────────────────────────────────────────────────────

_HOTEL_PROMPT = """\
你是日本酒店数据库工程师。请生成 {city_zh}（{city_en}）的{tier}酒店数据。

要求：
1. 只生成真实存在的知名酒店，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "东京文华东方酒店",
    "name_ja": "マンダリン オリエンタル 東京",
    "name_en": "Mandarin Oriental Tokyo",
    "city_code": "tokyo",
    "district": "日本桥",
    "lat": 35.6868,
    "lng": 139.7742,
    "star_rating": 5,
    "price_tier": "luxury",
    "price_per_night_jpy": 80000,
    "google_rating": 4.7,
    "google_review_count": 3200,
    "nearest_station": "三越前駅",
    "walk_minutes_to_station": 1,
    "has_onsen": false,
    "has_pool": true,
    "has_gym": true,
    "hotel_type": "city_hotel",
    "tags": ["luxury", "city_view", "spa", "michelin_dining"],
    "short_desc_zh": "位于日本桥三井塔38-38层，俯瞰东京全景，拥有米其林星级餐厅。",
    "tip_zh": "顶楼酒吧的夜景极佳，即使不住店也可前往消费。"
  }}
]

城市：{city_zh}
档位：{tier}
生成数量：{count} 条
price_tier 只能用：budget / mid / premium / luxury
hotel_type 只能用：city_hotel / ryokan / resort / business / capsule / hostel
"""

HOTEL_TIERS = ["budget", "mid", "premium", "luxury"]


_HOTEL_PROMPT_CN = """\
你是中国酒店数据库工程师。请生成{city_zh}（{city_en}）的{tier}酒店/民宿数据。

要求：
1. 只生成真实存在的知名酒店或精品民宿，不要捏造
2. 严格输出 JSON 数组，不要任何解释文字

输出格式（JSON 数组，{count} 条）：
[
  {{
    "name_zh": "广州白天鹅宾馆",
    "name_en": "White Swan Hotel Guangzhou",
    "city_code": "guangzhou",
    "district": "沙面",
    "lat": 23.1089,
    "lng": 113.2350,
    "star_rating": 5,
    "price_tier": "premium",
    "price_per_night_cny": 800,
    "google_rating": 4.5,
    "google_review_count": 2500,
    "nearest_station": "黄沙地铁站",
    "walk_minutes_to_station": 5,
    "has_pool": true,
    "has_gym": true,
    "hotel_type": "city_hotel",
    "tags": ["historic", "river_view", "dimsum"],
    "short_desc_zh": "中国第一家五星级酒店，坐落沙面岛，珠江景观一流。",
    "tip_zh": "早茶出名，住客可以在玉堂春暖餐厅吃到顶级广式早茶。"
  }}
]

城市：{city_zh}
档位：{tier}
生成数量：{count} 条
price_tier 只能用：budget / mid / premium / luxury
hotel_type 只能用：city_hotel / boutique / resort / business / hostel / guesthouse
"""


async def generate_hotels(
    city_code: str,
    price_tier: str = "mid",
    count: int = 4,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定档位的酒店数据。
    自动根据 city_code 选择日本版或中国版 prompt。
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    is_cn = city_code in _CN_CITIES
    tier_map = {"budget": "经济", "mid": "中档", "premium": "高档", "luxury": "豪华"}
    tier_zh = tier_map.get(price_tier, price_tier)

    if is_cn:
        prompt = _HOTEL_PROMPT_CN.format(
            city_zh=city_zh, city_en=city_en,
            tier=tier_zh, count=count,
        )
    else:
        prompt = _HOTEL_PROMPT.format(
            city_zh=city_zh, city_en=city_en,
            tier=tier_zh, count=count,
        )

    raw = await cached_ai_call(
        prompt=prompt,
        model=settings.ai_model,
        temperature=0.3,
        max_tokens=4000,
    )

    data = json.loads(_extract_json_array(raw or "[]"))

    for item in data:
        item["city_code"] = city_code
        if "price_tier" not in item:
            item["price_tier"] = price_tier
        # 中国城市：价格转换
        if is_cn and "price_per_night_cny" in item:
            item["price_per_night_jpy"] = int((item.pop("price_per_night_cny") or 0) * 21)

    return data


# ─────────────────────────────────────────────────────────────────────────────
# 定向单实体生成（按名字）
# ─────────────────────────────────────────────────────────────────────────────

_ENTITY_BY_NAME_PROMPT = """\
你是日本旅游数据库工程师。请生成以下这个真实地点的详细数据。

地点名称：{name_zh}
所在城市：{city_zh}（{city_en}）
实体类型：{type_zh}

要求：
1. 这是一个真实存在的地点，请基于真实信息生成
2. 严格输出单个 JSON 对象，不要任何解释文字
3. 所有字段必须准确

{format_block}
"""

_ENTITY_BY_NAME_PROMPT_CN = """\
你是中国旅游数据库工程师。请生成以下这个真实地点的详细数据。

地点名称：{name_zh}
所在城市：{city_zh}（{city_en}）
实体类型：{type_zh}

要求：
1. 这是一个真实存在的地点，请基于真实信息生成
2. 严格输出单个 JSON 对象，不要任何解释文字
3. 所有字段必须准确

{format_block}
"""

_POI_FORMAT = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "地点中文名",
  "name_ja": "地点日文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "poi_category": "temple",
  "lat": 35.0000,
  "lng": 135.0000,
  "address_ja": "日文地址",
  "address_zh": "中文地址",
  "google_rating": 4.5,
  "google_review_count": 10000,
  "avg_visit_minutes": 60,
  "entrance_fee_jpy": 400,
  "opening_hours": "09:00-17:00",
  "best_season": ["spring", "autumn"],
  "tags": ["temple", "history"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
poi_category 只能用：shrine / temple / castle / museum / park / onsen / garden / landmark / theme_park / tower / market / district"""

_POI_FORMAT_CN = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "地点中文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "poi_category": "landmark",
  "lat": 23.0000,
  "lng": 113.0000,
  "address_zh": "中文地址",
  "google_rating": 4.5,
  "google_review_count": 5000,
  "avg_visit_minutes": 60,
  "entrance_fee_cny": 10,
  "opening_hours": "08:30-17:30",
  "best_season": ["spring", "autumn"],
  "tags": ["history", "culture"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
poi_category 只能用：temple / museum / park / district / landmark / scenic / garden / mountain / market"""

_RESTAURANT_FORMAT = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "餐厅中文名",
  "name_ja": "餐厅日文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "cuisine_type": "sushi",
  "district": "所在区域",
  "lat": 35.0000,
  "lng": 135.0000,
  "tabelog_score": 3.8,
  "tabelog_review_count": 500,
  "price_lunch_jpy": 1500,
  "price_dinner_jpy": 5000,
  "price_tier": "mid",
  "has_lunch": true,
  "has_dinner": true,
  "reservation_required": false,
  "tags": ["sushi", "local"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
cuisine_type 只能用：sushi / ramen / tempura / yakitori / kaiseki / izakaya / teppanyaki / udon / soba / wagyu / seafood / japanese / western / cafe
price_tier 只能用：budget / mid / premium / luxury"""

_RESTAURANT_FORMAT_CN = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "餐厅中文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "cuisine_type": "cantonese",
  "district": "所在区域",
  "lat": 23.0000,
  "lng": 113.0000,
  "dianping_score": 4.3,
  "price_lunch_cny": 80,
  "price_dinner_cny": 120,
  "price_tier": "mid",
  "has_lunch": true,
  "has_dinner": true,
  "reservation_required": false,
  "tags": ["cantonese", "老字号"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
cuisine_type 只能用：cantonese / dimsum / teochew / hakka / hotpot / bbq / seafood / noodles / snack / muslim / western / cafe
price_tier 只能用：budget / mid / premium / luxury"""

_HOTEL_FORMAT = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "酒店中文名",
  "name_ja": "酒店日文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "district": "所在区域",
  "lat": 35.0000,
  "lng": 135.0000,
  "star_rating": 4,
  "price_tier": "mid",
  "price_per_night_jpy": 15000,
  "google_rating": 4.3,
  "google_review_count": 1500,
  "nearest_station": "最近车站",
  "walk_minutes_to_station": 5,
  "has_onsen": false,
  "has_pool": false,
  "has_gym": true,
  "hotel_type": "city_hotel",
  "tags": ["convenient", "clean"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
price_tier 只能用：budget / mid / premium / luxury
hotel_type 只能用：city_hotel / ryokan / resort / business / capsule / hostel"""

_HOTEL_FORMAT_CN = """\
输出格式（单个 JSON 对象）：
{{
  "name_zh": "酒店中文名",
  "name_en": "English Name",
  "city_code": "{city_code}",
  "district": "所在区域",
  "lat": 23.0000,
  "lng": 113.0000,
  "star_rating": 4,
  "price_tier": "mid",
  "price_per_night_cny": 500,
  "google_rating": 4.3,
  "google_review_count": 1500,
  "nearest_station": "最近地铁站",
  "walk_minutes_to_station": 5,
  "has_pool": false,
  "has_gym": true,
  "hotel_type": "city_hotel",
  "tags": ["convenient", "clean"],
  "short_desc_zh": "简短中文描述",
  "tip_zh": "实用贴士"
}}
price_tier 只能用：budget / mid / premium / luxury
hotel_type 只能用：city_hotel / boutique / resort / business / hostel / guesthouse"""


async def generate_entity_by_name(
    name_zh: str,
    city_code: str,
    entity_type: str = "poi",
) -> Optional[Dict[str, Any]]:
    """
    按名字定向生成单个实体数据。

    不同于 generate_pois/restaurants/hotels 的批量按类别生成，
    这个函数针对一个具体的真实地点生成详细数据。

    Args:
        name_zh: 实体中文名（如"清水寺""道顿堀"）
        city_code: 所在城市代码（须在 CITY_MAP 中）
        entity_type: poi / restaurant / hotel

    Returns:
        单个实体数据 dict（兼容 upsert_entity），或 None（生成失败）
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        return None

    city_zh, city_en = city_info
    is_cn = city_code in _CN_CITIES

    type_zh_map = {"poi": "景点/地标", "restaurant": "餐厅", "hotel": "酒店"}
    type_zh = type_zh_map.get(entity_type, "景点/地标")

    # 选择格式块
    format_blocks = {
        "poi":        (_POI_FORMAT_CN if is_cn else _POI_FORMAT),
        "restaurant": (_RESTAURANT_FORMAT_CN if is_cn else _RESTAURANT_FORMAT),
        "hotel":      (_HOTEL_FORMAT_CN if is_cn else _HOTEL_FORMAT),
    }
    format_block = format_blocks.get(entity_type, format_blocks["poi"])
    format_block = format_block.replace("{city_code}", city_code)

    template = _ENTITY_BY_NAME_PROMPT_CN if is_cn else _ENTITY_BY_NAME_PROMPT
    prompt = template.format(
        name_zh=name_zh,
        city_zh=city_zh,
        city_en=city_en,
        type_zh=type_zh,
        format_block=format_block,
    )

    raw = await cached_ai_call(
        prompt=prompt,
        model=settings.ai_model,
        temperature=0.2,
        max_tokens=2000,
    )

    if not raw:
        return None

    try:
        data = json.loads(_extract_json_object(raw))
    except json.JSONDecodeError:
        return None

    if not data or not data.get("name_zh"):
        return None

    data["city_code"] = city_code

    # 中国城市价格转换
    if is_cn:
        if "entrance_fee_cny" in data:
            data["entrance_fee_jpy"] = int((data.pop("entrance_fee_cny") or 0) * 21)
        for key in ("price_lunch_cny", "price_dinner_cny"):
            jpy_key = key.replace("_cny", "_jpy")
            if key in data:
                data[jpy_key] = int((data.pop(key) or 0) * 21)
        if "dianping_score" in data:
            data["tabelog_score"] = data.pop("dianping_score")
        if "price_per_night_cny" in data:
            data["price_per_night_jpy"] = int((data.pop("price_per_night_cny") or 0) * 21)

    return data
