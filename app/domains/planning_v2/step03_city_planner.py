"""
step03_city_planner.py — 城市组合规划（Opus深度决策）

调用 Opus 模型，根据用户约束和区域摘要，输出 3 个城市组合候选方案。

输入：
  - UserConstraints（旅行时间、用户画像、约束）
  - RegionSummary（区域统计）

输出：
  - 3 个城市组合方案，每个包含每日城市分配 + 推荐理由

API：Anthropic Claude Opus（低频调用，1次/行程）
思考强度：deep（extended thinking, budget_tokens=10000）
"""

import json
import logging
import re

import anthropic

from app.core.config import settings
from app.domains.planning_v2.models import CircleProfile, RegionSummary, UserConstraints

logger = logging.getLogger(__name__)

# ── Opus 模型配置 ─────────────────────────────────────────────────────────────
MODEL_ID = "claude-opus-4-6"
MAX_TOKENS = 16000  # extended thinking 需要更大的 max_tokens 空间
THINKING_BUDGET = 10000

# ── System Prompt ─────────────────────────────────────────────────────────────


def _build_system_prompt(circle: CircleProfile) -> str:
    region = circle.region_desc
    return f"""\
你是一位资深的{region}旅行规划师。

任务：根据用户的旅行约束和目的地数据，设计 3 个不同风格的城市组合方案。

## 强约束（必须遵守）
1. must_visit 中的地点必须被安排
2. do_not_go 中的地点绝不能出现
3. 第一天（到达日）和最后一天（离开日）强度必须为 light
4. 用户的 must_have_tags 必须在全程方案中被明显覆盖（不是每天都要，但全程必须足够体现）

## 体验约束（保证质量）
5. 城市切换不能过于频繁（同一城市建议连续 2+ 天）
6. 3 个方案必须有明显不同的风格（如：文化深度 vs 美食主题 vs 自然风光）
7. 避免单一品类连续堆叠：不要连续 3 天都以同类体验（如全是寺社）为主题
8. 每天的 theme 应该明确且有差异化，保证节奏变化

## 偏好处理
- must_have_tags 是用户的强偏好，全程方案必须明显向这些标签倾斜
- nice_to_have_tags 是软偏好，有则更好，不必强求
- 如果用户无偏好，默认保证体验多样性：文化遗产、自然户外、市井逛街、文化体验、城市地标至少各覆盖一次

输出格式要求：
严格返回 JSON 格式，不要任何额外文字。
JSON 结构如下：
{{
  "candidates": [
    {{
      "plan_name": "方案名称（简短中文）",
      "cities_by_day": {{
        "day1": {{"city": "城市代码", "theme": "当天主题", "intensity": "light|medium|heavy"}},
        "day2": {{"city": "城市代码", "theme": "当天主题", "intensity": "light|medium|heavy"}}
      }},
      "reasoning": "推荐理由（2-3句话）",
      "trade_offs": "取舍说明（1-2句话）"
    }}
  ],
  "recommended_index": 0
}}
"""


# ── User Prompt 模板 ──────────────────────────────────────────────────────────
_USER_PROMPT_TEMPLATE = """\
## 用户约束
- 旅行时间：{start_date} 到 {end_date}，共 {total_days} 天
- 同行类型：{party_type}
- 预算等级：{budget_tier}
- 必去地点：{must_visit}
- 不去地点：{do_not_go}
- 已去过：{visited}
- 强偏好（全程必须覆盖）：{must_have_tags}
- 软偏好（有则更好）：{nice_to_have_tags}

## 目的地数据
- 城市圈：{circle_name}
- 可选城市：{cities}
- POI 统计：{entities_by_type}
- 等级分布：{grade_distribution}

请输出 3 个城市组合候选方案，严格按 JSON 格式返回。\
"""


# ── JSON 提取 ─────────────────────────────────────────────────────────────────


def _extract_json(text: str) -> str:
    """从 AI 响应中提取 JSON 字符串，支持裸 JSON 和 markdown 代码块。"""
    text = text.strip()
    # 尝试 ```json ... ``` 格式
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # 尝试直接提取 { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


# ── Prompt 构造 ───────────────────────────────────────────────────────────────


def _build_user_prompt(
    user_constraints: UserConstraints,
    region_summary: RegionSummary,
) -> str:
    """根据 UserConstraints 和 RegionSummary 构造 user prompt。"""
    tw = user_constraints.trip_window
    up = user_constraints.user_profile
    cs = user_constraints.constraints

    return _USER_PROMPT_TEMPLATE.format(
        start_date=tw.get("start_date", "未指定"),
        end_date=tw.get("end_date", "未指定"),
        total_days=tw.get("total_days", "未知"),
        party_type=up.get("party_type", "未知"),
        budget_tier=up.get("budget_tier", "mid"),
        must_visit=", ".join(cs.get("must_visit", [])) or "无",
        do_not_go=", ".join(cs.get("do_not_go", [])) or "无",
        visited=", ".join(cs.get("visited", [])) or "无",
        must_have_tags=", ".join(up.get("must_have_tags", [])) or "无",
        nice_to_have_tags=", ".join(up.get("nice_to_have_tags", [])) or "无",
        circle_name=region_summary.circle_name,
        cities=", ".join(region_summary.cities),
        entities_by_type=json.dumps(region_summary.entities_by_type, ensure_ascii=False),
        grade_distribution=json.dumps(region_summary.grade_distribution, ensure_ascii=False),
    )


# ── 响应解析 ──────────────────────────────────────────────────────────────────


def _parse_opus_response(response) -> tuple[dict, int]:
    """
    从 Opus 响应中提取 JSON 结果和 thinking tokens 用量。

    Returns:
        (parsed_dict, thinking_tokens_used)

    Raises:
        ValueError: 如果 JSON 解析失败
    """
    text_content = ""

    for block in response.content:
        if block.type == "text":
            text_content += block.text

    # Extended thinking tokens 计入 output_tokens（Anthropic 官方计费方式）。
    # SDK 无独立 thinking_tokens 字段，output_tokens 包含 thinking + visible output。
    # 用 output_tokens 减去可见文本 token 数来估算 thinking 部分。
    output_tokens = 0
    input_tokens = 0
    if hasattr(response, "usage") and response.usage:
        output_tokens = getattr(response.usage, "output_tokens", 0)
        input_tokens = getattr(response.usage, "input_tokens", 0)
        logger.info(
            "Opus usage: input=%d, output=%d (includes thinking)",
            input_tokens,
            output_tokens,
        )
    # output_tokens 即为含 thinking 的总输出 token 数
    thinking_tokens = output_tokens

    raw_json = _extract_json(text_content)
    parsed = json.loads(raw_json)

    # 基本结构校验
    if "candidates" not in parsed:
        raise ValueError("响应缺少 'candidates' 字段")
    if not isinstance(parsed["candidates"], list) or len(parsed["candidates"]) == 0:
        raise ValueError("'candidates' 必须是非空列表")

    return parsed, thinking_tokens


# ── 主函数 ────────────────────────────────────────────────────────────────────


async def plan_city_combination(
    user_constraints: UserConstraints,
    region_summary: RegionSummary,
    circle: CircleProfile,
    api_key: str | None = None,
) -> dict:
    """
    调用 Opus 生成 3 个城市组合候选方案。

    流程：
      1. 构造 system + user prompt
      2. 调用 Opus（extended thinking）
      3. 解析 JSON 响应
      4. 若解析失败，重试 1 次
      5. 若仍失败，抛出 RuntimeError（不降级）

    Args:
        user_constraints: Step 1 输出的用户约束
        region_summary:   Step 2 输出的区域摘要
        api_key:          可选，覆盖 settings 中的 API key

    Returns:
        {
          "candidates": [...],          # 3 个候选方案
          "recommended_index": int,     # 推荐方案索引
          "thinking_tokens_used": int,  # thinking tokens 用量
        }
    """
    user_prompt = _build_user_prompt(user_constraints, region_summary)

    logger.info(
        f"Step03: calling Opus for city planning — "
        f"{region_summary.circle_name}, "
        f"{user_constraints.trip_window.get('total_days', '?')} days, "
        f"{len(region_summary.cities)} cities"
    )

    resolved_key = api_key or settings.anthropic_api_key
    if not resolved_key:
        raise RuntimeError("Step03: ANTHROPIC_API_KEY 未配置，无法调用 Opus")

    base_url = settings.anthropic_base_url or None
    client = anthropic.AsyncAnthropic(api_key=resolved_key, base_url=base_url)

    last_error: Exception | None = None
    max_attempts = 2  # 首次 + 1 次重试

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Step03: Opus API call attempt {attempt}/{max_attempts}")

            response = await client.messages.create(
                model=MODEL_ID,
                max_tokens=MAX_TOKENS,
                thinking={
                    "type": "enabled",
                    "budget_tokens": THINKING_BUDGET,
                },
                system=_build_system_prompt(circle),
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )

            parsed, thinking_tokens = _parse_opus_response(response)
            parsed["thinking_tokens_used"] = thinking_tokens

            logger.info(
                f"Step03: Opus returned {len(parsed['candidates'])} candidates, "
                f"recommended_index={parsed.get('recommended_index', 0)}, "
                f"thinking_tokens={thinking_tokens}"
            )

            return parsed

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Step03: JSON parse failed on attempt {attempt}: {e}")
            # 重试时继续循环
        except anthropic.APIError as e:
            last_error = e
            logger.error(f"Step03: Opus API error on attempt {attempt}: {e}")
            # API 错误（限流、服务端错误等）也重试一次
        except Exception as e:
            last_error = e
            logger.error(
                f"Step03: unexpected error on attempt {attempt}: {e}",
                exc_info=True,
            )
            break  # 未知错误不重试

    # 所有重试用尽，直接抛异常，不降级
    raise RuntimeError(
        f"Step03: all {max_attempts} attempts failed, last error: {last_error}"
    ) from last_error
