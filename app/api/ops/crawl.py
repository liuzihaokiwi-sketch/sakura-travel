"""
Ops API – 爬虫任务触发
供管理后台"数据抓取"页面使用。
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal

router = APIRouter()

# 内存中的任务状态表（进程内，重启后清空）
_jobs: dict[str, dict] = {}


class CrawlRequest(BaseModel):
    city_code: str
    sync_pois: bool = True
    sync_restaurants: bool = True
    sync_hotels: bool = True
    force_ai: bool = False
    poi_count: int = 5
    restaurant_count: int = 5
    hotel_count: int = 4


async def _run_crawl(job_id: str, req: CrawlRequest):
    """后台异步执行爬虫"""
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
    try:
        from app.domains.catalog.pipeline import run_city_pipeline
        async with AsyncSessionLocal() as session:
            result = await run_city_pipeline(
                session,
                city_code=req.city_code,
                sync_pois=req.sync_pois,
                sync_restaurants=req.sync_restaurants,
                sync_hotels=req.sync_hotels,
                force_ai=req.force_ai,
                poi_count=req.poi_count,
                restaurant_count=req.restaurant_count,
                hotel_count=req.hotel_count,
            )
            await session.commit()
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["result"] = result
    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(e)
    finally:
        _jobs[job_id]["finished_at"] = datetime.utcnow().isoformat()


@router.post("/crawl/city")
async def trigger_crawl(
    req: CrawlRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """触发城市数据抓取任务（后台运行）"""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "job_id": job_id,
        "city_code": req.city_code,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }
    background_tasks.add_task(_run_crawl, job_id, req)
    return {"job_id": job_id, "status": "queued", "city_code": req.city_code}


@router.get("/crawl/jobs")
async def list_jobs() -> dict:
    """列出所有抓取任务状态"""
    jobs = sorted(_jobs.values(), key=lambda x: x.get("created_at", ""), reverse=True)
    return {"jobs": jobs[:50]}


@router.get("/crawl/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """查询抓取任务状态"""
    if job_id not in _jobs:
        return {"job_id": job_id, "status": "not_found"}
    return _jobs[job_id]
