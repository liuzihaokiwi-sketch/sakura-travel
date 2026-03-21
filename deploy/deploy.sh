#!/bin/bash
# =============================================================
# deploy.sh — 日常更新部署脚本
# 用法: bash deploy/deploy.sh [image_tag]
# =============================================================
set -e

DEPLOY_DIR="/opt/travel-ai"
IMAGE_NAME="japan_ai_api"
IMAGE_TAG="${1:-latest}"

echo "=== [deploy] 开始部署 tag=${IMAGE_TAG} ==="
cd "$DEPLOY_DIR"

echo "--- 拉取最新代码 ---"
# 如果用 git 管理则拉取，否则跳过
if [ -d ".git" ]; then
  git pull origin main
fi

echo "--- 构建 Docker 镜像 ---"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -t "${IMAGE_NAME}:latest" .

echo "--- 运行数据库迁移 ---"
docker run --rm \
  --env-file "$DEPLOY_DIR/.env" \
  --network travel-ai_backend \
  "${IMAGE_NAME}:${IMAGE_TAG}" \
  alembic upgrade head

echo "--- 启动/更新服务 ---"
IMAGE_TAG="$IMAGE_TAG" DOCKER_IMAGE="$IMAGE_NAME" \
  docker compose -f docker-compose.prod.yml up -d --no-build --remove-orphans

echo "--- 清理旧镜像 ---"
docker image prune -f

echo "--- 等待健康检查 ---"
sleep 8
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== 部署完成 ==="
echo "  API: https://47.242.209.129/api/"
echo "  Health: https://47.242.209.129/health"