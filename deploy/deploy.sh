#!/bin/bash
# =============================================================
# deploy.sh — 日常更新部署脚本
#
# 用法:
#   bash deploy/deploy.sh           # 全量部署（后端 + 前端）
#   bash deploy/deploy.sh --backend # 只部署后端
#   bash deploy/deploy.sh --frontend # 只部署前端
# =============================================================
set -e

DEPLOY_DIR="/opt/travel-ai"
COMPOSE_FILE="deploy/docker-compose.yml"
IMAGE_NAME="japan_ai_api"

# ── 参数解析 ──────────────────────────────────────────────────
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true

if [ "$1" = "--backend" ]; then
  DEPLOY_FRONTEND=false
elif [ "$1" = "--frontend" ]; then
  DEPLOY_BACKEND=false
fi

echo "=== [deploy] 开始部署 (backend=$DEPLOY_BACKEND frontend=$DEPLOY_FRONTEND) ==="
cd "$DEPLOY_DIR"

# ── 拉取最新代码 ──────────────────────────────────────────────
echo "--- 拉取最新代码 ---"
if [ -d ".git" ]; then
  git pull origin main
fi

# ── 后端：构建 + 迁移 + 重启 ─────────────────────────────────
if [ "$DEPLOY_BACKEND" = true ]; then
  echo "--- 构建后端镜像 ---"
  docker compose -f "$COMPOSE_FILE" build backend

  echo "--- 运行数据库迁移 ---"
  docker compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head

  echo "--- 重启后端服务 ---"
  docker compose -f "$COMPOSE_FILE" up -d backend worker
fi

# ── 前端：构建 + 重启 ─────────────────────────────────────────
if [ "$DEPLOY_FRONTEND" = true ]; then
  echo "--- 构建前端镜像 ---"
  docker compose -f "$COMPOSE_FILE" build frontend

  echo "--- 重启前端服务 ---"
  docker compose -f "$COMPOSE_FILE" up -d frontend
fi

# ── nginx 确保运行 ────────────────────────────────────────────
echo "--- 确保 nginx 运行 ---"
docker compose -f "$COMPOSE_FILE" up -d nginx

# ── 清理 + 状态 ───────────────────────────────────────────────
echo "--- 清理旧镜像 ---"
docker image prune -f

echo "--- 等待健康检查 ---"
sleep 8
docker compose -f "$COMPOSE_FILE" ps

# ── 验证部署结果 ─────────────────────────────────────────────
HEALTH_OK=true
if [ "$DEPLOY_BACKEND" = true ]; then
  if ! curl -sf --max-time 10 http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: backend 健康检查失败"
    HEALTH_OK=false
  fi
fi
if [ "$DEPLOY_FRONTEND" = true ]; then
  if ! curl -sf --max-time 10 http://localhost:3000 > /dev/null 2>&1; then
    echo "ERROR: frontend 健康检查失败"
    HEALTH_OK=false
  fi
fi

echo ""
if [ "$HEALTH_OK" = true ]; then
  echo "=== 部署完成 ==="
  echo "  前端: https://47.242.209.129/"
  echo "  API:  https://47.242.209.129/api/"
  echo "  健康: https://47.242.209.129/health"
  exit 0
else
  echo "=== 部署完成但健康检查失败 ==="
  exit 1
fi