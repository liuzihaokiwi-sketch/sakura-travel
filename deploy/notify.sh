#!/bin/bash
# =============================================================
# notify.sh — 邮件告警通知
#
# 用法:
#   source deploy/notify.sh
#   notify "部署成功" "后端已更新到最新版本"
#   notify "服务异常" "$(cat /tmp/error.log | tail -50)"
#
# 依赖环境变量 (从 .env 加载):
#   SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL
# =============================================================

# 加载 .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

notify() {
  local subject="$1"
  local body="${2:-$subject}"
  local hostname
  hostname=$(hostname)
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  # 跳过：未配置 SMTP
  if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_USER" ] || [ -z "$ALERT_EMAIL" ]; then
    echo "[notify] SMTP 未配置，跳过邮件通知"
    return 0
  fi

  python3 -c "
import smtplib, sys
from email.mime.text import MIMEText
body = '''[$hostname] $timestamp
---
$body'''
msg = MIMEText(body, 'plain', 'utf-8')
msg['Subject'] = '[travel-ai] $subject'
msg['From'] = '$SMTP_USER'
msg['To'] = '$ALERT_EMAIL'
try:
    with smtplib.SMTP_SSL('$SMTP_HOST', 465, timeout=10) as s:
        s.login('$SMTP_USER', '$SMTP_PASSWORD')
        s.send_message(msg)
    print('[notify] 邮件已发送')
except Exception as e:
    print(f'[notify] 邮件发送失败: {e}', file=sys.stderr)
" 2>&1 || true
}
