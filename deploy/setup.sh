#!/bin/bash
# =============================================================
# setup.sh — ECS 首次初始化脚本（只需运行一次）
# 用法: bash deploy/setup.sh
# =============================================================
set -e

echo "=== [1/6] 更新系统 + 安装 Docker ==="
apt-get update -y
apt-get install -y ca-certificates curl gnupg git

# Docker 官方源
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

echo "=== [2/6] 创建项目目录 ==="
mkdir -p /opt/travel-ai
cd /opt/travel-ai

echo "=== [3/6] 配置防火墙 (ufw) ==="
apt-get install -y ufw
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

echo "=== [4/6] 生成自签 SSL 证书（临时用，之后用 certbot 替换）==="
mkdir -p /opt/travel-ai/deploy/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/travel-ai/deploy/ssl/key.pem \
  -out    /opt/travel-ai/deploy/ssl/cert.pem \
  -subj   "/C=CN/ST=HK/L=HK/O=TravelAI/CN=47.242.209.129"

echo "=== [5/6] 提示：请上传项目代码并创建 .env ==="
echo ""
echo "  # 上传代码（在本地执行）:"
echo "  rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \\"
echo "    ./ root@47.242.209.129:/opt/travel-ai/"
echo ""
echo "  # 在服务器上复制并编辑环境变量:"
echo "  cp /opt/travel-ai/.env.example /opt/travel-ai/.env"
echo "  nano /opt/travel-ai/.env"
echo ""

echo "=== [6/6] 初始化完成 ==="
docker --version
docker compose version
