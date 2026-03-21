"""
红黄绿校验引擎 — Validation Engine (M3)

读取 data/config/validation_rules.json，对 DetailForm 数据逐条执行检查，
返回结构化的红黄绿评分结果，用于：
  - 后台人工审核界面展示（M5）
  - 追问话术自动生成（L17）

颜色语义：
  🔴 RED    = 必须追问才能生成（致命缺失或冲突）
  🟡 YELLOW = 建议补充（影响质量但可继续）
  🟢 GREEN  = 通过

端点（在 detail_forms.py 中调用）：
  POST /detail-forms/{form_id}/validate → ValidationResult

独立调用：
  from app.domains.validation.engine import ValidationEngine
  engine = ValidationEngine()
  result = engine.validate(form_data)
"""
from __future__ import annotations

import json
import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent.parent.parent.parent / "data" / "config" / "validation_rules.json"


class RuleColor(str, Enum):
    RED    = "red"
    YELLOW = "yellow"
    GREEN  = "green"


class RuleResult:
    def __init__(
        self,
        rule_id: str,
        color: RuleColor,
        passed: bool,
        message: str,
        follow_up: Optional[str] = None,
        field: Optional[str] = None,
    ):
        self.rule_id   = rule_id
        self.color     = color
        self.passed    = passed
        self.message   = message
        self.follow_up = follow_up
        self.field     = field

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "color": self.color.value,
            "passed": self.passed,
            "message": self.message,
            "follow_up": self.follow_up,
            "field": self.field,
        }


class ValidationResult:
    def __init__(self, form_id: str, results: list[RuleResult]):
        self.form_id = form_id
        self.results = results

    @property
    def red_count(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.color == RuleColor.RED)

    @property
    def yellow_count(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.color == RuleColor.YELLOW)

    @property
    def can_generate(self) -> bool:
        return self.red_count == 0

    @property
    def overall_color(self) -> str:
        if self.red_count > 0:   return "red"
        if self.yellow_count > 0: return "yellow"
        return "green"

    def to_dict(self) -> dict[str, Any]:
        return {
            "form_id": self.form_id,
            "overall": self.overall_color,
            "can_generate": self.can_generate,
            "red_count": self.red_count,
            "yellow_count": self.yellow_count,
            "results": [r.to_dict() for r in self.results],
            "failed": [r.to_dict() for r in self.results if not r.passed],
            "follow_ups": [r.follow_up for r in self.results if not r.passed and r.follow_up],
        }


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    if not _RULES_PATH.exists():
        logger.warning("validation_rules.json not found at %s, using empty rules", _RULES_PATH)
        return {"rules": []}
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


class ValidationEngine:
    """
    规则化校验引擎，无 LLM 依赖。
    """

    def validate(self, form_data: dict[str, Any], form_id: str = "unknown") -> ValidationResult:
        rules_config = _load_rules()
        rules = rules_config.get("rules", [])
        results: list[RuleResult] = []

        for rule in rules:
            rule_id    = rule.get("id", "UNKNOWN")
            color_str  = rule.get("severity", "yellow").lower()
            color      = RuleColor.RED if color_str == "red" else RuleColor.YELLOW
            conditions = rule.get("conditions", [])
            message    = rule.get("message", "")
            follow_up  = rule.get("follow_up_template", "")
            field      = rule.get("field")

            # 逐条 condition 检查（AND 逻辑）
            try:
                passed = self._check_conditions(conditions, form_data)
            except Exception as e:
                logger.warning("Rule %s check error: %s", rule_id, e)
                passed = True  # 规则执行异常不阻断

            results.append(RuleResult(
                rule_id=rule_id,
                color=color,
                passed=passed,
                message=message if not passed else f"✓ {rule.get('pass_message', rule_id)}",
                follow_up=follow_up if not passed else None,
                field=field,
            ))

        return ValidationResult(form_id=form_id, results=results)

    def _check_conditions(
        self,
        conditions: list[dict],
        data: dict[str, Any],
    ) -> bool:
        """
        每条 condition 格式：
          {"field": "cities", "op": "not_empty"}
          {"field": "budget_level", "op": "in", "values": ["budget","mid","premium"]}
          {"field": "duration_days", "op": "gte", "value": 1}
          {"field": "arrival_time", "op": "exists"}
          {"field": "party_type", "op": "eq", "value": "family", "implies_field": "party_ages", "implies_op": "not_empty"}
        全部通过 → rule 通过（passed=True）
        """
        for cond in conditions:
            op    = cond.get("op", "not_empty")
            field = cond.get("field", "")
            val   = self._get_nested(data, field)

            ok = self._eval_op(op, val, cond)
            if not ok:
                return False

            # 隐含检查（当 field == value 时检查 implies_field）
            implies_field = cond.get("implies_field")
            if implies_field and ok:
                implies_op = cond.get("implies_op", "not_empty")
                impl_val = self._get_nested(data, implies_field)
                if not self._eval_op(implies_op, impl_val, {}):
                    return False

        return True

    def _eval_op(self, op: str, val: Any, cond: dict) -> bool:
        if op == "not_empty":
            return bool(val) and val != [] and val != ""
        if op == "empty":
            return not val or val == [] or val == ""
        if op == "exists":
            return val is not None
        if op == "not_exists":
            return val is None
        if op == "eq":
            return val == cond.get("value")
        if op == "neq":
            return val != cond.get("value")
        if op == "in":
            return val in cond.get("values", [])
        if op == "not_in":
            return val not in cond.get("values", [])
        if op == "gte":
            try: return float(val) >= float(cond.get("value", 0))
            except: return False
        if op == "lte":
            try: return float(val) <= float(cond.get("value", 0))
            except: return False
        if op == "gt":
            try: return float(val) > float(cond.get("value", 0))
            except: return False
        if op == "lt":
            try: return float(val) < float(cond.get("value", 0))
            except: return False
        if op == "min_length":
            try: return len(val) >= int(cond.get("value", 0))
            except: return False
        # 未知 op 默认通过
        logger.debug("Unknown validation op: %s", op)
        return True

    @staticmethod
    def _get_nested(data: dict, field: str) -> Any:
        """支持点分路径：'flight_info.arrival_time'"""
        parts = field.split(".")
        cur = data
        for p in parts:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(p)
        return cur
