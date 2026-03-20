from __future__ import annotations

"""
AI 意图解析模块
用户输入自然语言 → Claude 解析 → 结构化 TripProfile

示例输入：
  "我想五月初去东京大阪玩10天，两个大人一个小孩，预算中等，想看樱花和历史文化"

示例输出（TripIntentResult）：
  {
    "cities": [{"city_code": "tokyo", "nights": 6}, {"city_code": "osaka", "nights": 4}],
    "duration_days": 10,
    "travel_dates": {"start": "2025-05-01", "end": "2025-05-10"},
    "party_size": 3,
    "party_composition": {"adults": 2, "children": 1},
    "budget_level": "mid",
    "must_have_tags": ["sakura", "history", "culture"],
    "travel_style": "culture",
    "raw_message": "..."
  }
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings

# ── OpenAI 客户端（指向中转站）────────────────────────────────────────────────
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.ai_base_url,
        )
    return _client


# ── 结果数据类 ─────────────────────────────────────────────────────────────────

@dataclass
class TripIntentResult:
    """解析后的旅行意图，用于创建 TripRequest + TripProfile"""
    # 城市列表：[{"city_code": "tokyo", "nights": 5}, ...]
    cities: List[Dict[str, Any]] = field(default_factory=list)
    duration_days: int = 7
    travel_dates: Dict[str, str] = field(default_factory=dict)  # {"start": "2025-05-01"}
    party_size: int = 2
    party_composition: Dict[str, int] = field(default_factory=lambda: {"adults": 2})
    budget_level: str = "mid"          # budget / mid / premium / luxury
    must_have_tags: List[str] = field(default_factory=list)
    travel_style: str = "general"      # culture / nature / food / shopping / family
    language: str = "zh"               # 用户语言
    raw_message: str = ""
    confidence: float = 1.0            # 解析置信度 0-1
    clarification_needed: Optional[str] = None  # 需要用户澄清的问题


# ── JSON 提取工具 ─────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """
    从 AI 响应中提取 JSON 字符串。
    支持以下格式：
      - 裸 JSON：{ ... }
      - Markdown 代码块：```json\n{ ... }\n```
    """
    text = text.strip()
    # 尝试 ```json ... ``` 格式
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    # 尝试直接提取 { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text


# ── System Prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """你是日本旅行AI的意图解析引擎。
用户会用自然语言描述他们的日本旅行需求，你需要解析成结构化JSON。

**城市代码映射**（只用这些代码）：
- 东京/Tokyo → "tokyo"
- 大阪/Osaka → "osaka"  
- 京都/Kyoto → "kyoto"
- 奈良/Nara → "nara"
- 神户/Kobe → "kobe"
- 箱根/Hakone → "hakone"
- 镰仓/Kamakura → "kamakura"
- 日光/Nikko → "nikko"
- 北海道/Hokkaido/札幌/Sapporo → "sapporo"
- 冲绳/Okinawa/那霸 → "naha"
- 福冈/Fukuoka → "fukuoka"
- 广岛/Hiroshima → "hiroshima"
- 名古屋/Nagoya → "nagoya"
- 金泽/Kanazawa → "kanazawa"

**预算档位**：
- 便宜/省钱/背包 → "budget"
- 中等/普通/一般 → "mid"
- 高档/舒适/商务 → "premium"
- 奢华/豪华/顶级 → "luxury"

**标签列表**（从这里选）：
shrine, temple, castle, museum, park, onsen, shopping, food, sakura, autumn_leaves,
snow, beach, anime, history, culture, nature, family, romantic, nightlife, art

**旅行风格**：culture / nature / food / shopping / family / romantic / adventure

**输出格式**（严格JSON，不要任何解释）：
{
  "cities": [{"city_code": "tokyo", "nights": 5}, {"city_code": "osaka", "nights": 3}],
  "duration_days": 8,
  "travel_dates": {"start": "2025-05-01", "end": "2025-05-08"},
  "party_size": 2,
  "party_composition": {"adults": 2, "children": 0},
  "budget_level": "mid",
  "must_have_tags": ["sakura", "culture"],
  "travel_style": "culture",
  "language": "zh",
  "confidence": 0.9,
  "clarification_needed": null
}

**注意**：
- 如果用户没说具体日期，travel_dates 留空 {}
- 如果城市没提到天数分配，根据总天数平均分配
- 如果信息不完整，confidence < 0.7，并在 clarification_needed 中用中文提问
- 总 nights 之和应等于 duration_days - 1（最后一天回程）
"""


# ── 主解析函数 ────────────────────────────────────────────────────────────────

async def parse_trip_intent(user_message: str) -> TripIntentResult:
    """
    解析用户自然语言输入为结构化旅行意图。

    Args:
        user_message: 用户原始输入，如"我想去东京大阪玩10天"

    Returns:
        TripIntentResult 结构化意图

    Raises:
        不抛异常，解析失败时返回带默认值的结果
    """
    client = _get_client()

    try:
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,   # 低温度，保证输出稳定
            max_tokens=1000,
        )

        raw_content = response.choices[0].message.content or "{}"
        # 提取 JSON：支持 ```json ... ``` 或裸 JSON
        raw_json = _extract_json(raw_content)
        data = json.loads(raw_json)

        return TripIntentResult(
            cities=data.get("cities", [{"city_code": "tokyo", "nights": 6}]),
            duration_days=int(data.get("duration_days", 7)),
            travel_dates=data.get("travel_dates", {}),
            party_size=int(data.get("party_size", 2)),
            party_composition=data.get("party_composition", {"adults": 2}),
            budget_level=data.get("budget_level", "mid"),
            must_have_tags=data.get("must_have_tags", []),
            travel_style=data.get("travel_style", "general"),
            language=data.get("language", "zh"),
            confidence=float(data.get("confidence", 1.0)),
            clarification_needed=data.get("clarification_needed"),
            raw_message=user_message,
        )

    except Exception as e:
        # 解析失败时返回默认值，不崩溃
        return TripIntentResult(
            cities=[{"city_code": "tokyo", "nights": 6}],
            duration_days=7,
            raw_message=user_message,
            confidence=0.0,
            clarification_needed=f"抱歉，我没能理解您的需求，能描述得更详细一些吗？（错误：{str(e)[:100]}）",
        )


async def refine_intent(
    original_message: str,
    clarification: str,
    previous_result: TripIntentResult,
) -> TripIntentResult:
    """
    用户追加澄清后，重新解析意图（多轮对话）。

    Args:
        original_message:  用户第一条消息
        clarification:     用户补充的说明
        previous_result:   上一轮解析结果

    Returns:
        更新后的 TripIntentResult
    """
    combined = f"""
第一条消息：{original_message}
补充说明：{clarification}
上一轮解析结果（JSON）：{json.dumps({
    "cities": previous_result.cities,
    "duration_days": previous_result.duration_days,
    "budget_level": previous_result.budget_level,
    "must_have_tags": previous_result.must_have_tags,
}, ensure_ascii=False)}

请基于补充说明更新解析结果。
"""
    return await parse_trip_intent(combined)
