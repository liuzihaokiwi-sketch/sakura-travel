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

from openai import AsyncOpenAI

from app.core.config import settings

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.ai_base_url,
        )
    return _client


def _extract_json_array(text: str) -> str:
    """从 AI 响应中提取 JSON 数组"""
    text = text.strip()
    # ```json [...] ```
    match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    # 裸 [...]
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
    return '[]'


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

CITY_MAP = {
    "tokyo":     ("东京", "Tokyo"),
    "osaka":     ("大阪", "Osaka"),
    "kyoto":     ("京都", "Kyoto"),
    "nara":      ("奈良", "Nara"),
    "hakone":    ("箱根", "Hakone"),
    "kamakura":  ("镰仓", "Kamakura"),
    "sapporo":   ("札幌", "Sapporo"),
    "fukuoka":   ("福冈", "Fukuoka"),
    "hiroshima": ("广岛", "Hiroshima"),
    "naha":      ("那霸", "Naha"),
    "nikko":     ("日光", "Nikko"),
    "kanazawa":  ("金泽", "Kanazawa"),
}


async def generate_pois(
    city_code: str,
    category: str,
    count: int = 5,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定类别的景点数据。

    Args:
        city_code: 城市代码，如 "tokyo"
        category:  POI 类别，如 "shrine"
        count:     生成数量

    Returns:
        景点数据列表
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    cat_zh = POI_CATEGORIES.get(category, category)

    prompt = _POI_PROMPT.format(
        city_zh=city_zh, city_en=city_en,
        category=cat_zh, count=count,
    )

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content or "[]"
    data = json.loads(_extract_json_array(raw))

    # 确保 city_code 和 category 字段正确
    for item in data:
        item["city_code"] = city_code
        if "poi_category" not in item:
            item["poi_category"] = category

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


async def generate_restaurants(
    city_code: str,
    cuisine: str,
    count: int = 5,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定菜系的餐厅数据。
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    cuisine_zh = RESTAURANT_CUISINES.get(cuisine, cuisine)

    prompt = _RESTAURANT_PROMPT.format(
        city_zh=city_zh, city_en=city_en,
        cuisine=cuisine_zh, count=count,
    )

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content or "[]"
    data = json.loads(_extract_json_array(raw))

    for item in data:
        item["city_code"] = city_code
        if "cuisine_type" not in item:
            item["cuisine_type"] = cuisine

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


async def generate_hotels(
    city_code: str,
    price_tier: str = "mid",
    count: int = 4,
) -> List[Dict[str, Any]]:
    """
    用 Claude 生成指定城市、指定档位的酒店数据。
    """
    city_info = CITY_MAP.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市: {city_code}")

    city_zh, city_en = city_info
    tier_map = {"budget": "经济", "mid": "中档", "premium": "高档", "luxury": "豪华"}
    tier_zh = tier_map.get(price_tier, price_tier)

    prompt = _HOTEL_PROMPT.format(
        city_zh=city_zh, city_en=city_en,
        tier=tier_zh, count=count,
    )

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content or "[]"
    data = json.loads(_extract_json_array(raw))

    for item in data:
        item["city_code"] = city_code
        if "price_tier" not in item:
            item["price_tier"] = price_tier

    return data
