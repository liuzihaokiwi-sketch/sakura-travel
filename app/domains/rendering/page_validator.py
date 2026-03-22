"""
page_validator.py — 页面级校验（L3-14）

输入：list[PagePlan] + dict[str, PageViewModel]
输出：list[ValidationIssue]

6 条校验规则：
  PAGE_001: 每页必须有明确 page_type（在 PAGE_TYPE_REGISTRY 中存在）
  PAGE_002: required_slots 不得缺失（检查 PageViewModel.sections 是否覆盖）
  PAGE_003: primary_promise 不得和 topic_family 冲突
  PAGE_004: 同类对象不得重复占页（同一 entity_id 不得出现在多个 detail 页）
  PAGE_005: full size 页的对象不得被压成 half
  PAGE_006: print variant 不得 overflow（sections 数量 × 预估高度 ≤ A4 安全高度）

依赖：
  page_planner.PagePlan
  page_view_model.PageViewModel
  page_type_registry.PAGE_TYPE_REGISTRY
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, Optional

from app.domains.rendering.page_planner import PagePlan
from app.domains.rendering.page_type_registry import PAGE_TYPE_REGISTRY
from app.domains.rendering.page_view_model import PageViewModel

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    page_id: str
    rule_code: str                                   # "PAGE_001" ~ "PAGE_006"
    severity: Literal["error", "warning", "info"]
    message: str
    suggestion: Optional[str] = None


# ── 规则常量 ──────────────────────────────────────────────────────────────────

# 大约每个 SectionVM 在 A4 上占用的高度（单位：mm）
_SECTION_HEIGHT_EST: dict[str, float] = {
    "timeline":          60.0,
    "key_reasons":       25.0,
    "stat_strip":        18.0,
    "entity_card":       30.0,
    "risk_card":         20.0,
    "text_block":        20.0,
    "fulfillment_list":  35.0,
    "toc_list":          80.0,
}
_DEFAULT_SECTION_HEIGHT = 25.0

# A4 正文安全高度（去掉页眉 + 页脚约 30mm）
_A4_SAFE_HEIGHT_MM = 240.0
_HALF_SAFE_HEIGHT_MM = 110.0

# detail 页类型（用于 PAGE_004 重复检查）
_DETAIL_PAGE_TYPES = {
    "major_activity_detail",
    "hotel_detail",
    "restaurant_detail",
    "photo_theme_detail",
}


# ── 各规则实现 ────────────────────────────────────────────────────────────────

def _check_page_001(
    page: PagePlan,
    vm: Optional[PageViewModel],
) -> list[ValidationIssue]:
    issues = []
    if page.page_type not in PAGE_TYPE_REGISTRY:
        issues.append(ValidationIssue(
            page_id=page.page_id,
            rule_code="PAGE_001",
            severity="error",
            message=f"page_type '{page.page_type}' 未在 PAGE_TYPE_REGISTRY 中注册",
            suggestion=f"检查 page_type_registry.py，确认 '{page.page_type}' 已注册",
        ))
    return issues


def _check_page_002(
    page: PagePlan,
    vm: Optional[PageViewModel],
) -> list[ValidationIssue]:
    issues = []
    if not vm:
        return issues

    defn = PAGE_TYPE_REGISTRY.get(page.page_type)
    if not defn:
        return issues

    vm_section_types = {s.section_type for s in vm.sections}
    missing = [slot for slot in defn.required_slots if slot not in vm_section_types]

    if missing:
        issues.append(ValidationIssue(
            page_id=page.page_id,
            rule_code="PAGE_002",
            severity="warning",
            message=f"缺少 required_slots: {missing}（页型: {page.page_type}）",
            suggestion="检查 PageViewModelBuilder 对应的 _build_*_vm() 函数是否填充了所有必需 slot",
        ))
    return issues


def _check_page_003(
    page: PagePlan,
    vm: Optional[PageViewModel],
) -> list[ValidationIssue]:
    """
    primary_promise 不得和 topic_family 冲突：
    - frontmatter 页不应 promise "当天执行"
    - daily 页不应 promise "详情解析"
    """
    issues = []
    defn = PAGE_TYPE_REGISTRY.get(page.page_type)
    if not defn:
        return issues

    bad_combos = [
        ("frontmatter", "当天"),
        ("frontmatter", "执行"),
        ("daily", "深度解析"),
        ("daily", "酒店选择"),
    ]
    for family, keyword in bad_combos:
        if defn.topic_family == family and keyword in defn.primary_promise:
            issues.append(ValidationIssue(
                page_id=page.page_id,
                rule_code="PAGE_003",
                severity="warning",
                message=(
                    f"topic_family='{family}' 与 primary_promise 含有 '{keyword}' 可能冲突"
                ),
            ))
    return issues


def _check_page_004(
    pages: list[PagePlan],
) -> list[ValidationIssue]:
    """同一 entity_id 不得出现在多个 detail 页"""
    issues = []
    seen: dict[str, str] = {}  # entity_id → first page_id

    for page in pages:
        if page.page_type not in _DETAIL_PAGE_TYPES:
            continue
        for ref in page.object_refs:
            eid = ref.object_id
            if not eid:
                continue
            if eid in seen:
                issues.append(ValidationIssue(
                    page_id=page.page_id,
                    rule_code="PAGE_004",
                    severity="error",
                    message=(
                        f"entity '{eid}' 重复出现在 detail 页 "
                        f"'{seen[eid]}' 和 '{page.page_id}'"
                    ),
                    suggestion="检查 PagePlanner 的 assigned_detail_entity_ids 集合是否正确传递",
                ))
            else:
                seen[eid] = page.page_id

    return issues


def _check_page_005(
    page: PagePlan,
    vm: Optional[PageViewModel],
) -> list[ValidationIssue]:
    """
    full size 页的 required_slots 如果 > 3 个，而实际 page_size 是 half，
    则说明被不合理压缩。
    """
    issues = []
    defn = PAGE_TYPE_REGISTRY.get(page.page_type)
    if not defn:
        return issues

    if defn.default_size == "full" and page.page_size == "half":
        if len(defn.required_slots) > 3:
            issues.append(ValidationIssue(
                page_id=page.page_id,
                rule_code="PAGE_005",
                severity="warning",
                message=(
                    f"页型 '{page.page_type}' 默认 full，"
                    f"但被设为 half（required_slots={defn.required_slots}）"
                ),
                suggestion="检查 _trim_to_budget() 是否过度裁剪了此页",
            ))
    return issues


def _check_page_006(
    page: PagePlan,
    vm: Optional[PageViewModel],
) -> list[ValidationIssue]:
    """sections 总高度不超过 A4 安全高度"""
    issues = []
    if not vm:
        return issues

    safe_height = _HALF_SAFE_HEIGHT_MM if page.page_size == "half" else _A4_SAFE_HEIGHT_MM
    total_height = sum(
        _SECTION_HEIGHT_EST.get(s.section_type, _DEFAULT_SECTION_HEIGHT)
        for s in vm.sections
    )

    if total_height > safe_height:
        issues.append(ValidationIssue(
            page_id=page.page_id,
            rule_code="PAGE_006",
            severity="warning",
            message=(
                f"预估内容高度 {total_height:.1f}mm 超出安全区 {safe_height}mm"
                f"（页型: {page.page_type}, size: {page.page_size}）"
            ),
            suggestion="减少 optional_slots 数量，或将部分内容移入下一页",
        ))
    return issues


# ── 主函数 ────────────────────────────────────────────────────────────────────

def validate_page_plan(
    pages: list[PagePlan],
    view_models: dict[str, PageViewModel],
) -> list[ValidationIssue]:
    """
    对 page_plan + view_models 执行全部 6 条校验规则。

    Args:
        pages:        PagePlanner 输出的页面计划列表
        view_models:  PageViewModelBuilder 输出的 page_id → PageViewModel 字典

    Returns:
        ValidationIssue 列表，severity=error 表示阻断，warning 表示需人工确认
    """
    issues: list[ValidationIssue] = []

    # PAGE_004 需要全局视角，先单独运行
    issues.extend(_check_page_004(pages))

    for page in pages:
        vm = view_models.get(page.page_id)

        issues.extend(_check_page_001(page, vm))
        issues.extend(_check_page_002(page, vm))
        issues.extend(_check_page_003(page, vm))
        issues.extend(_check_page_005(page, vm))
        issues.extend(_check_page_006(page, vm))

    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")

    if issues:
        logger.info(
            "[PageValidator] 校验完成: %d pages, %d errors, %d warnings",
            len(pages), error_count, warning_count,
        )
    else:
        logger.info("[PageValidator] 校验通过: %d pages, no issues", len(pages))

    return issues
