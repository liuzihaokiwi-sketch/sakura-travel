"""
convert_mojor_to_seed.py — 把 mojor/ 下的活动簇 md 文件转成可执行的 seed Python 文件

用法：
    python scripts/convert_mojor_to_seed.py

输出：
    scripts/seed_{circle}_clusters.py × 8 个文件
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOJOR = ROOT / "data" / "mojor"
SCRIPTS = ROOT / "scripts"

# md 文件 → (circle_id, 输出文件名)
FILE_MAP = {
    "tokyo_metropolitan_circle_activity_clusters.md": ("tokyo_metropolitan_circle", "seed_tokyo_clusters.py"),
    "hokkaido_nature_circle_activity_clusters.md": ("hokkaido_nature_circle", "seed_hokkaido_clusters.py"),
    "kyushu_onsen_circle_activity_clusters.md": ("kyushu_onsen_circle", "seed_kyushu_clusters.py"),
    "guangfu_circle_core_clusters.md": ("guangfu_circle", "seed_guangfu_clusters.py"),
    "chubu_mountain_circle_activity_clusters.md": ("chubu_mountain_circle", "seed_chubu_clusters.py"),
    "huadong_circle_clusters.md": ("huadong_circle", "seed_huadong_clusters.py"),
    "xinjiang_yili_circle_clusters.md": ("xinjiang_yili_circle", "seed_xinjiang_clusters.py"),
    "kansai_classic_circle_activity_clusters.md": ("kansai_classic_circle", "seed_kansai_v2_clusters.py"),
}


def extract_clusters_json(content: str) -> list[dict]:
    """从 md 文件中提取 JSON 数组格式的活动簇。"""
    # 尝试直接解析整个文件为 JSON 数组
    stripped = content.strip()
    if stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # 尝试找 JSON 数组片段
    match = re.search(r"\[[\s\S]*\]", content)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return []


def extract_clusters_markdown(content: str) -> list[dict]:
    """从 markdown 格式（### `cluster_id` + bullet points）提取活动簇。"""
    clusters = []
    # 分割为每个 ### 块
    blocks = re.split(r"(?=^### `)", content, flags=re.MULTILINE)

    for block in blocks:
        m = re.match(r"^### `([^`]+)`", block)
        if not m:
            continue

        cluster_id = m.group(1)
        cluster = {"cluster_id": cluster_id}

        # 提取 bullet 字段
        for line in block.split("\n"):
            line = line.strip()
            # 格式: - `field`: `value` 或 * `field`: `value`
            fm = re.match(r"[-*]\s+`([^`]+)`:\s*`?([^`\n]+)`?", line)
            if fm:
                key = fm.group(1).strip()
                val = fm.group(2).strip().rstrip("`")

                # 解析值类型
                if val.startswith("["):
                    try:
                        val = json.loads(val.replace("'", '"'))
                    except json.JSONDecodeError:
                        val = [v.strip().strip("'\"") for v in val.strip("[]").split(",")]
                elif val in ("true", "True"):
                    val = True
                elif val in ("false", "False"):
                    val = False
                elif val.isdigit():
                    val = int(val)

                cluster[key] = val

        if len(cluster) > 2:  # 至少有 cluster_id + 一些字段
            clusters.append(cluster)

    return clusters


def normalize_booleans(clusters: list[dict]) -> list[dict]:
    """确保 boolean 值是 Python True/False。"""
    for c in clusters:
        for k, v in c.items():
            if v == "true" or v == "True":
                c[k] = True
            elif v == "false" or v == "False":
                c[k] = False
    return clusters


def generate_seed_file(circle_id: str, clusters: list[dict]) -> str:
    """生成 seed Python 文件内容。"""
    # 格式化 clusters 为 Python 代码
    clusters_str = json.dumps(clusters, ensure_ascii=False, indent=4)
    # 修 JSON true/false → Python True/False
    clusters_str = clusters_str.replace(": true", ": True").replace(": false", ": False")
    clusters_str = clusters_str.replace(": null", ": None")

    return f'''"""
seed_{circle_id}_clusters.py — {circle_id} 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_{circle_id.split("_")[0]}_clusters.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import ActivityCluster

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

CLUSTERS = {clusters_str}


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                skip_count += 1
                continue
            # 只传 ActivityCluster 已知的字段
            known_fields = {{c.key for c in ActivityCluster.__table__.columns}}
            filtered = {{k: v for k, v in data.items() if k in known_fields}}
            cluster = ActivityCluster(**filtered)
            session.add(cluster)
            new_count += 1
            logger.info("  NEW: %s [%s] %s", data["cluster_id"], data.get("level", "?"), data.get("city_code", "?"))
        await session.commit()
        logger.info("=== %s 完成: 新增=%d 跳过=%d 总计=%d ===",
                     "{circle_id}", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
'''


def main():
    total_clusters = 0
    total_files = 0

    for md_name, (circle_id, seed_name) in FILE_MAP.items():
        md_path = MOJOR / md_name
        if not md_path.exists():
            print(f"  SKIP {md_name}: not found")
            continue

        content = md_path.read_text(encoding="utf-8")

        # 尝试 JSON 格式
        clusters = extract_clusters_json(content)
        if not clusters:
            # 尝试 markdown 格式
            clusters = extract_clusters_markdown(content)

        if not clusters:
            print(f"  WARN {md_name}: 0 clusters extracted")
            continue

        clusters = normalize_booleans(clusters)

        # 生成 seed 文件
        seed_content = generate_seed_file(circle_id, clusters)
        seed_path = SCRIPTS / seed_name
        seed_path.write_text(seed_content, encoding="utf-8")

        total_clusters += len(clusters)
        total_files += 1
        print(f"  OK   {md_name:50s} → {seed_name:35s} ({len(clusters)} clusters)")

    print(f"\n  Generated {total_files} seed files with {total_clusters} total clusters")


if __name__ == "__main__":
    main()
