#!/bin/bash
# =============================================================
# watchdog.sh — 服务健康检查 + 自动重启
#
# cron 配置 (每5分钟):
#   */5 * * * * /opt/travel-ai/deploy/watchdog.sh >> /var/log/watchdog.log 2>&1
# =============================================================

DEPLOY_DIR="/opt/travel-ai"
COMPOSE_FILE="docker-compose.yml"
LOCK_FILE="/tmp/watchdog.lock"

cd "$DEPLOY_DIR" || exit 1

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
  lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0) ))
  if [ "$lock_age" -lt 300 ]; then
    exit 0
  fi
  rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# 加载通知函数
source deploy/notify.sh

# 抑制重复告警：同一问题 30 分钟内只发一次
should_alert() {
  local key="$1"
  local alert_file="/tmp/watchdog-alert-${key}"
  if [ -f "$alert_file" ]; then
    local age=$(( $(date +%s) - $(stat -c %Y "$alert_file" 2>/dev/null || echo 0) ))
    if [ "$age" -lt 1800 ]; then
      return 1
    fi
  fi
  touch "$alert_file"
  return 0
}

# ── 检查 api ──────────────────────────────────────────────────
if ! curl -sf --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
  echo "[$(date)] api 健康检查失败，正在重启..."
  docker compose -f "$COMPOSE_FILE" restart api
  if should_alert "api"; then
    notify "API 异常已重启" "健康检查 /health 失败，已自动重启 api 容器"
  fi
fi

# ── 检查 worker ───────────────────────────────────────────────
if ! docker ps --filter "name=japan_ai_worker" --filter "status=running" -q | grep -q .; then
  echo "[$(date)] worker 未运行，正在重启..."
  docker compose -f "$COMPOSE_FILE" restart worker
  if should_alert "worker"; then
    notify "Worker 异常已重启" "worker 容器未运行，已自动重启"
  fi
fi

# ── 检查 nginx ────────────────────────────────────────────────
if ! docker ps --filter "name=japan_ai_nginx" --filter "status=running" -q | grep -q .; then
  echo "[$(date)] nginx 未运行，正在启动..."
  docker start japan_ai_nginx 2>/dev/null || true
  if should_alert "nginx"; then
    notify "Nginx 异常已启动" "nginx 容器未运行，已自动启动"
  fi
fi

# ── 检查 frontend ─────────────────────────────────────────────
if ! curl -sf --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
  echo "[$(date)] frontend 健康检查失败，正在重启..."
  docker restart travel-web 2>/dev/null || true
  if should_alert "frontend"; then
    notify "Frontend 异常已重启" "前端服务无响应，已自动重启"
  fi
fi

# ── 检查磁盘空间 ──────────────────────────────────────────────
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
  echo "[$(date)] 磁盘使用率 ${DISK_USAGE}%，清理旧镜像..."
  docker image prune -af --filter "until=72h"
  docker system prune -f --filter "until=72h"
  if should_alert "disk"; then
    notify "磁盘空间告警 ${DISK_USAGE}%" "已自动清理 72h 前的旧镜像和容器"
  fi
fi
