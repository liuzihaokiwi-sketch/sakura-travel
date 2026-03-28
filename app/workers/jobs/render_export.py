from __future__ import annotations

"""arq job: render handbook export (PDF-only main chain)."""

import logging
import uuid
from pathlib import Path

from app.db.models.business import TripRequest
from app.db.models.derived import ExportAsset, ExportJob, ItineraryPlan
from app.db.session import AsyncSessionLocal as async_session_factory

logger = logging.getLogger(__name__)

EXPORTS_DIR = Path("exports")


async def render_export(
    ctx: dict,
    *,
    plan_id: str,
    run_id: str = "",
) -> dict:
    """
    Render and persist handbook PDF.

    Legacy HTML/H5 export path is retired from the main runtime chain.
    """
    del ctx
    pid = uuid.UUID(plan_id)
    logger.info("render_export start plan=%s run_id=%s", pid, run_id[:8] if run_id else "N/A")

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session_factory() as session:
        plan = await session.get(ItineraryPlan, pid)
        if plan is None:
            logger.error("plan_id=%s not found", pid)
            return {"status": "error", "reason": "plan not found"}

        trip = await session.get(TripRequest, plan.trip_request_id)

        watermark_text: str | None = None
        if trip:
            raw = trip.raw_input or {}
            wechat = str(raw.get("wechat_id") or "")
            order_tail = str(trip.trip_request_id).replace("-", "")[-4:].upper()
            nickname = wechat[:10] if wechat else f"USER{order_tail}"
            watermark_text = f"{nickname} | {order_tail} | personal itinerary copy"

        export_job = ExportJob(
            plan_id=pid,
            export_type="pdf",
            status="rendering",
        )
        session.add(export_job)
        await session.flush()

        try:
            from app.domains.rendering.magazine.pdf_renderer import render_pdf

            pdf_bytes = await render_pdf(pid, session, watermark_text=watermark_text)
            pdf_path = EXPORTS_DIR / f"{pid}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            logger.info("PDF written: %s", pdf_path)

            pdf_asset = ExportAsset(
                export_job_id=export_job.export_job_id,
                asset_type="pdf",
                storage_url=f"/exports/{pid}.pdf",
            )
            session.add(pdf_asset)

            export_job.status = "done"
            if trip:
                trip.status = "completed"
            await session.commit()

            # 通知运营：行程生成完成
            try:
                from app.core.wecom_notify import notify_trip_done
                meta = plan.plan_metadata or {}
                duration = meta.get("duration_days") or 0
                await notify_trip_done(
                    trip_request_id=str(plan.trip_request_id),
                    plan_id=str(pid),
                    duration_days=duration,
                    nickname=nickname if trip else None,
                )
            except Exception:
                pass  # 通知失败不影响主流程

        except Exception as exc:
            logger.exception("render_export failed plan=%s: %s", pid, exc)
            export_job.status = "failed"
            if trip:
                trip.status = "failed"
            await session.commit()

            # 通知运营：生成失败
            try:
                from app.core.wecom_notify import notify_trip_failed
                await notify_trip_failed(
                    trip_request_id=str(plan.trip_request_id) if plan else plan_id,
                    reason=str(exc)[:200],
                    nickname=nickname if trip else None,
                )
            except Exception:
                pass

            return {"status": "error", "reason": str(exc)}

    logger.info("render_export done plan=%s", pid)
    return {
        "status": "ok",
        "plan_id": plan_id,
        "pdf_url": f"/exports/{pid}.pdf",
    }

