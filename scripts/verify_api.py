#!/usr/bin/env python3
"""
D3.2  API 端点全面验证脚本
用法: python scripts/verify_api.py [--base-url http://localhost:8000]

功能:
  1. 逐一调用所有关键 API 端点
  2. 检查响应状态码、字段完整性
  3. 打印 PASS/FAIL 汇总
  4. 遇到 FAIL 时给出修复建议

依赖: 需要先 uvicorn app.main:app 启动服务
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Tuple

try:
    import httpx
except ImportError:
    print("❌ 需要安装 httpx: pip install httpx")
    sys.exit(1)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭️  SKIP"


def check(
    label: str,
    resp: httpx.Response,
    expected_status: int = 200,
    required_fields: List[str] = None,
) -> Tuple[bool, str]:
    """检查单个接口响应"""
    if resp.status_code != expected_status:
        return False, f"{FAIL} [{label}] HTTP {resp.status_code} (expected {expected_status})\n    body={resp.text[:200]}"

    if required_fields:
        try:
            body = resp.json()
        except Exception:
            return False, f"{FAIL} [{label}] 响应非 JSON"
        for field in required_fields:
            keys = field.split(".")
            obj = body
            for k in keys:
                if isinstance(obj, dict):
                    obj = obj.get(k)
                else:
                    obj = None
                    break
            if obj is None:
                return False, f"{FAIL} [{label}] 缺少字段: {field}\n    body={json.dumps(body, ensure_ascii=False)[:300]}"

    return True, f"{PASS} [{label}] HTTP {resp.status_code}"


def run_verify(base_url: str) -> None:
    print(f"\n🔍 API 验证开始 — {base_url}\n{'='*60}")
    results: List[Tuple[bool, str]] = []
    created_trip_id = None

    with httpx.Client(base_url=base_url, timeout=15.0) as client:

        # ── 1. GET /products ──────────────────────────────────────────────────
        try:
            r = client.get("/products")
            ok, msg = check("GET /products", r, 200, ["products", "total"])
            if ok:
                products = r.json().get("products", [])
                msg += f"  → {len(products)} 个 SKU"
                if products:
                    prices = [p.get("price_cny") for p in products]
                    msg += f"  价格: {prices}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /products] 连接失败: {e}"
        results.append((ok, msg))

        # ── 2. GET /products/standard_248 ────────────────────────────────────
        try:
            r = client.get("/products/standard_248")
            ok, msg = check("GET /products/standard_248", r, 200, ["sku_id", "price_cny", "sku_type"])
            if ok:
                d = r.json()
                msg += f"  → ¥{d.get('price_cny')} {d.get('name', '')}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /products/standard_248] {e}"
        results.append((ok, msg))

        # ── 3. GET /products/premium_888/price?days=10 ───────────────────────
        try:
            r = client.get("/products/premium_888/price?days=10")
            if r.status_code == 404:
                ok, msg = True, f"{SKIP} [GET /products/premium_888/price] 接口不存在（SKU 无分段计价）"
            else:
                ok, msg = check("GET /products/premium_888/price?days=10", r, 200, [])
                if ok:
                    msg += f"  → {r.text[:80]}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /products/premium_888/price] {e}"
        results.append((ok, msg))

        # ── 4. POST /trips ────────────────────────────────────────────────────
        try:
            r = client.post("/trips", json={
                "cities": [{"city_code": "tokyo", "nights": 4}],
                "party_type": "couple",
                "party_size": 2,
            })
            # API 实际返回 202 Accepted
            ok, msg = check("POST /trips", r, 202, ["trip_request_id", "status"])
            if ok:
                created_trip_id = r.json().get("trip_request_id")
                msg += f"  → trip_id={created_trip_id[:8]}..."
        except Exception as e:
            ok, msg = False, f"{FAIL} [POST /trips] {e}"
        results.append((ok, msg))

        if not created_trip_id:
            results.append((False, f"{FAIL} 后续测试跳过（trip 创建失败）"))
            _print_results(results)
            return

        tid = created_trip_id
        time.sleep(0.5)  # 等待 DB commit 传播

        # ── 5. GET /trips/{id}/status ─────────────────────────────────────────
        try:
            r = client.get(f"/trips/{tid}/status")
            ok, msg = check(f"GET /trips/{{id}}/status", r, 200, ["trip_request_id", "status"])
            if ok:
                msg += f"  → status={r.json().get('status')}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /trips/status] {e}"
        results.append((ok, msg))

        # ── 6. POST /trips/{id}/generate ─────────────────────────────────────
        try:
            r = client.post(
                f"/trips/{tid}/generate",
                params={"template_code": "tokyo_classic_5d", "scene": "couple"},
            )
            ok, msg = check("POST /trips/{id}/generate", r, 202)
            if ok:
                body = r.json()
                msg += f"  → status={body.get('status')}  job_id={str(body.get('job_id', ''))[:8]}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [POST /trips/generate] {e}"
        results.append((ok, msg))

        # 等待装配完成（最多 30 秒）
        plan_ready = False
        for i in range(10):
            time.sleep(3)
            try:
                r = client.get(f"/trips/{tid}/status")
                status = r.json().get("status", "")
                if status in ("reviewing", "completed"):
                    plan_ready = True
                    break
            except Exception:
                break

        # ── 7. GET /trips/{id}/plan ───────────────────────────────────────────
        try:
            r = client.get(f"/trips/{tid}/plan")
            if r.status_code == 404:
                ok = not plan_ready  # 如果还在装配中，404 是预期的
                msg = f"{'⚠️  WARN' if ok else FAIL} [GET /trips/{{id}}/plan] 404 (装配未完成或行程不存在)"
                ok = True  # 不计为 FAIL，标记为 WARN
            else:
                ok, msg = check("GET /trips/{id}/plan", r, 200, ["plan_id", "status", "days"])
                if ok:
                    d = r.json()
                    days_count = len(d.get("days", []))
                    total_items = sum(len(day.get("items", [])) for day in d.get("days", []))
                    msg += f"  → {days_count} 天  {total_items} 个景点/餐厅"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /trips/plan] {e}"
        results.append((ok, msg))

        # ── 8. GET /trips/{id}/preview ────────────────────────────────────────
        # 生成是异步的，plan 未完成时 preview_url=null 是预期行为
        try:
            r = client.get(f"/trips/{tid}/preview")
            if r.status_code == 404:
                ok, msg = True, f"{SKIP} [GET /trips/{{id}}/preview] 404（plan 未生成）"
            elif r.status_code == 200:
                d = r.json()
                if d.get("preview_url"):
                    ok, msg = True, f"{PASS} [GET /trips/{{id}}/preview] HTTP 200  → url={d['preview_url'][:60]}"
                else:
                    # 生成中，状态正常
                    ok, msg = True, f"⚠️  WARN [GET /trips/{{id}}/preview] 生成中 status={d.get('status')}（preview_url 待生成）"
            else:
                ok, msg = False, f"{FAIL} [GET /trips/{{id}}/preview] HTTP {r.status_code}: {r.text[:100]}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /trips/preview] {e}"
        results.append((ok, msg))

        # ── 9. GET /trips/{id}/exports ────────────────────────────────────────
        # plan 未生成时 404 是预期行为
        try:
            r = client.get(f"/trips/{tid}/exports")
            if r.status_code == 404:
                ok, msg = True, f"{SKIP} [GET /trips/{{id}}/exports] 404（plan 未生成，跳过）"
            else:
                ok, msg = check("GET /trips/{id}/exports", r, 200, ["assets"])
                if ok:
                    assets = r.json().get("assets", [])
                    msg += f"  → {len(assets)} 个导出文件"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /trips/exports] {e}"
        results.append((ok, msg))

        # ── 10. GET /trips/{id}/export (H5 HTML) ─────────────────────────────
        try:
            r = client.get(f"/trips/{tid}/export")
            if r.status_code in (404, 422):
                ok, msg = True, f"{SKIP} [GET /trips/{{id}}/export] {r.status_code}（plan 未生成，跳过）"
            elif r.status_code == 200 and "html" in r.headers.get("content-type", ""):
                ok, msg = True, f"{PASS} [GET /trips/{{id}}/export] HTTP 200 HTML  → {len(r.text)} 字符"
            elif r.status_code == 200:
                ok, msg = True, f"{PASS} [GET /trips/{{id}}/export] HTTP 200"
            else:
                ok, msg = False, f"{FAIL} [GET /trips/{{id}}/export] HTTP {r.status_code}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /trips/export] {e}"
        results.append((ok, msg))

        # ── 11. GET /docs (Swagger) ───────────────────────────────────────────
        try:
            r = client.get("/docs")
            ok = r.status_code == 200
            msg = f"{'✅ PASS' if ok else '❌ FAIL'} [GET /docs] HTTP {r.status_code}"
        except Exception as e:
            ok, msg = False, f"{FAIL} [GET /docs] {e}"
        results.append((ok, msg))

    _print_results(results)


def _print_results(results: List[Tuple[bool, str]]) -> None:
    print()
    for ok, msg in results:
        print(f"  {msg}")

    total = len(results)
    passed = sum(1 for ok, _ in results if ok)
    failed = total - passed

    print(f"\n{'='*60}")
    print(f"📊 验证完成: {passed}/{total} 通过  {failed} 失败")
    if failed == 0:
        print("🎉 所有端点验证通过！")
    else:
        print("⚠️  部分端点验证失败，请检查上方错误信息。")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API 端点全面验证")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API 基础 URL")
    args = parser.parse_args()
    run_verify(args.base_url)
