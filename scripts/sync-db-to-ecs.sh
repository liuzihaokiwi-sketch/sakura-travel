#!/bin/bash
# =============================================================
# sync-db-to-ecs.sh — 一键同步本地数据库到 ECS 生产环境
#
# 用法: bash scripts/sync-db-to-ecs.sh
#
# 流程:
#   1. 本地 docker postgres → pg_dump → 压缩
#   2. scp 传到 ECS
#   3. ECS 上停服务 → restore → 启服务
#
# 前提:
#   - 本地 docker 里 japan_ai_postgres 在运行
#   - SSH 密钥已配好 (ssh root@47.242.209.129 能连)
# =============================================================
set -e

ECS_HOST="47.242.209.129"
ECS_USER="root"
DUMP_FILE="/tmp/travel-ai-dump.sql.gz"

# 本地数据库配置
LOCAL_DB_USER="postgres"
LOCAL_DB_NAME="postgres"
LOCAL_CONTAINER="japan_ai_postgres"

# ECS 数据库配置
ECS_DB_USER="japan_ai"
ECS_DB_NAME="japan_ai"
ECS_CONTAINER="japan_ai_postgres"

echo "========================================="
echo "  数据库同步: 本地 → ECS"
echo "========================================="
echo ""
echo "  本地: ${LOCAL_DB_USER}@${LOCAL_DB_NAME}"
echo "  ECS:  ${ECS_DB_USER}@${ECS_DB_NAME} (${ECS_HOST})"
echo ""
echo "  ⚠️  这会覆盖 ECS 上的所有数据！"
echo ""
read -rp "  确认继续? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "  已取消"
  exit 0
fi

# ── 1. 本地 dump ─────────────────────────────────────────────
echo ""
echo "--- [1/4] 导出本地数据库 ---"
if ! docker ps --filter "name=${LOCAL_CONTAINER}" --filter "status=running" -q | grep -q .; then
  echo "ERROR: 本地容器 ${LOCAL_CONTAINER} 未运行"
  echo "请先执行: docker compose up -d postgres"
  exit 1
fi

docker exec "$LOCAL_CONTAINER" pg_dump \
  -U "$LOCAL_DB_USER" \
  -d "$LOCAL_DB_NAME" \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  | gzip > "$DUMP_FILE"

DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo "  导出完成: ${DUMP_FILE} (${DUMP_SIZE})"

# ── 2. 传输到 ECS ───────────────────────────────────────────
echo ""
echo "--- [2/4] 传输到 ECS ---"
scp "$DUMP_FILE" "${ECS_USER}@${ECS_HOST}:/tmp/"
echo "  传输完成"

# ── 3. ECS 上 restore ────────────────────────────────────────
echo ""
echo "--- [3/4] 在 ECS 上恢复数据库 ---"
ssh "${ECS_USER}@${ECS_HOST}" << REMOTE_EOF
  set -e
  cd /opt/travel-ai

  echo "  停止 api + worker..."
  docker compose stop api worker 2>/dev/null || true

  echo "  恢复数据库..."
  gunzip -c /tmp/travel-ai-dump.sql.gz | docker exec -i ${ECS_CONTAINER} psql -U ${ECS_DB_USER} -d ${ECS_DB_NAME} 2>&1 | tail -5

  echo "  启动 api + worker..."
  docker compose start api worker 2>/dev/null || docker compose up -d api worker

  echo "  验证数据..."
  docker exec ${ECS_CONTAINER} psql -U ${ECS_DB_USER} -d ${ECS_DB_NAME} -c "SELECT entity_type, count(*) FROM entity_base GROUP BY entity_type;"

  rm -f /tmp/travel-ai-dump.sql.gz
  echo "  ECS 恢复完成"
REMOTE_EOF

# ── 4. 清理 ──────────────────────────────────────────────────
echo ""
echo "--- [4/4] 清理临时文件 ---"
rm -f "$DUMP_FILE"

echo ""
echo "========================================="
echo "  同步完成!"
echo "  验证: https://kiwitrip.cn/admin/catalog"
echo "========================================="
