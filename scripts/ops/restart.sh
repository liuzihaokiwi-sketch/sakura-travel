#!/bin/bash
# 重启服务
# 用法: bash scripts/ops/restart.sh          (重启 api + worker)
#       bash scripts/ops/restart.sh api
#       bash scripts/ops/restart.sh all

HOST="root@47.242.209.129"
DIR="/opt/travel-ai"
SERVICE="${1:-api worker}"

if [ "$SERVICE" = "all" ]; then
    SERVICE="api worker frontend nginx"
fi

ssh $HOST "cd $DIR && docker compose restart $SERVICE && sleep 3 && docker compose ps"
