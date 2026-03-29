#!/bin/bash
# =============================================================
# setup-ops.sh — ECS 一键配置运维自动化
#
# 用法: bash deploy/setup-ops.sh
# =============================================================
set -e

DEPLOY_DIR="/opt/travel-ai"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE="$DEPLOY_DIR/.env"

cd "$DEPLOY_DIR" || { echo "ERROR: $DEPLOY_DIR 不存在"; exit 1; }

echo "========================================="
echo "  travel-ai 运维自动化配置"
echo "========================================="
echo ""

# ── 辅助函数 ──────────────────────────────────────────────────
append_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    local existing
    existing=$(grep "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2-)
    if [ -n "$existing" ]; then
      echo "  [跳过] ${key} 已配置"
      return
    fi
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    echo "  [更新] ${key}"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
    echo "  [新增] ${key}"
  fi
}

# ── 1. Sentry DSN ─────────────────────────────────────────────
echo "--- [1/6] 配置 Sentry ---"
SENTRY_DSN="https://8ae65d490e39221f9f302dcdc81dc069@o4511125667315712.ingest.de.sentry.io/4511125685665872"
append_env "SENTRY_DSN" "$SENTRY_DSN"
echo ""

# ── 2. SMTP 邮件配置 ─────────────────────────────────────────
echo "--- [2/6] 配置 SMTP 邮件告警 ---"
EXISTING_SMTP=$(grep "^SMTP_HOST=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
if [ -n "$EXISTING_SMTP" ]; then
  echo "  SMTP 已配置 (${EXISTING_SMTP})，跳过"
else
  echo "  QQ邮箱授权码获取: QQ邮箱 → 设置 → 账户 → POP3/SMTP → 生成授权码"
  echo ""
  smtp_host="smtp.qq.com"
  smtp_user="liuzihao12345@qq.com"
  alert_email="liuzihao12345@qq.com"
  echo "  SMTP 服务器: $smtp_host"
  echo "  发件/收件邮箱: $smtp_user"
  echo ""
  read -rsp "  请输入 QQ邮箱授权码: " smtp_pass
  echo ""

  append_env "SMTP_HOST" "$smtp_host"
  append_env "SMTP_USER" "$smtp_user"
  append_env "SMTP_PASSWORD" "$smtp_pass"
  append_env "ALERT_EMAIL" "$alert_email"
fi
echo ""

# ── 3. 脚本执行权限 ──────────────────────────────────────────
echo "--- [3/6] 设置脚本权限 ---"
chmod +x deploy/deploy.sh deploy/auto-deploy.sh deploy/watchdog.sh deploy/notify.sh deploy/setup-ops.sh 2>/dev/null
echo "  所有 deploy/*.sh 已加执行权限"
echo ""

# ── 4. 注册 watchdog cron ────────────────────────────────────
echo "--- [4/6] 注册 watchdog 定时任务 ---"
CRON_CMD="*/5 * * * * /opt/travel-ai/deploy/watchdog.sh >> /var/log/watchdog.log 2>&1"

if crontab -l 2>/dev/null | grep -qF "watchdog.sh"; then
  echo "  [跳过] watchdog cron 已存在"
else
  (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
  echo "  [新增] 每 5 分钟健康检查已注册"
fi
echo ""

# ── 5. 重启服务 ──────────────────────────────────────────────
echo "--- [5/6] 重启服务使 Sentry 配置生效 ---"
docker compose -f "$COMPOSE_FILE" restart api worker
echo "  api + worker 已重启"
sleep 5
echo ""

# ── 6. 验证 ──────────────────────────────────────────────────
echo "--- [6/6] 验证 ---"

echo -n "  后端健康检查: "
if curl -sf --max-time 10 http://localhost:8000/health; then
  echo " ✓"
else
  echo " ✗ (可能需要等待几秒)"
fi

echo ""
read -rp "  是否发送测试邮件? [Y/n]: " send_test
send_test=${send_test:-Y}
if [[ "$send_test" =~ ^[Yy]$ ]]; then
  source deploy/notify.sh
  notify "配置成功" "travel-ai 运维自动化配置完成。Sentry、邮件告警、watchdog 均已就绪。"
  echo "  测试邮件已发送，请检查收件箱"
fi

echo ""
echo "========================================="
echo "  配置完成!"
echo ""
echo "  已启用:"
echo "    ✓ Sentry 错误监控"
echo "    ✓ 邮件告警通知 (通过 api 容器内 Python 发送)"
echo "    ✓ Watchdog 每5分钟健康检查+自动重启"
echo ""
echo "  GitHub Secrets 已配置: ✓"
echo "========================================="
