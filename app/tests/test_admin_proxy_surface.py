from __future__ import annotations

from pathlib import Path


def test_admin_trace_pages_use_unified_next_proxy_surface():
    trace_list = Path("web/app/admin/trace/page.tsx").read_text(encoding="utf-8")
    trace_detail = Path("web/app/admin/trace/[runId]/page.tsx").read_text(encoding="utf-8")
    trace_route = Path("web/app/api/admin/trace/route.ts").read_text(encoding="utf-8")
    trace_detail_route = Path("web/app/api/admin/trace/[runId]/route.ts").read_text(encoding="utf-8")
    evals_page = Path("web/app/admin/evals/page.tsx").read_text(encoding="utf-8")
    evals_route = Path("web/app/api/admin/evals/runs/route.ts").read_text(encoding="utf-8")

    assert "/api/admin/trace?limit=50" in trace_list
    assert "/api/admin/trace/${run.run_id}" in trace_list
    assert "/api/admin/trace/${params.runId}" in trace_detail
    assert "/api/admin/evals/runs" in evals_page
    assert "NextResponse.json" in trace_route
    assert "NextResponse.json" in trace_detail_route
    assert "NextResponse.json" in evals_route


def test_admin_operator_actions_are_unified_via_review_surface():
    admin_api = Path("web/lib/admin-api.ts").read_text(encoding="utf-8")
    order_page = Path("web/app/admin/order/[id]/page.tsx").read_text(encoding="utf-8")

    assert 'export type OperatorAction = "publish" | "reject" | "edit" | "writeback"' in admin_api
    assert "performOperatorAction" in admin_api
    assert "publishOrder(orderId)" in order_page
    assert "rejectOrder(orderId)" in order_page
