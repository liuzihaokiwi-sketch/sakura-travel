#!/bin/bash
# =============================================================
# fix-ecs.sh — ECS 一键诊断修复脚本
#
# 用法: 在 ECS 上执行 bash scripts/fix-ecs.sh
# =============================================================
set -e

cd /opt/travel-ai
COMPOSE_FILE="docker-compose.yml"

echo "========================================="
echo "  ECS 诊断与修复"
echo "========================================="

# ── 1. 确保所有服务在跑 ──────────────────────────────────────
echo ""
echo "--- [1/6] 启动所有服务 ---"
docker compose up -d
sleep 5
docker compose ps

# ── 2. 检查后端 API ──────────────────────────────────────────
echo ""
echo "--- [2/6] 检查后端 API ---"
HEALTH=$(docker exec japan_ai_api python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())" 2>&1)
echo "  Health: $HEALTH"

# 检查 catalog API
CATALOG=$(docker exec japan_ai_api python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/ops/catalog/entities?entity_type=poi&limit=1').read().decode()[:200])" 2>&1)
echo "  Catalog: $CATALOG"

# ── 3. 检查前端环境变量 ──────────────────────────────────────
echo ""
echo "--- [3/6] 检查前端环境变量 ---"
BACKEND_URL=$(docker exec travel-web sh -c 'echo $BACKEND_URL' 2>&1)
echo "  BACKEND_URL=$BACKEND_URL"

# ── 4. 测试前端到后端连通性 ──────────────────────────────────
echo ""
echo "--- [4/6] 测试前端→后端连通性 ---"
FRONTEND_TO_API=$(docker exec travel-web wget -qO- http://api:8000/health 2>&1 || echo "FAILED")
echo "  frontend→api: $FRONTEND_TO_API"

# ── 5. 测试前端 API route ────────────────────────────────────
echo ""
echo "--- [5/6] 测试前端 API route ---"
# 用 node 来测试，因为 wget 可能有问题
FRONTEND_ROUTE=$(docker exec travel-web node -e "
  fetch('http://localhost:3000/api/admin/catalog/entities?entity_type=poi&limit=1')
    .then(r => r.text())
    .then(t => console.log('STATUS OK:', t.substring(0, 200)))
    .catch(e => console.log('ERROR:', e.message))
" 2>&1)
echo "  $FRONTEND_ROUTE"

# 如果 localhost 不行，试 0.0.0.0
if echo "$FRONTEND_ROUTE" | grep -q "ERROR"; then
  echo "  localhost 失败，尝试 0.0.0.0..."
  FRONTEND_ROUTE2=$(docker exec travel-web node -e "
    fetch('http://0.0.0.0:3000/api/admin/catalog/entities?entity_type=poi&limit=1')
      .then(r => r.text())
      .then(t => console.log('STATUS OK:', t.substring(0, 200)))
      .catch(e => console.log('ERROR:', e.message))
  " 2>&1)
  echo "  $FRONTEND_ROUTE2"
fi

# ── 6. 测试 nginx → 前端 → 后端 完整链路 ─────────────────────
echo ""
echo "--- [6/6] 测试完整链路 (nginx→frontend→api) ---"
FULL_CHAIN=$(docker exec japan_ai_nginx wget -qO- "http://frontend:3000/api/admin/catalog/entities?entity_type=poi&limit=1" 2>&1 || echo "FAILED: $?")
echo "  $FULL_CHAIN"

echo ""
echo "========================================="
echo "  诊断完成"
echo "========================================="
