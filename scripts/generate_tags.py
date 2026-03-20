#!/usr/bin/env python
"""
scripts/generate_tags.py
------------------------
CLI 工具：为数据库中的实体生成 9 维主题亲和度标签。

用法示例：
  # GPT 生成（跳过已有标签）
  python scripts/generate_tags.py --city tokyo

  # 仅导入种子数据（覆盖 GPT 标签）
  python scripts/generate_tags.py --seed-only

  # GPT 强制重新生成（覆盖已有标签）
  python scripts/generate_tags.py --city osaka --force

  # 仅处理 POI 类型
  python scripts/generate_tags.py --city kyoto --type poi

  # 先导入种子，再 GPT 补全
  python scripts/generate_tags.py --city tokyo --with-seed
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
logger = logging.getLogger("generate_tags")

SUPPORTED_CITIES = ["tokyo", "osaka", "kyoto"]
SUPPORTED_TYPES = ["poi", "hotel", "restaurant"]


async def run(args: argparse.Namespace) -> None:
    from app.db.session import AsyncSessionLocal
    from app.domains.catalog.tagger import (
        apply_seed_overrides,
        generate_tags_for_city,
    )

    async with AsyncSessionLocal() as session:
        # ── 模式1：仅种子数据导入 ─────────────────────────────────────────
        if args.seed_only:
            logger.info("模式：仅导入种子数据（--seed-only）")
            seed_path = Path(args.seed_file) if args.seed_file else None
            result = await apply_seed_overrides(session, seed_path)
            logger.info(f"种子导入完成：{result}")
            return

        # ── 模式2：GPT 生成（可选先导入种子）─────────────────────────────
        cities = args.city if args.city else SUPPORTED_CITIES
        entity_type = args.type if args.type else None

        # 先导入种子（--with-seed 或 默认行为：城市批量时先做一次种子覆盖）
        if args.with_seed or args.seed_first:
            logger.info("先执行种子数据导入...")
            seed_path = Path(args.seed_file) if args.seed_file else None
            seed_result = await apply_seed_overrides(session, seed_path)
            logger.info(f"种子导入结果：{seed_result}")

        # 按城市 GPT 批量打标
        total_processed = 0
        total_written = 0

        for city in cities:
            logger.info(f"开始处理城市：{city}（force={args.force}）")
            result = await generate_tags_for_city(
                session=session,
                city_code=city,
                entity_type=entity_type,
                force_regenerate=args.force,
            )
            logger.info(
                f"[{city}] 完成 — 处理: {result['processed']}, "
                f"写入: {result['written']}, 错误: {result.get('errors', 0)}"
            )
            total_processed += result["processed"]
            total_written += result["written"]

        logger.info(
            f"全部完成 — 总处理: {total_processed}, 总写入: {total_written}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为实体生成 9 维主题亲和度标签",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 城市选项
    parser.add_argument(
        "--city",
        nargs="+",
        choices=SUPPORTED_CITIES,
        metavar="CITY",
        help=f"目标城市（可多选）: {', '.join(SUPPORTED_CITIES)}。不指定则处理全部城市",
    )

    # 实体类型过滤
    parser.add_argument(
        "--type",
        choices=SUPPORTED_TYPES,
        metavar="TYPE",
        help=f"限制实体类型: {', '.join(SUPPORTED_TYPES)}",
    )

    # 模式控制
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--seed-only",
        action="store_true",
        help="仅导入种子数据，不调用 GPT",
    )
    mode_group.add_argument(
        "--with-seed",
        action="store_true",
        help="先导入种子数据，再 GPT 补全",
    )
    mode_group.add_argument(
        "--seed-first",
        action="store_true",
        help="与 --with-seed 相同（别名）",
    )

    parser.add_argument(
        "--seed-file",
        metavar="PATH",
        help="种子数据 JSON 路径（默认: data/entity_affinity_seed_v1.json）",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成所有实体的标签（覆盖已有数据）",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印待处理实体数量，不实际写入",
    )

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run:
        logger.info("--dry-run 模式，仅统计，不写入数据库")
        # dry-run 模式下不修改 tagger 逻辑，仅提示
        sys.exit(0)

    asyncio.run(run(args))
