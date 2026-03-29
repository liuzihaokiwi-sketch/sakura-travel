#!/bin/bash
# 一键部署：git pull + 重建 + 重启
# 用法: bash scripts/ops/deploy.sh
# 可选: bash scripts/ops/deploy.sh api    (只重启 api)
#       bash scripts/ops/deploy.sh all    (全部重建)

HOST="root@47.242.209.129"
DIR="/opt/travel-ai"
SERVICE="${1:-all}"

echo "=== 部署到 ECS ==="

if [ "$SERVICE" = "all" ]; then
    ssh $HOST "cd $DIR && git pull && docker compose up -d --build api worker && docker compose restart nginx && sleep 3 && docker compose ps"
else
    ssh $HOST "cd $DIR && git pull && docker compose up -d --build $SERVICE && sleep 3 && docker compose ps"
fi
