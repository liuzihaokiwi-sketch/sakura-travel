from __future__ import annotations

"""
单元测试：catalog 采集层
- upsert_entity 幂等性
- seed CSV 解析
- weather fetch 结果解析
"""

import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.catalog.upsert import _filter, _BASE_FIELDS, _POI_FIELDS
from scripts.seed_catalog import load_csv, _coerce


# ─────────────────────────────────────────────────────────────────────────────
# 辅助工具
# ─────────────────────────────────────────────────────────────────────────────

def _make_mock_entity(entity_id: Optional[str] = None) -> MagicMock:
    """构造一个假的 EntityBase 对象"""
    e = MagicMock()
    e.entity_id = uuid.UUID(entity_id) if entity_id else uuid.uuid4()
    return e


# ─────────────────────────────────────────────────────────────────────────────
# _filter 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def test_filter_keeps_only_allowed_keys():
    data = {"name_zh": "浅草寺", "lat": 35.7, "unknown_key": "x", "poi_category": "temple"}
    result = _filter(data, _BASE_FIELDS)
    assert "name_zh" in result
    assert "lat" in result
    assert "unknown_key" not in result
    assert "poi_category" not in result  # poi 字段不在 base 白名单


def test_filter_poi_fields():
    data = {"poi_category": "shrine", "name_zh": "明治", "google_rating": 4.5, "junk": 99}
    result = _filter(data, _POI_FIELDS)
    assert "poi_category" in result
    assert "google_rating" in result
    assert "name_zh" not in result
    assert "junk" not in result


# ─────────────────────────────────────────────────────────────────────────────
# upsert_entity —— 新建路径
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_creates_new_entity_when_not_found():
    """当 google_place_id 不存在时，应创建新 entity_base + pois"""
    from app.domains.catalog.upsert import upsert_entity

    mock_session = AsyncMock()
    added: List[Any] = []
    mock_session.add = MagicMock(side_effect=lambda obj: added.append(obj))

    # scalar_one_or_none 返回 None（查不到）
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    # flush 后给 entity 赋一个 entity_id（模拟 DB 生成 UUID）
    new_uuid = uuid.uuid4()

    async def fake_flush():
        for obj in added:
            if hasattr(obj, "entity_id") and obj.entity_id is None:
                object.__setattr__(obj, "entity_id", new_uuid)

    mock_session.flush = AsyncMock(side_effect=fake_flush)

    data = {
        "name_zh": "浅草寺",
        "city_code": "tokyo",
        "lat": 35.7148,
        "lng": 139.7967,
        "google_rating": 4.6,
        "poi_category": "temple",
    }

    entity = await upsert_entity(
        session=mock_session,
        entity_type="poi",
        data=data,
        google_place_id="ChIJ_test",
    )

    # 应该 add 了两个对象：EntityBase + Poi
    assert len(added) == 2
    assert mock_session.flush.call_count == 2  # 一次获取 entity_id，一次 flush sub


@pytest.mark.asyncio
async def test_upsert_updates_existing_entity():
    """当 google_place_id 已存在时，应更新而不是新建"""
    from app.domains.catalog.upsert import upsert_entity
    from app.db.models.catalog import EntityBase, Poi

    mock_session = AsyncMock()
    added: List[Any] = []
    mock_session.add = MagicMock(side_effect=lambda obj: added.append(obj))

    existing_id = uuid.uuid4()
    existing_entity = MagicMock(spec=EntityBase)
    existing_entity.entity_id = existing_id

    existing_poi = MagicMock(spec=Poi)
    existing_poi.entity_id = existing_id

    call_count = 0

    async def mock_execute(stmt):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # 第一次查 entity_base → 返回已有实体
            result.scalar_one_or_none.return_value = existing_entity
        else:
            # 第二次查 Poi 子表 → 返回已有子表
            result.scalar_one_or_none.return_value = existing_poi
        call_count += 1
        return result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    mock_session.flush = AsyncMock()

    data = {
        "name_zh": "浅草寺（更新）",
        "city_code": "tokyo",
        "google_rating": 4.8,  # 更新评分
    }

    entity = await upsert_entity(
        session=mock_session,
        entity_type="poi",
        data=data,
        google_place_id="ChIJ_test",
    )

    # 不应新 add 对象（已存在）
    assert len(added) == 0
    # 应更新了 entity 的字段
    assert existing_entity.name_zh == "浅草寺（更新）"
    assert existing_poi.google_rating == 4.8


@pytest.mark.asyncio
async def test_upsert_raises_on_invalid_entity_type():
    """传入非法 entity_type 应 raise ValueError"""
    from app.domains.catalog.upsert import upsert_entity

    mock_session = AsyncMock()
    with pytest.raises(ValueError, match="Unsupported entity_type"):
        await upsert_entity(
            session=mock_session,
            entity_type="flight",  # 非法
            data={"name_zh": "测试"},
        )


# ─────────────────────────────────────────────────────────────────────────────
# CSV 解析
# ─────────────────────────────────────────────────────────────────────────────

def test_coerce_bool():
    assert _coerce("admission_free", "true") is True
    assert _coerce("admission_free", "false") is False
    assert _coerce("admission_free", "1") is True
    assert _coerce("admission_free", "") is None


def test_coerce_float():
    assert _coerce("lat", "35.7148") == pytest.approx(35.7148)
    assert _coerce("google_rating", "4.6") == pytest.approx(4.6)


def test_coerce_int():
    assert _coerce("google_review_count", "1234") == 1234
    assert _coerce("michelin_star", "2") == 2


def test_load_csv_basic(tmp_path):
    """load_csv 能正确解析标准格式"""
    csv_content = (
        "name_zh,city_code,entity_type,lat,lng,google_rating,admission_free\n"
        "浅草寺,tokyo,poi,35.7148,139.7967,4.6,true\n"
        "金阁寺,kyoto,poi,35.0394,135.7292,4.5,false\n"
    )
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    rows = load_csv(str(csv_file))

    assert len(rows) == 2
    assert rows[0]["name_zh"] == "浅草寺"
    assert rows[0]["lat"] == pytest.approx(35.7148)
    assert rows[0]["google_rating"] == pytest.approx(4.6)
    assert rows[0]["admission_free"] is True
    assert rows[1]["city_code"] == "kyoto"


# ─────────────────────────────────────────────────────────────────────────────
# 天气模块（mock HTTP）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_weather_parses_response():
    """fetch_weather 应正确解析 Open-Meteo 响应"""
    from app.domains.live_inventory.weather import fetch_weather

    fake_response = {
        "daily": {
            "time": ["2024-04-01"],
            "temperature_2m_max": [18.5],
            "temperature_2m_min": [12.1],
            "weathercode": [2],
            "precipitation_sum": [0.0],
        }
    }

    with patch("httpx.AsyncClient") as MockClient:
        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_response
        mock_resp.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_resp)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client_instance

        result = await fetch_weather("tokyo", "2024-04-01")

    assert result["city"] == "tokyo"
    assert result["date"] == "2024-04-01"
    assert result["temp_high_c"] == pytest.approx(18.5)
    assert result["temp_low_c"] == pytest.approx(12.1)
    assert result["condition"] == "partly_cloudy"
    assert result["precipitation_mm"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_fetch_weather_invalid_city():
    """不支持的城市应 raise ValueError"""
    from app.domains.live_inventory.weather import fetch_weather

    with pytest.raises(ValueError, match="Unsupported city"):
        await fetch_weather("berlin", "2024-04-01")
