"""
image_collector.py — 小规模图片采集管线框架

当前阶段：流程验证（小规模），不做大规模爬取。
后续上云后切换为异步队列+分布式采集。

采集策略（参考 fix/图片采集与描述评价数据方案_v1.md）：
  1. Google Places Photos API（主来源，合规）
  2. 官方网页 OG 图片（辅助来源）
  3. 人工上传（高价值对象）

管线步骤：
  fetch_candidates → classify_roles → dedup_and_filter → score → persist
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── 图片角色分类规则 ──────────────────────────────────────────────────────────

ROLE_KEYWORDS = {
    "hotel": {
        "exterior": ["外観", "exterior", "building", "外观", "外立面"],
        "lobby": ["ロビー", "lobby", "大堂", "reception"],
        "room": ["客室", "room", "guest", "客房", "ルーム", "和室"],
        "bath": ["温泉", "onsen", "浴場", "bath", "大浴场", "露天風呂"],
        "breakfast": ["朝食", "breakfast", "早餐", "モーニング"],
        "interior": ["館内", "interior", "restaurant", "bar", "ラウンジ"],
    },
    "restaurant": {
        "signature_dish": ["料理", "dish", "menu", "コース", "course", "招牌", "おまかせ"],
        "interior": ["店内", "interior", "席", "カウンター", "counter", "seat"],
        "entrance": ["外観", "entrance", "入口", "门头", "暖簾"],
        "menu": ["メニュー", "menu", "菜单", "price"],
    },
    "poi": {
        "main_scene": ["景色", "view", "scene", "風景", "主场景"],
        "entrance": ["入口", "entrance", "gate", "鳥居", "torii"],
        "transit_hint": ["駅", "station", "bus", "バス", "缆车"],
        "experience": ["体験", "experience", "activity", "体验"],
    },
}


def classify_image_role(
    entity_type: str,
    caption: str = "",
    filename: str = "",
    index_in_set: int = 0,
) -> str:
    """
    根据图片 caption/filename 推断 image_role。

    如果无法推断，第一张默认 hero，其余 main_scene/room。
    """
    text = (caption + " " + filename).lower()
    type_key = entity_type if entity_type in ROLE_KEYWORDS else "poi"

    for role, keywords in ROLE_KEYWORDS.get(type_key, {}).items():
        if any(kw in text for kw in keywords):
            return role

    # 默认规则
    if index_in_set == 0:
        return "hero"
    return "main_scene" if entity_type == "poi" else "room" if entity_type == "hotel" else "signature_dish"


# ── 采集结果数据结构 ──────────────────────────────────────────────────────────

@dataclass
class ImageCandidate:
    url: str
    source_kind: str            # google_places / official_site / manual_upload
    source_page_url: str = ""
    attribution_text: str = ""
    caption: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    file_size_kb: Optional[int] = None


@dataclass
class CollectionResult:
    entity_id: uuid.UUID
    entity_type: str
    candidates_found: int = 0
    persisted: int = 0
    skipped_duplicate: int = 0
    skipped_low_quality: int = 0
    errors: list[str] = field(default_factory=list)


# ── 去重 ──────────────────────────────────────────────────────────────────────

def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


# ── 核心管线 ──────────────────────────────────────────────────────────────────

async def collect_images_for_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
    entity_type: str,
    candidates: list[ImageCandidate],
    max_persist: int = 15,
) -> CollectionResult:
    """
    将采集到的图片候选写入 entity_media。

    步骤：
    1. 分类 image_role
    2. 去重（同 entity 同 URL 不重复写入）
    3. 过滤低质量（宽高 < 200px）
    4. 写入 entity_media（needs_review=True）

    Args:
        candidates: 已从外部源获取的图片候选列表
        max_persist: 最多写入多少张
    """
    from app.db.models.catalog import EntityMedia

    result = CollectionResult(entity_id=entity_id, entity_type=entity_type)
    result.candidates_found = len(candidates)

    # 加载已有 URL 哈希（去重）
    existing_q = await session.execute(
        select(EntityMedia.url).where(EntityMedia.entity_id == entity_id)
    )
    existing_hashes = {_url_hash(row[0]) for row in existing_q.all()}

    persisted = 0
    for idx, cand in enumerate(candidates):
        if persisted >= max_persist:
            break

        # 去重
        h = _url_hash(cand.url)
        if h in existing_hashes:
            result.skipped_duplicate += 1
            continue

        # 低质量过滤
        if cand.width and cand.height and (cand.width < 200 or cand.height < 200):
            result.skipped_low_quality += 1
            continue

        # 分类
        role = classify_image_role(entity_type, cand.caption, cand.url, idx)

        # 写入
        media = EntityMedia(
            entity_id=entity_id,
            media_type="image",
            url=cand.url,
            caption_zh=cand.caption[:500] if cand.caption else None,
            sort_order=idx,
            is_cover=(idx == 0),
            source=cand.source_kind.split("_")[0],  # 向后兼容旧 source 字段
            source_kind=cand.source_kind,
            source_page_url=cand.source_page_url or None,
            attribution_text=cand.attribution_text or None,
            license_status="allowed" if cand.source_kind in ("official_site", "manual_upload") else "review_needed",
            image_role=role,
            season_tag="all_season",
            daypart_tag="all_day",
            is_selected=False,
            needs_review=True,
            width=cand.width,
            height=cand.height,
            file_size_kb=cand.file_size_kb,
        )
        session.add(media)
        existing_hashes.add(h)
        persisted += 1

    result.persisted = persisted
    await session.flush()

    logger.info(
        "collect_images: entity=%s type=%s found=%d persisted=%d dup=%d low=%d",
        entity_id, entity_type, result.candidates_found,
        result.persisted, result.skipped_duplicate, result.skipped_low_quality,
    )
    return result


async def collect_descriptions_for_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
    descriptions: list[dict],
) -> int:
    """
    写入实体描述候选。

    Args:
        descriptions: [{source_kind, description_type, content, language, confidence_score}]

    Returns:
        写入条数
    """
    from app.db.models.catalog import EntityDescription

    written = 0
    for desc in descriptions:
        if not desc.get("content"):
            continue

        # 检查重复
        existing = await session.execute(
            select(EntityDescription).where(and_(
                EntityDescription.entity_id == entity_id,
                EntityDescription.description_type == desc["description_type"],
                EntityDescription.source_kind == desc["source_kind"],
                EntityDescription.language == desc.get("language", "zh"),
            ))
        )
        if existing.scalar_one_or_none():
            continue

        ed = EntityDescription(
            entity_id=entity_id,
            source_kind=desc["source_kind"],
            description_type=desc["description_type"],
            content=desc["content"],
            language=desc.get("language", "zh"),
            confidence_score=desc.get("confidence_score"),
            needs_review=True,
        )
        session.add(ed)
        written += 1

    await session.flush()
    return written


async def collect_review_signals(
    session: AsyncSession,
    entity_id: uuid.UUID,
    signals: list[dict],
) -> int:
    """
    写入/更新实体评价信号。

    Args:
        signals: [{rating_source, aggregate_rating, review_count, positive_tags, negative_tags, ...}]

    Returns:
        写入/更新条数
    """
    from app.db.models.catalog import EntityReviewSignal

    updated = 0
    for sig in signals:
        existing_q = await session.execute(
            select(EntityReviewSignal).where(and_(
                EntityReviewSignal.entity_id == entity_id,
                EntityReviewSignal.rating_source == sig["rating_source"],
            ))
        )
        existing = existing_q.scalar_one_or_none()

        if existing:
            # 更新
            existing.aggregate_rating = sig.get("aggregate_rating", existing.aggregate_rating)
            existing.review_count = sig.get("review_count", existing.review_count)
            existing.positive_tags = sig.get("positive_tags", existing.positive_tags)
            existing.negative_tags = sig.get("negative_tags", existing.negative_tags)
            existing.summary_tags = sig.get("summary_tags", existing.summary_tags)
            existing.queue_risk_level = sig.get("queue_risk_level", existing.queue_risk_level)
            existing.last_checked_at = datetime.now(timezone.utc)
        else:
            rs = EntityReviewSignal(
                entity_id=entity_id,
                rating_source=sig["rating_source"],
                aggregate_rating=sig.get("aggregate_rating"),
                review_count=sig.get("review_count"),
                positive_tags=sig.get("positive_tags", []),
                negative_tags=sig.get("negative_tags", []),
                summary_tags=sig.get("summary_tags", []),
                queue_risk_level=sig.get("queue_risk_level"),
                last_checked_at=datetime.now(timezone.utc),
            )
            session.add(rs)

        updated += 1

    await session.flush()
    return updated
