#!/usr/bin/env python
"""
scripts/batch_translate.py
--------------------------
批量翻译脚本：将数据库中 entity_base 的日文名称翻译为中文。

使用 DeepL 免费 API，翻译结果缓存至 Redis（永不过期）。

用法示例：
  # 翻译全部城市
  python scripts/batch_translate.py

  # 仅翻译东京
  python scripts/batch_translate.py --city tokyo

  # 预览模式（不写入数据库）
  python scripts/batch_translate.py --city osaka --dry-run

  # 强制重新翻译（覆盖已有中文名）
  python scripts/batch_translate.py --city kyoto --force
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("batch_translate")

SUPPORTED_CITIES = ["tokyo", "osaka", "kyoto"]
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
REDIS_CACHE_PREFIX = "translate:ja:zh"
BATCH_SIZE = 50  # DeepL 单次请求最大文本数


async def translate_texts_deepl(
    texts: list[str],
    api_key: str,
) -> list[str]:
    """
    调用 DeepL 免费 API 批量翻译日文→中文。

    Args:
        texts:    待翻译文本列表
        api_key:  DeepL API Key

    Returns:
        翻译后文本列表（与输入等长）
    """
    import httpx

    if not texts:
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            DEEPL_API_URL,
            data={
                "auth_key": api_key,
                "text": texts,
                "source_lang": "JA",
                "target_lang": "ZH",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        translations = data.get("translations", [])
        return [t.get("text", "") for t in translations]


async def translate_with_cache(
    text: str,
    api_key: str,
    redis_client=None,
) -> str:
    """
    带 Redis 缓存的单条翻译。
    缓存 key: translate:ja:zh:{text}，永不过期。
    """
    if not text or not text.strip():
        return ""

    cache_key = f"{REDIS_CACHE_PREFIX}:{text}"

    # 尝试读缓存
    if redis_client is not None:
        try:
            cached = await redis_client.get(cache_key)
            if cached is not None:
                return cached.decode("utf-8") if isinstance(cached, bytes) else cached
        except Exception as e:
            logger.warning("Redis cache read failed: %s", e)

    # 调用 DeepL
    results = await translate_texts_deepl([text], api_key)
    translated = results[0] if results else ""

    # 写入缓存（永不过期）
    if redis_client is not None and translated:
        try:
            await redis_client.set(cache_key, translated)
        except Exception as e:
            logger.warning("Redis cache write failed: %s", e)

    return translated


async def batch_translate_with_cache(
    texts: list[str],
    api_key: str,
    redis_client=None,
) -> list[str]:
    """
    批量翻译，优先从 Redis 缓存读取，未命中的统一调用 DeepL。
    """
    results = [""] * len(texts)
    uncached_indices: list[int] = []
    uncached_texts: list[str] = []

    # 1. 先从缓存批量查
    for i, text in enumerate(texts):
        if not text or not text.strip():
            results[i] = ""
            continue

        cache_key = f"{REDIS_CACHE_PREFIX}:{text}"
        if redis_client is not None:
            try:
                cached = await redis_client.get(cache_key)
                if cached is not None:
                    results[i] = cached.decode("utf-8") if isinstance(cached, bytes) else cached
                    continue
            except Exception:
                pass

        uncached_indices.append(i)
        uncached_texts.append(text)

    if not uncached_texts:
        return results

    logger.info(f"  缓存命中 {len(texts) - len(uncached_texts)}/{len(texts)}，需翻译 {len(uncached_texts)} 条")

    # 2. 分批调用 DeepL
    for batch_start in range(0, len(uncached_texts), BATCH_SIZE):
        batch = uncached_texts[batch_start:batch_start + BATCH_SIZE]
        batch_indices = uncached_indices[batch_start:batch_start + BATCH_SIZE]

        try:
            translated = await translate_texts_deepl(batch, api_key)
            for j, (idx, text, trans) in enumerate(zip(batch_indices, batch, translated)):
                results[idx] = trans
                # 写入缓存（永不过期）
                if redis_client is not None and trans:
                    try:
                        cache_key = f"{REDIS_CACHE_PREFIX}:{text}"
                        await redis_client.set(cache_key, trans)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"  DeepL 翻译批次失败: {e}")

    return results


async def run(args: argparse.Namespace) -> None:
    from app.core.config import settings
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select, func

    # 检查 DeepL API Key
    deepl_key = settings.deepl_api_key
    if not deepl_key:
        logger.error("未配置 DEEPL_API_KEY，请在 .env 中设置")
        sys.exit(1)

    # 尝试连接 Redis（可选）
    redis_client = None
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        await redis_client.ping()
        logger.info("Redis 连接成功，启用翻译缓存")
    except Exception as e:
        logger.warning(f"Redis 连接失败，不使用缓存: {e}")
        redis_client = None

    async with AsyncSessionLocal() as session:
        from app.db.models.catalog import EntityBase

        # 构建查询
        stmt = select(EntityBase).where(EntityBase.is_active == True)  # noqa: E712

        if args.city:
            stmt = stmt.where(EntityBase.city_code.in_(args.city))

        if not args.force:
            # 仅翻译 name_zh 为空但 name_ja 有值的实体
            stmt = stmt.where(
                EntityBase.name_ja.isnot(None),
                EntityBase.name_ja != "",
                (EntityBase.name_zh.is_(None)) | (EntityBase.name_zh == ""),
            )

        result = await session.execute(stmt)
        entities = result.scalars().all()

        if not entities:
            logger.info("没有需要翻译的实体")
            return

        logger.info(f"共 {len(entities)} 个实体需要翻译")

        if args.dry_run:
            logger.info("--dry-run 模式，仅预览：")
            for e in entities[:20]:
                logger.info(f"  [{e.city_code}] {e.entity_type}: {e.name_ja} → (待翻译)")
            if len(entities) > 20:
                logger.info(f"  ... 还有 {len(entities) - 20} 条")
            return

        # 提取所有日文名
        ja_names = [e.name_ja or "" for e in entities]

        # 批量翻译
        logger.info("开始批量翻译...")
        translated_names = await batch_translate_with_cache(ja_names, deepl_key, redis_client)

        # 写入数据库
        updated = 0
        for entity, zh_name in zip(entities, translated_names):
            if zh_name and zh_name.strip():
                entity.name_zh = zh_name.strip()
                updated += 1

        await session.commit()
        logger.info(f"翻译完成 — 更新 {updated}/{len(entities)} 条记录")

    # 关闭 Redis
    if redis_client:
        await redis_client.aclose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="批量翻译实体日文名称为中文（DeepL API）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--city",
        nargs="+",
        choices=SUPPORTED_CITIES,
        metavar="CITY",
        help=f"目标城市（可多选）: {', '.join(SUPPORTED_CITIES)}。不指定则处理全部城市",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览待翻译数量，不实际写入",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新翻译所有实体（包括已有中文名的）",
    )

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run(args))
