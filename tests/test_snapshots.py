"""
单元测试：record_snapshot 工具函数
（使用 SQLite in-memory 模拟，不需要 Docker）
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.core.snapshots import record_snapshot
from app.db.models.snapshots import SourceSnapshot


@pytest.mark.asyncio
async def test_record_snapshot_basic():
    """record_snapshot 应将 SourceSnapshot 添加到 session"""
    mock_session = AsyncMock()
    added_objects = []
    mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

    snap = await record_snapshot(
        session=mock_session,
        source_name="google_places",
        object_type="poi",
        object_id="ChIJ_test_id",
        raw_payload={"name": "浅草寺", "rating": 4.7},
        expires_in_days=7,
        http_status=200,
        request_url="https://maps.googleapis.com/...",
    )

    assert isinstance(snap, SourceSnapshot)
    assert snap.source_name == "google_places"
    assert snap.object_type == "poi"
    assert snap.object_id == "ChIJ_test_id"
    assert snap.raw_payload == {"name": "浅草寺", "rating": 4.7}
    assert snap.http_status == 200
    assert len(added_objects) == 1
    mock_session.add.assert_called_once_with(snap)


@pytest.mark.asyncio
async def test_record_snapshot_expires_at_calculation():
    """expires_at 应精确为 now + expires_in_days"""
    mock_session = AsyncMock()

    before = datetime.now(tz=timezone.utc)
    snap = await record_snapshot(
        session=mock_session,
        source_name="booking",
        object_type="hotel",
        object_id="hotel_12345",
        raw_payload={"price": 15000},
        expires_in_days=1,
    )
    after = datetime.now(tz=timezone.utc)

    assert snap.expires_at is not None
    expected_min = before + timedelta(days=1)
    expected_max = after + timedelta(days=1)
    assert expected_min <= snap.expires_at <= expected_max


@pytest.mark.asyncio
async def test_record_snapshot_no_expiry():
    """expires_in_days=None 时 expires_at 应为 None"""
    mock_session = AsyncMock()

    snap = await record_snapshot(
        session=mock_session,
        source_name="tabelog",
        object_type="restaurant",
        object_id="r_abc123",
        raw_payload={"score": 3.85},
        expires_in_days=None,
    )

    assert snap.expires_at is None
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
https://docker.mirrors.ustc.edu.cn
https://hub-mirror.c.163.com