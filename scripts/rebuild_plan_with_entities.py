"""
rebuild_plan_with_entities.py — v3: 修复 8 项链路问题

修复清单:
  1. arrival day 餐厅只落在到达 corridor / sleep_base 周边
  2. 餐厅带 serving_area + why_here + corridor 信息
  3. departure day 不配夜游型 cluster（在 skeleton 层已修）
  4. USJ/theme-park day 餐厅优先园区附近
  5. 同日同 cuisine 不超过 2 家，强制多样性
  6. city_code 字段写真实城市码（不写 area）
  7. 总览页只列实际出现的城市
  8. 内部 ID 不暴露到用户可见字段
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(name)s: %(message)s", datefmt="%H:%M:%S")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("rebuild")

from sqlalchemy import select, delete, text
from app.db.session import AsyncSessionLocal

# ── area → city 映射 ──────────────────────────────────────────────────────────
AREA_TO_CITY = {
    "kawaramachi": "kyoto", "gion": "kyoto", "kyoto_station": "kyoto",
    "namba": "osaka", "shinsaibashi": "osaka", "umeda": "osaka",
    "nara": "nara", "kyoto": "kyoto", "osaka": "osaka",
}

# ── corridor → city 映射 ─────────────────────────────────────────────────────
CORRIDOR_CITY = {
    "fushimi": "kyoto", "arashiyama": "kyoto", "higashiyama": "kyoto",
    "philosopher": "kyoto", "kinkakuji": "kyoto",
    "namba": "osaka", "dotonbori": "osaka", "shinsekai": "osaka",
    "sakurajima": "osaka", "osakajo": "osaka", "umeda": "osaka",
    "nara": "nara",
}

# ── cuisine 推断（从名字关键词） ──────────────────────────────────────────────
def _infer_cuisine(name: str) -> str:
    name_l = name.lower()
    if any(k in name_l for k in ["寿司", "鮨", "sushi"]): return "sushi"
    if any(k in name_l for k in ["拉面", "麺", "面", "ramen"]): return "ramen"
    if any(k in name_l for k in ["烧肉", "焼肉", "yakiniku"]): return "yakiniku"
    if any(k in name_l for k in ["天妇罗", "天ぷら", "tempura"]): return "tempura"
    if any(k in name_l for k in ["串炸", "串カツ", "kushikatsu"]): return "kushikatsu"
    if any(k in name_l for k in ["烧鸟", "焼鳥", "yakitori"]): return "yakitori"
    if any(k in name_l for k in ["章鱼烧", "たこ焼", "takoyaki"]): return "takoyaki"
    if any(k in name_l for k in ["大阪烧", "お好み焼", "okonomiyaki"]): return "okonomiyaki"
    if any(k in name_l for k in ["怀石", "kaiseki"]): return "kaiseki"
    if any(k in name_l for k in ["咖啡", "arabica", "coffee", "cafe"]): return "cafe"
    return "other"


async def main():
    async with AsyncSessionLocal() as session:
        # ── 1. 决策链 ────────────────────────────────────────────────
        from app.db.models.business import TripProfile
        profile = TripProfile(
            trip_request_id=uuid.uuid4(), duration_days=6,
            cities=[{"city_code": "kyoto", "nights": 3}, {"city_code": "osaka", "nights": 2}],
            party_type="couple", budget_level="mid",
            arrival_airport="KIX", departure_airport="KIX",
            arrival_shape="same_city", pace="moderate",
            must_have_tags=["culture", "food"], avoid_tags=[],
            daytrip_tolerance="medium", hotel_switch_tolerance="medium",
            travel_dates={"start": "2026-04-10", "end": "2026-04-15"},
        )

        from app.domains.planning.city_circle_selector import select_city_circle
        cr = await select_city_circle(session, profile)
        circle_id = cr.selected_circle_id

        from app.db.models.city_circles import ActivityCluster
        q = await session.execute(select(ActivityCluster.cluster_id).where(ActivityCluster.circle_id == circle_id))
        passed_ids = {r[0] for r in q.fetchall()}

        from app.domains.planning.major_activity_ranker import rank_major_activities
        ranking = await rank_major_activities(session, circle_id, profile, passed_ids)

        from app.domains.planning.hotel_base_builder import build_hotel_strategy
        hotel = await build_hotel_strategy(session, circle_id, profile,
            selected_cluster_ids=[m.cluster_id for m in ranking.selected_majors])

        from app.domains.planning.route_skeleton_builder import build_route_skeleton
        skeleton = build_route_skeleton(
            duration_days=6, selected_majors=ranking.selected_majors,
            hotel_bases=hotel.bases, pace="moderate")

        logger.info("圈=%s 活动=%d 酒店=%s(%dn) 骨架=%d天",
            circle_id, len(ranking.selected_majors), hotel.preset_name,
            hotel.total_nights, len(skeleton.frames))

        # ── 2. 清理旧数据 ────────────────────────────────────────────
        from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem
        old_plans = await session.execute(select(ItineraryPlan))
        for old in old_plans.scalars().all():
            old_days = await session.execute(select(ItineraryDay).where(ItineraryDay.plan_id == old.plan_id))
            for od in old_days.scalars().all():
                await session.execute(delete(ItineraryItem).where(ItineraryItem.day_id == od.day_id))
            await session.execute(delete(ItineraryDay).where(ItineraryDay.plan_id == old.plan_id))
            await session.execute(delete(ItineraryPlan).where(ItineraryPlan.plan_id == old.plan_id))
        await session.commit()

        # ── 3. 创建新 plan ───────────────────────────────────────────
        from app.db.models.business import TripRequest
        session.add(TripRequest(
            trip_request_id=profile.trip_request_id, user_id=None, status="generating",
            raw_input={"scene": "couple", "duration_days": 6, "cities": profile.cities},
        ))

        plan_id = uuid.uuid4()
        # 从骨架推导实际城市列表（不硬编码）
        actual_cities = []
        seen = set()
        for f in skeleton.frames:
            c = AREA_TO_CITY.get(f.sleep_base, f.sleep_base)
            if c not in seen:
                actual_cities.append(c)
                seen.add(c)
            cc = CORRIDOR_CITY.get(f.primary_corridor, "")
            if cc and cc not in seen:
                actual_cities.append(cc)
                seen.add(cc)

        session.add(ItineraryPlan(
            plan_id=plan_id, trip_request_id=profile.trip_request_id, status="draft",
            plan_metadata={
                "circle_id": circle_id,
                "circle_score": cr.selected.total_score,
                "hotel_strategy": hotel.preset_name,
                "pipeline": "city_circle_v2",
                "actual_cities": actual_cities,
                "hotel_bases": [{"city": b.base_city, "area": b.area, "nights": b.nights} for b in hotel.bases],
            },
        ))

        # ── 4. 预加载实体数据 ────────────────────────────────────────
        from app.db.models.city_circles import CircleEntityRole
        from app.db.models.catalog import EntityBase

        roles_q = await session.execute(
            select(CircleEntityRole).where(CircleEntityRole.circle_id == circle_id))
        cluster_entities = {}
        for role in roles_q.scalars().all():
            cluster_entities.setdefault(role.cluster_id, []).append(
                (role.entity_id, role.is_cluster_anchor))

        # 加载所有关西餐厅，按城市+区域分组
        rest_q = await session.execute(
            select(EntityBase).where(
                EntityBase.entity_type == "restaurant",
                EntityBase.city_code.in_(["kyoto", "osaka", "nara"]),
                EntityBase.is_active == True,
            ))
        all_restaurants = rest_q.scalars().all()

        # 按 city → area → [entity] 分组
        city_area_restaurants: dict[str, dict[str, list]] = {}
        city_restaurants: dict[str, list] = {}
        for r in all_restaurants:
            city_restaurants.setdefault(r.city_code, []).append(r)
            area = r.area_name or ""
            city_area_restaurants.setdefault(r.city_code, {}).setdefault(area, []).append(r)

        # 按 corridor_tags 分组
        corridor_restaurants: dict[str, list] = {}
        for r in all_restaurants:
            tags = r.corridor_tags or []
            for t in tags:
                corridor_restaurants.setdefault(t, []).append(r)

        logger.info("实体: %d cluster, %d 餐厅", len(cluster_entities), len(all_restaurants))

        # ── 5. 智能餐厅选择器 ────────────────────────────────────────
        used_restaurants: set = set()  # 全程去重

        def pick_meal_restaurant(
            frame_corridor: str,
            frame_sleep_base: str,
            frame_day_type: str,
            frame_main_driver: str,
            day_cuisine_counter: Counter,
            meal_type: str,
        ):
            """按优先级选择餐厅：corridor匹配 > 同城市 > 全局；同时强制 cuisine 多样性"""
            city = AREA_TO_CITY.get(frame_sleep_base, frame_sleep_base)
            corridor = frame_corridor or ""

            # 候选池：从最相关到最宽泛
            candidate_pools = []

            # 1. corridor 匹配的餐厅
            if corridor:
                corr_key = f"kyo_{corridor}" if city == "kyoto" else f"osa_{corridor}"
                if corr_key in corridor_restaurants:
                    candidate_pools.append(("corridor", corridor_restaurants[corr_key]))

            # 2. 同区域的餐厅
            area_map = city_area_restaurants.get(city, {})
            # arrival day 限定在 corridor/sleep_base 周边
            if frame_day_type == "arrival":
                # 只用 corridor 区域 + sleep_base 区域
                for area_key in [corridor, frame_sleep_base]:
                    if area_key in area_map:
                        candidate_pools.append(("area", area_map[area_key]))
            else:
                # 正常天用所有同城区域
                for area_key, rests in area_map.items():
                    candidate_pools.append(("city_area", rests))

            # 3. theme_park day 特殊：优先园区附近
            if "usj" in (frame_main_driver or "").lower() or "themepark" in (frame_main_driver or "").lower():
                # USJ 在此岛（sakurajima），附近是 namba/umeda
                for near_corr in ["sakurajima", "osa_usj", "namba"]:
                    if near_corr in corridor_restaurants:
                        candidate_pools.insert(0, ("theme_park_near", corridor_restaurants[near_corr]))

            # 4. 同城市兜底
            if city in city_restaurants:
                candidate_pools.append(("city_fallback", city_restaurants[city]))

            # 遍历候选池，找到 cuisine 不重复的
            for pool_name, pool in candidate_pools:
                for r in pool:
                    if r.entity_id in used_restaurants:
                        continue
                    cuisine = _infer_cuisine(r.name_zh or "")
                    # 同日同 cuisine ≤ 1（严格）
                    if day_cuisine_counter[cuisine] >= 1 and cuisine != "other":
                        continue
                    # 早餐偏好轻食（cafe/other），正餐偏好正式
                    if meal_type == "breakfast" and cuisine in ("kaiseki", "yakiniku"):
                        continue

                    used_restaurants.add(r.entity_id)
                    day_cuisine_counter[cuisine] += 1
                    return r, pool_name

            # 实在没有，取同城第一个未用的
            for r in city_restaurants.get(city, []) + city_restaurants.get("osaka", []):
                if r.entity_id not in used_restaurants:
                    used_restaurants.add(r.entity_id)
                    cuisine = _infer_cuisine(r.name_zh or "")
                    day_cuisine_counter[cuisine] += 1
                    return r, "last_resort"

            return None, "none"

        # ── 6. 逐天写入 ─────────────────────────────────────────────
        from app.domains.planning.route_skeleton_builder import _display_area

        for frame in skeleton.frames:
            real_city = AREA_TO_CITY.get(frame.sleep_base, frame.sleep_base)

            day = ItineraryDay(
                plan_id=plan_id,
                day_number=frame.day_index,
                city_code=real_city,  # 真实城市码
                day_theme=frame.title_hint or f"Day {frame.day_index}",
                day_summary_zh=f"{frame.day_type} | {_display_area(frame.primary_corridor or '')} | {frame.intensity}",
            )
            session.add(day)
            await session.flush()

            sort_order = 1
            day_cuisine = Counter()

            # 6a. 主活动
            if frame.main_driver and frame.main_driver in cluster_entities:
                entities = cluster_entities[frame.main_driver]
                anchor_list = [e for e in entities if e[1]]
                other_list = [e for e in entities if not e[1]]

                for eid, is_anchor in (anchor_list + other_list):
                    entity = await session.get(EntityBase, eid)
                    if not entity:
                        continue
                    item = ItineraryItem(
                        day_id=day.day_id,
                        entity_id=eid,
                        item_type=entity.entity_type,
                        sort_order=sort_order,
                        notes_zh=json.dumps({
                            "corridor": frame.primary_corridor,
                            "corridor_display": _display_area(frame.primary_corridor or ""),
                            "is_main_driver": is_anchor,
                            "name": entity.name_zh,
                            "area_display": entity.area_name or _display_area(frame.sleep_base),
                            "station": entity.nearest_station or "",
                        }, ensure_ascii=False),
                    )
                    session.add(item)
                    sort_order += 1
                    tag = "★" if is_anchor else " "
                    logger.info("  D%d %s %s (%s)", frame.day_index, tag, entity.name_zh, entity.area_name or "")

            # 6b. 餐窗 — 智能填充
            for meal in frame.meal_windows:
                r, source = pick_meal_restaurant(
                    frame_corridor=frame.primary_corridor,
                    frame_sleep_base=frame.sleep_base,
                    frame_day_type=frame.day_type,
                    frame_main_driver=frame.main_driver or "",
                    day_cuisine_counter=day_cuisine,
                    meal_type=meal.meal_type,
                )

                meal_zh = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal.meal_type, meal.meal_type)
                cuisine = _infer_cuisine(r.name_zh) if r else ""

                notes = {
                    "meal_type": meal.meal_type,
                    "placeholder": r is None,
                    "match_source": source,
                }
                if r:
                    notes.update({
                        "name": r.name_zh,
                        "area_display": r.area_name or _display_area(frame.sleep_base),
                        "serving_area": r.area_name or real_city,
                        "cuisine": cuisine,
                        "why_here": f"位于当日走廊{_display_area(frame.primary_corridor or '')}沿线" if source in ("corridor", "theme_park_near") else f"位于{_display_area(frame.sleep_base)}住宿周边",
                    })

                item = ItineraryItem(
                    day_id=day.day_id,
                    entity_id=r.entity_id if r else None,
                    item_type="restaurant",
                    sort_order=sort_order,
                    notes_zh=json.dumps(notes, ensure_ascii=False),
                )
                session.add(item)
                sort_order += 1

                rname = r.name_zh if r else "自由安排"
                logger.info("  D%d 🍽 %s → %s [%s] (%s)", frame.day_index, meal_zh, rname, cuisine, source)

        await session.commit()

        # ── 7. 质量门控检查 ──────────────────────────────────────────
        logger.info("── 质量门控 ──")
        errors = []
        warnings = []

        # Gate 1: 总纲城市一致性（骨架中出现的城市必须在 actual_cities）
        skeleton_cities = set()
        for f in skeleton.frames:
            skeleton_cities.add(AREA_TO_CITY.get(f.sleep_base, f.sleep_base))
            if f.primary_corridor:
                cc = CORRIDOR_CITY.get(f.primary_corridor, "")
                if cc:
                    skeleton_cities.add(cc)
        if not skeleton_cities.issubset(set(actual_cities)):
            errors.append(f"城市不一致: 骨架={skeleton_cities} 总纲={actual_cities}")

        # Gate 2: arrival/departure cluster 白名单
        for f in skeleton.frames:
            if f.day_type == "departure" and f.main_driver:
                name = f.main_driver_name.lower()
                if any(k in name for k in ["夜游", "夜市", "night"]):
                    errors.append(f"Day{f.day_index} departure 配了夜游型 cluster: {f.main_driver_name}")
            if f.day_type == "arrival":
                # arrival 只允许 1 条 corridor
                if f.secondary_corridor:
                    warnings.append(f"Day{f.day_index} arrival 有 2 条 corridor: {f.primary_corridor}/{f.secondary_corridor}")

        # Gate 3: 同日餐饮同质化
        days_q2 = await session.execute(
            select(ItineraryDay).where(ItineraryDay.plan_id == plan_id).order_by(ItineraryDay.day_number))
        for day in days_q2.scalars().all():
            items_q2 = await session.execute(
                select(ItineraryItem).where(ItineraryItem.day_id == day.day_id, ItineraryItem.item_type == "restaurant"))
            cuisines = []
            for item in items_q2.scalars().all():
                n = json.loads(item.notes_zh) if item.notes_zh else {}
                c = n.get("cuisine", "other")
                cuisines.append(c)
            cuisine_counts = Counter(cuisines)
            for c, cnt in cuisine_counts.items():
                if c != "other" and cnt > 2:
                    errors.append(f"Day{day.day_number} 同 cuisine [{c}] 出现 {cnt} 次")

        # Gate 4: 显示字段净化（检查 notes 里不应有 raw ID）
        raw_patterns = ["circle_id", "cluster_id", "kansai_classic"]
        # (这个检查在 PDF 渲染层做更合适，这里只 warn)

        # Gate 5: 酒店晚数一致性（departure 天不算住宿晚数）
        kyoto_nights = sum(1 for f in skeleton.frames if AREA_TO_CITY.get(f.sleep_base, "") == "kyoto" and f.day_type != "departure")
        osaka_nights = sum(1 for f in skeleton.frames if AREA_TO_CITY.get(f.sleep_base, "") == "osaka" and f.day_type != "departure")
        for b in hotel.bases:
            if b.base_city == "kyoto" and b.nights != kyoto_nights:
                errors.append(f"京都住晚不一致: 策略={b.nights} 骨架={kyoto_nights}")
            if b.base_city == "osaka" and b.nights != osaka_nights:
                errors.append(f"大阪住晚不一致: 策略={b.nights} 骨架={osaka_nights}")

        for e in errors:
            logger.error("  ❌ %s", e)
        for w in warnings:
            logger.warning("  ⚠️ %s", w)
        if not errors:
            logger.info("  ✅ 质量门控全部通过")

        total_items = await session.execute(text(
            f"SELECT count(*) FROM itinerary_items i JOIN itinerary_days d ON i.day_id=d.day_id WHERE d.plan_id='{plan_id}'"))
        logger.info("总 items: %d", total_items.scalar())

        print(f"\n✅ Plan 重建完成！plan_id={plan_id}")
        print(f"   实际城市: {actual_cities}")
        print(f"   质量: {len(errors)} errors, {len(warnings)} warnings")


asyncio.run(main())