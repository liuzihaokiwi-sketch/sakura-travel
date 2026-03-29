#!/bin/bash
# =============================================================
# setup-ssl.sh — 用 certbot 申请 Let's Encrypt HTTPS 证书
#
# 用法: bash deploy/setup-ssl.sh
# =============================================================
set -e

DOMAIN="kiwitrip.cn"
EMAIL="liuzihao12345@qq.com"

echo "=== 申请 SSL 证书: $DOMAIN ==="

# 1. 安装 certbot（如果没有）
if ! command -v certbot &> /dev/null; then
  echo "--- 安装 certbot ---"
  dnf install -y certbot 2>/dev/null || yum install -y certbot 2>/dev/null || apt install -y certbot
fi

# 2. 确保 certbot 验证目录存在
mkdir -p /var/www/certbot

# 3. 临时让 nginx 80 端口直接服务静态文件（不跳转 HTTPS）
# 先停 nginx 用 standalone 模式申请
echo "--- 临时停止 nginx ---"
docker stop japan_ai_nginx

# 4. 申请证书
echo "--- 申请证书 ---"
certbot certonly --standalone \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive

# 5. 复制证书到 nginx 挂载目录
echo "--- 部署证书 ---"
CERT_DIR="/opt/travel-ai/deploy/ssl"
mkdir -p "$CERT_DIR"
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$CERT_DIR/cert.pem"
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$CERT_DIR/key.pem"

# 6. 重启 nginx
echo "--- 重启 nginx ---"
docker start japan_ai_nginx

# 7. 设置自动续期 cron
RENEW_CMD="0 3 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $CERT_DIR/cert.pem && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $CERT_DIR/key.pem && docker restart japan_ai_nginx"
if ! crontab -l 2>/dev/null | grep -qF "certbot renew"; then
  (crontab -l 2>/dev/null; echo "$RENEW_CMD") | crontab -
  echo "  [新增] 证书自动续期 cron 已注册（每2个月）"
fi

echo ""
echo "=== SSL 配置完成 ==="
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
