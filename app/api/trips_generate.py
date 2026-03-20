from __future__ import annotations

"""
行程规划 & 导出 API
  POST /trips/{id}/generate           → 触发规划 job → 202
        ?template_code=tokyo_classic_5d&scene=couple  (Phase 1 模板引擎)
  GET  /trips/{id}/plan               → 返回行程 JSON
  GET  /trips/{id}/preview            → 返回 H5 预览 URL（从 export_assets 查询）
  GET  /trips/{id}/exports            → 返回 PDF 下载链接列表
  GET  /trips/{id}/export             → 直接渲染 HTML/PDF（旧接口保留）
"""

import uuid
from typing import Any, Dict, List, Optional

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.models.derived import ExportAsset, ExportJob, ItineraryDay, ItineraryItem, ItineraryPlan
from app.db.session import get_db

router = APIRouter(prefix="/trips", tags=["trips-plan"])


# ── 响应模型 ──────────────────────────────────────────────────────────────────

class ItemOut(BaseModel):
    item_type: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_min: Optional[int]
    notes_zh: Optional[str]
    estimated_cost_jpy: Optional[int]
    is_optional: bool
    class Config:
        from_attributes = True


class DayOut(BaseModel):
    day_number: int
    date: Optional[str]
    city_code: str
    day_theme: Optional[str]
    estimated_cost_jpy: Optional[int]
    items: List[ItemOut]


class PlanOut(BaseModel):
    plan_id: str
    trip_request_id: str
    status: str
    plan_metadata: Optional[Dict[str, Any]]
    days: List[DayOut]


class GenerateResponse(BaseModel):
    message: str
    trip_request_id: str
    job_queued: bool
    template_code: Optional[str] = None
    scene: Optional[str] = None


class PreviewResponse(BaseModel):
    trip_request_id: str
    plan_id: Optional[str]
    preview_url: Optional[str]
    status: str
    message: str


class ExportAssetOut(BaseModel):
    asset_id: int
    asset_type: str          # pdf / h5 / cover_image
    storage_url: str
    file_size_bytes: Optional[int]
    created_at: str


class ExportsResponse(BaseModel):
    trip_request_id: str
    plan_id: Optional[str]
    exports: List[ExportAssetOut]
    total: int


# ── POST /trips/{id}/generate ─────────────────────────────────────────────────

@router.post("/{trip_request_id}/generate", response_model=GenerateResponse, status_code=202)
async def generate_trip(
    trip_request_id: str,
    template_code: Optional[str] = Query(
        None,
        description="路线模板代码，如 tokyo_classic_5d（使用模板引擎时必填）",
        examples=["tokyo_classic_5d"],
    ),
    scene: Optional[str] = Query(
        None,
        description="出行场景：couple / family / solo / senior",
        examples=["couple"],
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    触发行程规划 arq job。

    **两种调用模式：**
    1. **模板模式（Phase 1 推荐）**：传入 `template_code` + `scene`，
       使用 `generate_trip` job（模板引擎）生成高质量攻略
    2. **传统模式**：不传参数，使用 `generate_itinerary_plan` job（要求状态为 profiled）

    返回 202 后，通过 `GET /trips/{id}/status` 轮询状态，
    完成后用 `GET /trips/{id}/preview` 获取预览链接。
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    result = await db.execute(select(TripRequest).where(TripRequest.trip_request_id == req_uuid))
    trip_req = result.scalar_one_or_none()
    if trip_req is None:
        raise HTTPException(status_code=404, detail="TripRequest not found")

    if template_code:
        # ── Phase 1 模板引擎模式 ────────────────────────────────────────────
        _valid_scenes = {"couple", "family", "solo", "senior"}
        _scene = scene or "couple"
        if _scene not in _valid_scenes:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid scene '{_scene}', must be one of {sorted(_valid_scenes)}",
            )

        # 允许 pending/profiled/failed 状态触发（模板模式不依赖 profiling 流程）
        if trip_req.status in ("assembling", "reviewing"):
            raise HTTPException(
                status_code=409,
                detail=f"Trip is already being processed (status={trip_req.status})",
            )

        trip_req.status = "assembling"
        await db.commit()

        queued = None
        try:
            queued = await enqueue_job(
                "generate_trip",
                trip_request_id=trip_request_id,
                template_code=template_code,
                scene=_scene,
            )
        except Exception:
            queued = None

        if not queued:
            # Redis 不可用 → 直接在当前进程异步执行装配（开发 / 单机模式）
            from app.db.session import AsyncSessionLocal as _SessionFactory
            from app.domains.planning.assembler import assemble_trip, enrich_itinerary_with_copy

            async def _run_inline() -> None:
                async with _SessionFactory() as _sess:
                    try:
                        plan_id = await assemble_trip(
                            session=_sess,
                            trip_request_id=req_uuid,
                            template_code=template_code,
                            scene=_scene,
                        )
                        await enrich_itinerary_with_copy(
                            session=_sess, plan_id=plan_id, scene=_scene
                        )
                        # 更新 trip_request 状态为 reviewing
                        async with _SessionFactory() as _s2:
                            _tr = await _s2.get(TripRequest, req_uuid)
                            if _tr:
                                _tr.status = "reviewing"
                                await _s2.commit()
                    except Exception as _exc:
                        import logging as _log
                        _log.getLogger(__name__).exception("inline assemble_trip 失败: %s", _exc)
                        async with _SessionFactory() as _s3:
                            _tr = await _s3.get(TripRequest, req_uuid)
                            if _tr:
                                _tr.status = "failed"
                                await _s3.commit()

            asyncio.ensure_future(_run_inline())

        return GenerateResponse(
            message=f"模板行程生成{'已加入队列' if queued else '正在生成'}（{template_code}/{_scene}），请稍候",
            trip_request_id=trip_request_id,
            job_queued=bool(queued),
            template_code=template_code,
            scene=_scene,
        )

    else:
        # ── 传统 profiling 模式 ─────────────────────────────────────────────
        if trip_req.status not in ("profiled", "failed"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot generate: status is '{trip_req.status}', expected 'profiled'",
            )

        trip_req.status = "planning"
        await db.commit()

        queued = await enqueue_job("generate_itinerary_plan", trip_request_id)
        return GenerateResponse(
            message="行程规划已加入队列，请稍候",
            trip_request_id=trip_request_id,
            job_queued=queued,
        )


# ── GET /trips/{id}/plan ──────────────────────────────────────────────────────

@router.get("/{trip_request_id}/plan", response_model=PlanOut)
async def get_plan(trip_request_id: str, db: AsyncSession = Depends(get_db)):
    """获取已生成的行程方案"""
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    days_result = await db.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan.plan_id).order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    days_out = []
    for day in days:
        items_result = await db.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id).order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()
        days_out.append(DayOut(
            day_number=day.day_number, date=day.date, city_code=day.city_code,
            day_theme=day.day_theme, estimated_cost_jpy=day.estimated_cost_jpy,
            items=[ItemOut.model_validate(i) for i in items],
        ))

    return PlanOut(
        plan_id=str(plan.plan_id), trip_request_id=str(plan.trip_request_id),
        status=plan.status, plan_metadata=plan.plan_metadata, days=days_out,
    )


# ── GET /trips/{id}/export ────────────────────────────────────────────────────

@router.get("/{trip_request_id}/export")
async def export_plan(trip_request_id: str, fmt: str = "html", db: AsyncSession = Depends(get_db)):
    """导出行程 HTML 或 PDF（?fmt=pdf）"""
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan_result = await db.execute(
        select(ItineraryPlan).where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    from app.domains.rendering.renderer import render_html, render_pdf
    html_content = await render_html(db, str(plan.plan_id))

    if fmt == "pdf":
        try:
            pdf_bytes = await render_pdf(html_content)
        except ImportError as e:
            raise HTTPException(status_code=501, detail=str(e))
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=itinerary_{trip_request_id[:8]}.pdf"},
        )

    return Response(content=html_content, media_type="text/html; charset=utf-8")


# ── GET /trips/{id}/preview ───────────────────────────────────────────────────

@router.get("/{trip_request_id}/preview", response_model=PreviewResponse)
async def get_preview(
    trip_request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取行程 H5 预览 URL。

    从 `export_assets` 表查询最新的 `h5` 类型产物，返回访问链接。
    若渲染尚未完成，返回当前状态供前端轮询。
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    # 找到最新 plan
    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    if plan is None:
        # 检查 trip 状态
        trip = await db.get(TripRequest, req_uuid)
        if trip is None:
            raise HTTPException(status_code=404, detail="TripRequest not found")
        return PreviewResponse(
            trip_request_id=trip_request_id,
            plan_id=None,
            preview_url=None,
            status=trip.status,
            message=f"行程尚未生成完成，当前状态：{trip.status}",
        )

    plan_id_str = str(plan.plan_id)

    # 查询最新的完成的 export_job（h5 类型）
    job_result = await db.execute(
        select(ExportJob)
        .where(
            ExportJob.plan_id == plan.plan_id,
            ExportJob.export_type == "h5",
            ExportJob.status == "done",
        )
        .order_by(ExportJob.completed_at.desc())
        .limit(1)
    )
    job = job_result.scalar_one_or_none()

    if job is None:
        # 检查是否有进行中的 job
        pending_result = await db.execute(
            select(ExportJob)
            .where(
                ExportJob.plan_id == plan.plan_id,
                ExportJob.export_type == "h5",
            )
            .order_by(ExportJob.created_at.desc())
            .limit(1)
        )
        pending_job = pending_result.scalar_one_or_none()
        job_status = pending_job.status if pending_job else "not_started"

        return PreviewResponse(
            trip_request_id=trip_request_id,
            plan_id=plan_id_str,
            preview_url=None,
            status=job_status,
            message=f"H5 预览渲染中（状态：{job_status}），请稍后重试",
        )

    # 取 h5 asset URL
    asset_result = await db.execute(
        select(ExportAsset)
        .where(
            ExportAsset.export_job_id == job.export_job_id,
            ExportAsset.asset_type == "h5",
        )
        .limit(1)
    )
    asset = asset_result.scalar_one_or_none()

    preview_url = asset.storage_url if asset else None

    return PreviewResponse(
        trip_request_id=trip_request_id,
        plan_id=plan_id_str,
        preview_url=preview_url,
        status="completed",
        message="H5 预览已就绪" if preview_url else "H5 Asset 记录异常，请联系管理员",
    )


# ── GET /trips/{id}/exports ───────────────────────────────────────────────────

@router.get("/{trip_request_id}/exports", response_model=ExportsResponse)
async def get_exports(
    trip_request_id: str,
    asset_type: Optional[str] = Query(
        None,
        description="筛选资产类型：pdf / h5 / cover_image，不传则返回全部",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    获取行程导出资产列表（PDF 下载链接、H5 预览链接等）。

    返回最新 plan 对应的所有已完成的 export_assets，
    按 `asset_type` 过滤（可选）。
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    # 找到最新 plan
    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found for this trip")

    plan_id_str = str(plan.plan_id)

    # 查询所有完成的 export_jobs
    jobs_result = await db.execute(
        select(ExportJob)
        .where(
            ExportJob.plan_id == plan.plan_id,
            ExportJob.status == "done",
        )
        .order_by(ExportJob.completed_at.desc())
    )
    jobs = jobs_result.scalars().all()

    if not jobs:
        return ExportsResponse(
            trip_request_id=trip_request_id,
            plan_id=plan_id_str,
            exports=[],
            total=0,
        )

    job_ids = [j.export_job_id for j in jobs]

    # 查询 assets
    assets_query = select(ExportAsset).where(ExportAsset.export_job_id.in_(job_ids))
    if asset_type:
        assets_query = assets_query.where(ExportAsset.asset_type == asset_type)
    assets_query = assets_query.order_by(ExportAsset.created_at.desc())

    assets_result = await db.execute(assets_query)
    assets = assets_result.scalars().all()

    exports_out = [
        ExportAssetOut(
            asset_id=a.asset_id,
            asset_type=a.asset_type,
            storage_url=a.storage_url,
            file_size_bytes=a.file_size_bytes,
            created_at=a.created_at.isoformat(),
        )
        for a in assets
    ]

    return ExportsResponse(
        trip_request_id=trip_request_id,
        plan_id=plan_id_str,
        exports=exports_out,
        total=len(exports_out),
    )
