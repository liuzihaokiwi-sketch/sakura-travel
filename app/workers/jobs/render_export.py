"""
arq Job: render_export
调用渲染引擎生成 PDF + H5，写入 export_jobs / export_assets，更新 trip 状态为 completed
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.models.derived import ExportAsset, ExportJob, ItineraryPlan
from app.db.session import AsyncSessionLocal as async_session_factory

logger = logging.getLogger(__name__)

EXPORTS_DIR = Path("exports")


async def render_export(
    ctx: dict,
    *,
    plan_id: str,
) -> dict:
    """
    arq Job: 渲染行程 PDF + H5，写入文件系统和数据库。
    """
    pid = uuid.UUID(plan_id)
    logger.info("render_export 开始 plan=%s", pid)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session_factory() as session:
        plan = await session.get(ItineraryPlan, pid)
        if plan is None:
            logger.error("plan_id=%s 不存在", pid)
            return {"status": "error", "reason": "plan not found"}

        trip = await session.get(TripRequest, plan.trip_request_id)

        # 创建 h5 export_job 记录
        export_job = ExportJob(
            plan_id=pid,
            export_type="h5",
            status="rendering",
        )
        session.add(export_job)
        await session.flush()  # 获取 export_job.export_job_id

        try:
            # ── HTML 渲染（独立 session 避免 greenlet 上下文冲突）────────
            from app.domains.rendering.magazine.html_renderer import render_html

            async with async_session_factory() as render_session:
                html_content = await render_html(pid, render_session)
            html_path = EXPORTS_DIR / f"{pid}.html"
            html_path.write_text(html_content, encoding="utf-8")
            logger.info("HTML 写入 %s", html_path)

            # 写入 export_assets（HTML）
            html_asset = ExportAsset(
                export_job_id=export_job.export_job_id,
                asset_type="h5",
                storage_url=f"/exports/{pid}.html",
            )
            session.add(html_asset)

            # ── PDF 渲染 ──────────────────────────────────────────────
            try:
                from app.domains.rendering.magazine.pdf_renderer import render_pdf

                pdf_bytes = await render_pdf(pid, session)
                pdf_path = EXPORTS_DIR / f"{pid}.pdf"
                pdf_path.write_bytes(pdf_bytes)
                logger.info("PDF 写入 %s", pdf_path)

                # 为 PDF 单独创建一条 export_job 记录
                pdf_job = ExportJob(
                    plan_id=pid,
                    export_type="pdf",
                    status="done",
                )
                session.add(pdf_job)
                await session.flush()

                pdf_asset = ExportAsset(
                    export_job_id=pdf_job.export_job_id,
                    asset_type="pdf",
                    storage_url=f"/exports/{pid}.pdf",
                )
                session.add(pdf_asset)

            except Exception as pdf_err:
                # PDF 失败不阻断，H5 仍可交付
                logger.warning("PDF 渲染失败（跳过）: %s", pdf_err)

            # 更新 h5 export_job 状态
            export_job.status = "done"

            # 更新 trip 状态为 completed
            if trip:
                trip.status = "completed"

            await session.commit()

        except Exception as exc:
            logger.exception("render_export 失败 plan=%s: %s", pid, exc)
            export_job.status = "failed"
            if trip:
                trip.status = "failed"
            await session.commit()
            return {"status": "error", "reason": str(exc)}

    logger.info("render_export 完成 plan=%s", pid)
    return {
        "status": "ok",
        "plan_id": plan_id,
        "html_url": f"/exports/{pid}.html",
    }
