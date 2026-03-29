#!/bin/bash
# 一键执行所有活动簇 seed 脚本
# 用法: bash scripts/seed_all_clusters.sh

set -e
cd "$(dirname "$0")/.."

echo "=== 活动簇数据入库 ==="
echo ""

# 先跑城市圈定义（如果还没有）
echo ">>> 城市圈定义..."
python scripts/seed_all_circles.py 2>&1 | tail -5
echo ""

# 关西圈（基础 + 扩展 + v2补充）
echo ">>> 关西圈活动簇..."
python scripts/seed_kansai_circle.py 2>&1 | tail -3
python scripts/seed_kansai_extended_circles.py 2>&1 | tail -3
python scripts/seed_kansai_supplemental_clusters.py 2>&1 | tail -3
python scripts/seed_kansai_v2_clusters.py 2>&1 | tail -3
echo ""

# 其余 7 圈
for circle in tokyo hokkaido kyushu guangfu chubu huadong xinjiang; do
    echo ">>> ${circle} 活动簇..."
    python "scripts/seed_${circle}_clusters.py" 2>&1 | tail -3
    echo ""
done

echo "=== 全部完成 ==="
