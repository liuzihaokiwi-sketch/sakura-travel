#!/usr/bin/env python
"""
scripts/batch_translate.py
--------------------------
批量翻译实体名称（日文 → 中文），使用 DeepL Free API + Redis 缓存。

用法示例：
  python scripts/batch_translate.py --city tokyo
  python scripts/batch_translate.py --city osaka --dry-run
  python scripts/batch_translate.py
  python scripts/batch_translate.py --city kyoto --force
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import httpx
import redis.asyncio as aioredis

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("batch_translate")

SUPPORTED_CITIES = ["tokyo", "osaka", "kyoto", "hakone", "nikko", "kamakura",
                     "nara", "hiroshima", "fukuoka", "sapporo", "okinawa", "kobe"]

DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"
REDIS_CACHE_PREFIX = "translate:ja:zh"
BATCH_SIZE = 50


async def translate_texts_deepl(
    texts: list[str], api_key: str, use_pro: bool = False,
) -> list[str]:
    url = DEEPL_PRO_URL if use_pro else DEEPL_FREE_URL
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, data={
            "auth_key": api_key, "text": texts,
            "source_lang": "JA", "target_lang": "ZH",
        })
        resp.raise_for_status()
    return [t.get("text", "") for t in resp.json().get("translations", [])]


async def batch_translate_with_cache(
    texts: list[str], api_key: str,
    redis_client: aioredis.Redis | None = None, use_pro: bool = False,
) -> dict[str, str]:
    result_map: dict[str, str] = {}
    need_translate: list[str] = []

    for text in texts:
        if not text or not text.strip():
            result_map[text] = text
            continue
        cached = None
        if redis_client:
            try:
                cached = await redis_client.get(f"{REDIS_CACHE_PREFIX}:{text}")
            except Exception:
                pass
        if cached:
            result_map[text] = cached.decode("utf-8") if isinstance(cached, bytes) else cached
        else:
            need_translate.append(text)

    logger.info(f"缓存命中: {len(texts) - len(need_translate)}, 需翻译: {len(need_translate)}")

    for i in range(0, len(need_translate), BATCH_SIZE):
        batch = need_translate[i: i + BATCH_SIZE]
        try:
            translated = await translate_texts_deepl(batch, api_key, use_pro)
            for orig, trans in zip(batch, translated):
                result_map[orig] = trans
                if redis_client and trans:
                    try:
                        await redis_client.set(f"{REDIS_CACHE_PREFIX}:{orig}", trans)
                    except Exception:
                        pass
            logger.info(f"批次 {i // BATCH_SIZE + 1} 翻译完成: {len(batch)} 条")
        except Exception as e:
            logger.error(f"DeepL 翻译失败（批次 {i // BATCH_SIZE + 1}）: {e}")
            for orig in batch:
                result_map[orig] = orig

    return result_map


async def run(args: argparse.Namespace) -> None:
    from app.core.config import settings
    from app.db.session import AsyncSessionLocal
    from app.db.models.catalog import EntityBase
    from sqlalchemy import select

    api_key = settings.deepl_api_key
    if not api_key or api_key.startswith("your_"):
        logger.error("❌ 请在 .env 中设置 DEEPL_API_KEY")
        sys.exit(1)

    redis_client = None
    try:
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
        await redis_client.ping()
        logger.info("✅ Redis 已连接（缓存可用）")
    except Exception:
        logger.warning("⚠️ Redis 不可用，本次不使用缓存")
        redis_client = None

    async with AsyncSessionLocal() as session:
        stmt = select(EntityBase).where(EntityBase.is_active == True)  # noqa: E712
        if args.city:
            stmt = stmt.where(EntityBase.city_code.in_(args.city))
        if not args.force:
            stmt = stmt.where(
                (EntityBase.name_zh == None) | (EntityBase.name_zh == "")  # noqa: E711
            )

        entities = (await session.execute(stmt)).scalars().all()

        if not entities:
            logger.info("✅ 没有需要翻译的实体")
            return

        logger.info(f"待翻译实体: {len(entities)} 条")

        if args.dry_run:
            for e in entities[:20]:
                logger.info(f"  [预览] {e.city_code} / {e.entity_type} / {e.name_ja or e.name_local or '?'}")
            if len(entities) > 20:
                logger.info(f"  ... 还有 {len(entities) - 20} 条")
            return

        entity_map: dict[str, list] = {}
        for e in entities:
            name = e.name_ja or e.name_local or ""
            if name:
                entity_map.setdefault(name, []).append(e)

        unique_texts = list(entity_map.keys())
        logger.info(f"去重后待翻译: {len(unique_texts)} 条")

        translation_map = await batch_translate_with_cache(
            unique_texts, api_key, redis_client, use_pro=args.pro
        )

        updated = 0
        for ja_name, zh_name in translation_map.items():
            if ja_name == zh_name:
                continue
            for entity in entity_map.get(ja_name, []):
                entity.name_zh = zh_name
                updated += 1

        await session.commit()
        logger.info(f"✅ 翻译完成 — 更新: {updated} 条实体")

    if redis_client:
        await redis_client.aclose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量翻译实体名称（日文→中文）")
    parser.add_argument("--city", nargs="+", choices=SUPPORTED_CITIES, metavar="CITY")
    parser.add_argument("--force", action="store_true", help="覆盖已有中文名")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--pro", action="store_true", help="使用 DeepL Pro API")
    return parser


if __name__ == "__main__":
    asyncio.run(run(build_parser().parse_args()))