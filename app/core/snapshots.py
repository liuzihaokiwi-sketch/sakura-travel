from __future__ import annotations

"""
source_snapshots 写入工具。
所有外部 API 调用（Google Places、Booking.com 等）都应通过此函数记录原始响应。
"""
from datetime import datetime, timedelta, timezone
from inspect import isawaitable
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.snapshots import SourceSnapshot


async def record_snapshot(
    session: AsyncSession,
    source_name: str,
    object_type: str,
    object_id: str,
    raw_payload: dict[str, Any],
    expires_in_days: Optional[int] = None,
    http_status: Optional[int] = None,
    request_url: Optional[str] = None,
) -> SourceSnapshot:
    """
    将外部 API 原始响应写入 source_snapshots 表。

    Args:
        session:         AsyncSession（调用方传入，不自行 commit）
        source_name:     数据源名称，如 "google_places" / "booking" / "tabelog"
        object_type:     对象类型，如 "hotel" / "poi" / "restaurant" / "flight"
        object_id:       外部系统 ID 或内部 entity_id（字符串化）
        raw_payload:     原始 API 响应（dict）
        expires_in_days: 过期天数，None 表示永不过期
        http_status:     HTTP 状态码（可选）
        request_url:     请求 URL（可选，用于调试）

    Returns:
        已添加到 session（未 commit）的 SourceSnapshot 实例
    """
    expires_at: Optional[datetime] = None
    if expires_in_days is not None:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=expires_in_days)

    snapshot = SourceSnapshot(
        source_name=source_name,
        object_type=object_type,
        object_id=object_id,
        raw_payload=raw_payload,
        expires_at=expires_at,
        http_status=http_status,
        request_url=request_url,
    )
    add_result = session.add(snapshot)
    if isawaitable(add_result):
        await add_result
    return snapshot
