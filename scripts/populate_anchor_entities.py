"""
populate_anchor_entities.py — 为活动簇填充 anchor_entities 结构化字段

用 AI（通过 cached_ai_call）读取每个活动簇的 name_zh + notes + city_code，
输出该簇需要的核心景点/餐厅/酒店列表，写入 anchor_entities JSONB 字段。

与 regex 提取不同：
- AI 能理解"眺望富士山倒影"意味着需要"富士山"实体
- AI 能补充 notes 没提到但该活动显然需要的景点
- AI 能区分"银座"是路过的区域名还是需要单独建实体的目的地

用法：
    # 全部活动簇
    python scripts/populate_anchor_entities.py

    # 只处理某个城市圈
    python scripts/populate_anchor_entities.py --circle kansai_classic_circle

    # 只处理 anchor_entities 为空的簇
    python scripts/populate_anchor_entities.py --only-empty

    # 只看 AI 输出不写入
    python scripts/populate_anchor_entities.py --dry-run

    # 每次处理的簇数量（默认 15，太多会超 token）
    python scripts/populate_anchor_entities.py --batch-size 10
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """\
你是日本和中国旅游数据库工程师，精通东亚各城市的旅游景点、餐厅和酒店。
你的任务是为旅行活动簇（activity cluster）列出它需要的核心实体。"""

_BATCH_PROMPT = """\
以下是 {count} 个活动簇的信息。请为每个活动簇列出它需要的核心实体（景点/餐厅/酒店）。

规则：
1. 每个实体必须是真实存在的具体地点，不是区域名或通用描述
2. name 用中文名（如"清水寺"不是"Kiyomizu-dera"）
3. type 只能是 poi / restaurant / hotel
4. role 只能是 anchor（核心必去）或 secondary（次要/顺路）
5. 每个簇列出 3-8 个实体，S 级多列几个，B 级少列几个
6. 如果 notes 提到了具体景点名，一定要包含
7. 如果 notes 没提到但该活动显然需要的知名景点，也要补上
8. 不要列区域名（如"银座""涩谷"），要列具体景点（如"银座和光""涩谷 Sky"）
9. 餐厅：只列具体店名或特色美食街（如"筑地场外市场"），不列菜系名
10. city_code 必须与该实体的实际所在地匹配（不一定等于活动簇的 city_code）

活动簇列表：
{clusters_json}

请严格输出 JSON 对象，key 是 cluster_id，value 是实体数组。不要任何解释文字。

输出格式：
{{
  "cluster_id_1": [
    {{"name": "清水寺", "type": "poi", "role": "anchor", "city_code": "kyoto"}},
    {{"name": "二年坂", "type": "poi", "role": "secondary", "city_code": "kyoto"}}
  ],
  "cluster_id_2": [...]
}}
"""


async def populate(
    circle_id: str | None = None,
    only_empty: bool = False,
    batch_size: int = 15,
    dry_run: bool = False,
    delay: float = 2.0,
):
    """为活动簇批量填充 anchor_entities。"""
    from sqlalchemy import select, and_
    from app.db.session import AsyncSessionLocal
    from app.db.models.city_circles import ActivityCluster
    from app.core.ai_cache import cached_ai_call
    from app.core.config import settings
    from app.domains.catalog.ai_generator import _extract_json_object

    async with AsyncSessionLocal() as session:
        # 加载活动簇
        q = select(ActivityCluster).where(ActivityCluster.is_active == True)
        if circle_id:
            q = q.where(ActivityCluster.circle_id == circle_id)
        if only_empty:
            q = q.where(ActivityCluster.anchor_entities == None)

        result = await session.execute(q)
        clusters = list(result.scalars().all())
        logger.info("加载了 %d 个活动簇", len(clusters))

        if not clusters:
            logger.info("没有需要处理的活动簇")
            return

        # 按城市圈分组
        by_circle: dict[str, list] = {}
        for c in clusters:
            by_circle.setdefault(c.circle_id, []).append(c)

        total_updated = 0
        total_entities = 0

        for cir_id, cir_clusters in by_circle.items():
            logger.info("=" * 60)
            logger.info("城市圈: %s (%d 个簇)", cir_id, len(cir_clusters))

            # 分批处理
            for batch_start in range(0, len(cir_clusters), batch_size):
                batch = cir_clusters[batch_start:batch_start + batch_size]
                batch_end = batch_start + len(batch)
                logger.info("  批次 %d-%d / %d",
                            batch_start + 1, batch_end, len(cir_clusters))

                # 构建 prompt 输入
                clusters_info = []
                for c in batch:
                    clusters_info.append({
                        "cluster_id": c.cluster_id,
                        "city_code": c.city_code,
                        "name_zh": c.name_zh,
                        "level": c.level,
                        "notes": c.notes or "",
                    })

                prompt = _BATCH_PROMPT.format(
                    count=len(batch),
                    clusters_json=json.dumps(clusters_info, ensure_ascii=False, indent=2),
                )

                # 调 AI
                try:
                    raw = await cached_ai_call(
                        prompt=prompt,
                        model=settings.ai_model,
                        system_prompt=_SYSTEM_PROMPT,
                        temperature=0.2,
                        max_tokens=8000,
                    )
                except Exception as exc:
                    logger.error("  AI 调用失败: %s", exc)
                    await asyncio.sleep(delay)
                    continue

                if not raw:
                    logger.warning("  AI 返回空")
                    continue

                # 解析
                try:
                    parsed = json.loads(_extract_json_object(raw))
                except json.JSONDecodeError as exc:
                    logger.error("  JSON 解析失败: %s", exc)
                    logger.error("  原始输出前 500 字: %s", raw[:500])
                    continue

                # 写入
                for c in batch:
                    entities = parsed.get(c.cluster_id, [])
                    if not entities:
                        logger.warning("    %s: AI 未返回实体", c.cluster_id)
                        continue

                    # 基本校验
                    valid = []
                    for ent in entities:
                        if not isinstance(ent, dict):
                            continue
                        if not ent.get("name"):
                            continue
                        if ent.get("type") not in ("poi", "restaurant", "hotel"):
                            ent["type"] = "poi"
                        if ent.get("role") not in ("anchor", "secondary"):
                            ent["role"] = "secondary"
                        valid.append({
                            "name": ent["name"],
                            "type": ent["type"],
                            "role": ent["role"],
                            "city_code": ent.get("city_code", c.city_code),
                        })

                    if dry_run:
                        logger.info("    %s [%s]: %d 个实体",
                                     c.cluster_id, c.level, len(valid))
                        for v in valid:
                            logger.info("      [%s] %s (%s, %s)",
                                         v["role"], v["name"],
                                         v["type"], v["city_code"])
                    else:
                        c.anchor_entities = valid
                        total_updated += 1
                        total_entities += len(valid)
                        logger.info("    %s: %d 个实体已写入",
                                     c.cluster_id, len(valid))

                if not dry_run:
                    await session.commit()

                await asyncio.sleep(delay)

    if dry_run:
        logger.info("\n[DRY RUN] 未写入数据库")
    else:
        logger.info("\n完成: 更新了 %d 个活动簇, 共 %d 个实体声明",
                     total_updated, total_entities)


def main():
    parser = argparse.ArgumentParser(
        description="为活动簇填充 anchor_entities 结构化字段")
    parser.add_argument("--circle", help="只处理指定城市圈")
    parser.add_argument("--only-empty", action="store_true",
                        help="只处理 anchor_entities 为空的簇")
    parser.add_argument("--batch-size", type=int, default=15,
                        help="每批处理的簇数量（默认 15）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只看 AI 输出不写入 DB")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="批次间延迟秒数（默认 2.0）")
    args = parser.parse_args()

    asyncio.run(populate(
        circle_id=args.circle,
        only_empty=args.only_empty,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        delay=args.delay,
    ))


if __name__ == "__main__":
    main()
