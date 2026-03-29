from __future__ import annotations

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.logging_config import setup_logging
from app.core.rate_limiter import RateLimitMiddleware, InMemoryBackend
from app.core.sentry import init_sentry
from app.api import trips
from app.api import trips_generate
from app.api import trips_preview
from app.api import trips_tuning
from app.api import chat
from app.api import pois
from app.api import products
from app.api import quiz
from app.api import submissions
from app.api import orders
from app.api import modifications
from app.api import review
from app.api import config as config_api
from app.api import intensity as intensity_api
from app.api import self_adjustment as self_adjustment_api
from app.api import detail_forms
from app.api import destinations
from app.api import attribution
from app.api.ops import editorial, entities, ranked, catalog as catalog_ops
from app.api import admin_review
from app.core.config import settings
from app.core.queue import close_redis_pool, init_redis_pool
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import logging
import traceback
from app.db.session import AsyncSessionLocal, engine
from app.db.models import catalog, business, derived, snapshots  # noqa: F401 触发模型注册
from app.db.models import detail_forms as _df, fragments as _frag, trace as _trace  # noqa: F401


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 生产环境凭证校验（测试/开发环境跳过）
    settings.validate_production_secrets()

    # Startup: 结构化日志初始化
    setup_logging(
        json_output=settings.is_production,
        log_level="DEBUG" if settings.app_debug else "INFO",
    )
    init_sentry()

    # Startup: 自动建表（开发模式，失败不阻断启动）
    from app.db.session import Base
    if settings.app_env == "development":
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ 数据库表已创建/已存在")
        except Exception as e:
            print(f"⚠️  数据库连接失败，跳过建表: {e}")

    # 加载区域种子数据（失败不阻断启动）
    try:
        from app.domains.geography.region_router import load_seed_data
        result = load_seed_data()
        print(f"✅ 区域种子数据加载: {result}")
    except Exception as e:
        print(f"⚠️  区域种子数据加载失败，使用内置数据: {e}")

    # 尝试连接 Redis（失败不阻断启动）
    try:
        await init_redis_pool()
    except Exception:
        pass
    yield
    # Shutdown
    try:
        await close_redis_pool()
    except Exception:
        pass


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Japan Travel AI",
    version="0.1.0",
    description="Japan Travel AI – Backend Planning & Delivery Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(RateLimitMiddleware, backend=InMemoryBackend())

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router)                              # /chat/*
app.include_router(trips.router, prefix="/trips", tags=["trips"])
app.include_router(trips_generate.router, tags=["trips-plan"])
app.include_router(trips_preview.router, tags=["trips-preview"])
app.include_router(trips_tuning.router, tags=["self-serve-tuning"])
app.include_router(products.router, tags=["products"])       # /products
app.include_router(pois.router, tags=["pois"])               # /pois/*
app.include_router(pois.cities_router, tags=["cities"])      # /cities
app.include_router(entities.router, prefix="/ops", tags=["ops"])
app.include_router(editorial.router, prefix="/ops", tags=["ops-editorial"])
app.include_router(ranked.router, prefix="/ops", tags=["ops-ranked"])
app.include_router(catalog_ops.router, prefix="/ops", tags=["ops-catalog"])
app.include_router(quiz.router, tags=["quiz"])               # /quiz
app.include_router(submissions.router)                       # /submissions
app.include_router(orders.router, tags=["orders"])           # /orders
app.include_router(modifications.router, tags=["modifications"])  # /orders/{id}/modify
app.include_router(review.router, tags=["admin-reviews"])    # /admin/reviews/*
app.include_router(config_api.router, tags=["config"])       # /config/*
app.include_router(intensity_api.router, tags=["trips-intensity"])  # /trips/{id}/intensity
app.include_router(self_adjustment_api.router, tags=["self-adjustment"])  # /trips/{id}/alternatives, /swap
app.include_router(detail_forms.router, tags=["detail-forms"])           # /detail-forms/*
app.include_router(destinations.router, tags=["destinations"])           # /destinations/*
app.include_router(attribution.router, tags=["attribution"])             # /attribution/*
app.include_router(admin_review.router, tags=["admin-review"])           # /admin/entities/*


# ── Admin 认证 ────────────────────────────────────────────────────────────────
_http_basic = HTTPBasic()


def verify_admin_token(credentials: HTTPBasicCredentials = Depends(_http_basic)) -> None:
    """验证 Admin 端点的 HTTP Basic 认证（username=admin, password=ADMIN_PASSWORD env）。"""
    correct_password = settings.admin_password.encode("utf-8")
    provided_password = credentials.password.encode("utf-8")
    password_ok = secrets.compare_digest(provided_password, correct_password)
    username_ok = secrets.compare_digest(credentials.username.encode("utf-8"), b"admin")
    if not (password_ok and username_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


# ── 数据采集管理接口 ──────────────────────────────────────────────────────────
@app.post("/admin/sync/{city_code}", tags=["admin"])
async def admin_sync_city(
    city_code: str,
    sync_pois: bool = True,
    sync_restaurants: bool = True,
    sync_hotels: bool = True,
    force_ai: bool = True,
    poi_count: int = 5,
    restaurant_count: int = 5,
    hotel_count: int = 4,
    _: None = Depends(verify_admin_token),
):
    """
    管理接口：一键采集指定城市的景点/餐厅/酒店数据。

    - force_ai=true (默认)：使用 Claude AI 生成，无需外部网络
    - force_ai=false：优先使用 OSM+Tabelog 真实爬虫，网络不通时自动降级到 AI

    示例:
      POST /admin/sync/tokyo
      POST /admin/sync/kyoto?sync_hotels=false&poi_count=8
      POST /admin/sync/osaka?force_ai=false
    """
    from app.domains.catalog.pipeline import run_city_pipeline
    async with AsyncSessionLocal() as session:
        try:
            result = await run_city_pipeline(
                session,
                city_code=city_code,
                sync_pois=sync_pois,
                sync_restaurants=sync_restaurants,
                sync_hotels=sync_hotels,
                force_ai=force_ai,
                poi_count=poi_count,
                restaurant_count=restaurant_count,
                hotel_count=hotel_count,
            )
            await session.commit()
            return {"status": "ok", **result}
        except Exception as e:
            await session.rollback()
            return {"status": "error", "city": city_code, "message": str(e)}


@app.post("/admin/sync-all", tags=["admin"])
async def admin_sync_all_cities(
    force_ai: bool = True,
    poi_count: int = 5,
    restaurant_count: int = 5,
    hotel_count: int = 4,
    _: None = Depends(verify_admin_token),
):
    """
    管理接口：批量采集所有城市数据（东京、大阪、京都等12个城市）。
    ⚠️ 耗时较长（约15-30分钟），建议在后台运行。
    """
    from app.domains.catalog.pipeline import run_all_cities
    async with AsyncSessionLocal() as session:
        try:
            results = await run_all_cities(
                session,
                force_ai=force_ai,
                poi_count=poi_count,
                restaurant_count=restaurant_count,
                hotel_count=hotel_count,
            )
            await session.commit()
            total_pois = sum(r.get("pois", 0) for r in results)
            total_rests = sum(r.get("restaurants", 0) for r in results)
            total_hotels = sum(r.get("hotels", 0) for r in results)
            return {
                "status": "ok",
                "cities_processed": len(results),
                "total_pois": total_pois,
                "total_restaurants": total_rests,
                "total_hotels": total_hotels,
                "details": results,
            }
        except Exception as e:
            await session.rollback()
            return {"status": "error", "message": str(e)}


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    """Check DB and Redis connectivity."""
    result: dict = {"status": "ok", "db": "ok", "redis": "ok"}

    # DB check
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        result["db"] = f"error: {e}"
        result["status"] = "degraded"

    # Redis check
    try:
        from app.core.queue import get_redis_pool
        pool = get_redis_pool()
        if pool:
            await pool.ping()
        else:
            result["redis"] = "not initialized"
            result["status"] = "degraded"
    except Exception as e:
        result["redis"] = f"error: {e}"
        result["status"] = "degraded"

    return result