from __future__ import annotations

"""
数据采集调度器（Crawler Pipeline）
自动选择数据源：
  - 网络可用 → OSM + Tabelog 真实爬虫（数据更准确）
  - 网络不可用 → AI 生成器（Claude 生成，立即可用）
  - 两者结合 → 真实爬虫为主，AI 补充缺失字段

用法：
  python -m scripts.crawl --city tokyo --type all
  或直接 import 调用 run_city_pipeline()
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.core.snapshots import record_snapshot
from app.domains.catalog.ai_generator import (
    CITY_MAP,
    POI_CATEGORIES,
    POI_CATEGORIES_CN,
    RESTAURANT_CUISINES,
    RESTAURANT_CUISINES_CN,
    HOTEL_TIERS,
    _CN_CITIES,
    generate_pois,
    generate_restaurants,
    generate_hotels,
    validate_entity,
)
from app.domains.catalog.web_crawler import (
    check_connectivity,
    fetch_osm_pois,
    fetch_tabelog_restaurants,
    fetch_wikipedia_summary,
)
from app.domains.catalog.upsert import upsert_entity

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 数据写入 DB
# ─────────────────────────────────────────────────────────────────────────────

async def _check_duplicate(session: AsyncSession, name_zh: str, city_code: str, entity_type: str) -> bool:
    """检查 name_zh + city_code + entity_type 是否已存在，存在则返回 True。"""
    from app.db.models.catalog import EntityBase
    from sqlalchemy import select
    try:
        existing = (await session.execute(
            select(EntityBase.entity_id).where(
                EntityBase.name_zh == name_zh,
                EntityBase.city_code == city_code,
                EntityBase.entity_type == entity_type,
            ).limit(1)
        )).scalar_one_or_none()
        return existing is not None
    except Exception:
        return False


async def _write_poi(session: AsyncSession, data: Dict[str, Any]) -> Optional[str]:
    """将 POI 数据写入数据库，返回 entity_id"""
    # 数据质量校验
    errs = validate_entity(data)
    if errs:
        logger.debug("跳过无效 POI [%s]: %s", data.get("name_zh", "?"), errs)
        return None
    # 去重检查
    name_zh = data.get("name_zh") or data.get("name_ja", "")
    city_code = data.get("city_code", "")
    if name_zh and city_code and await _check_duplicate(session, name_zh, city_code, "poi"):
        logger.debug("跳过重复 POI: %s / %s", name_zh, city_code)
        return None
    # 字段映射：ai_generator / web_crawler → upsert_entity 白名单字段
    db_data = {
        # entity_base 字段
        "name_zh":             data.get("name_zh") or data.get("name_ja", ""),
        "name_ja":             data.get("name_ja", ""),
        "name_en":             data.get("name_en", ""),
        "city_code":           data.get("city_code", ""),
        "lat":                 data.get("lat"),
        "lng":                 data.get("lng"),
        "address_ja":          data.get("address_ja", ""),
        "address_en":          data.get("address_en", ""),
        "data_tier":           "A" if data.get("source") == "osm" else "B",
        # pois 子表字段（按 upsert.py 白名单命名）
        "poi_category":        data.get("poi_category", "landmark"),
        "typical_duration_min": data.get("avg_visit_minutes"),
        "admission_fee_jpy":   data.get("entrance_fee_jpy"),
        "opening_hours_json":  data.get("opening_hours", ""),
        "best_season":         ",".join(data.get("best_season", [])) if isinstance(data.get("best_season"), list) else data.get("best_season", ""),
        "google_rating":       data.get("google_rating"),
        "google_review_count": data.get("google_review_count"),
    }
    # 去掉 None 和空字符串
    db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}

    google_place_id = data.get("google_place_id") or data.get("place_id")
    source_name = "osm" if data.get("source") == "osm" else "ai_generator"

    try:
        entity = await upsert_entity(
            session=session,
            entity_type="poi",
            data=db_data,
            google_place_id=google_place_id,
        )
        entity_id = str(entity.entity_id)
        # 写采集快照
        try:
            await record_snapshot(
                session=session,
                source_name=source_name,
                object_type="poi_batch",
                object_id=entity_id,
                raw_payload=data,
                expires_in_days=90,
            )
        except Exception as snap_err:
            logger.debug(f"快照写入失败 (POI {entity_id}): {snap_err}")
        return entity_id
    except Exception as e:
        logger.warning(f"写入 POI 失败: {data.get('name_ja', '?')} — {e}")
        await session.rollback()
        return None


async def _write_restaurant(session: AsyncSession, data: Dict[str, Any]) -> Optional[str]:
    """将餐厅数据写入数据库"""
    errs = validate_entity(data)
    if errs:
        logger.debug("跳过无效餐厅 [%s]: %s", data.get("name_zh", "?"), errs)
        return None
    name_zh = data.get("name_zh") or data.get("name_ja", "")
    city_code = data.get("city_code", "")
    if name_zh and city_code and await _check_duplicate(session, name_zh, city_code, "restaurant"):
        logger.debug("跳过重复餐厅: %s / %s", name_zh, city_code)
        return None
    db_data = {
        # entity_base 字段
        "name_zh":              data.get("name_zh") or data.get("name_ja", ""),
        "name_ja":              data.get("name_ja", ""),
        "name_en":              data.get("name_en", ""),
        "city_code":            data.get("city_code", ""),
        "lat":                  data.get("lat"),
        "lng":                  data.get("lng"),
        "data_tier":            "B",
        # restaurants 子表字段（按 upsert.py 白名单命名）
        "cuisine_type":         data.get("cuisine_type") or _guess_cuisine(data.get("cuisine_raw", "")),
        "tabelog_score":        data.get("tabelog_score"),
        "requires_reservation": data.get("reservation_required", False),
        "budget_lunch_jpy":     data.get("price_lunch_jpy"),
        "budget_dinner_jpy":    data.get("price_dinner_jpy"),
        "price_range_min_jpy":  data.get("price_lunch_jpy"),
        "price_range_max_jpy":  data.get("price_dinner_jpy"),
    }
    db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}

    tabelog_id = data.get("tabelog_id")

    source_name = "tabelog" if tabelog_id else "ai_generator"
    try:
        entity = await upsert_entity(
            session=session,
            entity_type="restaurant",
            data=db_data,
            tabelog_id=tabelog_id,
        )
        entity_id = str(entity.entity_id)
        try:
            await record_snapshot(
                session=session,
                source_name=source_name,
                object_type="restaurant_batch",
                object_id=entity_id,
                raw_payload=data,
                expires_in_days=90,
            )
        except Exception as snap_err:
            logger.debug(f"快照写入失败 (Restaurant {entity_id}): {snap_err}")
        return entity_id
    except Exception as e:
        logger.warning(f"写入餐厅失败: {data.get('name_ja', '?')} — {e}")
        await session.rollback()
        return None


async def _write_hotel(session: AsyncSession, data: Dict[str, Any]) -> Optional[str]:
    """将酒店数据写入数据库"""
    errs = validate_entity(data)
    if errs:
        logger.debug("跳过无效酒店 [%s]: %s", data.get("name_zh", "?"), errs)
        return None
    name_zh = data.get("name_zh") or data.get("name_ja", "")
    city_code = data.get("city_code", "")
    if name_zh and city_code and await _check_duplicate(session, name_zh, city_code, "hotel"):
        logger.debug("跳过重复酒店: %s / %s", name_zh, city_code)
        return None
    db_data = {
        "name_zh":                  data.get("name_zh") or data.get("name_ja", ""),
        "name_ja":                  data.get("name_ja", ""),
        "name_en":                  data.get("name_en", ""),
        "city_code":                data.get("city_code", ""),
        "lat":                      data.get("lat"),
        "lng":                      data.get("lng"),
        "star_rating":              data.get("star_rating"),
        "price_tier":               data.get("price_tier", "mid"),
        "price_per_night_jpy":      data.get("price_per_night_jpy"),
        "google_rating":            data.get("google_rating"),
        "google_review_count":      data.get("google_review_count"),
        "nearest_station":          data.get("nearest_station", ""),
        "walk_minutes_to_station":  data.get("walk_minutes_to_station"),
        "has_onsen":                data.get("has_onsen", False),
        "has_pool":                 data.get("has_pool", False),
        "has_gym":                  data.get("has_gym", False),
        "hotel_type":               data.get("hotel_type", "city_hotel"),
        "tags":                     data.get("tags", []),
        "short_desc_zh":            data.get("short_desc_zh", ""),
        "tip_zh":                   data.get("tip_zh", ""),
        "district":                 data.get("district", ""),
        "data_tier":                "B",
    }
    db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}

    try:
        entity = await upsert_entity(
            session=session,
            entity_type="hotel",
            data=db_data,
        )
        entity_id = str(entity.entity_id)
        try:
            await record_snapshot(
                session=session,
                source_name="ai_generator",
                object_type="hotel_batch",
                object_id=entity_id,
                raw_payload=data,
                expires_in_days=90,
            )
        except Exception as snap_err:
            logger.debug(f"快照写入失败 (Hotel {entity_id}): {snap_err}")
        return entity_id
    except Exception as e:
        logger.warning(f"写入酒店失败: {data.get('name_ja', '?')} — {e}")
        await session.rollback()
        return None


def _guess_cuisine(raw: str) -> str:
    """从日文菜系文字猜测 cuisine_type"""
    mapping = {
        "寿司": "sushi", "スシ": "sushi",
        "ラーメン": "ramen", "拉麺": "ramen",
        "天ぷら": "tempura",
        "焼き鳥": "yakitori", "居酒屋": "izakaya",
        "懐石": "kaiseki", "料亭": "kaiseki",
        "うどん": "udon", "蕎麦": "soba",
        "焼肉": "wagyu", "牛": "wagyu",
        "海鮮": "seafood",
    }
    for k, v in mapping.items():
        if k in raw:
            return v
    return "japanese"


def _guess_price_tier(price: Optional[int]) -> str:
    if not price:
        return "mid"
    if price < 2000:
        return "budget"
    elif price < 6000:
        return "mid"
    elif price < 15000:
        return "premium"
    return "luxury"


# ─────────────────────────────────────────────────────────────────────────────
# 主采集流程
# ─────────────────────────────────────────────────────────────────────────────

async def run_city_pipeline(
    session: AsyncSession,
    city_code: str,
    sync_pois: bool = True,
    sync_restaurants: bool = True,
    sync_hotels: bool = True,
    force_ai: bool = False,      # 强制使用 AI 生成（跳过网络检查）
    poi_count: int = 5,          # 每个类别生成数量
    restaurant_count: int = 5,
    hotel_count: int = 4,
) -> Dict[str, Any]:
    """
    一键采集指定城市的所有数据，自动选择数据源。

    Args:
        session:          数据库会话
        city_code:        城市代码，如 "tokyo"
        sync_pois:        是否采集景点
        sync_restaurants: 是否采集餐厅
        sync_hotels:      是否采集酒店
        force_ai:         强制 AI 生成（不检查网络）
        poi_count:        每类别景点数量
        restaurant_count: 每菜系餐厅数量
        hotel_count:      每档位酒店数量

    Returns:
        统计结果字典
    """
    if city_code not in CITY_MAP:
        return {"error": f"未知城市: {city_code}"}

    # 检查网络连通性
    if force_ai:
        connectivity = {"osm_overpass": False, "tabelog": False}
    else:
        logger.info(f"[{city_code}] 检查网络连通性...")
        connectivity = await check_connectivity()

    use_osm = connectivity.get("osm_overpass", False)
    use_tabelog = connectivity.get("tabelog", False)
    use_wiki = connectivity.get("wikipedia_ja", False)

    logger.info(
        f"[{city_code}] 数据源: OSM={'✅' if use_osm else '❌'} "
        f"Tabelog={'✅' if use_tabelog else '❌'} "
        f"Wiki={'✅' if use_wiki else '❌'} "
        f"→ {'真实爬虫' if (use_osm or use_tabelog) else 'AI生成'}"
    )

    stats: Dict[str, Any] = {
        "city": city_code,
        "mode": "crawler" if (use_osm or use_tabelog) else "ai_generator",
        "pois": 0, "restaurants": 0, "hotels": 0,
        "errors": [],
    }

    # ── 景点采集 ─────────────────────────────────────────────────────────────
    if sync_pois:
        poi_ids = []
        if use_osm:
            for osm_cat in ["shrine", "temple", "castle", "museum", "park", "attraction"]:
                try:
                    raw_list = await fetch_osm_pois(city_code, osm_cat, limit=poi_count)
                    for raw in raw_list:
                        if use_wiki and raw.get("name_ja") and not raw.get("short_desc_zh"):
                            wiki = await fetch_wikipedia_summary(raw["name_ja"])
                            if wiki.get("description"):
                                raw["short_desc_zh"] = wiki["description"]
                            if wiki.get("lat") and not raw.get("lat"):
                                raw["lat"] = wiki["lat"]
                                raw["lng"] = wiki["lng"]
                        eid = await _write_poi(session, raw)
                        if eid:
                            poi_ids.append(eid)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    stats["errors"].append(f"OSM POI [{osm_cat}]: {e}")
        else:
            # AI 批量生成 — 一次调用生成所有类别的 POI（减少 API 调用次数）
            _poi_cats = POI_CATEGORIES_CN if city_code in _CN_CITIES else POI_CATEGORIES
            all_cats = ", ".join(f"{v}({k})" for k, v in _poi_cats.items())
            total_count = poi_count * len(_poi_cats)
            try:
                # 单次调用，让 AI 一口气生成所有类别
                from app.domains.catalog.ai_generator import _extract_json_array, _CN_CITIES as _CN
                from app.core.ai_cache import cached_ai_call
                from app.core.config import settings as _settings

                city_zh, city_en = CITY_MAP[city_code]
                is_cn = city_code in _CN

                if is_cn:
                    prompt = (
                        f"你是中国旅游数据库工程师。请生成{city_zh}（{city_en}）的景点数据。\n\n"
                        f"要求：\n1. 只生成真实存在的知名景点\n2. 严格输出 JSON 数组\n"
                        f"3. 覆盖以下所有类别，每类 {poi_count} 条，共 {total_count} 条：{all_cats}\n\n"
                        f"输出格式同标准 POI 格式，包含 name_zh, name_en, city_code, poi_category, "
                        f"lat, lng, address_zh, google_rating, avg_visit_minutes, entrance_fee_cny, "
                        f"opening_hours, best_season, tags, short_desc_zh, tip_zh"
                    )
                else:
                    prompt = (
                        f"你是日本旅游数据库工程师。请生成{city_zh}（{city_en}）的景点数据。\n\n"
                        f"要求：\n1. 只生成真实存在的知名景点\n2. 严格输出 JSON 数组\n"
                        f"3. 覆盖以下所有类别，每类 {poi_count} 条，共 {total_count} 条：{all_cats}\n\n"
                        f"输出格式同标准 POI 格式，包含 name_zh, name_ja, name_en, city_code, poi_category, "
                        f"lat, lng, address_ja, google_rating, avg_visit_minutes, entrance_fee_jpy, "
                        f"opening_hours, best_season, tags, short_desc_zh, tip_zh"
                    )

                import json as _json
                raw_list = []
                for attempt in range(3):
                    try:
                        raw = await cached_ai_call(prompt=prompt, model=_settings.ai_model, temperature=0.3, max_tokens=8000)
                        parsed = _json.loads(_extract_json_array(raw or "[]"))
                        if parsed:
                            raw_list = parsed
                            break
                        logger.warning(f"[{city_code}] POI JSON 解析为空, attempt {attempt+1}/3")
                    except (_json.JSONDecodeError, Exception) as parse_err:
                        logger.warning(f"[{city_code}] POI JSON 解析失败, attempt {attempt+1}/3: {parse_err}")
                    if attempt < 2:
                        await asyncio.sleep(5)
                else:
                    stats["errors"].append(f"AI POI batch: JSON parse failed after 3 attempts")

                for raw_item in raw_list:
                    raw_item["city_code"] = city_code
                    if is_cn and "entrance_fee_cny" in raw_item:
                        raw_item["entrance_fee_jpy"] = int((raw_item.pop("entrance_fee_cny") or 0) * 21)
                    eid = await _write_poi(session, raw_item)
                    if eid:
                        poi_ids.append(eid)

                logger.info(f"[{city_code}] AI POI 批量生成: {len(poi_ids)} 条（1次API调用）")
            except Exception as e:
                stats["errors"].append(f"AI POI batch: {e}")
                logger.warning(f"[{city_code}] AI POI 批量失败: {e}")

        stats["pois"] = len(poi_ids)

    # ── 等待间隔（POI → 餐厅之间）─────────────────────────────────────────────
    if sync_pois and (sync_restaurants or sync_hotels):
        await asyncio.sleep(10)

    # ── 餐厅采集 ─────────────────────────────────────────────────────────────
    if sync_restaurants:
        rest_ids = []
        if use_tabelog:
            for cuisine in RESTAURANT_CUISINES:
                try:
                    raw_list = await fetch_tabelog_restaurants(
                        city_code, cuisine, limit=restaurant_count
                    )
                    for raw in raw_list:
                        eid = await _write_restaurant(session, raw)
                        if eid:
                            rest_ids.append(eid)
                    await asyncio.sleep(1.5)
                except Exception as e:
                    stats["errors"].append(f"Tabelog [{cuisine}]: {e}")
        else:
            # AI 批量生成 — 一次调用生成所有菜系
            _rest_cuisines = RESTAURANT_CUISINES_CN if city_code in _CN_CITIES else RESTAURANT_CUISINES
            all_cuisines = ", ".join(f"{v}({k})" for k, v in _rest_cuisines.items())
            total_rest = restaurant_count * len(_rest_cuisines)
            try:
                from app.domains.catalog.ai_generator import _extract_json_array, _CN_CITIES as _CN
                from app.core.ai_cache import cached_ai_call
                from app.core.config import settings as _settings

                city_zh, city_en = CITY_MAP[city_code]
                is_cn = city_code in _CN

                if is_cn:
                    prompt = (
                        f"你是中国美食数据库工程师。请生成{city_zh}（{city_en}）的餐厅数据。\n\n"
                        f"要求：\n1. 只生成真实存在的知名餐厅\n2. 严格输出 JSON 数组\n"
                        f"3. 覆盖以下菜系，每类 {restaurant_count} 条，共 {total_rest} 条：{all_cuisines}\n\n"
                        f"输出格式同标准餐厅格式，包含 name_zh, name_en, city_code, cuisine_type, "
                        f"district, lat, lng, dianping_score, price_lunch_cny, price_dinner_cny, "
                        f"price_tier, reservation_required, tags, short_desc_zh, tip_zh"
                    )
                else:
                    prompt = (
                        f"你是日本美食数据库工程师。请生成{city_zh}（{city_en}）的餐厅数据。\n\n"
                        f"要求：\n1. 只生成真实存在的知名餐厅\n2. 严格输出 JSON 数组\n"
                        f"3. 覆盖以下菜系，每类 {restaurant_count} 条，共 {total_rest} 条：{all_cuisines}\n\n"
                        f"输出格式同标准餐厅格式，包含 name_zh, name_ja, name_en, city_code, cuisine_type, "
                        f"district, lat, lng, tabelog_score, price_lunch_jpy, price_dinner_jpy, "
                        f"price_tier, reservation_required, tags, short_desc_zh, tip_zh"
                    )

                import json as _json
                raw_list = []
                for attempt in range(3):
                    try:
                        raw = await cached_ai_call(prompt=prompt, model=_settings.ai_model, temperature=0.3, max_tokens=8000)
                        parsed = _json.loads(_extract_json_array(raw or "[]"))
                        if parsed:
                            raw_list = parsed
                            break
                        logger.warning(f"[{city_code}] 餐厅 JSON 解析为空, attempt {attempt+1}/3")
                    except (_json.JSONDecodeError, Exception) as parse_err:
                        logger.warning(f"[{city_code}] 餐厅 JSON 解析失败, attempt {attempt+1}/3: {parse_err}")
                    if attempt < 2:
                        await asyncio.sleep(5)
                else:
                    stats["errors"].append(f"AI Restaurant batch: JSON parse failed after 3 attempts")

                for raw_item in raw_list:
                    raw_item["city_code"] = city_code
                    if is_cn:
                        for key in ("price_lunch_cny", "price_dinner_cny"):
                            jpy_key = key.replace("_cny", "_jpy")
                            if key in raw_item:
                                raw_item[jpy_key] = int((raw_item.pop(key) or 0) * 21)
                        if "dianping_score" in raw_item:
                            raw_item["tabelog_score"] = raw_item.pop("dianping_score")
                    eid = await _write_restaurant(session, raw_item)
                    if eid:
                        rest_ids.append(eid)

                logger.info(f"[{city_code}] AI 餐厅批量生成: {len(rest_ids)} 条（1次API调用）")
            except Exception as e:
                stats["errors"].append(f"AI Restaurant batch: {e}")
                logger.warning(f"[{city_code}] AI 餐厅批量失败: {e}")

        stats["restaurants"] = len(rest_ids)

    # ── 等待间隔（餐厅 → 酒店之间）──────────────────────────────────────────
    if sync_restaurants and sync_hotels:
        await asyncio.sleep(10)

    # ── 酒店采集（AI 批量生成）──────────────────────────────────────────────
    if sync_hotels:
        hotel_ids = []
        tier_zh_map = {"budget": "经济", "mid": "中档", "premium": "高档", "luxury": "豪华"}
        all_tiers = ", ".join(f"{tier_zh_map[t]}({t})" for t in HOTEL_TIERS)
        total_hotel = hotel_count * len(HOTEL_TIERS)
        try:
            from app.domains.catalog.ai_generator import _extract_json_array, _CN_CITIES as _CN
            from app.core.ai_cache import cached_ai_call
            from app.core.config import settings as _settings

            city_zh, city_en = CITY_MAP[city_code]
            is_cn = city_code in _CN
            tier_list = "经济(budget), 中档(mid), 高档(premium), 豪华(luxury)"

            if is_cn:
                prompt = (
                    f"你是中国酒店数据库工程师。请生成{city_zh}（{city_en}）的酒店数据。\n\n"
                    f"要求：\n1. 只生成真实存在的酒店\n2. 严格输出 JSON 数组\n"
                    f"3. 覆盖以下档位，每档 {hotel_count} 条，共 {total_hotel} 条：{tier_list}\n\n"
                    f"输出格式同标准酒店格式，包含 name_zh, name_en, city_code, district, "
                    f"lat, lng, star_rating, price_tier, price_per_night_cny, google_rating, "
                    f"nearest_station, walk_minutes_to_station, hotel_type, tags, short_desc_zh, tip_zh"
                )
            else:
                prompt = (
                    f"你是日本酒店数据库工程师。请生成{city_zh}（{city_en}）的酒店数据。\n\n"
                    f"要求：\n1. 只生成真实存在的酒店\n2. 严格输出 JSON 数组\n"
                    f"3. 覆盖以下档位，每档 {hotel_count} 条，共 {total_hotel} 条：{tier_list}\n\n"
                    f"输出格式同标准酒店格式，包含 name_zh, name_ja, name_en, city_code, district, "
                    f"lat, lng, star_rating, price_tier, price_per_night_jpy, google_rating, "
                    f"nearest_station, walk_minutes_to_station, has_onsen, hotel_type, tags, short_desc_zh, tip_zh"
                )

            import json as _json
            raw_list = []
            for attempt in range(3):
                try:
                    raw = await cached_ai_call(prompt=prompt, model=_settings.ai_model, temperature=0.3, max_tokens=8000)
                    parsed = _json.loads(_extract_json_array(raw or "[]"))
                    if parsed:
                        raw_list = parsed
                        break
                    logger.warning(f"[{city_code}] 酒店 JSON 解析为空, attempt {attempt+1}/3")
                except (_json.JSONDecodeError, Exception) as parse_err:
                    logger.warning(f"[{city_code}] 酒店 JSON 解析失败, attempt {attempt+1}/3: {parse_err}")
                if attempt < 2:
                    await asyncio.sleep(5)
            else:
                stats["errors"].append(f"AI Hotel batch: JSON parse failed after 3 attempts")

            for raw_item in raw_list:
                raw_item["city_code"] = city_code
                if "price_tier" not in raw_item:
                    raw_item["price_tier"] = "mid"
                if is_cn and "price_per_night_cny" in raw_item:
                    raw_item["price_per_night_jpy"] = int((raw_item.pop("price_per_night_cny") or 0) * 21)
                eid = await _write_hotel(session, raw_item)
                if eid:
                    hotel_ids.append(eid)

            logger.info(f"[{city_code}] AI 酒店批量生成: {len(hotel_ids)} 条（1次API调用）")
        except Exception as e:
            stats["errors"].append(f"AI Hotel batch: {e}")
            logger.warning(f"[{city_code}] AI 酒店批量失败: {e}")

        stats["hotels"] = len(hotel_ids)

    logger.info(
        f"[{city_code}] 完成 — "
        f"景点:{stats['pois']} 餐厅:{stats['restaurants']} 酒店:{stats['hotels']}"
    )

    # 自动触发评分：有任意类型数据写入时入队
    total_written = stats["pois"] + stats["restaurants"] + stats["hotels"]
    if total_written > 0:
        try:
            await enqueue_job("score_entities", city_code=city_code)
            logger.info(f"[{city_code}] 已入队 score_entities job")
        except Exception as eq_err:
            logger.warning(f"[{city_code}] 入队评分 job 失败（不影响采集结果）: {eq_err}")

    return stats


async def run_all_cities(
    session: AsyncSession,
    cities: Optional[List[str]] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    批量采集多个城市（顺序执行，避免请求过快）。

    Args:
        session: 数据库会话
        cities:  城市列表，默认采集所有城市
        **kwargs: 透传给 run_city_pipeline 的参数
    """
    target_cities = cities or list(CITY_MAP.keys())
    all_stats = []

    for city_code in target_cities:
        try:
            stats = await run_city_pipeline(session, city_code, **kwargs)
            all_stats.append(stats)
            await asyncio.sleep(2)   # 城市间间隔
        except Exception as e:
            all_stats.append({"city": city_code, "error": str(e)})

    return all_stats


# ─────────────────────────────────────────────────────────────────────────────
# D1.1  酒店爬虫原始数据 → hotels + entity_base
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_hotel_crawl(
    session: AsyncSession,
    data_dir: str = "data/hotels_raw",
) -> Dict[str, Any]:
    """
    读取 data/hotels_raw/*.json，将酒店数据 upsert 到 entity_base + hotels。

    JSON 格式:
      { "meta": {...}, "hotels": { "booking": [...], "agoda": [...] } }
    """
    import glob, json as _json, os

    stats: Dict[str, Any] = {"inserted": 0, "skipped": 0, "errors": []}
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        logger.warning(f"[ingest_hotel_crawl] 未找到文件: {data_dir}/*.json")
        return stats

    for fpath in files:
        try:
            raw = _json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            stats["errors"].append(f"读取失败 {fpath}: {e}")
            continue

        hotels_by_platform = raw.get("hotels", {})
        if isinstance(hotels_by_platform, list):
            hotels_by_platform = {"unknown": hotels_by_platform}

        for platform, items in hotels_by_platform.items():
            if not isinstance(items, list):
                continue
            for h in items:
                if not h.get("name_ja") and not h.get("name_zh"):
                    stats["skipped"] += 1
                    continue
                # star_rating: booking 用满分10制，DB 字段 NUMERIC(2,1) 最大 9.9
                raw_star = h.get("star_rating")
                star_rating = None
                if raw_star is not None:
                    try:
                        sr = float(raw_star)
                        star_rating = min(sr, 9.9) if sr > 0 else None
                    except (TypeError, ValueError):
                        pass

                db_data = {
                    "name_zh":               h.get("name_zh") or h.get("name_ja", ""),
                    "name_ja":               h.get("name_ja", ""),
                    "name_en":               h.get("name_en", ""),
                    "city_code":             h.get("city_code", ""),
                    "lat":                   h.get("lat"),
                    "lng":                   h.get("lng"),
                    "data_tier":             "A" if platform in ("booking", "agoda") else "B",
                    "hotel_type":            h.get("hotel_type", "city_hotel"),
                    "star_rating":           star_rating,
                    "typical_price_min_jpy": h.get("typical_price_min_jpy"),
                    "booking_score":         h.get("booking_score"),
                    "price_tier":            h.get("price_tier") or _guess_price_tier(h.get("typical_price_min_jpy")),
                    "booking_hotel_id":      h.get("booking_hotel_id"),
                }
                db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}
                try:
                    async with session.begin_nested():   # savepoint — 失败只回滚本条
                        entity = await upsert_entity(session=session, entity_type="hotel", data=db_data)
                        try:
                            await record_snapshot(
                                session=session,
                                source_name=f"hotel_crawl_{platform}",
                                object_type="hotel_batch",
                                object_id=str(entity.entity_id),
                                raw_payload=h,
                                expires_in_days=90,
                            )
                        except Exception:
                            pass
                    stats["inserted"] += 1
                except Exception as e:
                    stats["errors"].append(f"写入酒店失败 {h.get('name_ja')}: {e}")
                    stats["skipped"] += 1

    logger.info(f"[ingest_hotel_crawl] 完成: {stats}")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# D1.2  Tabelog 餐厅原始数据 → restaurants + entity_base
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_tabelog_crawl(
    session: AsyncSession,
    data_dir: str = "data/tabelog_raw",
) -> Dict[str, Any]:
    """
    读取 data/tabelog_raw/*.json，将餐厅数据 upsert 到 entity_base + restaurants。

    JSON 格式:
      { "meta": {...}, "restaurants": [...] }
    """
    import glob, json as _json, os

    stats: Dict[str, Any] = {"inserted": 0, "skipped": 0, "errors": []}
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        logger.warning(f"[ingest_tabelog_crawl] 未找到文件: {data_dir}/*.json")
        return stats

    for fpath in files:
        try:
            raw = _json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            stats["errors"].append(f"读取失败 {fpath}: {e}")
            continue

        restaurants = raw.get("restaurants", [])
        if not isinstance(restaurants, list):
            restaurants = []

        for r in restaurants:
            if not r.get("name_ja") and not r.get("name_zh"):
                stats["skipped"] += 1
                continue
            db_data = {
                "name_zh":             r.get("name_zh") or r.get("name_ja", ""),
                "name_ja":             r.get("name_ja", ""),
                "name_en":             r.get("name_en", ""),
                "city_code":           r.get("city_code", ""),
                "lat":                 r.get("lat"),
                "lng":                 r.get("lng"),
                "data_tier":           "A" if r.get("tabelog_score") else "B",
                "cuisine_type":        r.get("cuisine_type") or _guess_cuisine(
                    r.get("cuisine_query", "") + " " + r.get("cuisine_raw", "")
                ),
                "tabelog_score":       r.get("tabelog_score"),
                "budget_lunch_jpy":    r.get("price_lunch_jpy"),
                "budget_dinner_jpy":   r.get("price_dinner_jpy"),
                "price_range_min_jpy": r.get("price_lunch_jpy"),
                "price_range_max_jpy": r.get("price_dinner_jpy"),
                "tabelog_id":          r.get("tabelog_id"),
            }
            db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}
            tabelog_id = r.get("tabelog_id")
            try:
                async with session.begin_nested():   # savepoint
                    entity = await upsert_entity(
                        session=session,
                        entity_type="restaurant",
                        data=db_data,
                        tabelog_id=tabelog_id,
                    )
                    try:
                        await record_snapshot(
                            session=session,
                            source_name="tabelog_crawl",
                            object_type="restaurant_batch",
                            object_id=str(entity.entity_id),
                            raw_payload=r,
                            expires_in_days=90,
                        )
                    except Exception:
                        pass
                stats["inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"写入餐厅失败 {r.get('name_ja')}: {e}")
                stats["skipped"] += 1

    logger.info(f"[ingest_tabelog_crawl] 完成: {stats}")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# D1.3  JNTO / GO TOKYO 官方景点 → entity_base(type='poi')
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_jnto_spots(
    session: AsyncSession,
    data_dir: str = "data/raw/official",
) -> Dict[str, Any]:
    """
    读取 data/raw/official/*.json，将官方景点数据 upsert 到 entity_base(type='poi')。
    data_tier = 'A'（官方数据）。
    """
    import glob, json as _json, os
    from app.db.models.catalog import EntityTag
    from sqlalchemy import select

    stats: Dict[str, Any] = {"inserted": 0, "skipped": 0, "errors": []}
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        logger.warning(f"[ingest_jnto_spots] 未找到文件: {data_dir}/*.json")
        return stats

    for fpath in files:
        try:
            raw = _json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            stats["errors"].append(f"读取失败 {fpath}: {e}")
            continue

        spots = raw if isinstance(raw, list) else raw.get("spots", raw.get("data", []))
        if not isinstance(spots, list):
            stats["errors"].append(f"无法解析文件格式: {fpath}")
            continue

        for spot in spots:
            name_zh = spot.get("name_zh") or spot.get("name_en", "")
            if not name_zh:
                stats["skipped"] += 1
                continue

            city_code = spot.get("city_code") or spot.get("city", "")
            db_data = {
                "name_zh":      name_zh,
                "name_en":      spot.get("name_en", ""),
                "name_ja":      spot.get("name_ja", ""),
                "city_code":    city_code,
                "lat":          spot.get("lat"),
                "lng":          spot.get("lng"),
                "area_name":    spot.get("area") or spot.get("area_name", ""),
                "data_tier":    "A",
                "poi_category": spot.get("category", "landmark"),
            }
            db_data = {k: v for k, v in db_data.items() if v is not None and v != ""}
            try:
                async with session.begin_nested():   # savepoint
                    entity = await upsert_entity(session=session, entity_type="poi", data=db_data)
                    eid = entity.entity_id
                    for tag_val in (spot.get("tags") or []):
                        existing = (await session.execute(
                            select(EntityTag).where(
                                EntityTag.entity_id == eid,
                                EntityTag.tag_namespace == "feature",
                                EntityTag.tag_value == str(tag_val),
                            )
                        )).scalar_one_or_none()
                        if not existing:
                            session.add(EntityTag(
                                entity_id=eid,
                                tag_namespace="feature",
                                tag_value=str(tag_val),
                            ))
                    await session.flush()
                    try:
                        await record_snapshot(
                            session=session,
                            source_name="jnto_official",
                            object_type="poi_batch",
                            object_id=str(eid),
                            raw_payload=spot,
                            expires_in_days=180,
                        )
                    except Exception:
                        pass
                stats["inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"写入景点失败 {name_zh}: {e}")
                stats["skipped"] += 1

    logger.info(f"[ingest_jnto_spots] 完成: {stats}")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# D1.4  Events / Experiences → entity_base(type='event'/'experience')
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_events(
    session: AsyncSession,
    data_dir: str = "data/events_raw",
    event_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    读取 data/events_raw/*.json，将活动数据写入 entity_base(type='event')。
    event_types=None 表示写入所有类型。
    """
    import glob, json as _json, os
    from app.db.models.catalog import EntityBase
    from sqlalchemy import select

    stats: Dict[str, Any] = {"inserted": 0, "skipped": 0, "errors": []}
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))

    for fpath in files:
        try:
            raw = _json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            stats["errors"].append(f"读取失败 {fpath}: {e}")
            continue

        events = raw if isinstance(raw, list) else raw.get("events", [])
        if not isinstance(events, list):
            continue

        for ev in events:
            etype = ev.get("event_type", "festival")
            if event_types and etype not in event_types:
                stats["skipped"] += 1
                continue

            name = ev.get("name_zh") or ev.get("name_en") or ev.get("name_ja", "")
            if not name:
                stats["skipped"] += 1
                continue

            city_code = ev.get("city_code") or ev.get("city") or ""
            if not city_code:
                venue = (ev.get("venue") or "").lower()
                for kw in ("tokyo", "osaka", "kyoto", "nara", "hokkaido"):
                    if kw in venue:
                        city_code = kw
                        break

            existing = (await session.execute(
                select(EntityBase).where(
                    EntityBase.name_zh == name,
                    EntityBase.city_code == (city_code or "japan"),
                    EntityBase.entity_type == "event",
                )
            )).scalar_one_or_none()

            if existing:
                stats["skipped"] += 1
                continue

            try:
                async with session.begin_nested():  # savepoint
                    entity = EntityBase(
                        entity_type="event",
                        name_zh=name,
                        name_en=ev.get("name_en", ""),
                        name_ja=ev.get("name_ja", ""),
                        city_code=city_code or "japan",
                        data_tier="B",
                        is_active=True,
                    )
                    session.add(entity)
                    await session.flush()
                    try:
                        await record_snapshot(
                            session=session,
                            source_name=ev.get("source", "japan-guide"),
                            object_type="event_batch",
                            object_id=str(entity.entity_id),
                            raw_payload=ev,
                            expires_in_days=90,
                        )
                    except Exception:
                        pass
                stats["inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"写入 event 失败 {name}: {e}")
                stats["skipped"] += 1

    logger.info(f"[ingest_events] 完成: {stats}")
    return stats


async def ingest_experiences(
    session: AsyncSession,
    data_dir: str = "data/experiences_raw",
) -> Dict[str, Any]:
    """
    读取 data/experiences_raw/*.json，将体验活动写入 entity_base(type='experience')。
    字段来自 VELTRA 爬虫格式。
    """
    import glob, json as _json, os
    from app.db.models.catalog import EntityBase
    from sqlalchemy import select

    stats: Dict[str, Any] = {"inserted": 0, "skipped": 0, "errors": []}
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))

    for fpath in files:
        try:
            raw = _json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            stats["errors"].append(f"读取失败 {fpath}: {e}")
            continue

        items = raw if isinstance(raw, list) else raw.get("experiences", [])
        if not isinstance(items, list):
            continue

        for exp in items:
            name = exp.get("name") or exp.get("name_en", "")
            if not name:
                stats["skipped"] += 1
                continue

            city_code = (exp.get("city") or "tokyo").lower()

            existing = (await session.execute(
                select(EntityBase).where(
                    EntityBase.name_zh == name,
                    EntityBase.city_code == city_code,
                    EntityBase.entity_type == "experience",
                )
            )).scalar_one_or_none()

            if existing:
                stats["skipped"] += 1
                continue

            try:
                async with session.begin_nested():  # savepoint
                    entity = EntityBase(
                        entity_type="experience",
                        name_zh=name,
                        name_en=exp.get("name_en") or name,
                        city_code=city_code,
                        data_tier="B",
                        is_active=True,
                    )
                    session.add(entity)
                    await session.flush()
                    try:
                        await record_snapshot(
                            session=session,
                            source_name=exp.get("source", "veltra"),
                            object_type="experience_batch",
                            object_id=str(entity.entity_id),
                            raw_payload=exp,
                            expires_in_days=90,
                        )
                    except Exception:
                        pass
                stats["inserted"] += 1
            except Exception as e:
                stats["errors"].append(f"写入体验失败 {name}: {e}")
                stats["skipped"] += 1

    logger.info(f"[ingest_experiences] 完成: {stats}")
    return stats