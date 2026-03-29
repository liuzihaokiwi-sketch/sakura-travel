#!/bin/bash
# 远程 DB 操作
# 用法: bash scripts/ops/db.sh                    (进入 psql)
#       bash scripts/ops/db.sh "SELECT COUNT(*) FROM entity_base"

HOST="root@47.242.209.129"

if [ -z "$1" ]; then
    ssh -t $HOST "docker exec -it japan_ai_postgres psql -U postgres -d postgres"
else
    ssh $HOST "docker exec japan_ai_postgres psql -U postgres -d postgres -c \"$1\""
fi
