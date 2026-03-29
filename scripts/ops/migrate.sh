#!/bin/bash
# 远程执行 migration
# 用法: bash scripts/ops/migrate.sh              (upgrade head)
#       bash scripts/ops/migrate.sh current       (查看当前版本)

HOST="root@47.242.209.129"
DIR="/opt/travel-ai"
ACTION="${1:-upgrade head}"

ssh $HOST "cd $DIR && docker exec japan_ai_api python -m alembic $ACTION"
