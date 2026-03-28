"""
多模型评审流水线（Multi-Agent Review Pipeline）

在行程装配完成后、人工审核前自动执行 6 角色链式评审。
步骤 2-5 可并行（asyncio.gather），步骤 6 等全部完成后裁决。

角色：
  1. Planner    — 城市圈决策链 + page pipeline，不在此模块
  2. QA Checker — hard_fail / soft_fail 检查
  3. User Proxy — 客群视角 satisfaction_score + complaints
  4. Ops Proxy  — 执行风险检查（预约/定休/交通/天气）
  5. Tuning Guard — 判断可微调 / 不可微调模块
  6. Final Judge — 综合裁决 publish / rewrite / human

rewrite 最多 2 轮，第 3 轮自动转人工。
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── 枚举与数据结构 ─────────────────────────────────────────────────────────────

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HARD_FAIL = "hard_fail"
    SOFT_FAIL = "soft_fail"
    CRITICAL = "critical"


class Verdict(str, Enum):
    PUBLISH = "publish"
    REWRITE = "rewrite"
    HUMAN = "human"


@dataclass
class ReviewIssue:
    """评审发现的单个问题"""
    agent: str            # 哪个 agent 报的
    severity: str         # hard_fail / soft_fail / warning / info / critical
    category: str         # 问题类型（time_conflict / missing_meal / etc）
    day: int | None       # 第几天（None = 全局问题）
    entity_id: str | None # 相关实体
    description: str      # 问题描述
    fix_suggestion: str   # 修复建议
    auto_fixable: bool    # 是否可自动修复


@dataclass
class AgentResult:
    """单个 Agent 的执行结果"""
    agent_name: str
    raw_output: dict[str, Any]
    issues: list[ReviewIssue]
    score: float | None = None          # User Proxy 才有
    token_usage: int = 0
    duration_ms: int = 0
    error: str | None = None


@dataclass
class PipelineResult:
    """整条 Pipeline 的执行结果"""
    plan_id: str
    round_number: int
    qa_result: AgentResult
    user_proxy_result: AgentResult
    ops_proxy_result: AgentResult
    tuning_guard_result: AgentResult
    final_verdict: Verdict
    final_reason: str
    total_tokens: int = 0
    total_duration_ms: int = 0


MAX_REWRITE_ROUNDS = 2


# ── Agent 基类 ─────────────────────────────────────────────────────────────────

class ReviewAgent:
    """评审 Agent 基类"""

    name: str = "base"
    model: str = "gpt-4o-mini"

    async def review(
        self,
        plan_json: dict[str, Any],
        context: dict[str, Any],
        ai_client: Any = None,
    ) -> AgentResult:
        raise NotImplementedError


# ── QA Checker ─────────────────────────────────────────────────────────────────

QA_SYSTEM_PROMPT = """你是一个日本旅行攻略的质量检查员（QA）。你需要检查行程计划的结构性问题。

检查项（按严重程度）：

**hard_fail（必须修复）：**
1. 某天没有午餐安排（11:00-14:00 之间无餐厅）
2. 某天没有晚餐安排（17:00-20:00 之间无餐厅）
3. 同一实体在行程中出现两次
4. 时间线冲突（两个活动时间重叠）
5. 实体在安排的日期/时段不营业（如周一安排了周一闭馆的博物馆）
6. 交通不可达（相邻景点间无合理交通方式）

**soft_fail（建议修复）：**
1. 某天步行总距离超过 15km
2. 某天安排超过 6 个景点（节奏太赶）
3. 连续两天去同一个区域（缺乏新鲜感）
4. 全程没有日本料理推荐
5. 某天的第一个景点和酒店不在同一区域（通勤太远）

输出格式（JSON）：
{
  "issues": [
    {
      "severity": "hard_fail" | "soft_fail",
      "category": "missing_meal" | "duplicate_entity" | "time_conflict" | "closed_entity" | "unreachable" | "overloaded_day" | "long_walk" | "repetitive_area" | "no_washoku" | "far_start",
      "day": 2,
      "entity_id": "xxx" | null,
      "description": "Day 2 没有午餐安排",
      "fix_suggestion": "在 12:00 插入一个附近的餐厅",
      "auto_fixable": true
    }
  ],
  "summary": "发现 X 个 hard_fail，Y 个 soft_fail"
}"""


class QAChecker(ReviewAgent):
    name = "qa_checker"
    model = "gpt-4o-mini"

    async def review(self, plan_json, context, ai_client=None):
        start = time.monotonic()
        prompt = self._build_prompt(plan_json, context)

        if ai_client is None:
            return self._mock_result()

        try:
            resp = await ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": QA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content
            tokens = resp.usage.total_tokens if resp.usage else 0
            return self._parse(content, tokens, time.monotonic() - start)
        except Exception as e:
            logger.error("QA Checker failed: %s", e)
            return AgentResult(
                agent_name=self.name, raw_output={}, issues=[],
                error=str(e), duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _build_prompt(self, plan_json, context):
        # 提取关键信息，控制 token
        days_summary = []
        for day in plan_json.get("days", []):
            items = []
            for item in day.get("items", []):
                items.append(f"  {item.get('time', '??:??')} {item.get('name', '未知')} ({item.get('entity_type', 'poi')})")
            days_summary.append(f"Day {day.get('day_number', '?')} ({day.get('city', '')}):\n" + "\n".join(items))

        operational_ctx = context.get("operational_context", "无")

        return f"""请检查以下行程计划的质量问题：

{chr(10).join(days_summary)}

城市上下文：
- 定休日信息：{operational_ctx}

请按照系统提示中的检查项逐一检查，输出 JSON。"""

    def _parse(self, content, tokens, elapsed):
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"issues": []}

        issues = []
        for raw in data.get("issues", []):
            issues.append(ReviewIssue(
                agent=self.name,
                severity=raw.get("severity", "soft_fail"),
                category=raw.get("category", "unknown"),
                day=raw.get("day"),
                entity_id=raw.get("entity_id"),
                description=raw.get("description", ""),
                fix_suggestion=raw.get("fix_suggestion", ""),
                auto_fixable=raw.get("auto_fixable", False),
            ))

        return AgentResult(
            agent_name=self.name, raw_output=data, issues=issues,
            token_usage=tokens, duration_ms=int(elapsed * 1000),
        )

    def _mock_result(self):
        return AgentResult(agent_name=self.name, raw_output={}, issues=[], error="no ai_client")


# ── User Proxy ─────────────────────────────────────────────────────────────────

USER_PROXY_PROMPTS = {
    "couple": """你是一对即将去日本蜜月旅行的情侣中的一位。你会特别关注：
- 有没有浪漫氛围的场景（日落、夜景、私密感）
- 出片点够不够（朋友圈/小红书能发的照片）
- 节奏是否太赶（情侣旅行不想暴走）
- 晚上有没有有情调的活动（居酒屋/酒吧/夜景）
- 餐厅是否适合约会""",

    "besties": """你是一群闺蜜中的一位，和 2-3 个好朋友一起去日本玩。你会特别关注：
- 有没有闺蜜合照的场景（和服体验/花园/咖啡厅）
- 美食推荐是否丰富多样（不想只吃拉面）
- 夜间活动是否精彩（居酒屋/酒吧/购物）
- 购物时间是否充足
- 有没有可以一起体验的活动""",

    "parents": """你是一位带父母（60+岁）去日本旅行的子女。你会特别关注：
- 节奏是否太赶（老人走不动太多路）
- 有没有无障碍设施（扶梯/电梯/平坦的路）
- 餐厅是否适合老人口味（不全是生冷食物）
- 休息时间够不够（下午是否有喘口气的安排）
- 交通是否需要太多步行/换乘""",

    "first_time_fit": """你是第一次去日本的游客，对日本不太了解。你会特别关注：
- 是否涵盖了经典必去景点（浅草寺/东京塔/清水寺等）
- 交通指引是否足够清晰（怎么坐车/买什么卡）
- 有没有让人安心的确定感（不会到了发现关门/排长队）
- 餐厅推荐是否有具体推荐菜品
- 有没有容易踩的坑被提前避免""",

    "family_child": """你是一位带小孩（3-10岁）去日本旅行的家长。你会特别关注：
- 有没有适合孩子的景点（公园/水族馆/互动体验）
- 餐厅是否有儿童餐/儿童椅
- 步行距离是否对孩子友好
- 有没有太晚的夜间活动（孩子要早睡）
- 是否有安全隐患（人多拥挤的地方）""",

    "friends_small_group": """你是一群朋友（3-5人）中的一位，一起去日本旅行。你会特别关注：
- 活动是否有趣多样（不全是逛神社）
- 晚上有没有可以一起喝酒聊天的地方
- 有没有可以一起体验的团体活动
- 餐厅座位是否能容纳一群人
- 费用是否合理""",
}

USER_PROXY_SYSTEM = """你是一位即将出发的旅行者。请以第一人称视角评估这份行程计划，给出你的真实感受。

输出格式（JSON）：
{
  "satisfaction_score": 1-10,
  "overall_feel": "一段话描述整体感受",
  "complaints": [
    {
      "day": 2,
      "description": "Day 2 节奏太赶了，6 个景点走不完",
      "fix_suggestion": "删掉 1-2 个景点，加入下午茶时间"
    }
  ],
  "highlights": ["Day 3 的日落时间点安排得很好"]
}"""


class UserProxy(ReviewAgent):
    name = "user_proxy"
    model = "gpt-4o"  # User Proxy 用强模型

    async def review(self, plan_json, context, ai_client=None):
        start = time.monotonic()
        segment = context.get("segment", "first_time_fit")
        persona = USER_PROXY_PROMPTS.get(segment, USER_PROXY_PROMPTS["first_time_fit"])

        if ai_client is None:
            return self._mock_result()

        prompt = self._build_prompt(plan_json, persona)
        try:
            resp = await ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": USER_PROXY_SYSTEM + "\n\n" + persona},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=1200,
            )
            content = resp.choices[0].message.content
            tokens = resp.usage.total_tokens if resp.usage else 0
            return self._parse(content, tokens, time.monotonic() - start)
        except Exception as e:
            logger.error("User Proxy failed: %s", e)
            return AgentResult(
                agent_name=self.name, raw_output={}, issues=[], score=5.0,
                error=str(e), duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _build_prompt(self, plan_json, persona):
        days_text = []
        for day in plan_json.get("days", []):
            items_text = []
            for item in day.get("items", []):
                line = f"  {item.get('time', '')} {item.get('name', '未知')}"
                reason = item.get("recommendation_reason", "")
                if reason:
                    line += f" — {reason}"
                items_text.append(line)
            days_text.append(
                f"Day {day.get('day_number', '?')} {day.get('theme', '')}:\n" + "\n".join(items_text)
            )

        return f"""请以你的视角评估这份行程：

{chr(10).join(days_text)}

总天数：{len(plan_json.get('days', []))} 天
请输出 JSON 格式的评估结果。"""

    def _parse(self, content, tokens, elapsed):
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"satisfaction_score": 5, "complaints": []}

        score = float(data.get("satisfaction_score", 5))
        issues = []
        for c in data.get("complaints", []):
            issues.append(ReviewIssue(
                agent=self.name,
                severity="soft_fail" if score >= 5 else "hard_fail",
                category="user_complaint",
                day=c.get("day"),
                entity_id=None,
                description=c.get("description", ""),
                fix_suggestion=c.get("fix_suggestion", ""),
                auto_fixable=False,
            ))

        return AgentResult(
            agent_name=self.name, raw_output=data, issues=issues,
            score=score, token_usage=tokens, duration_ms=int(elapsed * 1000),
        )

    def _mock_result(self):
        return AgentResult(agent_name=self.name, raw_output={}, issues=[], score=7.0, error="no ai_client")


# ── Ops Proxy ──────────────────────────────────────────────────────────────────

OPS_SYSTEM_PROMPT = """你是一个日本旅行运营专家，负责检查行程的执行可行性风险。

你要检查的风险类型：
1. **预约风险**：需要预约但没提醒的景点/餐厅
2. **定休日风险**：安排在定休日的实体
3. **排队风险**：高峰期去热门景点可能排队 > 1 小时
4. **交通末班车风险**：晚间活动后是否能赶上末班电车
5. **季节性风险**：季节限定活动/樱花/红叶期间人流影响
6. **天气风险**：全天室外行程无雨天备案

输出格式（JSON）：
{
  "ops_issues": [
    {
      "severity": "critical" | "warning" | "info",
      "category": "reservation_needed" | "closed_day" | "queue_risk" | "last_train" | "seasonal_crowd" | "weather_risk",
      "day": 3,
      "entity_id": "xxx",
      "description": "TeamLab Borderless 周一-周三闭馆，但 Day 3 是周二",
      "fix_suggestion": "移到 Day 4（周五）或替换为 teamLab Planets",
      "has_alternative": true
    }
  ],
  "summary": "发现 X 个 critical，Y 个 warning"
}"""


class OpsProxy(ReviewAgent):
    name = "ops_proxy"
    model = "gpt-4o-mini"

    async def review(self, plan_json, context, ai_client=None):
        start = time.monotonic()

        if ai_client is None:
            return self._mock_result()

        prompt = self._build_prompt(plan_json, context)
        try:
            resp = await ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": OPS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1200,
            )
            content = resp.choices[0].message.content
            tokens = resp.usage.total_tokens if resp.usage else 0
            return self._parse(content, tokens, time.monotonic() - start)
        except Exception as e:
            logger.error("Ops Proxy failed: %s", e)
            return AgentResult(
                agent_name=self.name, raw_output={}, issues=[],
                error=str(e), duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _build_prompt(self, plan_json, context):
        days_text = []
        for day in plan_json.get("days", []):
            items = []
            for item in day.get("items", []):
                line = f"  {item.get('time', '')} {item.get('name', '未知')} ({item.get('entity_type', '')})"
                items.append(line)
            day_of_week = day.get("day_of_week", "未知")
            days_text.append(
                f"Day {day.get('day_number', '?')} ({day_of_week}):\n" + "\n".join(items)
            )

        operational = context.get("operational_context", "无已知营业限制")
        seasonal = context.get("seasonal_events", "无已知季节活动")
        travel_date = context.get("travel_date", "未知")

        return f"""请检查以下行程的执行可行性风险：

旅行日期：{travel_date}

{chr(10).join(days_text)}

已知营业限制：
{operational}

季节活动信息：
{seasonal}

请输出 JSON 格式的风险评估。"""

    def _parse(self, content, tokens, elapsed):
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"ops_issues": []}

        issues = []
        for raw in data.get("ops_issues", []):
            issues.append(ReviewIssue(
                agent=self.name,
                severity=raw.get("severity", "warning"),
                category=raw.get("category", "unknown"),
                day=raw.get("day"),
                entity_id=raw.get("entity_id"),
                description=raw.get("description", ""),
                fix_suggestion=raw.get("fix_suggestion", ""),
                auto_fixable=raw.get("has_alternative", False),
            ))

        return AgentResult(
            agent_name=self.name, raw_output=data, issues=issues,
            token_usage=tokens, duration_ms=int(elapsed * 1000),
        )

    def _mock_result(self):
        return AgentResult(agent_name=self.name, raw_output={}, issues=[], error="no ai_client")


# ── Tuning Guard ───────────────────────────────────────────────────────────────

TUNING_SYSTEM_PROMPT = """你是一个行程微调可行性评估员。你需要判断行程中哪些模块可以开放给用户自助微调，哪些必须锁定。

可微调模块（用户可自助替换，不消耗正式修改次数）：
- 景点替换：用同区域同类型的候选替换
- 餐厅替换：用同时段同区域的候选替换
- 夜间方案切换：开启/关闭夜间活动
- 节奏调整：轻松/充实模式切换

不可微调模块（需消耗正式修改次数）：
- 城市顺序变更
- 天数增减
- 整天行程重做
- 交通方式变更

你需要判断当前行程中具体哪些条目可微调，输出列表。

输出格式（JSON）：
{
  "tunable_modules": [
    {"day": 2, "item_index": 3, "name": "明治神宫", "type": "poi", "reason": "同区域有 4 个候选景点可替换"}
  ],
  "locked_modules": [
    {"day": 1, "item_index": 0, "name": "浅草寺", "type": "poi", "reason": "经典必去，不建议替换"}
  ],
  "tunable_count": 8,
  "summary": "共 12 个安排项，8 个可微调，4 个建议锁定"
}"""


class TuningGuard(ReviewAgent):
    name = "tuning_guard"
    model = "gpt-4o-mini"

    async def review(self, plan_json, context, ai_client=None):
        start = time.monotonic()

        if ai_client is None:
            return self._mock_result()

        prompt = self._build_prompt(plan_json)
        try:
            resp = await ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TUNING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content
            tokens = resp.usage.total_tokens if resp.usage else 0
            return self._parse(content, tokens, time.monotonic() - start)
        except Exception as e:
            logger.error("Tuning Guard failed: %s", e)
            return AgentResult(
                agent_name=self.name, raw_output={}, issues=[],
                error=str(e), duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _build_prompt(self, plan_json):
        days_text = []
        for day in plan_json.get("days", []):
            items = []
            for i, item in enumerate(day.get("items", [])):
                items.append(f"  [{i}] {item.get('time', '')} {item.get('name', '未知')} ({item.get('entity_type', '')})")
            days_text.append(f"Day {day.get('day_number', '?')}:\n" + "\n".join(items))

        return f"""请判断以下行程中哪些可以开放自助微调：

{chr(10).join(days_text)}

请输出 JSON 格式。"""

    def _parse(self, content, tokens, elapsed):
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"tunable_modules": [], "locked_modules": []}

        tunable_count = data.get("tunable_count", len(data.get("tunable_modules", [])))
        issues = []
        if tunable_count < 2:
            issues.append(ReviewIssue(
                agent=self.name,
                severity="warning",
                category="low_tunability",
                day=None, entity_id=None,
                description=f"可微调模块仅 {tunable_count} 个，用户自助体验受限",
                fix_suggestion="增加可替换的候选实体",
                auto_fixable=False,
            ))

        return AgentResult(
            agent_name=self.name, raw_output=data, issues=issues,
            token_usage=tokens, duration_ms=int(elapsed * 1000),
        )

    def _mock_result(self):
        return AgentResult(agent_name=self.name, raw_output={"tunable_count": 5}, issues=[], error="no ai_client")


# ── Final Judge ────────────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """你是一个日本旅行产品的最终质量裁决员。你收到了 4 个评审 Agent 的结果，需要做出最终裁决。

裁决选项：
- **publish**：行程质量达标，可以直接发布给用户
- **rewrite**：存在可自动修复的问题，系统应重写受影响的天
- **human**：存在需要人工判断的问题，转人工审核

裁决规则：
1. 如果 QA 有 ≥1 hard_fail → 优先 rewrite（如果 auto_fixable）否则 human
2. 如果 User Proxy score < 5 → rewrite
3. 如果 User Proxy score < 3 → human
4. 如果 Ops 有 ≥2 critical 且无替代方案 → human
5. 如果 Tuning 可微调点 < 2 → rewrite（需要增加候选）
6. 其他情况 → publish

输出格式（JSON）：
{
  "verdict": "publish" | "rewrite" | "human",
  "reason": "一段话说明裁决理由",
  "rewrite_targets": [{"day": 2, "reason": "缺午餐"}],
  "priority_issues": ["最需要关注的问题"]
}"""


class FinalJudge(ReviewAgent):
    name = "final_judge"
    model = "gpt-4o-mini"

    async def review(self, plan_json, context, ai_client=None):
        """
        Final Judge 的 review 方法不同：context 中必须包含其他 4 个 agent 的结果。
        """
        start = time.monotonic()

        qa = context.get("qa_result", {})
        user = context.get("user_proxy_result", {})
        ops = context.get("ops_proxy_result", {})
        tuning = context.get("tuning_guard_result", {})
        round_num = context.get("round_number", 1)

        # 如果已经重写 2 轮还有问题，直接转人工
        if round_num > MAX_REWRITE_ROUNDS:
            return AgentResult(
                agent_name=self.name,
                raw_output={"verdict": "human", "reason": f"已重写 {round_num - 1} 轮仍有问题，转人工"},
                issues=[],
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        if ai_client is None:
            return self._rule_based_judge(qa, user, ops, tuning, round_num, start)

        prompt = self._build_prompt(qa, user, ops, tuning, round_num)
        try:
            resp = await ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=800,
            )
            content = resp.choices[0].message.content
            tokens = resp.usage.total_tokens if resp.usage else 0
            return self._parse(content, tokens, time.monotonic() - start)
        except Exception as e:
            logger.error("Final Judge LLM failed, falling back to rule-based: %s", e)
            return self._rule_based_judge(qa, user, ops, tuning, round_num, start)

    def _rule_based_judge(self, qa, user, ops, tuning, round_num, start):
        """规则引擎兜底裁决（不依赖 LLM）"""
        qa_issues = qa.get("issues", []) if isinstance(qa, dict) else []
        user_score = user.get("score", 7.0) if isinstance(user, dict) else 7.0
        ops_issues = ops.get("issues", []) if isinstance(ops, dict) else []
        tunable_count = tuning.get("raw_output", {}).get("tunable_count", 5) if isinstance(tuning, dict) else 5

        hard_fails = sum(1 for i in qa_issues if getattr(i, "severity", i.get("severity", "")) == "hard_fail")
        critical_ops = sum(1 for i in ops_issues if getattr(i, "severity", i.get("severity", "")) == "critical")

        if hard_fails >= 3 or (isinstance(user_score, (int, float)) and user_score < 3):
            verdict = "human"
            reason = f"严重问题过多（{hard_fails} hard_fail, user_score={user_score}）"
        elif hard_fails >= 1 or (isinstance(user_score, (int, float)) and user_score < 5):
            verdict = "rewrite"
            reason = f"需要修复（{hard_fails} hard_fail, user_score={user_score}）"
        elif critical_ops >= 2:
            verdict = "human"
            reason = f"执行风险高（{critical_ops} critical ops issues）"
        elif isinstance(tunable_count, (int, float)) and tunable_count < 2:
            verdict = "rewrite"
            reason = f"可微调点不足（{tunable_count}）"
        else:
            verdict = "publish"
            reason = "质量达标"

        return AgentResult(
            agent_name=self.name,
            raw_output={"verdict": verdict, "reason": reason, "method": "rule_based"},
            issues=[],
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    def _build_prompt(self, qa, user, ops, tuning, round_num):
        import json

        def _safe_dump(obj):
            if hasattr(obj, "__dict__"):
                return json.dumps(obj.__dict__, ensure_ascii=False, default=str)
            return json.dumps(obj, ensure_ascii=False, default=str)

        return f"""这是第 {round_num} 轮评审。请综合以下 4 个 Agent 的结果做出裁决：

## QA Checker 结果
{_safe_dump(qa)}

## User Proxy 结果
{_safe_dump(user)}

## Ops Proxy 结果
{_safe_dump(ops)}

## Tuning Guard 结果
{_safe_dump(tuning)}

请输出 JSON 裁决。"""

    def _parse(self, content, tokens, elapsed):
        import json
        try:
            data = json.loads(content)
        except Exception:
            data = {"verdict": "human", "reason": "解析失败"}

        return AgentResult(
            agent_name=self.name, raw_output=data, issues=[],
            token_usage=tokens, duration_ms=int(elapsed * 1000),
        )

    def _mock_result(self):
        return AgentResult(
            agent_name=self.name,
            raw_output={"verdict": "publish", "reason": "mock"},
            issues=[], error="no ai_client",
        )


# ── Pipeline 主函数 ────────────────────────────────────────────────────────────

async def run_review_pipeline(
    plan_json: dict[str, Any],
    context: dict[str, Any],
    ai_client: Any = None,
    round_number: int = 1,
) -> PipelineResult:
    """
    执行一轮完整评审。

    Args:
        plan_json: 行程 JSON（包含 days / items / metadata）
        context: 上下文信息（segment / operational_context / seasonal_events / travel_date）
        ai_client: OpenAI AsyncClient
        round_number: 第几轮（1=首次，2=第一次重写后...）

    Returns:
        PipelineResult
    """
    plan_id = str(plan_json.get("plan_id", "unknown"))
    logger.info("Review pipeline round %d starting for plan %s", round_number, plan_id)
    start = time.monotonic()

    # Step 1: 并行执行 QA + User Proxy + Ops Proxy + Tuning Guard
    qa = QAChecker()
    user_proxy = UserProxy()
    ops_proxy = OpsProxy()
    tuning_guard = TuningGuard()

    qa_result, user_result, ops_result, tuning_result = await asyncio.gather(
        qa.review(plan_json, context, ai_client),
        user_proxy.review(plan_json, context, ai_client),
        ops_proxy.review(plan_json, context, ai_client),
        tuning_guard.review(plan_json, context, ai_client),
    )

    # Step 2: Final Judge（需要前 4 步的结果）
    judge_context = {
        **context,
        "qa_result": qa_result.raw_output,
        "user_proxy_result": {"score": user_result.score, "issues": [i.__dict__ for i in user_result.issues]},
        "ops_proxy_result": {"issues": [i.__dict__ for i in ops_result.issues]},
        "tuning_guard_result": tuning_result.raw_output,
        "round_number": round_number,
    }
    judge = FinalJudge()
    judge_result = await judge.review(plan_json, judge_context, ai_client)

    # 提取裁决
    verdict_str = judge_result.raw_output.get("verdict", "human")
    try:
        verdict = Verdict(verdict_str)
    except ValueError:
        verdict = Verdict.HUMAN

    total_tokens = sum(r.token_usage for r in [qa_result, user_result, ops_result, tuning_result, judge_result])
    total_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "Review pipeline round %d complete: verdict=%s, tokens=%d, duration=%dms",
        round_number, verdict.value, total_tokens, total_ms,
    )

    return PipelineResult(
        plan_id=plan_id,
        round_number=round_number,
        qa_result=qa_result,
        user_proxy_result=user_result,
        ops_proxy_result=ops_result,
        tuning_guard_result=tuning_result,
        final_verdict=verdict,
        final_reason=judge_result.raw_output.get("reason", ""),
        total_tokens=total_tokens,
        total_duration_ms=total_ms,
    )


async def run_review_with_retry(
    plan_json: dict[str, Any],
    context: dict[str, Any],
    ai_client: Any = None,
    rewrite_callback: Any = None,
) -> PipelineResult:
    """
    执行评审 + 自动重写循环。

    Args:
        plan_json: 行程 JSON
        context: 上下文
        ai_client: OpenAI client
        rewrite_callback: async 函数，接收 (plan_json, rewrite_targets) → 新 plan_json
                         如果为 None，rewrite 等同于 human

    Returns:
        最终的 PipelineResult
    """
    current_plan = plan_json

    for round_num in range(1, MAX_REWRITE_ROUNDS + 2):
        result = await run_review_pipeline(current_plan, context, ai_client, round_num)

        if result.final_verdict == Verdict.PUBLISH:
            logger.info("Plan %s published after round %d", result.plan_id, round_num)
            return result

        if result.final_verdict == Verdict.HUMAN:
            logger.info("Plan %s sent to human review after round %d", result.plan_id, round_num)
            return result

        # REWRITE
        if result.final_verdict == Verdict.REWRITE:
            if rewrite_callback is None:
                logger.warning("No rewrite callback, treating rewrite as human")
                result.final_verdict = Verdict.HUMAN
                return result

            rewrite_targets = result.qa_result.raw_output.get("rewrite_targets", [])
            if not rewrite_targets:
                # 从 judge 结果中获取
                rewrite_targets = result.ops_proxy_result.raw_output.get("rewrite_targets", [])

            logger.info("Rewriting plan (round %d), targets: %s", round_num, rewrite_targets)
            try:
                current_plan = await rewrite_callback(current_plan, rewrite_targets)
            except Exception as e:
                logger.error("Rewrite failed: %s", e)
                result.final_verdict = Verdict.HUMAN
                result.final_reason = f"重写失败: {e}"
                return result

    # 超过最大重写次数
    logger.warning("Max rewrite rounds exceeded for plan %s", plan_json.get("plan_id"))
    return result
