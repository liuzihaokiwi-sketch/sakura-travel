#!/bin/bash
# =============================================================
# auto-deploy.sh — GitHub Actions CD 触发的自动部署入口
#
# 用法: bash deploy/auto-deploy.sh [--backend|--frontend]
# =============================================================
set -o pipefail

DEPLOY_DIR="/opt/travel-ai"
COMPOSE_FILE="docker-compose.yml"
LOG_FILE="/tmp/deploy-$(date +%Y%m%d-%H%M%S).log"

cd "$DEPLOY_DIR" || exit 1

# 加载通知函数
source deploy/notify.sh

echo "=== 自动部署开始 $(date) ===" | tee "$LOG_FILE"

# 执行部署，捕获输出
if bash deploy/deploy.sh "$@" 2>&1 | tee -a "$LOG_FILE"; then
  notify "部署成功 ✓" "$(tail -10 "$LOG_FILE")"
  echo "=== 部署成功 ==="
else
  notify "部署失败 ✗" "$(tail -50 "$LOG_FILE")"
  echo "=== 部署失败，已发送告警 ==="
  exit 1
fi

# 清理 7 天前的部署日志
find /tmp -name "deploy-*.log" -mtime +7 -delete 2>/dev/null || true
