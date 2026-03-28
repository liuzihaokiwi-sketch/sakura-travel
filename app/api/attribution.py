"""
attribution.py — 营销归因 API

用于记录用户的流量来源（UTM参数/工具页/推荐码）。
前端在用户提交表单时，把从 URL 读取的参数一并发送。

POST /attribution/{trip_request_id}  — 写入/更新归因数据（幂等）
GET  /attribution/{trip_request_id}  — 读取归因数据（管理后台用）
GET  /attribution/stats              — 汇总统计（管理后台用）
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attribution", tags=["attribution"])


# ── Schema ────────────────────────────────────────────────────────────────────

class AttributionIn(BaseModel):
    """前端提交的归因数据，来自 URL 参数"""
    utm_source: Optional[str] = Field(None, max_length=100, description="如 xhs / douyin / google")
    utm_medium: Optional[str] = Field(None, max_length=100, description="如 social / organic / cpc")
    utm_campaign: Optional[str] = Field(None, max_length=200, description="如 sakura_2026")
    utm_content: Optional[str] = Field(None, max_length=200, description="帖子ID等")
    from_tool: Optional[str] = Field(None, max_length=100, description="如 sakura_tool / budget_tool")
    referral_code: Optional[str] = Field(None, max_length=100, description="老用户推荐码")
    landing_page: Optional[str] = Field(None, max_length=500, description="落地页 URL")
    referrer: Optional[str] = Field(None, max_length=500, description="HTTP Referer")


# ── POST /attribution/{trip_request_id} ──────────────────────────────────────

@router.post("/{trip_request_id}", status_code=200)
async def upsert_attribution(
    trip_request_id: UUID,
    body: AttributionIn,
    db: AsyncSession = Depends(get_db),
):
    """
    写入或更新归因数据（幂等 upsert）。
    同一 trip_request_id 只保留一条记录，重复调用覆盖更新。
    """
    # 验证 trip_request 存在
    check = await db.execute(
        text("SELECT 1 FROM trip_requests WHERE trip_request_id = :id"),
        {"id": str(trip_request_id)},
    )
    if not check.fetchone():
        raise HTTPException(status_code=404, detail="trip_request not found")

    # 如果 body 全空则不写入（节省写操作）
    payload = body.model_dump(exclude_none=True)
    if not payload:
        return {"ok": True, "skipped": True}

    await db.execute(
        text("""
            INSERT INTO marketing_attribution
                (trip_request_id, utm_source, utm_medium, utm_campaign, utm_content,
                 from_tool, referral_code, landing_page, referrer)
            VALUES
                (:trip_request_id, :utm_source, :utm_medium, :utm_campaign, :utm_content,
                 :from_tool, :referral_code, :landing_page, :referrer)
            ON CONFLICT (trip_request_id) DO UPDATE SET
                utm_source    = COALESCE(EXCLUDED.utm_source,    marketing_attribution.utm_source),
                utm_medium    = COALESCE(EXCLUDED.utm_medium,    marketing_attribution.utm_medium),
                utm_campaign  = COALESCE(EXCLUDED.utm_campaign,  marketing_attribution.utm_campaign),
                utm_content   = COALESCE(EXCLUDED.utm_content,   marketing_attribution.utm_content),
                from_tool     = COALESCE(EXCLUDED.from_tool,     marketing_attribution.from_tool),
                referral_code = COALESCE(EXCLUDED.referral_code, marketing_attribution.referral_code),
                landing_page  = COALESCE(EXCLUDED.landing_page,  marketing_attribution.landing_page),
                referrer      = COALESCE(EXCLUDED.referrer,      marketing_attribution.referrer)
        """),
        {
            "trip_request_id": str(trip_request_id),
            "utm_source": body.utm_source,
            "utm_medium": body.utm_medium,
            "utm_campaign": body.utm_campaign,
            "utm_content": body.utm_content,
            "from_tool": body.from_tool,
            "referral_code": body.referral_code,
            "landing_page": body.landing_page,
            "referrer": body.referrer,
        },
    )
    await db.commit()
    logger.info("attribution upserted: trip=%s source=%s tool=%s", trip_request_id, body.utm_source, body.from_tool)
    return {"ok": True}


# ── GET /attribution/{trip_request_id} ───────────────────────────────────────

@router.get("/{trip_request_id}")
async def get_attribution(
    trip_request_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """读取单个 trip_request 的归因数据（管理后台用）"""
    result = await db.execute(
        text("SELECT * FROM marketing_attribution WHERE trip_request_id = :id"),
        {"id": str(trip_request_id)},
    )
    row = result.mappings().first()
    if not row:
        return None
    return dict(row)


# ── GET /attribution/stats ────────────────────────────────────────────────────

@router.get("/stats/summary")
async def attribution_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """
    汇总归因统计（最近N天）。
    返回：按 utm_source / from_tool 分组的下单量。
    """
    result = await db.execute(
        text("""
            SELECT
                COALESCE(a.utm_source, '(direct)') AS source,
                COALESCE(a.from_tool, '(none)')    AS tool,
                COUNT(*)                            AS count
            FROM marketing_attribution a
            WHERE a.created_at >= NOW() - INTERVAL ':days days'
            GROUP BY source, tool
            ORDER BY count DESC
            LIMIT 50
        """),
        {"days": days},
    )
    rows = result.mappings().all()
    return {"days": days, "rows": [dict(r) for r in rows]}
