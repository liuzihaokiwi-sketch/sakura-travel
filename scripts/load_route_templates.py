#!/usr/bin/env python3
"""
scripts/load_route_templates.py
幂等加载路线模板 JSON → route_templates 表
用法: python scripts/load_route_templates.py [--dir data/route_templates]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# 保证能找到 app 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.db.models.derived import RouteTemplate
from app.db.session import AsyncSessionLocal as async_session_factory

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def load_templates(template_dir: Path) -> None:
    json_files = sorted(template_dir.glob("*.json"))
    if not json_files:
        logger.warning("未找到任何 JSON 文件：%s", template_dir)
        return

    async with async_session_factory() as session:
        for path in json_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            template_code: str = data["template_code"]
            name_zh: str = data["name_zh"]
            city_code: str = data["city_code"]
            total_days: int = data["total_days"]

            # 用 name_zh 做幂等 key（模型没有 template_code 字段）
            existing = await session.scalar(
                select(RouteTemplate).where(RouteTemplate.name_zh == name_zh)
            )

            if existing:
                await session.execute(
                    update(RouteTemplate)
                    .where(RouteTemplate.name_zh == name_zh)
                    .values(
                        city_code=city_code,
                        duration_days=total_days,
                        template_data=data,
                        is_active=True,
                    )
                )
                logger.info("已更新模板：%s", name_zh)
            else:
                session.add(
                    RouteTemplate(
                        name_zh=name_zh,
                        city_code=city_code,
                        duration_days=total_days,
                        template_data=data,
                        is_active=True,
                    )
                )
                logger.info("已创建模板：%s", name_zh)

        await session.commit()

    logger.info("✅ 共加载 %d 条路线模板", len(json_files))


def main() -> None:
    parser = argparse.ArgumentParser(description="加载路线模板到数据库")
    parser.add_argument(
        "--dir",
        default="data/route_templates",
        help="模板 JSON 目录（默认：data/route_templates）",
    )
    args = parser.parse_args()

    template_dir = Path(args.dir)
    if not template_dir.exists():
        logger.error("目录不存在：%s", template_dir)
        sys.exit(1)

    asyncio.run(load_templates(template_dir))


if __name__ == "__main__":
    main()
