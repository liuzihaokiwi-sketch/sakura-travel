"""
Data models for planning_v2 module.

Defines core dataclasses for trip planning workflow, including time windows,
user constraints, region summaries, candidate pools, daily constraints,
feasibility checks, and generation steps.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Circle registry (singleton cache)
# ---------------------------------------------------------------------------

_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "circle_registry.json"
_registry_cache: dict | None = None


def _load_registry() -> dict:
    """加载 circle_registry.json，带缓存。"""
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    try:
        with open(_REGISTRY_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        # 过滤掉以 _ 开头的文档字段
        _registry_cache = {k: v for k, v in raw.items() if not k.startswith("_")}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        _logger.warning("无法加载 circle_registry.json: %s", e)
        _registry_cache = {}
    return _registry_cache


@dataclass
class CircleProfile:
    """城市圈环境描述 — 管线的一等公民上下文。

    所有 step 从此结构获取地区相关信息，不允许硬编码。
    数据来源：data/circle_registry.json。
    """

    circle_id: str
    name: str
    region_desc: str
    country: str
    currency: str
    cny_rate: float
    timezone: str
    default_location: tuple[float, float]
    cities: list[str]
    data_dir: str
    budget_config: dict

    @property
    def taxonomy_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "data" / self.data_dir / "taxonomy.json"

    @property
    def corridor_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[3]
            / "data"
            / self.data_dir
            / "corridor_definitions.json"
        )

    def validate(self) -> list[str]:
        """校验圈配置资产是否齐备。返回缺失项列表，空列表=全部就绪。"""
        issues: list[str] = []

        # 1. taxonomy.json 存在且有必要字段
        if not self.taxonomy_path.exists():
            issues.append(f"taxonomy 缺失: {self.taxonomy_path}")
        else:
            try:
                import json as _json

                with open(self.taxonomy_path, encoding="utf-8") as f:
                    tax = _json.load(f)
                for key in ("regions", "sub_region_codes"):
                    if key not in tax:
                        issues.append(f"taxonomy 缺少字段: {key}")
            except Exception as e:
                issues.append(f"taxonomy 无法解析: {e}")

        # 2. corridor_definitions.json 存在
        if not self.corridor_path.exists():
            issues.append(f"corridor_definitions 缺失: {self.corridor_path}")

        # 3. budget_config 必要键
        _REQUIRED_BUDGET_KEYS = {
            "hotel_per_night",
            "transport_per_day",
            "food_floor_per_day",
            "default_admission",
            "restaurant_price_cap",
            "admission_cap",
        }
        missing_budget = _REQUIRED_BUDGET_KEYS - set(self.budget_config.keys())
        if missing_budget:
            issues.append(f"budget_config 缺少: {missing_budget}")

        # 4. budget 子键完整性（每个 tier 配置都要有 budget/mid/premium/luxury）
        _TIERS = {"budget", "mid", "premium", "luxury"}
        for bkey in ("hotel_per_night", "transport_per_day", "food_floor_per_day"):
            sub = self.budget_config.get(bkey, {})
            missing_tiers = _TIERS - set(sub.keys())
            if missing_tiers:
                issues.append(f"budget_config.{bkey} 缺少档位: {missing_tiers}")

        # 5. 基本字段非空
        if not self.cities:
            issues.append("cities 为空")
        if not self.region_desc:
            issues.append("region_desc 为空")

        return issues

    @classmethod
    def from_registry(cls, circle_id: str) -> "CircleProfile":
        """从 circle_registry.json 加载指定圈。"""
        registry = _load_registry()
        data = registry.get(circle_id)
        if not data:
            raise ValueError(f"circle_registry.json 中未找到圈: {circle_id}")
        loc = data.get("default_location", [0, 0])
        return cls(
            circle_id=circle_id,
            name=data["name"],
            region_desc=data["region_desc"],
            country=data["country"],
            currency=data["currency"],
            cny_rate=data.get("cny_rate", 1.0),
            timezone=data["timezone"],
            default_location=(loc[0], loc[1]),
            cities=data["cities"],
            data_dir=data["data_dir"],
            budget_config=data.get("budget_config", {}),
        )

    @classmethod
    def infer_from_cities(cls, cities: list[str]) -> "CircleProfile":
        """根据城市列表推断所属圈。遍历 registry 找交集最大的圈。"""
        registry = _load_registry()
        if not registry:
            raise ValueError("circle_registry.json 为空或未加载")

        cities_lower = {c.lower() for c in cities}
        best_id, best_overlap = None, 0

        for cid, data in registry.items():
            circle_cities = {c.lower() for c in data.get("cities", [])}
            overlap = len(cities_lower & circle_cities)
            if overlap > best_overlap:
                best_overlap = overlap
                best_id = cid

        if best_id is None:
            raise ValueError(f"无法从城市列表推断圈: {cities}")
        return cls.from_registry(best_id)


@dataclass
class TimeWindow:
    """Represents a time window with start, end, and duration.

    Attributes:
        start: Start time in HH:MM format
        end: End time in HH:MM format
        duration_mins: Duration in minutes
    """

    start: str
    end: str
    duration_mins: int


@dataclass
class UserConstraints:
    """User constraints for trip planning.

    Encapsulates trip window, user profile, and various constraints
    including must-visit items, do-not-go locations, and visited items.

    Attributes:
        trip_window: Dict with keys {start_date, end_date, total_days}
        user_profile: Dict with keys {party_type, budget_tier, must_have_tags, nice_to_have_tags}
        constraints: Dict with keys {must_visit, do_not_go, visited, booked_items}
    """

    trip_window: dict
    user_profile: dict
    constraints: dict


@dataclass
class RegionSummary:
    """Summary statistics for a geographic region/circle.

    Provides overview of available entities and their distribution
    across types and quality grades.

    Attributes:
        circle_name: Name of the city circle (e.g., "kansai", "guangfu")
        cities: List of city names in this region
        entity_count: Total number of entities
        entities_by_type: Dict mapping entity type to count {poi, restaurant, hotel, ...}
        grade_distribution: Dict mapping grade letter to count {S, A, B, C, ...}
    """

    circle_name: str
    cities: list
    entity_count: int
    entities_by_type: dict
    grade_distribution: dict


@dataclass
class CandidatePool:
    """Represents a single candidate entity for itinerary planning.

    Contains all metadata needed for feasibility checking and scheduling
    including location, tags, time requirements, costs, and review signals.

    Attributes:
        entity_id: Unique identifier for the entity
        name_zh: Chinese name of the entity
        entity_type: Type of entity (poi, restaurant, hotel, event, etc.)
        city_code: City code the entity belongs to
        grade: Quality grade (S/A/B/C)
        latitude: Geographic latitude
        longitude: Geographic longitude
        tags: List of semantic tags (e.g., "outdoor", "cultural", "seasonal")
        visit_minutes: Recommended visit duration in minutes
        cost_local: Estimated cost in local currency (JPY/CNY depending on circle)
        currency: Currency code (JPY, CNY, etc.)
        sub_type: Fine-grained type from entity_base (e.g., history_religion, onsen_resort)
        open_hours: Dict with opening time info
        review_signals: Dict with review metadata and sentiment signals
    """

    entity_id: str
    name_zh: str
    entity_type: str
    grade: str
    latitude: float
    longitude: float
    tags: list
    visit_minutes: int
    cost_local: int
    city_code: str = ""
    currency: str = "JPY"
    sub_type: str = ""
    open_hours: dict | None = field(default_factory=dict)
    review_signals: dict | None = field(default_factory=dict)


@dataclass
class DailyConstraints:
    """Constraints and context for a single day in the itinerary.

    Captures day-specific information including weather, operating hours,
    closed entities, transportation limitations, and anchorpoints.

    Attributes:
        date: Date in YYYY-MM-DD format
        day_of_week: Day name (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
        sunrise: Sunrise time in HH:MM format
        sunset: Sunset time in HH:MM format
        closed_entities: List of entity_ids that are closed on this day
        low_freq_transits: List of dicts describing low-frequency transit options
        anchors: List of dicts for fixed timepoint items (flights, booked reservations)
        hotel_breakfast_included: Whether hotel breakfast is included
        hotel_dinner_included: Whether hotel dinner is included
    """

    date: str
    day_of_week: str
    sunrise: str
    sunset: str
    closed_entities: list = field(default_factory=list)
    low_freq_transits: list = field(default_factory=list)
    anchors: list = field(default_factory=list)
    hotel_breakfast_included: bool = False
    hotel_dinner_included: bool = False


@dataclass
class FeasibilityResult:
    """Result of feasibility checking for a proposed itinerary segment.

    Contains pass/fail status along with violations and recommendations.

    Attributes:
        status: Overall status (pass, fail, warning)
        violations: List of dicts describing constraint violations
        suggestions: List of suggestions to resolve violations
    """

    status: str
    violations: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)


@dataclass
class GenerationStep:
    """Tracks a single step in the itinerary generation pipeline.

    Records execution metadata including input hash, output, errors,
    and token usage for monitoring and debugging.

    Attributes:
        step_id: Step identifier (01, 02, 03, etc.)
        status: Execution status (running, success, failed)
        input_hash: Hash of input data for caching/deduplication
        output: Step output data
        error: Error message if status is failed
        thinking_tokens: Number of tokens used for extended thinking
    """

    step_id: str
    status: str
    input_hash: str
    output: dict
    error: str | None = None
    thinking_tokens: int = 0


# Type aliases for common patterns
EntityType = str  # poi, restaurant, hotel, event, etc.
Grade = str  # S, A, B, C, etc.
