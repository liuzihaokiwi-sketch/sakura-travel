#!/bin/bash
# 查看 ECS 状态：容器 + 最近 commit + 磁盘
# 用法: bash scripts/ops/status.sh

HOST="root@47.242.209.129"
DIR="/opt/travel-ai"

ssh $HOST "
echo '=== 容器状态 ==='
cd $DIR && docker compose ps
echo ''
echo '=== 最近提交 ==='
git log --oneline -5
echo ''
echo '=== 磁盘 ==='
df -h / | tail -1
echo ''
echo '=== 内存 ==='
free -h | head -2
"
