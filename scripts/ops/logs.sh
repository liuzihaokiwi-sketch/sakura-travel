#!/bin/bash
# 查看服务日志
# 用法: bash scripts/ops/logs.sh          (默认看 api)
#       bash scripts/ops/logs.sh worker
#       bash scripts/ops/logs.sh frontend
#       bash scripts/ops/logs.sh nginx

HOST="root@47.242.209.129"
SERVICE="${1:-api}"

CONTAINERS="api:japan_ai_api worker:japan_ai_worker frontend:travel-web nginx:japan_ai_nginx postgres:japan_ai_postgres redis:japan_ai_redis"

CONTAINER=""
for pair in $CONTAINERS; do
    key="${pair%%:*}"
    val="${pair#*:}"
    if [ "$key" = "$SERVICE" ]; then
        CONTAINER="$val"
        break
    fi
done

if [ -z "$CONTAINER" ]; then
    echo "未知服务: $SERVICE"
    echo "可选: api worker frontend nginx postgres redis"
    exit 1
fi

ssh $HOST "docker logs $CONTAINER --tail 80"
