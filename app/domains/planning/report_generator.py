"""
攻略报告生成器 — v2 架构（决策型攻略）

改造目标（fix/TASK_A_内容架构改造任务拆解.md T2-T5）：
  - _collect_plan_data() 扩充 8 个结构字段（不走 AI）
  - 新增 _build_design_brief() 从 profile+days 规则推导总纲设计策略
  - 新增 _check_structure() 装配前 5 类结构检查
  - 重写 _P_OVERVIEW / _P_DAILY，AI 只负责解释，不决定结构
  - 替换 _trigger_conditional() 为规则驱动触发器（T4）
  - generate_report() 组装 v2 payload（含 schema_version: v2）

向后兼容：
  - v1 结构字段保留，renderer 通过 schema_version 判断走哪条分支
  - 片段复用、重试、JSON 清洗逻辑 100% 保留

输出 → itinerary_plans.report_content (JSONB)

3 层结构：
  layer1_overview  — 总纲（design_brief / overview / booking_alerts / prep_checklist）
  layer2_daily     — 每日骨架（含 8 个结构字段 + AI 解释）
  layer3_appendix  — 附录（静态块 + 条件页）
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_cache import cached_ai_call
from app.core.config import settings
from app.db.models.catalog import EntityBase
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 静态块（timeless — 一次编码，永久复用，不走 AI）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATIC_PREP = {
    "title": "出发前准备 / 总注意事项",
    "sections": [
        {"heading": "📱 eSIM & 网络",
         "content": "提前在淘宝购买日本 eSIM（推荐 IIJmio / Ubigi），落地开机即用。Pocket WiFi 适合多人共享。"},
        {"heading": "💳 支付",
         "content": "备 3-5 万日元现金；Visa/Master 大部分商场可用；7-11 ATM 支持银联取现；PayPay 覆盖越来越广。"},
        {"heading": "🚃 交通卡",
         "content": "Suica / PASMO 可刷地铁、JR、公交、便利店。Apple Wallet 可直接开虚拟 Suica。跨城多考虑 JR Pass。"},
        {"heading": "🧳 行李",
         "content": "日本室内暖气足，外套里穿薄。鞋子选舒适步行鞋，日均 1.5-2 万步。带一个折叠行李袋备购物。"},
        {"heading": "📲 常用 App",
         "content": "Google Maps（导航）、Tabelog（餐厅评分）、乗換案内（电车）、Google 翻译（拍照翻译菜单）。"},
        {"heading": "🏥 紧急联系",
         "content": "110 警察 / 119 火警·救护。中国驻日大使馆 03-3403-3388。建议买旅行保险。"},
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T2 辅助函数：8 个结构字段的纯 Python 规则计算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _calc_primary_area(items: list[dict]) -> str:
    """出现频次最高的 area"""
    from collections import Counter
    areas = [it.get("area", "") for it in items if it.get("area")]
    if not areas:
        return ""
    return Counter(areas).most_common(1)[0][0]


def _calc_secondary_area(items: list[dict]) -> str:
    """第二高频 area（与主区域不同）"""
    from collections import Counter
    areas = [it.get("area", "") for it in items if it.get("area")]
    if not areas:
        return ""
    counter = Counter(areas).most_common(3)
    primary = counter[0][0] if counter else ""
    for area, _ in counter[1:]:
        if area != primary:
            return area
    return ""


def _calc_day_goal(theme: str, primary_area: str) -> str:
    """从 day_theme + primary_area 拼装今日主线描述"""
    if theme and primary_area:
        return f"{primary_area} · {theme}"
    return theme or primary_area or "自由探索"


def _calc_must_keep(items: list[dict]) -> str:
    """data_tier=S 或 rating≥4.3 的最高分项（最不能砍的）"""
    candidates = []
    for it in items:
        tier = it.get("data_tier", "")
        rating = it.get("google_rating")
        name = it.get("name", "")
        if not name:
            continue
        score = 0.0
        if tier == "S":
            score += 2.0
        elif tier == "A":
            score += 1.0
        if rating:
            try:
                score += float(rating)
            except (ValueError, TypeError):
                pass
        candidates.append((score, name))
    if not candidates:
        return items[0]["name"] if items else ""
    return max(candidates, key=lambda x: x[0])[1]


def _calc_first_cut(items: list[dict]) -> str:
    """is_optional=True 或 data_tier=B/C 的最低评分项（晚了先砍的）"""
    candidates = []
    for it in items:
        tier = it.get("data_tier", "")
        rating = it.get("google_rating")
        is_optional = it.get("is_optional", False)
        name = it.get("name", "")
        if not name:
            continue
        # 优先找 is_optional 的
        if is_optional:
            score = -1.0
        elif tier in ("B", "C"):
            score = 0.0
        else:
            continue  # S/A 且不 optional 的不作为候选
        if rating:
            try:
                score -= float(rating)  # 评分越低越优先砍
            except (ValueError, TypeError):
                pass
        candidates.append((score, name))
    if candidates:
        return min(candidates, key=lambda x: x[0])[1]
    # fallback：最后一个 non-must 项
    must = _calc_must_keep(items)
    for it in reversed(items):
        if it.get("name") and it["name"] != must:
            return it["name"]
    return ""


def _calc_integrity(items: list[dict]) -> float:
    """区域跳跃评分：每天只允许 1 主区域 + 1 副区域，超限扣分。返回 0.0-1.0"""
    from collections import Counter
    areas = [it.get("area", "") for it in items if it.get("area")]
    if not areas:
        return 1.0
    unique_areas = len(Counter(areas))
    if unique_areas <= 2:
        return 1.0
    elif unique_areas == 3:
        return 0.75
    elif unique_areas == 4:
        return 0.5
    else:
        return max(0.0, 1.0 - (unique_areas - 2) * 0.2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T5 新增：design_brief 规则推导 + 结构检查
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_design_brief(profile: dict, days: list[dict]) -> dict:
    """
    从 profile + days 特征用规则推导路线设计策略。
    不走 AI，纯 Python 规则，返回 design_brief dict。
    """
    party = profile.get("party_type", "")
    pace = profile.get("pace", "moderate")
    budget = profile.get("budget_level", "mid")
    styles = profile.get("styles", [])
    total = len(days)

    route_strategy = []
    tradeoffs = []
    stay_strategy = []
    budget_strategy = []
    execution_principles = []

    # 路线策略
    if total >= 4:
        # 判断是否有多城市
        cities = list({d.get("city_code", "") for d in days if d.get("city_code")})
        if len(cities) > 1:
            route_strategy.append(f"多城巡游：{' → '.join(cities)}")
        else:
            route_strategy.append("单城深玩，减少城际移动时间")
    if total >= 5:
        route_strategy.append("最后一天安排轻松收尾，预留返程缓冲")

    # 节奏策略
    pace_map = {"relaxed": "轻松", "moderate": "均衡", "packed": "密集"}
    pace_zh = pace_map.get(pace, "均衡")
    execution_principles.append(f"整体节奏：{pace_zh}，每天避免超过 2 个主要区域")

    if pace == "relaxed":
        execution_principles.append("每天最多安排 4 个核心点位，保留充足发呆时间")
        tradeoffs.append("为保证节奏，主动放弃部分人气景点，优先深度体验")
    elif pace == "packed":
        execution_principles.append("每天可安排 6 个点位，注意穿插休息与餐饮")

    # 预算策略
    if budget == "high":
        budget_strategy.append("品质优先：高价餐和体验集中安排，不做过度压缩")
    elif budget == "budget":
        budget_strategy.append("性价比导向：优先口碑佳的平价选择，避免景区溢价消费")
        tradeoffs.append("放弃部分高消费体验，用节省的时间换更多街区漫步")
    else:
        budget_strategy.append("均衡预算：该花的花，该省的省，重点体验不将就")

    # 同行人策略
    if party == "couple":
        tradeoffs.append("优先选浪漫、出片、有私密感的点位，主动放弃人流密集打卡点")
        stay_strategy.append("酒店优先选位置好、有仪式感的区域")
    elif party in ("family", "family_elderly"):
        execution_principles.append("景点间步行距离控制在 15 分钟以内，安排午休缓冲")
        tradeoffs.append("主动放弃步行量大、换乘复杂的区域")
    elif party == "solo":
        tradeoffs.append("独行可以随机应变，但仍保留核心锚点确保不后悔")

    # 风格策略
    if "小众" in styles or "深玩" in styles:
        tradeoffs.append("主动减少标准打卡景点，替换为当地人才知道的体验")
    if "出片" in styles or "审美" in styles:
        execution_principles.append("每天安排 1-2 个强出片锚点，注意光线时间（黄金时段优先）")

    # 住宿策略
    stay_strategy = stay_strategy or ["根据路线重心选择住宿区域，减少不必要的通勤时间"]

    return {
        "route_strategy": route_strategy or ["按目的地特点安排最优路线顺序"],
        "tradeoffs": tradeoffs or ["在时间和体验之间做合理取舍"],
        "stay_strategy": stay_strategy,
        "budget_strategy": budget_strategy,
        "execution_principles": execution_principles,
    }


def _check_structure(days: list[dict]) -> list[str]:
    """
    在 AI 生成前做 5 类结构检查，返回警告列表。
    不抛异常，只记录问题供日志和质量标记使用。
    """
    warnings = []
    seen_entities: set[str] = set()

    for d in days:
        day_num = d.get("day_number", "?")
        items = d.get("items", [])
        primary_area = d.get("primary_area", "")
        must_keep = d.get("must_keep", "")
        integrity = d.get("route_integrity_score", 1.0)
        title = d.get("theme", "")

        # 检查 1：日主线完整性
        if not primary_area:
            warnings.append(f"Day {day_num}: primary_area 为空")
        if not must_keep:
            warnings.append(f"Day {day_num}: must_keep 未能推导，建议人工确认")

        # 检查 2：区域跳跃
        if integrity < 0.5:
            unique_areas = len({it.get("area", "") for it in items if it.get("area")})
            warnings.append(f"Day {day_num}: 区域跳跃过多（{unique_areas}个区域），完整性={integrity:.2f}")

        # 检查 3：重复实体
        day_entities = []
        for it in items:
            eid = it.get("entity_id") or it.get("name", "")
            if eid:
                if eid in seen_entities:
                    warnings.append(f"Day {day_num}: 实体重复出现 [{eid}]")
                day_entities.append(eid)
        seen_entities.update(day_entities)

        # 检查 4：标题一致性（title 中是否包含 primary_area 关键词）
        if title and primary_area:
            if primary_area not in title and len(title) > 2:
                warnings.append(f"Day {day_num}: 标题「{title}」未体现主区域「{primary_area}」，请确认")

        # 检查 5：must_keep 必须来自实际 slot
        if must_keep:
            item_names = [it.get("name", "") for it in items]
            if must_keep not in item_names:
                warnings.append(f"Day {day_num}: must_keep「{must_keep}」不在 items 列表中")

    return warnings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI Prompt 模板
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 预热 System Prompt 模板（根据用户信息动态生成）────────────────────
def _build_system_prompt(dest: str, party: str, styles: str, budget: str, pace: str, total_days: int) -> str:
    """基于用户填写的信息生成定制化的 system prompt，让 AI 预热进入角色"""

    party_desc = {
        "couple": "情侣",
        "friends": "闺蜜/好友",
        "family": "带孩子的家庭",
        "family_elderly": "带长辈的家庭",
        "solo": "独自旅行者",
        "senior": "退休长辈",
    }.get(party, "旅行者")

    dest_desc = {
        "tokyo": "东京",
        "osaka": "大阪",
        "kyoto": "京都",
        "hokkaido": "北海道",
        "okinawa": "冲绳",
    }.get(dest, dest)

    budget_desc = {
        "budget": "穷游（能省则省，但不委屈自己）",
        "mid": "轻奢（该花花，该省省，追求性价比）",
        "high": "品质优先（住好吃好，不差钱）",
    }.get(budget, "中等预算")

    pace_desc = {
        "relaxed": "慢节奏（每天3-4个点，享受发呆时间）",
        "moderate": "均衡（每天5-6个点，有松有紧）",
        "packed": "暴走型（一天恨不得打卡10个点）",
    }.get(pace, "均衡节奏")

    return f"""\
# 你的身份
你叫「小樱」，是 Sakura Rush 的首席日本旅行规划师。
你曾在{dest_desc}生活多年，对这座城市的每个街区、每家店、每条交通线路了如指掌。

# 这位客户的情况
- 同行：{party_desc}
- 目的地：{dest_desc} {total_days}天
- 风格偏好：{styles}
- 预算：{budget_desc}
- 节奏：{pace_desc}

你要根据这些信息，给出最适合他们的建议。比如：
{f'- 情侣出行 → 选浪漫的、出片的、有私密感的地方' if party == 'couple' else ''}
{f'- 带孩子 → 选安全的、有趣的、走路少的地方，注意午休时间' if 'family' in party else ''}
{f'- 独自旅行 → 可以推荐深度体验、当地人才知道的小店' if party == 'solo' else ''}

# 你的写作风格
- 像朋友推荐一样，有温度有画面感
- 每个判断都有理由（"因为…所以…"）
- 绝对不说"著名""知名""值得一去"这种废话
- 用具体数字：步行几分钟、排队几分钟、花费多少日元
- 每段 3-5 句话，不堆砌
- 带点个人观点和踩坑经验

# 示例（你的风格）
✓ "浅草寺早上9点前人很少，阳光打在雷门上特别好拍。但仲见世通的人形烧排队要20分钟，不如走旁边小巷找'梅园'的抹茶冰淇淋，350日元。"
✓ "涩谷Sky提前官网买票2000日元，现场排队平均40分钟。16:30上去能同时看日落和夜景。"
✗ "浅草寺是东京著名景点，值得一去。"（废话！不要写！）

# 输出规则
- 严格输出纯 JSON 对象
- 不要用 ```json 或 markdown 包裹
- 不要在 JSON 外面加任何解释文字
- 每个字段都要填，不确定就写最佳猜测"""


# ── JSON 清洗 + 质量检测 + 自动重试 ──────────────────────────────────
import re as _re

def _clean_json(raw: str) -> str:
    """清洗 AI 返回的 JSON — 去掉 ```json 包裹和多余文本"""
    if not raw:
        return "{}"
    s = raw.strip()
    # 去掉 ```json ... ``` 包裹
    m = _re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', s, _re.DOTALL)
    if m:
        s = m.group(1).strip()
    # 如果开头不是 { ，找到第一个 {
    idx = s.find('{')
    if idx > 0:
        s = s[idx:]
    # 如果结尾不是 } ，找到最后一个 }
    ridx = s.rfind('}')
    if ridx >= 0 and ridx < len(s) - 1:
        s = s[:ridx + 1]
    return s


def _check_overview_quality(data: dict) -> tuple[bool, str]:
    """检查总纲质量，返回 (pass, reason)"""
    dp = data.get("design_philosophy", {})
    ov = data.get("overview", {})
    if not dp.get("summary") or len(dp.get("summary", "")) < 20:
        return False, "design_philosophy.summary 太短或缺失"
    if not dp.get("key_points") or len(dp.get("key_points", [])) < 2:
        return False, "design_philosophy.key_points 少于2个"
    if not ov.get("route_summary") or len(ov.get("route_summary", "")) < 20:
        return False, "overview.route_summary 太短"
    if not ov.get("highlights") or len(ov.get("highlights", [])) < 3:
        return False, "overview.highlights 少于3个"
    # 检测废话/拒绝回答
    bad_signals = ["I'm Kiro", "I am Kiro", "developer-focused", "I appreciate", "I need to clarify"]
    for sig in bad_signals:
        if sig.lower() in dp.get("summary", "").lower():
            return False, f"检测到拒绝回答: {sig}"
    return True, "OK"


def _check_daily_quality(data: dict) -> tuple[bool, str]:
    """检查每日报告质量"""
    eo = data.get("execution_overview", {})
    if not eo.get("timeline_summary") or len(eo.get("timeline_summary", "")) < 20:
        return False, "timeline_summary 太短"
    if not eo.get("area"):
        return False, "area 缺失"
    if not data.get("highlights") or len(data.get("highlights", [])) < 1:
        return False, "highlights 缺失"
    if not data.get("notes_and_planb"):
        return False, "notes_and_planb 缺失"
    bad_signals = ["I'm Kiro", "I am Kiro", "developer-focused", "I appreciate", "I need to clarify"]
    for sig in bad_signals:
        if sig.lower() in eo.get("timeline_summary", "").lower():
            return False, f"检测到拒绝回答: {sig}"
    return True, "OK"


MAX_RETRIES = 2  # 最多重试次数


async def _ai_call_with_retry(
    prompt: str,
    sys_prompt: str,
    quality_checker,
    label: str,
    max_tokens: int = 2000,
) -> dict:
    """带质量检测的 AI 调用，不合格自动重试"""
    for attempt in range(1 + MAX_RETRIES):
        raw = await cached_ai_call(
            prompt=prompt,
            model=settings.ai_model_standard,
            system_prompt=sys_prompt,
            temperature=0.7 + (attempt * 0.1),  # 重试时提高温度
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            ttl=3600 if attempt > 0 else 7 * 24 * 3600,  # 重试时缓存时间短
        )
        cleaned = _clean_json(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("[%s] attempt %d JSON 解析失败, raw[:200]=%s", label, attempt + 1, raw[:200])
            if attempt < MAX_RETRIES:
                continue
            return {"_error": "json_parse_failed", "_raw": raw[:500]}

        passed, reason = quality_checker(data)
        if passed:
            if attempt > 0:
                logger.info("[%s] attempt %d 通过质量检测 (之前失败: %s)", label, attempt + 1, reason)
            return data
        else:
            logger.warning("[%s] attempt %d 质量不合格: %s", label, attempt + 1, reason)
            if attempt < MAX_RETRIES:
                # 追加纠正提示
                prompt = prompt + f"\n\n⚠️ 上次回答有问题：{reason}。请严格按要求重新输出完整 JSON。"

    return data  # 最后一次结果，即使不合格也用

# ── v2 总纲 prompt（注入 design_brief，AI 只做解释润色）────────────────
_P_OVERVIEW = """\
请为这份 {days}天{dest}行程撰写「总纲解释」。

以下设计策略已经确定，不要修改，只在此基础上写解释：
- 路线策略：{route_strategy}
- 主要取舍：{tradeoffs}
- 住宿策略：{stay_strategy}
- 预算策略：{budget_strategy}
- 执行原则：{execution_principles}

行程骨架（每天主区域已确定）：
{skeleton}

用户画像：同行={party}，风格={styles}，预算={budget}，节奏={pace}

你只需要写：
1. 总设计思路解释（1段话，3-5句，说清楚为什么这样设计）
2. 全程最值得期待的5个体验亮点（具体，有画面感，不说废话）
3. 需要提前预约的项目（每项说明不预约的后果）
4. 当季旅行提醒（2-3句）

输出 JSON：
{{
  "design_philosophy": {{
    "summary": "总设计思路（1段话，3-5句，解释上面的策略为什么这样决定）",
    "key_points": ["策略要点1（带理由）", "策略要点2（带理由）", "策略要点3（带理由）"]
  }},
  "overview": {{
    "route_summary": "总路线概述（何日在哪，一段话，体现区域流动逻辑）",
    "intensity_map": ["Day1:轻松", "Day2:均衡", "..."],
    "highlights": ["全程5个最值得期待的体验（具体，不说著名/知名）"]
  }},
  "booking_reminders": [
    {{"item": "需提前预约的项目名称", "deadline": "最迟几天前预约", "impact": "不预约会怎样"}}
  ],
  "seasonal_tips": "当季旅行提醒（2-3句，具体）"
}}"""

# ── v2 每日 prompt（注入 8 个结构字段，AI 只负责解释）────────────────
_P_DAILY = """\
请为行程第 {day_num} 天（{city}）生成「每日解释」。

以下信息已经确定，不要修改：
- 主区域：{primary_area}
- 副区域：{secondary_area}
- 今天主线：{day_goal}
- 最不能砍：{must_keep}
- 晚了先砍：{first_cut}
- 起点：{start_anchor}，终点：{end_anchor}

今日具体安排：
{items_text}

用户：同行={party}，风格={styles}，节奏={pace}

你只需要写：
1. 为什么这样排（3-5个判断，每个1句话，说清楚逻辑）
2. 亮点体验描述（每个亮点2-3句，有画面感，有具体数字/时间）
3. 风险/雨天/体力备选（具体可执行）

输出 JSON：
{{
  "execution_overview": {{
    "timeline_summary": "今日时间轴（1段话，体现{primary_area}为主的区域逻辑）",
    "area": "{primary_area}",
    "intensity": "轻松/均衡/偏满",
    "top_expectation": "今天最值得期待的1-2件事（具体说）"
  }},
  "why_this_arrangement": ["判断1（为什么…所以…）", "判断2", "判断3"],
  "highlights": [
    {{
      "name": "亮点名称",
      "description": "2-3句体验描述，带具体数字和画面感",
      "photo_tip": "拍照建议（1句，具体时间/角度/位置）",
      "nearby_bonus": "附近顺便可逛的点（1句）"
    }}
  ],
  "notes_and_planb": {{
    "risk_warnings": ["具体的排队/营业时间/踩坑提醒"],
    "weather_plan": "下雨时具体怎么调整（说替代地点）",
    "energy_plan": "体力不够时先砍「{first_cut}」，因为…",
    "clothing_tip": "穿着建议（具体）"
  }}
}}"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T4 条件页触发 — 规则驱动版（替换原 12 行硬编码）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 视觉触发标签集合（对应出片页）
_VISUAL_TAGS = {"sakura", "night_view", "sea", "mountain", "sunset", "temple", "garden", "snow"}


def _trigger_conditional(day_num: int, total: int, items: list[dict], day_context: dict | None = None) -> list[str]:
    """
    规则驱动的条件页触发器（T4）。

    触发规则：
    - transport：第一天 / 最后天 / 跨城日
    - hotel：第一天 / 区域切换日
    - restaurant：有评分 ≥ 4.0 的餐厅（高评分 / 纪念日 / 稀缺预约）
    - photo：trigger_tags 含视觉关键词
    - budget：当天明显高消费（预留钩子，当前用估算标记）
    """
    pages: list[str] = []
    ctx = day_context or {}

    # ── 交通页：第一/最后天，或跨城 ──
    if day_num == 1 or day_num == total:
        pages.append("transport")
    elif ctx.get("city_changed"):
        pages.append("transport")

    # ── 酒店页：第一天，或区域切换 ──
    if day_num == 1:
        pages.append("hotel")
    elif ctx.get("hotel_changed"):
        pages.append("hotel")

    # ── 餐厅页：评分 ≥ 4.0 的餐厅（值得重点介绍）──
    for it in items:
        if it.get("entity_type") == "restaurant":
            r = it.get("google_rating")
            if r:
                try:
                    if float(r) >= 4.0:
                        pages.append("restaurant")
                        break
                except (ValueError, TypeError):
                    pass

    # ── 出片页：trigger_tags 含视觉关键词 ──
    trigger_tags = set(ctx.get("trigger_tags", []))
    if not trigger_tags:
        # 从 items 的 area / entity_type 推断
        for it in items:
            area_lower = (it.get("area") or "").lower()
            if any(tag in area_lower for tag in ("公园", "神社", "寺", "海", "山", "湖")):
                trigger_tags.add("scenic")
    if trigger_tags & _VISUAL_TAGS or "scenic" in trigger_tags:
        pages.append("photo")

    return list(set(pages))  # 去重


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 片段复用 — Phase 1 检查
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _try_reuse_fragments(
    session: AsyncSession,
    city_code: str,
    party_type: str,
    day_count: int,
) -> dict:
    """尝试从 guide_fragments 表复用 route / decision / experience 片段。
    返回 {day_index: [fragment_dict, ...], "decision": [...], ...}
    如果 guide_fragments 表为空或没有匹配，返回空 dict（Phase 1 回退到纯模板）。
    """
    reused: dict = {"route_fragments": [], "decision_fragments": [], "experience_fragments": []}
    try:
        from app.db.models.fragments import GuideFragment
        q = (
            select(GuideFragment)
            .where(
                GuideFragment.city_code == city_code,
                GuideFragment.is_active == True,  # noqa: E712
                GuideFragment.status == "active",
            )
            .order_by(GuideFragment.quality_score.desc())
            .limit(20)
        )
        result = await session.execute(q)
        fragments = result.scalars().all()

        for f in fragments:
            # 时效检查
            if f.time_sensitivity == "hard_ttl" and f.valid_until:
                if datetime.now(tz=timezone.utc) > f.valid_until:
                    continue
            # party_type 匹配
            if f.party_types and party_type not in f.party_types:
                continue

            entry = {
                "fragment_id": str(f.fragment_id),
                "type": f.fragment_type,
                "title": f.title,
                "body_skeleton": f.body_skeleton,
                "body_prose": f.body_prose,
                "quality": f.quality_score,
                "day_hint": f.day_index_hint,
                "time_sensitivity": f.time_sensitivity,
            }
            if f.fragment_type == "route":
                reused["route_fragments"].append(entry)
            elif f.fragment_type == "decision":
                reused["decision_fragments"].append(entry)
            elif f.fragment_type in ("experience", "dining"):
                reused["experience_fragments"].append(entry)
    except Exception as e:
        logger.debug("片段复用查询失败（可能表不存在），回退到纯 AI: %s", e)

    return reused


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据收集
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _collect_plan_data(session: AsyncSession, plan_id: uuid.UUID) -> dict:
    """
    从 DB 收集 plan + days + items + entity 信息，返回结构化 dict。

    T2 改造：在现有字段基础上，每天额外追加 8 个结构字段（纯规则，不走 AI）：
      primary_area, secondary_area, day_goal, must_keep, first_cut,
      start_anchor, end_anchor, route_integrity_score
    """
    plan = await session.get(ItineraryPlan, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")

    meta = plan.plan_metadata or {}
    dest = (meta.get("city_codes") or ["tokyo"])[0]

    days_result = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id).order_by(ItineraryDay.day_number)
    )
    days_list = []
    for day in days_result.scalars().all():
        items_result = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id).order_by(ItineraryItem.sort_order)
        )
        item_dicts = []
        for item in items_result.scalars().all():
            entity = await session.get(EntityBase, item.entity_id) if item.entity_id else None
            notes_parsed = {}
            if item.notes_zh:
                try:
                    notes_parsed = json.loads(item.notes_zh)
                except (json.JSONDecodeError, TypeError):
                    notes_parsed = {"copy_zh": item.notes_zh}

            item_dicts.append({
                "sort": item.sort_order,
                "type": item.item_type,
                "duration": item.duration_min,
                "entity_id": str(item.entity_id) if item.entity_id else None,
                "name": (getattr(entity, "name_zh", None) or getattr(entity, "name_en", "")) if entity else "自由安排",
                "entity_type": getattr(entity, "entity_type", "") if entity else item.item_type,
                "area": getattr(entity, "area_name", "") if entity else "",
                "google_rating": getattr(entity, "google_rating", None) if entity else None,
                # T2 新增：data_tier 和 is_optional（用于 must_keep / first_cut 计算）
                "data_tier": getattr(entity, "data_tier", "") if entity else "",
                "is_optional": getattr(item, "is_optional", False),
                "copy_zh": notes_parsed.get("copy_zh", ""),
                "tips_zh": notes_parsed.get("tips_zh", ""),
            })

        day_theme = day.day_theme or ""

        # ── T2：追加 8 个结构字段（纯 Python 规则，不走 AI）──
        primary_area = _calc_primary_area(item_dicts)
        secondary_area = _calc_secondary_area(item_dicts)
        day_goal = _calc_day_goal(day_theme, primary_area)
        must_keep = _calc_must_keep(item_dicts)
        first_cut = _calc_first_cut(item_dicts)
        start_anchor = item_dicts[0]["name"] if item_dicts else ""
        end_anchor = item_dicts[-1]["name"] if item_dicts else ""
        integrity_score = _calc_integrity(item_dicts)

        days_list.append({
            "day_number": day.day_number,
            "city_code": day.city_code,
            "theme": day_theme,
            "items": item_dicts,
            # T2 新增的 8 个结构字段
            "primary_area": primary_area,
            "secondary_area": secondary_area,
            "day_goal": day_goal,
            "must_keep": must_keep,
            "first_cut": first_cut,
            "start_anchor": start_anchor,
            "end_anchor": end_anchor,
            "route_integrity_score": integrity_score,
        })

    return {"plan": plan, "dest": dest, "days": days_list, "total": len(days_list), "meta": meta}


def _items_to_text(items: list[dict]) -> str:
    """将一天的 items 转成可读文本供 AI 使用"""
    lines = []
    for it in items:
        rating_str = f" (★{it['google_rating']})" if it.get("google_rating") else ""
        copy = f" — {it['copy_zh']}" if it.get("copy_zh") else ""
        lines.append(f"  [{it['type']:10s}] {it['name']}{rating_str} ({it['duration']}min) @ {it['area']}{copy}")
    return "\n".join(lines) if lines else "  （暂无具体安排）"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def generate_report(
    session: AsyncSession,
    plan_id: uuid.UUID,
    user_context: Optional[dict] = None,
) -> dict:
    """
    4 阶段生成完整攻略报告，写入 itinerary_plans.report_content。

    Returns: report_content dict
    """
    ctx = user_context or {}
    party = ctx.get("party_type", "couple")
    styles = ", ".join(ctx.get("styles", ["经典"]))
    budget = ctx.get("budget_level", "mid")
    pace = ctx.get("pace", "moderate")

    # ── 数据收集 ──
    data = await _collect_plan_data(session, plan_id)
    plan = data["plan"]
    dest = data["dest"]
    days = data["days"]
    total = data["total"]

    # ── Phase 1: 骨架 — 优先复用片段 ──
    reused = await _try_reuse_fragments(session, dest, party, total)
    reuse_summary = {
        "route": len(reused.get("route_fragments", [])),
        "decision": len(reused.get("decision_fragments", [])),
        "experience": len(reused.get("experience_fragments", [])),
    }
    logger.info("Phase1 片段复用: %s", reuse_summary)

    # ── 构建定制化 system prompt（基于用户信息预热）──
    sys_prompt = _build_system_prompt(dest, party, styles, budget, pace, total)

    # ── T5: 构建 design_brief（规则推导，不走 AI）──
    profile_for_brief = {"party_type": party, "pace": pace, "budget_level": budget, "styles": ctx.get("styles", [])}
    design_brief = _build_design_brief(profile_for_brief, days)

    # ── T5: 结构检查（在 AI 前）──
    structure_warnings = _check_structure(days)
    if structure_warnings:
        logger.warning("结构检查警告 plan=%s: %s", plan_id, structure_warnings)

    # ── Phase 2+3: 总纲 + 每日骨架（AI 生成，v2 prompt 注入结构字段）──
    skeleton_text = "\n".join(
        f"Day {d['day_number']}: {d['city_code']} — {d.get('day_goal', d['theme'])} "
        f"[主区域:{d.get('primary_area','')}] ({len(d['items'])} 项)"
        for d in days
    )

    # 如果有复用片段，注入到 prompt 上下文
    reuse_context = ""
    for rf in reused.get("decision_fragments", [])[:3]:
        reuse_context += f"\n参考决策片段「{rf['title']}」: {rf.get('body_prose', '')[:200]}"

    # ── v2 总纲 prompt（注入 design_brief）──
    overview_prompt = _P_OVERVIEW.format(
        days=total,
        dest=dest,
        route_strategy="、".join(design_brief.get("route_strategy", [])),
        tradeoffs="、".join(design_brief.get("tradeoffs", [])),
        stay_strategy="、".join(design_brief.get("stay_strategy", [])),
        budget_strategy="、".join(design_brief.get("budget_strategy", [])),
        execution_principles="、".join(design_brief.get("execution_principles", [])),
        skeleton=skeleton_text + reuse_context,
        party=party,
        styles=styles,
        budget=budget,
        pace=pace,
    )

    logger.info("Phase3 生成总纲 v2 plan=%s (model=%s)", plan_id, settings.ai_model_standard)
    overview = await _ai_call_with_retry(
        prompt=overview_prompt,
        sys_prompt=sys_prompt,
        quality_checker=_check_overview_quality,
        label=f"overview-{str(plan_id)[:8]}",
        max_tokens=2000,
    )

    # ── Phase 2: 每日骨架（v2 prompt 注入 8 个结构字段）──
    daily_reports = []
    for d in days:
        items_text = _items_to_text(d["items"])
        # 如果有匹配的 experience 片段，注入
        exp_context = ""
        for ef in reused.get("experience_fragments", []):
            if ef.get("day_hint") == d["day_number"]:
                exp_context += f"\n可参考体验片段「{ef['title']}」: {ef.get('body_prose', '')[:150]}"

        # ── v2 每日 prompt（注入 8 个结构字段，AI 只解释）──
        daily_prompt = _P_DAILY.format(
            day_num=d["day_number"],
            city=d["city_code"],
            primary_area=d.get("primary_area", ""),
            secondary_area=d.get("secondary_area", "无") or "无",
            day_goal=d.get("day_goal", d["theme"]),
            must_keep=d.get("must_keep", ""),
            first_cut=d.get("first_cut", ""),
            start_anchor=d.get("start_anchor", ""),
            end_anchor=d.get("end_anchor", ""),
            items_text=items_text + exp_context,
            party=party,
            styles=styles,
            pace=pace,
        )

        logger.info("Phase2 生成 Day %d plan=%s (v2 prompt)", d["day_number"], plan_id)
        daily_content = await _ai_call_with_retry(
            prompt=daily_prompt,
            sys_prompt=sys_prompt,
            quality_checker=_check_daily_quality,
            label=f"day{d['day_number']}-{str(plan_id)[:8]}",
            max_tokens=1500,
        )

        # ── T4 v2 条件页触发（传入 day_context）──
        day_ctx = {
            "trigger_tags": [it.get("area", "") for it in d["items"] if it.get("area")],
            "hotel_changed": False,   # TODO: 从 profile 中取换酒店信息
            "city_changed": d["city_code"] != (days[d["day_number"] - 2]["city_code"] if d["day_number"] > 1 else d["city_code"]),
        }
        cond_pages = _trigger_conditional(d["day_number"], total, d["items"], day_ctx)

        daily_reports.append({
            "day_number": d["day_number"],
            "city_code": d["city_code"],
            "day_theme": d["theme"],
            # T2：8 个结构字段透传到输出
            "primary_area": d.get("primary_area", ""),
            "secondary_area": d.get("secondary_area", ""),
            "day_goal": d.get("day_goal", ""),
            "must_keep": d.get("must_keep", ""),
            "first_cut": d.get("first_cut", ""),
            "start_anchor": d.get("start_anchor", ""),
            "end_anchor": d.get("end_anchor", ""),
            "route_integrity_score": d.get("route_integrity_score", 1.0),
            "items": d["items"],
            "report": daily_content,
            "conditional_pages": cond_pages,
            "fragment_reuse": [
                ef["fragment_id"] for ef in reused.get("experience_fragments", [])
                if ef.get("day_hint") == d["day_number"]
            ],
        })

    # ── T5: 组装 v2 report_content ──
    report = {
        # v2 标记，renderer 检测到走 v2 模板分支
        "schema_version": "v2",
        "version": "4phase-v2",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        # v2 新增：design_brief（总纲真相源）
        "design_brief": design_brief,
        "layer1_overview": {
            "design_philosophy": overview.get("design_philosophy", {}),
            "overview": overview.get("overview", {}),
            "booking_reminders": overview.get("booking_reminders", []),
            "seasonal_tips": overview.get("seasonal_tips", ""),
            "prep_checklist": STATIC_PREP,
        },
        "layer2_daily": daily_reports,
        "layer3_appendix": {
            "prep_checklist": STATIC_PREP,
        },
        "meta": {
            "total_days": total,
            "destination": dest,
            "party_type": party,
            "styles": styles,
            "budget_level": budget,
            "pace": pace,
            "fragment_reuse_summary": reuse_summary,
            # T5：结构检查结果也放入 meta
            "structure_warnings": structure_warnings,
            "structure_warning_count": len(structure_warnings),
        },
    }

    # ── 写入 DB（使用 raw SQL 确保可靠写入，不依赖 ORM dirty tracking）──
    await session.execute(
        text("""
            UPDATE itinerary_plans 
            SET report_content = :rc, status = 'done', updated_at = NOW()
            WHERE plan_id = :pid
        """),
        {"rc": json.dumps(report, ensure_ascii=False), "pid": str(plan_id)},
    )
    await session.commit()

    logger.info("报告生成完成 plan=%s %d天 reuse=%s", plan_id, total, reuse_summary)
    return report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P2: 城市圈链路入口（vNext — 消费 DayFrame 骨架）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── L3-15: 新字段填充函数（纯规则，不调 AI）──────────────────────────────────

def _build_preference_fulfillment(
    trip_goals: list[str],
    decisions: list[dict],
) -> list[dict]:
    """
    L3-15: 偏好兑现列表。

    遍历 trip_goals，对每条 goal 在 generation_decisions 中搜索匹配的 evidence。
    """
    fulfillment = []
    # 收集所有 why_selected 文本（来自 decisions）
    evidence_pool = []
    for dec in decisions:
        val = dec.get("decision_value", "")
        reason = dec.get("decision_reason", "")
        stage = dec.get("decision_stage", "")
        if stage in ("major_activity_plan", "hotel_strategy", "circle_selection"):
            evidence_pool.append({
                "stage": stage, "value": str(val), "reason": reason
            })

    for goal in trip_goals:
        if not goal or not goal.strip():
            continue
        goal_lower = goal.lower()
        matched_evidence = None
        for ev in evidence_pool:
            if any(kw in ev["reason"].lower() or kw in ev["value"].lower()
                   for kw in goal_lower.split() if len(kw) > 1):
                matched_evidence = ev
                break

        if matched_evidence:
            fulfillment.append({
                "preference_text": goal,
                "fulfillment_type": "fully_met",
                "evidence": matched_evidence["reason"],
                "object_ref": matched_evidence.get("value", ""),
                "explanation": f"通过 {matched_evidence['stage']} 阶段兑现",
            })
        else:
            fulfillment.append({
                "preference_text": goal,
                "fulfillment_type": "not_applicable",
                "evidence": "",
                "object_ref": None,
                "explanation": "未在决策链中找到直接对应",
            })

    return fulfillment


def _build_skipped_options(decisions: list[dict]) -> list[dict]:
    """
    L3-15: 跳过的选项。

    从 generation_decisions 中取 major_activity_plan 的 alternatives 里 selected=False 的。
    """
    skipped = []
    for dec in decisions:
        if dec.get("decision_stage") != "major_activity_plan":
            continue
        alts = dec.get("alternatives_considered") or []
        for alt in alts:
            if isinstance(alt, dict) and not alt.get("selected", True):
                skipped.append({
                    "name": alt.get("id", ""),
                    "entity_type": "cluster",
                    "why_skipped": alt.get("reason", "未选中"),
                    "would_fit_if": None,
                })
    return skipped[:10]  # 最多 10 个


def _build_emotional_goals(day_frames: list[dict]) -> list[dict]:
    """
    L3-15: 每日情绪目标。

    规则映射: intensity + day_type → mood_keyword + mood_sentence。
    """
    INTENSITY_MOOD = {
        "light": ("放松", "慢下来，享受不赶路的一天"),
        "balanced": ("探索", "张弛有度，主次分明的一天"),
        "dense": ("充实", "信息量丰富、值得全力以赴的一天"),
    }
    DAY_TYPE_MOOD = {
        "arrival": ("初见", "初见这座城市，从容落地、轻松探索"),
        "departure": ("收官", "最后的散步与收官，留下完整的记忆"),
        "transfer": ("转场", "换一个舞台，路上也是风景"),
    }

    goals = []
    for frame in day_frames:
        day_idx = frame.get("day_index", frame.get("day_number", 0))
        day_type = frame.get("day_type", "normal")
        intensity = frame.get("intensity", "balanced")

        if day_type in DAY_TYPE_MOOD:
            kw, sentence = DAY_TYPE_MOOD[day_type]
        else:
            kw, sentence = INTENSITY_MOOD.get(intensity, ("探索", "张弛有度的一天"))

        # 如果有 title_hint，用它补充 sentence
        hint = frame.get("title_hint", "")
        if hint:
            sentence = f"{hint} — {sentence}"

        goals.append({
            "day_index": day_idx,
            "mood_keyword": kw,
            "mood_sentence": sentence,
        })

    return goals


async def generate_report_v2(
    session: AsyncSession,
    plan_id: uuid.UUID,
    day_frames: list[dict],
    design_brief_override: Optional[dict] = None,
    user_context: Optional[dict] = None,
) -> dict:
    """
    城市圈链路的报告生成入口。

    与 generate_report() 的区别：
    1. day_frames 来自 route_skeleton_builder（已包含骨架字段）
    2. 骨架字段 **优先** 使用 day_frames 而非从 items 计算
    3. design_brief 可以从上游传入（hotel_strategy + circle 决策）
    4. 其他逻辑（AI prompt、fragment reuse、quality check）完全复用

    Args:
        plan_id: 行程计划 ID
        day_frames: 来自 route_skeleton_builder 的骨架列表
                    每个 dict 包含 day_index, primary_corridor, main_driver_name,
                    intensity, title_hint, must_keep_ids, cut_order, meal_windows 等
        design_brief_override: 来自上游决策链的设计策略（如果为 None，走规则推导）
        user_context: 用户画像上下文
    """
    ctx = user_context or {}
    party = ctx.get("party_type", "couple")
    styles = ", ".join(ctx.get("styles", ["经典"]))
    budget = ctx.get("budget_level", "mid")
    pace = ctx.get("pace", "moderate")

    # ── 数据收集（复用现有逻辑）──
    data = await _collect_plan_data(session, plan_id)
    plan = data["plan"]
    dest = data["dest"]
    days = data["days"]
    total = data["total"]

    # ── 合并骨架字段：day_frames 优先级 > 从 items 计算的值 ──
    frame_map = {f.get("day_index", f.get("day_number", i + 1)): f for i, f in enumerate(day_frames)}
    for d in days:
        frame = frame_map.get(d["day_number"])
        if frame:
            # 骨架字段覆盖（如果骨架提供了，优先用骨架的值）
            if frame.get("primary_corridor"):
                d["primary_area"] = frame["primary_corridor"]
            if frame.get("secondary_corridor"):
                d["secondary_area"] = frame["secondary_corridor"]
            if frame.get("main_driver_name"):
                d["day_goal"] = frame["main_driver_name"]
            if frame.get("must_keep_ids"):
                # 从 must_keep_ids 找到第一个匹配的实体名
                keep_ids = frame["must_keep_ids"]
                for it in d["items"]:
                    if it.get("entity_id") in keep_ids or it.get("name") in keep_ids:
                        d["must_keep"] = it["name"]
                        break
            if frame.get("cut_order"):
                # 从 cut_order 找到第一个匹配的实体名
                for cut_id in frame["cut_order"]:
                    for it in d["items"]:
                        if it.get("entity_id") == cut_id or it.get("name") == cut_id:
                            d["first_cut"] = it["name"]
                            break
                    if d.get("first_cut"):
                        break
            if frame.get("title_hint"):
                d["title_hint"] = frame["title_hint"]
            if frame.get("intensity"):
                d["intensity"] = frame["intensity"]
            if frame.get("day_type"):
                d["day_type"] = frame["day_type"]
            if frame.get("sleep_base"):
                d["sleep_base"] = frame["sleep_base"]
            if frame.get("fallback_corridor"):
                d["fallback_corridor"] = frame["fallback_corridor"]

    # ── 片段复用 ──
    reused = await _try_reuse_fragments(session, dest, party, total)
    reuse_summary = {
        "route": len(reused.get("route_fragments", [])),
        "decision": len(reused.get("decision_fragments", [])),
        "experience": len(reused.get("experience_fragments", [])),
    }

    # ── System prompt ──
    sys_prompt = _build_system_prompt(dest, party, styles, budget, pace, total)

    # ── Design brief（优先用上游传入的）──
    if design_brief_override:
        design_brief = design_brief_override
    else:
        profile_for_brief = {"party_type": party, "pace": pace, "budget_level": budget, "styles": ctx.get("styles", [])}
        design_brief = _build_design_brief(profile_for_brief, days)

    # ── 结构检查 ──
    structure_warnings = _check_structure(days)
    if structure_warnings:
        logger.warning("v2 结构检查警告 plan=%s: %s", plan_id, structure_warnings)

    # ── 总纲 AI（复用 v2 prompt）──
    skeleton_text = "\n".join(
        f"Day {d['day_number']}: {d.get('day_type', 'normal')} — "
        f"{d.get('day_goal', d['theme'])} "
        f"[走廊:{d.get('primary_area','')}] "
        f"[住:{d.get('sleep_base','')}] "
        f"[节奏:{d.get('intensity','balanced')}] "
        f"({len(d['items'])} 项)"
        for d in days
    )

    reuse_context = ""
    for rf in reused.get("decision_fragments", [])[:3]:
        reuse_context += f"\n参考决策片段「{rf['title']}」: {rf.get('body_prose', '')[:200]}"

    overview_prompt = _P_OVERVIEW.format(
        days=total, dest=dest,
        route_strategy="、".join(design_brief.get("route_strategy", [])),
        tradeoffs="、".join(design_brief.get("tradeoffs", [])),
        stay_strategy="、".join(design_brief.get("stay_strategy", [])),
        budget_strategy="、".join(design_brief.get("budget_strategy", [])),
        execution_principles="、".join(design_brief.get("execution_principles", [])),
        skeleton=skeleton_text + reuse_context,
        party=party, styles=styles, budget=budget, pace=pace,
    )

    overview = await _ai_call_with_retry(
        prompt=overview_prompt, sys_prompt=sys_prompt,
        quality_checker=_check_overview_quality,
        label=f"overview-v2-{str(plan_id)[:8]}", max_tokens=2000,
    )

    # ── 每日 AI（复用 v2 prompt）──
    daily_reports = []
    for d in days:
        items_text = _items_to_text(d["items"])
        exp_context = ""
        for ef in reused.get("experience_fragments", []):
            if ef.get("day_hint") == d["day_number"]:
                exp_context += f"\n可参考体验片段「{ef['title']}」: {ef.get('body_prose', '')[:150]}"

        daily_prompt = _P_DAILY.format(
            day_num=d["day_number"], city=d["city_code"],
            primary_area=d.get("primary_area", ""),
            secondary_area=d.get("secondary_area", "无") or "无",
            day_goal=d.get("day_goal", d["theme"]),
            must_keep=d.get("must_keep", ""),
            first_cut=d.get("first_cut", ""),
            start_anchor=d.get("start_anchor", ""),
            end_anchor=d.get("end_anchor", ""),
            items_text=items_text + exp_context,
            party=party, styles=styles, pace=pace,
        )

        daily_content = await _ai_call_with_retry(
            prompt=daily_prompt, sys_prompt=sys_prompt,
            quality_checker=_check_daily_quality,
            label=f"day{d['day_number']}-v2-{str(plan_id)[:8]}", max_tokens=1500,
        )

        # 条件页触发
        frame = frame_map.get(d["day_number"], {})
        day_ctx = {
            "trigger_tags": [it.get("area", "") for it in d["items"] if it.get("area")],
            "hotel_changed": d.get("sleep_base", "") != (
                days[d["day_number"] - 2].get("sleep_base", "") if d["day_number"] > 1 else d.get("sleep_base", "")
            ),
            "city_changed": d["city_code"] != (
                days[d["day_number"] - 2]["city_code"] if d["day_number"] > 1 else d["city_code"]
            ),
        }
        cond_pages = _trigger_conditional(d["day_number"], total, d["items"], day_ctx)

        daily_reports.append({
            "day_number": d["day_number"],
            "city_code": d["city_code"],
            "day_theme": d.get("title_hint", d["theme"]),
            "day_type": d.get("day_type", "normal"),
            "primary_area": d.get("primary_area", ""),
            "secondary_area": d.get("secondary_area", ""),
            "day_goal": d.get("day_goal", ""),
            "must_keep": d.get("must_keep", ""),
            "first_cut": d.get("first_cut", ""),
            "start_anchor": d.get("start_anchor", ""),
            "end_anchor": d.get("end_anchor", ""),
            "route_integrity_score": d.get("route_integrity_score", 1.0),
            "intensity": d.get("intensity", "balanced"),
            "sleep_base": d.get("sleep_base", ""),
            "fallback_corridor": d.get("fallback_corridor", ""),
            "items": d["items"],
            "report": daily_content,
            "conditional_pages": cond_pages,
            "fragment_reuse": [
                ef["fragment_id"] for ef in reused.get("experience_fragments", [])
                if ef.get("day_hint") == d["day_number"]
            ],
        })

    # ── L3-15: 填充新字段（纯规则）──
    # 读取 generation_decisions 用于偏好兑现和跳过选项
    decisions_rows = []
    try:
        from app.db.models.derived import GenerationDecision
        dec_q = await session.execute(
            select(GenerationDecision).where(
                GenerationDecision.trip_request_id == plan.trip_request_id,
                GenerationDecision.is_current == True,
            )
        )
        decisions_rows = [
            {
                "decision_stage": d.decision_stage,
                "decision_key": d.decision_key,
                "decision_value": d.decision_value,
                "decision_reason": d.decision_reason,
                "alternatives_considered": d.alternatives_considered,
            }
            for d in dec_q.scalars().all()
        ]
    except Exception:
        pass

    trip_goals = ctx.get("trip_goals", [])
    preference_fulfillment = _build_preference_fulfillment(trip_goals, decisions_rows)
    skipped_options = _build_skipped_options(decisions_rows)
    emotional_goals = _build_emotional_goals(day_frames)

    # ── 组装 vNext payload ──
    report = {
        "schema_version": "v2",
        "version": "circle-v1",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "design_brief": design_brief,
        "layer1_overview": {
            "design_philosophy": overview.get("design_philosophy", {}),
            "overview": overview.get("overview", {}),
            "booking_reminders": overview.get("booking_reminders", []),
            "seasonal_tips": overview.get("seasonal_tips", ""),
            "prep_checklist": STATIC_PREP,
        },
        "layer2_daily": daily_reports,
        "layer3_appendix": {
            "prep_checklist": STATIC_PREP,
        },
        # L3-15 新字段
        "preference_fulfillment": preference_fulfillment,
        "skipped_options": skipped_options,
        "emotional_goals": emotional_goals,
        "meta": {
            "total_days": total,
            "destination": dest,
            "party_type": party,
            "styles": styles,
            "budget_level": budget,
            "pace": pace,
            "generation_path": "city_circle",
            "fragment_reuse_summary": reuse_summary,
            "structure_warnings": structure_warnings,
            "structure_warning_count": len(structure_warnings),
            # L4-04: pipeline 版本跟踪
            "pipeline_versions": {
                "scorer": "base_quality_v2",
                "planner": "circle_v1",
                "report_schema": "v2",
                "report_generator": "v2_circle",
            },
        },
    }

    # ── 写入 DB ──
    await session.execute(
        text("""
            UPDATE itinerary_plans 
            SET report_content = :rc, status = 'done', updated_at = NOW()
            WHERE plan_id = :pid
        """),
        {"rc": json.dumps(report, ensure_ascii=False), "pid": str(plan_id)},
    )
    await session.commit()

    logger.info("报告 v2(circle) 生成完成 plan=%s %d天", plan_id, total)
    return report
