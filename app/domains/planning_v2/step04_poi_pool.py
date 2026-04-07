"""
step04_poi_pool.py — POI 候选池构建与缩减

从 entity_base 读取 POI 数据并按规则顺序过滤，生成候选景点池。

所有过滤策略从配置数据驱动（CircleProfile + taxonomy.json），不硬编码：
  - 城市圈扩展：taxonomy.json.regions
  - Grade 准入策略：按天数动态调整，通过 PoolConfig 控制
  - 画像加成：taxonomy.json.profile_boost_rules
  - Party type 属性：从 profile_dimensions 推断
  - taxonomy 路径：从 CircleProfile.taxonomy_path 获取（不硬编码目录名）

过滤规则（顺序执行）：
  1. city_code in circle_cities（含 regions 下属子区域）
  2. is_active=true
  3. 按天数动态过滤 grade（应用画像加成后的有效等级）
  4. 按 party_type 过滤（儿童/老人不宜场景）
  5. 按 budget_tier + cost_local 过滤
  6. 按 season 过滤（best_season + travel dates）
  7. 排除 do_not_go_places
  8. 排除 visited_places
  9. 定休日初筛
  10. 排除 risk_flags
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityTag, Poi
from app.db.models.soft_rules import EntityOperatingFact
from app.domains.planning_v2.models import (
    CandidatePool,
    CircleProfile,
    RegionSummary,
    UserConstraints,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配置数据加载（从 taxonomy.json，按圈缓存）
# ---------------------------------------------------------------------------

_taxonomy_cache: dict[str, dict] = {}


def _load_taxonomy(taxonomy_path: Path) -> dict:
    """加载 taxonomy.json，按路径缓存。"""
    key = str(taxonomy_path)
    if key in _taxonomy_cache:
        return _taxonomy_cache[key]
    try:
        with open(taxonomy_path, encoding="utf-8") as f:
            _taxonomy_cache[key] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("无法加载 taxonomy.json (%s): %s，使用空配置", taxonomy_path, e)
        _taxonomy_cache[key] = {}
    return _taxonomy_cache[key]


def _build_region_city_map(taxonomy_path: Path) -> dict[str, set[str]]:
    """
    从 taxonomy.json.regions 构建「主城市 → 所有子区域 city_code」映射。

    子区域名称→city_code 的映射从 taxonomy.json.sub_region_codes 读取，不硬编码。
    """
    taxonomy = _load_taxonomy(taxonomy_path)
    regions = taxonomy.get("regions", {})
    sub_region_codes = taxonomy.get("sub_region_codes", {})

    region_map: dict[str, set[str]] = {}

    for region_key, region_data in regions.items():
        codes = {region_key.lower()}
        for sub_name in region_data.get("sub_regions", []):
            code = sub_region_codes.get(sub_name)
            if code:
                codes.add(code.lower())
            codes.add(sub_name.lower())
        region_map[region_key.lower()] = codes

    return region_map


def _build_day_trip_targets(taxonomy_path: Path) -> dict[str, set[str]]:
    """
    从 taxonomy.json.day_trip_links 构建「主城市 → 当日可达目的地」映射。
    """
    taxonomy = _load_taxonomy(taxonomy_path)
    links = taxonomy.get("day_trip_links", {}).get("links", [])

    targets: dict[str, set[str]] = {}
    for link in links:
        from_city = (link.get("from") or "").lower()
        to_city = (link.get("to") or "").lower()
        if from_city and to_city:
            targets.setdefault(from_city, set()).add(to_city)
    return targets


def _get_profile_boost_rules(taxonomy_path: Path) -> dict:
    """从 taxonomy.json 获取画像加成规则。"""
    taxonomy = _load_taxonomy(taxonomy_path)
    return taxonomy.get("profile_boost_rules", {})


# ---------------------------------------------------------------------------
# 池配置（可被 orchestrator 或测试覆盖）
# ---------------------------------------------------------------------------


@dataclass
class PoolConfig:
    """POI 池过滤策略配置，所有阈值集中在此，不散落在代码里。"""

    # grade 准入：按天数分段
    grade_tiers: dict[str, list[str]] = field(
        default_factory=lambda: {
            "short": ["S", "A", "B"],  # ≤3天
            "medium": ["S", "A", "B", "C"],  # 4-5天
            "long": ["S", "A", "B", "C"],  # ≥6天
        }
    )
    short_max_days: int = 3
    medium_max_days: int = 5

    # budget 门票价格上限（日元）
    admission_cap: dict[str, int] = field(
        default_factory=lambda: {
            "budget": 1000,
            "mid": 3000,
            "premium": 8000,
            "luxury": 999999,
        }
    )

    # party_type 属性推断规则
    children_party_types: set[str] = field(
        default_factory=lambda: {
            "family_young",
            "family_teen",
            "family_young_child",
            "family_school_age",
            "family_kids",
            "family",
        }
    )
    elderly_party_types: set[str] = field(
        default_factory=lambda: {
            "family_parents",
            "family_elderly",
            "senior",
        }
    )

    # 不适合儿童的标签
    children_exclude_tags: set[str] = field(
        default_factory=lambda: {
            "adults_only",
            "bar",
            "nightclub",
        }
    )
    # 不适合老人的标签
    elderly_exclude_tags: set[str] = field(
        default_factory=lambda: {
            "extreme_physical",
            "hiking",
        }
    )

    # 池大小控制
    max_pool_size: int = 45  # 分桶合并后的总上限
    surprise_slots: int = 4  # 惊喜候选保留位

    def allowed_grades(self, total_days: int) -> list[str]:
        if total_days <= self.short_max_days:
            return self.grade_tiers["short"]
        elif total_days <= self.medium_max_days:
            return self.grade_tiers["medium"]
        return self.grade_tiers["long"]


# 模块级默认配置（可被测试或 orchestrator 替换）
DEFAULT_POOL_CONFIG = PoolConfig()

# ---------------------------------------------------------------------------
# 月份→季节映射
# ---------------------------------------------------------------------------

_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
    12: "winter",
}

# Grade 排序权重（用于画像加成计算）
_GRADE_ORDER: list[str] = ["S", "A", "B", "C"]


def _parse_best_season(best_season_str: str | None) -> set[str]:
    """将 best_season 字符串解析为季节集合。

    格式: "all", "all_year", "全年" 或 "spring,summer" 或 "spring" 等
    """
    if not best_season_str:
        return {"all"}

    bs = best_season_str.lower().strip()
    if bs in ("all", "all_year", "全年", ""):
        return {"all"}

    # 逗号分隔的季节列表
    seasons = {s.strip() for s in bs.split(",")}
    seasons = {s for s in seasons if s}  # 去空字符串

    return seasons if seasons else {"all"}


def _apply_profile_boost(
    name_zh: str,
    base_grade: str,
    party_type: str,
    boost_rules: dict,
) -> str:
    """
    应用 taxonomy.json 的画像加成规则，计算有效 grade。

    例：海游馆 base=B, family_kids → +1 → effective=A
    例：USJ base=S, culture_deep → -1 → effective=A

    Args:
        name_zh: 景点中文名（用于匹配 boost_rules）
        base_grade: 原始 data_tier
        party_type: 用户的 party_type
        boost_rules: taxonomy.json 中的 profile_boost_rules

    Returns:
        有效 grade（S/A/B/C）
    """
    # boost_rules 格式: {"example": {"海游馆": {"base": "B", "boosts": {"family_kids": "+1"}}}}
    # 也可能是扁平格式: {"海游馆": {"base": "B", "boosts": {...}}}
    examples = boost_rules.get("example", boost_rules)
    if not isinstance(examples, dict):
        return base_grade

    spot_boost = examples.get(name_zh)
    if not spot_boost or not isinstance(spot_boost, dict):
        return base_grade

    boosts = spot_boost.get("boosts", {})
    if not boosts:
        return base_grade

    # 查找与 party_type 匹配的加成
    delta = 0
    for profile_key, boost_val in boosts.items():
        if profile_key == party_type or profile_key in party_type:
            try:
                delta = int(boost_val)
            except (ValueError, TypeError):
                pass
            break

    if delta == 0:
        return base_grade

    # 应用升降级
    try:
        idx = _GRADE_ORDER.index(base_grade)
    except ValueError:
        return base_grade

    new_idx = max(0, min(len(_GRADE_ORDER) - 1, idx - delta))  # -delta: +1 升级=index减1
    return _GRADE_ORDER[new_idx]


async def build_poi_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    region_summary: RegionSummary,
    travel_dates: list[str],  # [YYYY-MM-DD, ...]
    circle: CircleProfile,
    config: PoolConfig | None = None,
) -> list[CandidatePool]:
    """
    从 entity_base 读取并按规则缩减 POI 候选池。

    所有过滤阈值从 PoolConfig 读取（可被 orchestrator/测试覆盖）。
    城市圈扩展从 taxonomy.json.regions 读取。
    画像加成从 taxonomy.json.profile_boost_rules 读取。

    Args:
        session: 数据库会话
        user_constraints: 用户约束
        region_summary: 地区摘要
        travel_dates: 旅行日期列表
        config: 池过滤配置（不传用默认）

    Returns:
        list[CandidatePool]: 通过过滤的 POI 候选池
    """
    cfg = config or DEFAULT_POOL_CONFIG
    trace_log = []

    # 0. 初始数据准备
    circle_cities = list(region_summary.cities or [])
    if not circle_cities:
        logger.warning("region_summary.cities 为空")
        return []

    taxonomy_path = circle.taxonomy_path
    currency = circle.currency

    # 从 taxonomy.json 扩展城市圈（两层扩展）
    # 1) regions: 行政归属（kyoto 包含 uji/天桥立等）
    # 2) day_trip_links: 跨圈当日往返可达（osaka → arima/kobe/himeji 等）
    region_map = _build_region_city_map(taxonomy_path)
    day_trip_targets = _build_day_trip_targets(taxonomy_path)

    circle_cities_set = set()
    for city in circle_cities:
        city_l = city.lower()
        circle_cities_set.add(city_l)
        # 行政归属扩展
        if city_l in region_map:
            circle_cities_set |= region_map[city_l]
        for region_key, sub_codes in region_map.items():
            if city_l in sub_codes:
                circle_cities_set |= sub_codes
        # 跨圈当日往返扩展
        if city_l in day_trip_targets:
            circle_cities_set |= day_trip_targets[city_l]

    circle_cities_expanded = list(circle_cities_set)

    # 解析约束
    do_not_go_places = set(user_constraints.constraints.get("do_not_go", []))
    visited_places = set(user_constraints.constraints.get("visited", []))
    must_visit = set(user_constraints.constraints.get("must_visit", []))

    # 提取用户画像
    user_profile = user_constraints.user_profile or {}
    party_type = user_profile.get("party_type", "couple")
    has_children = party_type in cfg.children_party_types
    children_ages = user_profile.get("children_ages", [])
    has_elderly = party_type in cfg.elderly_party_types or user_profile.get("has_elderly", False)

    budget_tier = user_profile.get("budget_tier", "mid")
    admission_cap = cfg.admission_cap.get(budget_tier, 3000)
    avoid_tags = user_profile.get("avoid_tags", [])

    # 旅行月份（用于季节检查）
    travel_month = None
    if travel_dates:
        try:
            first_date = datetime.strptime(travel_dates[0], "%Y-%m-%d")
            travel_month = first_date.month
        except (ValueError, IndexError):
            logger.warning("无法解析旅行日期")

    travel_season = _MONTH_TO_SEASON.get(travel_month) if travel_month else None

    # 从 config 读取 grade 策略
    total_days = user_constraints.trip_window.get("total_days", 5)
    allowed_grades = cfg.allowed_grades(total_days)

    # 加载画像加成规则（用于后续 effective grade 计算）
    boost_rules = _get_profile_boost_rules(taxonomy_path)
    taxonomy = _load_taxonomy(taxonomy_path)

    trace_log.append(
        f"circle_cities={circle_cities}, expanded={circle_cities_expanded}, "
        f"travel_month={travel_month}, season={travel_season}"
    )
    trace_log.append(f"party_type={party_type}, budget_tier={budget_tier}, total_days={total_days}")
    trace_log.append(f"allowed_grades={allowed_grades}")

    # 1. 查询基础 POI
    # SQL 层宽查：取所有 S/A/B/C（profile_boost 可能把 B 升为 A），
    # 精确 grade 过滤在 Python 层做（应用画像加成后）。
    query = (
        select(EntityBase)
        .where(
            and_(
                EntityBase.entity_type == "poi",
                EntityBase.city_code.in_(circle_cities_expanded),
                EntityBase.is_active.is_(True),
            )
        )
        .order_by(EntityBase.entity_id)
    )

    result = await session.execute(query)
    entities = result.scalars().all()
    count_after_base = len(entities)
    trace_log.append(f"Step 1 (base filter, all grades): {count_after_base} POI")

    if not entities:
        logger.info(f"[POI池] 无符合条件的 POI: cities={circle_cities}, tier=S/A")
        return []

    entity_ids = [e.entity_id for e in entities]

    # 2. 批量加载 Poi 扩展数据
    poi_query = select(Poi).where(Poi.entity_id.in_(entity_ids))
    poi_result = await session.execute(poi_query)
    poi_map: dict[uuid.UUID, Poi] = {p.entity_id: p for p in poi_result.scalars().all()}

    # 3. 批量加载标签
    tags_query = select(EntityTag).where(EntityTag.entity_id.in_(entity_ids))
    tags_result = await session.execute(tags_query)
    entity_tags: dict[uuid.UUID, set[str]] = {}
    for tag in tags_result.scalars().all():
        entity_tags.setdefault(tag.entity_id, set()).add(
            tag.tag_value.lower() if tag.tag_value else ""
        )

    # 4. 批量加载运营事实（用于定休日和风险检查）
    facts_query = select(EntityOperatingFact).where(EntityOperatingFact.entity_id.in_(entity_ids))
    facts_result = await session.execute(facts_query)
    entity_facts: dict[uuid.UUID, list[EntityOperatingFact]] = {}
    for fact in facts_result.scalars().all():
        entity_facts.setdefault(fact.entity_id, []).append(fact)

    # 5. 执行过滤规则
    filtered_entities = []

    for entity in entities:
        eid = entity.entity_id
        poi = poi_map.get(eid)
        tags = entity_tags.get(eid, set())
        facts = entity_facts.get(eid, [])

        # Rule 3: Grade 过滤（应用画像加成后的有效等级）
        base_grade = entity.data_tier or "C"
        effective_grade = _apply_profile_boost(
            entity.name_zh,
            base_grade,
            party_type,
            boost_rules,
        )
        if effective_grade not in allowed_grades:
            continue

        # Rule 4: 按 party_type 过滤（标签驱动，不硬编码人群列表）
        if has_children:
            if tags & cfg.children_exclude_tags:
                continue
            if children_ages:
                min_age = min(children_ages)
                if min_age < 6 and "extreme_physical" in tags:
                    continue

        if has_elderly:
            if tags & cfg.elderly_exclude_tags:
                continue

        # Rule 5: 按 budget_tier + cost_local 过滤
        if budget_tier in ("budget", "mid"):
            if "luxury_only" in tags or "vip_only" in tags:
                continue

        entity_cost = 0
        if poi and poi.admission_fee_jpy:
            entity_cost = int(poi.admission_fee_jpy)
        if entity_cost > admission_cap and str(eid) not in must_visit:
            continue

        # Rule 6: 按 season 过滤
        if travel_season and poi:
            best_season = poi.best_season
            if best_season:
                valid_seasons = _parse_best_season(best_season)
                if "all" not in valid_seasons and travel_season not in valid_seasons:
                    continue

        # Rule 7: 排除 do_not_go_places
        if str(eid) in do_not_go_places:
            continue

        # Rule 8: 排除 visited_places
        if str(eid) in visited_places:
            continue

        # Rule 9: 定休日初筛
        if facts:
            is_permanently_closed = False
            for fact in facts:
                fact_key = (fact.fact_key or "").lower()
                fact_value = (fact.fact_value or "").lower()
                closed_statuses = ("permanently_closed", "long_term_closed")
                if fact_key == "status" and fact_value in closed_statuses:
                    is_permanently_closed = True
                    break
            if is_permanently_closed:
                continue

        # Rule 10: 排除 risk_flags
        if entity.risk_flags:
            # risk_flags 包含 施工中、不稳定等风险标签
            skip_risk_flags = {"renovation", "construction", "unstable", "dangerous"}
            if any(flag in skip_risk_flags for flag in entity.risk_flags):
                continue

        # Rule 6 补充：用户 avoid_tags
        if avoid_tags:
            avoid_set = {t.lower() for t in avoid_tags}
            if tags & avoid_set:
                continue

        # 通过所有过滤规则
        filtered_entities.append(entity)

    count_after_filter = len(filtered_entities)
    trace_log.append(f"Step 2-10 (all filters): {count_after_filter} POI")

    # 6. 转换为 CandidatePool
    candidate_pools = []
    for entity in filtered_entities:
        eid = entity.entity_id
        poi = poi_map.get(eid)
        tags = entity_tags.get(eid, set())

        # 提取费用（DB 字段名仍是 admission_fee_jpy，读取时映射到 cost_local）
        cost_local = 0
        if poi and poi.admission_fee_jpy:
            cost_local = int(poi.admission_fee_jpy)

        # 提取 visit_minutes
        visit_minutes = 60  # 默认
        if poi and poi.typical_duration_min:
            visit_minutes = int(poi.typical_duration_min)
        elif entity.typical_duration_baseline:
            visit_minutes = int(entity.typical_duration_baseline)

        # 获取 best_season 用于展示
        best_season = None
        if poi and poi.best_season:
            best_season = poi.best_season

        # 构建开放时间字典
        open_hours = {}
        if poi and poi.opening_hours_json:
            open_hours = poi.opening_hours_json

        # 构建评分信号
        review_signals = {}
        if poi:
            if poi.google_rating:
                review_signals["google_rating"] = float(poi.google_rating)
            if poi.google_review_count:
                review_signals["google_review_count"] = int(poi.google_review_count)

        # 创建 CandidatePool
        pool = CandidatePool(
            entity_id=str(eid),
            name_zh=entity.name_zh,
            entity_type="poi",
            grade=entity.data_tier,
            latitude=float(entity.lat) if entity.lat else 0.0,
            longitude=float(entity.lng) if entity.lng else 0.0,
            tags=list(tags),
            visit_minutes=visit_minutes,
            cost_local=cost_local,
            city_code=entity.city_code or "",
            currency=currency,
            sub_type=entity.sub_type or "",
            open_hours=open_hours,
            review_signals=review_signals,
        )
        candidate_pools.append(pool)

    # ── 分桶配额截取（P2/P3/P4）─────────────────────────────
    # 从 taxonomy 加载体验桶定义
    bucket_defs = taxonomy.get("experience_buckets", {})
    # 去掉文档字段
    bucket_defs = {k: v for k, v in bucket_defs.items() if not k.startswith("_")}

    if bucket_defs and len(candidate_pools) > cfg.max_pool_size:
        # 构建 sub_type → bucket 映射
        sub_type_to_bucket: dict[str, str] = {}
        for bucket_id, bucket_def in bucket_defs.items():
            for st in bucket_def.get("sub_types", []):
                sub_type_to_bucket[st] = bucket_id

        # 按桶分组
        bucketed: dict[str, list[CandidatePool]] = {}
        unbucketed: list[CandidatePool] = []
        for pool in candidate_pools:
            bucket_id = sub_type_to_bucket.get(pool.sub_type, "")
            if bucket_id:
                bucketed.setdefault(bucket_id, []).append(pool)
            else:
                unbucketed.append(pool)

        # 确定配额
        duration_tier = "short" if total_days <= 6 else ("medium" if total_days <= 10 else "long")
        user_tags = set(user_profile.get("must_have_tags", []))

        # 偏好桶的 sub_type 集合（用于判断哪些桶需要扩容）
        boosted_buckets: set[str] = set()
        for bucket_id, bucket_def in bucket_defs.items():
            # 检查桶的继承标签是否与用户偏好有交集
            inherited = set()
            tag_rules = taxonomy.get("tag_inheritance_rules", {}).get("by_sub_type", {})
            for st in bucket_def.get("sub_types", []):
                inherited.update(tag_rules.get(st, []))
            if user_tags & inherited:
                boosted_buckets.add(bucket_id)

        # 按桶取额
        final_pools: list[CandidatePool] = []
        for bucket_id, bucket_def in bucket_defs.items():
            items = bucketed.get(bucket_id, [])
            if not items:
                continue
            # 桶内按 grade 排序（S > A > B > C）
            items.sort(key=lambda p: _GRADE_ORDER.index(p.grade) if p.grade in _GRADE_ORDER else 99)

            quota = bucket_def.get("default_quota", {}).get(duration_tier, 3)
            min_q = bucket_def.get("min_quota", 1)

            if bucket_id in boosted_buckets:
                quota = int(quota * 1.5)  # 偏好桶扩容 50%
            else:
                quota = max(quota, min_q)  # 非偏好桶至少保底

            final_pools.extend(items[:quota])

        # must_visit 保护：确保 must_visit 的实体一定在池中
        final_ids = {p.entity_id for p in final_pools}
        for pool in candidate_pools:
            if pool.entity_id in must_visit and pool.entity_id not in final_ids:
                final_pools.append(pool)
                final_ids.add(pool.entity_id)

        # 惊喜候选保留（P4：local_benchmark + 质量达标）
        surprise_count = 0
        for pool in candidate_pools:
            if surprise_count >= cfg.surprise_slots:
                break
            if pool.entity_id in final_ids:
                continue
            tags_set = set(pool.tags) if pool.tags else set()
            is_local = "local_benchmark" in tags_set
            is_quality = pool.grade in ("S", "A", "B")
            if is_local and is_quality:
                final_pools.append(pool)
                final_ids.add(pool.entity_id)
                surprise_count += 1

        # 补入未分桶的（截断到总上限）
        remaining_slots = cfg.max_pool_size - len(final_pools)
        if remaining_slots > 0 and unbucketed:
            unbucketed.sort(
                key=lambda p: _GRADE_ORDER.index(p.grade) if p.grade in _GRADE_ORDER else 99
            )
            final_pools.extend(unbucketed[:remaining_slots])

        trace_log.append(
            f"Bucket truncation: {len(candidate_pools)} -> {len(final_pools)} "
            f"(boosted={boosted_buckets}, surprise={surprise_count})"
        )
        candidate_pools = final_pools

    logger.info(
        "[POI池] 完成过滤: %d -> %d -> %d pools. circle=%s, season=%s",
        count_after_base,
        count_after_filter,
        len(candidate_pools),
        region_summary.circle_name,
        travel_season,
    )
    for line in trace_log:
        logger.debug(f"  {line}")

    return candidate_pools
