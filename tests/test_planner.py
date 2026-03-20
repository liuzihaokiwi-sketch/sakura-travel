from __future__ import annotations

"""轨道 C 单元测试：day_builder 时间槽、距离过滤、降级处理"""

import pytest
from app.domains.trip_core.day_builder import (
    EntityCandidate, PlannedItem,
    _add_minutes, _haversine_km, _distance_km,
    build_day, estimate_day_cost_jpy,
)


def test_add_minutes_basic():
    assert _add_minutes("09:00", 90) == "10:30"
    assert _add_minutes("23:30", 60) == "00:30"
    assert _add_minutes("12:00", 0)  == "12:00"


def test_haversine_tokyo_osaka():
    dist = _haversine_km(35.6762, 139.6503, 34.6937, 135.5023)
    assert 380 < dist < 420


def test_haversine_same_point():
    assert _haversine_km(35.0, 135.0, 35.0, 135.0) == pytest.approx(0.0, abs=0.001)


def test_distance_km_no_coords():
    a = EntityCandidate(entity_id="1", entity_type="poi", name_zh="A")
    b = EntityCandidate(entity_id="2", entity_type="poi", name_zh="B")
    assert _distance_km(a, b) == 999.0


def _poi(idx, lat=35.7, lng=139.7, cat="shrine"):
    return EntityCandidate(
        entity_id=str(idx), entity_type="poi", name_zh=f"景点{idx}",
        lat=lat, lng=lng, poi_category=cat, google_rating=4.5,
        typical_duration_min=90, admission_fee_jpy=1000,
    )

def _rest(idx):
    return EntityCandidate(
        entity_id=f"r{idx}", entity_type="restaurant", name_zh=f"餐厅{idx}",
        cuisine_type="sushi", budget_lunch_jpy=2000, budget_dinner_jpy=4000,
    )

def _hotel():
    return EntityCandidate(entity_id="h1", entity_type="hotel", name_zh="测试酒店")


def test_build_day_full_has_required_types():
    items = build_day([_poi(i) for i in range(5)], [_rest(i) for i in range(4)], _hotel())
    types = [i.item_type for i in items]
    assert types.count("restaurant") == 2
    assert types.count("hotel") == 1
    assert "free_time" in types
    assert types.count("poi") >= 2


def test_build_day_sort_order_continuous():
    items = build_day([_poi(i) for i in range(4)], [_rest(i) for i in range(3)], _hotel())
    orders = [i.sort_order for i in items]
    assert orders == list(range(len(orders)))


def test_build_day_start_times_ordered():
    items = build_day([_poi(i) for i in range(4)], [_rest(i) for i in range(3)])
    times = [i.start_time for i in items]
    assert times == sorted(times), f"时间乱序：{times}"


def test_build_day_morning_poi2_distance_filter():
    """morning_poi_2 距离过远时、该槽应被跳过（afternoon_poi 仍可取到它）"""
    poi_tokyo = _poi(1, lat=35.6762, lng=139.6503)
    poi_osaka  = _poi(2, lat=34.6937, lng=135.5023)  # 远，morning_poi_2 不应取
    poi_nearby = _poi(3, lat=35.6780, lng=139.6550)  # 近

    items = build_day([poi_tokyo, poi_osaka, poi_nearby], [], max_poi_distance_km=5.0)
    poi_items = [i for i in items if i.item_type == "poi"]

    # 第一个 POI 必须是东京
    assert poi_items[0].entity_id == "1"
    # 第二个 POI（如果存在）不能是 osaka（应跳到 afternoon_poi 槽或更后面）
    if len(poi_items) >= 2:
        # morning_poi_2 被跳过，所以第二个是 afternoon_poi → 可能是 osaka 或 nearby
        # 关键断言：3 个 poi 里，osaka 不是 sort_order 最小的那个（不是 morning_poi_2）
        morning_poi_2_candidates = [i for i in poi_items if i.sort_order == 1]
        assert all(c.entity_id != "2" for c in morning_poi_2_candidates), \
            "osaka 不应出现在 morning_poi_2 槽（sort_order=1）"


def test_build_day_no_restaurants_falls_back_to_note():
    items = build_day([_poi(i) for i in range(3)], [])
    note_items = [i for i in items if i.item_type == "note"]
    assert len(note_items) == 2
    assert all("自行安排" in (i.notes_zh or "") for i in note_items)


def test_build_day_no_pois():
    items = build_day([], [_rest(i) for i in range(2)])
    assert all(i.item_type != "poi" for i in items)


def test_build_day_no_hotel():
    items = build_day([_poi(i) for i in range(3)], [_rest(i) for i in range(2)], hotel=None)
    assert all(i.item_type != "hotel" for i in items)


def test_estimate_day_cost_basic():
    items = [
        PlannedItem(0, "poi", "1", "09:00", "10:30", 90, estimated_cost_jpy=1000),
        PlannedItem(1, "restaurant", "r1", "12:00", "13:00", 60, estimated_cost_jpy=2000),
        PlannedItem(2, "free_time", None, "17:00", "18:00", 60, estimated_cost_jpy=None),
    ]
    assert estimate_day_cost_jpy(items) == 3000


def test_estimate_day_cost_all_none():
    items = [PlannedItem(0, "poi", "1", "09:00", "10:30", 90)]
    assert estimate_day_cost_jpy(items) == 0
