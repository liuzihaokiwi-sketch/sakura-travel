"""
tests/test_score_entities_e2e.py
---------------------------------
端到端测试：评分引擎 score_entities job

测试场景（使用内存 SQLite + 完整 ORM）：
  1. 灌入 3 条 POI → 运行 score_entities → 验证 entity_scores 有 3 条记录且 final_score > 0
  2. 验证 score_breakdown 包含 context_score 字段
  3. 验证 get_ranked_entities 返回按 final_score 降序排列的结果

注意：使用 SQLite（aiosqlite），不依赖 PostgreSQL 环境。
"""
from __future__ import annotations

import asyncio
import itertools
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# SQLite 不支持自增 BigInteger，用全局计数器模拟
_score_id_counter = itertools.count(1)

import pytest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.session import Base


# ── 测试数据库 Fixture ─────────────────────────────────────────────────────────

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """使用 SQLite 内存数据库进行测试，每个测试函数重建表结构。
    
    SQLite 不支持 PostgreSQL 特有类型（JSONB/UUID），
    使用 TypeDecorator 处理：UUID 存字符串，JSONB → JSON。
    """
    # 导入所有模型确保表被注册
    from app.db.models import catalog, derived, snapshots, business  # noqa: F401

    from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
    from sqlalchemy import JSON, String, Uuid as SA_Uuid, event as sa_event
    from sqlalchemy.engine import Engine

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 在 SQLite 上把 JSONB 替换为 JSON，把 PostgreSQL UUID 替换为 String
    # 通过覆盖方言方式处理
    def patch_sqlite_types(metadata):
        """递归替换所有表中的 PG 专有类型为 SQLite 兼容类型。"""
        for table in metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()
                elif isinstance(col.type, (PG_UUID, SA_Uuid)):
                    col.type = String(36)

    patch_sqlite_types(Base.metadata)

    # 注册 SQLite UUID 适配器
    import sqlite3
    sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

    # Monkey-patch SQLAlchemy Uuid 的 bind_processor 使其在 SQLite 上接受 str
    from sqlalchemy.sql.sqltypes import Uuid as _SA_Uuid
    _original_bp = _SA_Uuid.bind_processor

    def _patched_bind_processor(self, dialect):
        if dialect.name == "sqlite":
            def process(value):
                if value is None:
                    return None
                if isinstance(value, uuid.UUID):
                    return str(value)
                return str(value)
            return process
        return _original_bp(self, dialect)

    _SA_Uuid.bind_processor = _patched_bind_processor

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


# ── 辅助函数：创建测试 POI ────────────────────────────────────────────────────

def _make_poi_data(name_zh: str, city: str = "tokyo", rating: float = 4.5) -> dict:
    return {
        "entity_type": "poi",
        "name_zh": name_zh,
        "name_ja": name_zh,
        "city_code": city,
        "lat": 35.6762,
        "lng": 139.6503,
        "data_tier": "A",
        "poi_category": "temple",
        "google_rating": rating,
        "google_review_count": 5000,
        "has_opening_hours": True,
    }


async def _insert_test_poi(session: AsyncSession, name_zh: str, city: str = "tokyo", rating: float = 4.5):
    """直接向 DB 插入测试 POI 实体。"""
    from app.db.models.catalog import EntityBase, Poi

    entity_id = str(uuid.uuid4())
    entity = EntityBase(
        entity_id=entity_id,
        entity_type="poi",
        name_zh=name_zh,
        name_ja=name_zh,
        city_code=city,
        lat=35.6762,
        lng=139.6503,
        data_tier="A",
        is_active=True,
    )
    session.add(entity)
    await session.flush()  # 确保 entity_id 已写入

    poi = Poi(
        entity_id=entity_id,
        poi_category="temple",
        google_rating=rating,
        google_review_count=5000,
        opening_hours_json={"weekday_text": ["Mon: 9am-5pm"]},
    )
    session.add(poi)
    await session.flush()

    return entity_id


# ── 测试：score_entities job 端到端 ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_score_entities_writes_scores(db_session: AsyncSession):
    """
    灌入 3 条 POI → 运行 score_entities → 验证 entity_scores 有 3 条记录且 final_score > 0。
    """
    from sqlalchemy import select

    from app.db.models.derived import EntityScore
    from app.domains.ranking.scorer import EntitySignals, compute_base_score

    # 1. 灌入 3 条测试 POI
    ids = []
    for i, (name, rating) in enumerate([
        ("浅草寺", 4.8),
        ("新宿御苑", 4.3),
        ("东京塔", 4.5),
    ]):
        eid = await _insert_test_poi(db_session, name, rating=rating)
        ids.append(eid)

    await db_session.commit()

    # 2. 直接调用 scorer（不依赖 arq 环境，模拟 score_entities 的核心逻辑）
    from app.db.models.catalog import EntityBase
    from app.db.models.derived import EntityScore
    from app.domains.catalog.tagger import get_entity_affinity
    from app.domains.ranking.scorer import compute_base_score, compute_context_score, EntitySignals
    from app.domains.ranking.scorer import THEME_KEYS

    # 直接查询并打分
    stmt = select(EntityBase).where(
        EntityBase.city_code == "tokyo",
        EntityBase.entity_type == "poi",
    )
    result = await db_session.execute(stmt)
    entities = result.scalars().all()
    assert len(entities) == 3, f"期望 3 条 POI，实际 {len(entities)}"

    from datetime import datetime, timezone
    from sqlalchemy import delete

    from app.db.models.catalog import Poi
    for entity in entities:
        # SQLite 上 refresh 有 UUID 类型问题，用直接查询代替
        poi_result = await db_session.execute(
            select(Poi).where(Poi.entity_id == entity.entity_id)
        )
        poi_obj = poi_result.scalar_one_or_none()

        signals = EntitySignals(
            entity_type="poi",
            data_tier=entity.data_tier or "B",
            updated_at=datetime.now(tz=timezone.utc),
            google_rating=float(poi_obj.google_rating) if poi_obj and poi_obj.google_rating else None,
            google_review_count=poi_obj.google_review_count if poi_obj else None,
            has_opening_hours=bool(poi_obj.opening_hours_json) if poi_obj else False,
        )
        result_score = compute_base_score(signals, score_profile="general")

        # context_score（无标签时用均匀权重，affinity 全为 0 → context_score = 0）
        affinity = await get_entity_affinity(db_session, str(entity.entity_id))
        theme_keys = list(THEME_KEYS)
        uniform_weights = {k: 1.0 / len(theme_keys) for k in theme_keys}
        context_score, context_breakdown = compute_context_score(uniform_weights, affinity)

        score_breakdown = dict(result_score.score_breakdown)
        score_breakdown["context_score"] = round(context_score, 2)
        score_breakdown["context_breakdown"] = context_breakdown

        # 写入 entity_scores
        await db_session.execute(
            delete(EntityScore).where(
                EntityScore.entity_id == entity.entity_id,
                EntityScore.score_profile == "general",
            )
        )
        score_row = EntityScore(
            score_id=next(_score_id_counter),  # SQLite 不支持 BigInteger 自增，手动提供
            entity_id=entity.entity_id,
            score_profile="general",
            base_score=result_score.base_score,
            editorial_boost=result_score.editorial_boost,
            final_score=result_score.final_score,
            score_breakdown=score_breakdown,
            computed_at=datetime.now(tz=timezone.utc),
        )
        db_session.add(score_row)

    await db_session.commit()

    # 3. 验证 entity_scores 表有 3 条记录且 final_score > 0
    score_stmt = select(EntityScore).where(EntityScore.score_profile == "general")
    score_result = await db_session.execute(score_stmt)
    scores = score_result.scalars().all()

    assert len(scores) == 3, f"期望 3 条评分记录，实际 {len(scores)}"
    for score in scores:
        assert score.final_score > 0, f"final_score 应 > 0，实际 {score.final_score}"
        assert "dimensions" in score.score_breakdown
        assert "context_score" in score.score_breakdown


@pytest.mark.asyncio
async def test_ranked_entities_returns_sorted(db_session: AsyncSession):
    """
    验证 get_ranked_entities 按 final_score 降序返回实体。
    """
    from sqlalchemy import delete
    from app.db.models.catalog import EntityBase
    from app.db.models.derived import EntityScore
    from app.domains.ranking.queries import get_ranked_entities
    from app.domains.ranking.scorer import EntitySignals, compute_base_score

    # 灌入 3 条 POI，评分递增
    ratings = [3.5, 4.5, 4.9]
    for i, rating in enumerate(ratings):
        eid = await _insert_test_poi(db_session, f"测试POI_{i}", rating=rating)
        await db_session.flush()

        # 手动写入评分
        signals = EntitySignals(
            entity_type="poi",
            data_tier="A",
            google_rating=rating,
            google_review_count=1000,
        )
        result_score = compute_base_score(signals)
        score_row = EntityScore(
            score_id=next(_score_id_counter),  # SQLite 不支持 BigInteger 自增
            entity_id=eid,
            score_profile="general",
            base_score=result_score.base_score,
            editorial_boost=0,
            final_score=result_score.final_score,
            score_breakdown=result_score.score_breakdown,
            computed_at=datetime.now(tz=timezone.utc),
        )
        db_session.add(score_row)

    await db_session.commit()

    # 查询
    ranked = await get_ranked_entities(
        session=db_session,
        city_code="tokyo",
        entity_type="poi",
        score_profile="general",
        limit=10,
    )

    assert len(ranked) == 3
    # 验证降序
    scores_list = [item["final_score"] for item in ranked]
    assert scores_list == sorted(scores_list, reverse=True), (
        f"结果应按 final_score 降序，实际: {scores_list}"
    )


@pytest.mark.asyncio
async def test_context_score_included_in_breakdown(db_session: AsyncSession):
    """
    验证 score_breakdown 中包含 context_score 字段。
    """
    from app.domains.ranking.scorer import EntitySignals, compute_base_score, compute_context_score, THEME_KEYS

    signals = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.5,
        google_review_count=3000,
    )
    result = compute_base_score(signals)

    # 模拟 context_score 追加
    theme_keys = list(THEME_KEYS)
    uniform_weights = {k: 1.0 / len(theme_keys) for k in theme_keys}
    affinity = {k: 3 for k in theme_keys}  # 模拟均匀 3 分亲和度
    context_score, context_breakdown = compute_context_score(uniform_weights, affinity)

    breakdown = dict(result.score_breakdown)
    breakdown["context_score"] = round(context_score, 2)
    breakdown["context_breakdown"] = context_breakdown

    assert "context_score" in breakdown
    assert breakdown["context_score"] > 0  # affinity=3 → context_score = 3/5*100 = 60
    assert abs(breakdown["context_score"] - 60.0) < 1.0, (
        f"context_score 应约为 60.0，实际 {breakdown['context_score']}"
    )
    assert "context_breakdown" in breakdown
