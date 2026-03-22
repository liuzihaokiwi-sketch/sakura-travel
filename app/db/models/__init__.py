# Import all models so Alembic autogenerate can detect them.
# The order matters for foreign key resolution.

from app.db.models.catalog import (  # noqa: F401
    EntityBase,
    EntityEditorNote,
    EntityMedia,
    EntityTag,
    Hotel,
    HotelAreaGuide,
    Poi,
    Restaurant,
)
from app.db.models.snapshots import (  # noqa: F401
    FlightOfferSnapshot,
    HotelOfferLine,
    HotelOfferSnapshot,
    PoiOpeningSnapshot,
    SourceSnapshot,
    WeatherSnapshot,
)
from app.db.models.business import (  # noqa: F401
    Order,
    ProductSku,
    ReviewAction,
    ReviewJob,
    TripProfile,
    TripRequest,
    TripVersion,
    User,
)
from app.db.models.derived import (  # noqa: F401
    CandidateSet,
    EntityScore,
    ExportAsset,
    ExportJob,
    ItineraryDay,
    ItineraryItem,
    ItineraryPlan,
    ItineraryScore,
    PlanArtifact,
    PlannerRun,
    RenderTemplate,
    RouteMatrixCache,
    RouteTemplate,
)
from app.db.models.detail_forms import (  # noqa: F401
    DetailForm,
    DetailFormStep,
)
from app.db.models.trace import (  # noqa: F401
    ExportLog,
    FragmentHitLog,
    GenerationRun,
    GenerationStepRun,
    PromptRunLog,
    ReviewActionLog,
    RuleEvaluationLog,
)
from app.db.models.fragments import (  # noqa: F401
    FragmentCompatibility,
    FragmentDistillationQueue,
    FragmentEmbedding,
    FragmentEntity,
    FragmentUsageStats,
    GuideFragment,
)
from app.db.models.city_circles import (  # noqa: F401
    ActivityCluster,
    CircleEntityRole,
    CityCircle,
    HotelStrategyPreset,
)
from app.db.models.temporal import (  # noqa: F401
    EntityTemporalProfile,
)
from app.db.models.catalog import (  # noqa: F401 - T1/T3/T10 + 图片采集
    EntityAlias,
    EntityFieldProvenance,
    EntityMappingReview,
    EntityDescription,
    EntityReviewSignal,
)
from app.db.models.corridors import (  # noqa: F401 - T14
    Corridor,
    CorridorAliasMap,
)
from app.db.models.page_assets import (  # noqa: F401 - T12
    PageHeroRegistry,
)
from app.db.models.derived import (  # noqa: F401 - T11 追加
    GenerationDecision,
)
from app.db.models.operator_overrides import (  # noqa: F401 - L4-01
    OperatorOverride,
)
from app.db.models.live_risk_rules import (  # noqa: F401 - L4-03
    LiveRiskRule,
)
from app.db.models.config_center import (  # noqa: F401 - 运营配置中心
    ConfigPack,
    ConfigPackVersion,
    ConfigScope,
    ConfigPreviewRun,
    ConfigReleaseRecord,
)
from app.db.models.soft_rules import (  # noqa: F401
    AreaProfile,
    AudienceFit,
    EditorialSeedOverride,
    EntityOperatingFact,
    EntitySoftScore,
    FeatureFlag,
    PreviewTriggerScore,
    ProductConfig,
    SeasonalEvent,
    SegmentWeightPack,
    SoftRuleExplanation,
    SoftRuleFeedbackLog,
    StageWeightPack,
    SwapCandidateSoftScore,
    TimeslotRule,
    TransportLink,
    UserEvent,
)

__all__ = [
    # Catalog
    "EntityBase", "Poi", "Hotel", "Restaurant",
    "EntityTag", "EntityMedia", "EntityEditorNote", "HotelAreaGuide",
    "EntityAlias", "EntityFieldProvenance", "EntityMappingReview",
    # Snapshots
    "SourceSnapshot", "HotelOfferSnapshot", "HotelOfferLine",
    "FlightOfferSnapshot", "PoiOpeningSnapshot", "WeatherSnapshot",
    # Business
    "User", "ProductSku", "Order", "TripRequest", "TripProfile",
    "TripVersion", "ReviewJob", "ReviewAction",
    # Derived
    "EntityScore", "ItineraryPlan", "ItineraryScore", "PlannerRun",
    "CandidateSet", "RouteMatrixCache", "ItineraryDay", "ItineraryItem",
    "RouteTemplate", "RenderTemplate", "ExportJob", "ExportAsset", "PlanArtifact",
    # Soft Rules
    "EntitySoftScore", "EditorialSeedOverride", "SoftRuleExplanation",
    "SegmentWeightPack", "StageWeightPack", "PreviewTriggerScore",
    "SwapCandidateSoftScore", "SoftRuleFeedbackLog",
    "AreaProfile", "TimeslotRule", "SeasonalEvent", "TransportLink",
    "AudienceFit", "EntityOperatingFact", "ProductConfig", "FeatureFlag", "UserEvent",
    # Detail Forms
    "DetailForm", "DetailFormStep",
    # Trace
    "GenerationRun", "GenerationStepRun", "FragmentHitLog",
    "RuleEvaluationLog", "PromptRunLog", "ReviewActionLog", "ExportLog",
    # Fragments
    "GuideFragment", "FragmentEntity", "FragmentEmbedding",
    "FragmentCompatibility", "FragmentUsageStats", "FragmentDistillationQueue",
    # City Circles
    "CityCircle", "ActivityCluster", "CircleEntityRole", "HotelStrategyPreset",
    # Corridors
    "Corridor", "CorridorAliasMap",
    # Temporal
    "EntityTemporalProfile",
    # Page Assets
    "PageHeroRegistry",
    # Generation Decisions
    "GenerationDecision",
    # Operator Overrides (L4-01)
    "OperatorOverride",
    # Live Risk Rules (L4-03)
    "LiveRiskRule",
    # Config Center
    "ConfigPack", "ConfigPackVersion", "ConfigScope",
    "ConfigPreviewRun", "ConfigReleaseRecord",
]
