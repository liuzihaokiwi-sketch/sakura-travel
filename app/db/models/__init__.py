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
]