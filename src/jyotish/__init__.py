"""JRE-003 Jyotish Coordinate and State layer — deterministic Jyotish facts.

Deterministic, interpretation-free coordinate/state facts on top of JRE-002:

- Sidereal/tropical coordinate classification: rashi, nakshatra, pada, DMS.
- Planet-to-planet geometry: exact angular separation, conjunction, aspects
  (ADR-004) — never "same house" semantics.
- Houses/lagna through an explicit, configurable ``HouseCuspProvider``
  (ADR-002); whole-sign derived in pure code.
- Continuous transit events (ingress/egress/stations) via a deterministic
  bisection engine (ADR-005).
- Eclipse facts through the ``EclipseProvider`` interface (ADR-006) — data
  only, no significance/causation claims.

GENERIC vs INDIVIDUAL: ``JyotishService.planetary_state`` /
``pair_geometry`` / ``events_between`` / ``eclipses`` never touch birth data;
``chart`` / ``transit_through_houses`` accept ``BirthData`` as request input
and echo it as ``birth_snapshot`` — personal data is never engine state.

This layer performs NO interpretation: no benefic/malefic, yogas, dashas,
gochar judgements, or predictions. Those belong to future engines.
"""

from .config import load_config
from .eclipse import (
    SWISSEPH_ECLIPSE_PROVIDER_ID,
    EclipseProvider,
    EclipseRegistry,
)
from .errors import (
    EclipseError,
    InvalidBirthDataError,
    InvalidConfigError,
    InvalidOrbError,
    JyotishError,
    ProviderCompatibilityError,
    TransitSearchError,
    UnsupportedHouseSystemError,
    UnsupportedReferencePointError,
)
from .geometry import (
    ASPECT_IDEAL_ANGLES,
    all_pairs,
    angular_separation_deg,
    normalized_separation_deg,
    pair_geometry,
)
from .houses import (
    SWISSEPH_HOUSE_PROVIDER_ID,
    HouseCuspProvider,
    HouseCuspRegistry,
    bhava_containing_longitude,
    compute_bhavas,
    whole_sign_cusps,
)
from .lagna import derive_lagna
from .models import (
    ApplyingSeparating,
    AspectKind,
    AspectRelationship,
    Bhava,
    BirthData,
    DmsValue,
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    GeographicVisibility,
    HouseCuspResult,
    HouseProviderMetadata,
    HouseSystem,
    HouseTransitEntry,
    JyotishConfig,
    LagnaState,
    NakshatraId,
    NatalChart,
    Pada,
    PairGeometry,
    PlanetState,
    RashiId,
    SearchMetadata,
    TransitEvent,
    TransitEventKind,
    TransitReferencePoint,
    TransitThroughHouses,
    ZodiacMode,
)
from .nakshatra import (
    NAKSHATRA_CATALOG_VERSION,
    NAKSHATRA_ORDER,
    degree_in_nakshatra,
    lord_of,
    nakshatra_of,
    pada_of,
)
from .position import classify_longitude, derive_planet_state
from .rashi import (
    RASHI_CATALOG_VERSION,
    RASHI_ORDER,
    degree_in_rashi,
    rashi_of,
)
from .serialize import (
    birth_from_dict,
    config_from_dict,
    eclipse_query_from_dict,
    planetary_request_from_dict,
    result_to_dict,
    result_to_json,
    transit_query_from_dict,
)
from .service import (
    JyotishService,
    default_eclipse_registry,
    default_house_registry,
    get_eclipse_provider,
    get_house_provider,
)
from .transit import ContinuousTransitEngine, iso_utc_to_jd, jd_to_iso_utc

__version__ = "0.3.0"

__all__ = [
    # facade
    "JyotishService",
    "default_house_registry",
    "default_eclipse_registry",
    "get_house_provider",
    "get_eclipse_provider",
    # config
    "JyotishConfig",
    "ZodiacMode",
    "load_config",
    # classification
    "RashiId",
    "NakshatraId",
    "Pada",
    "DmsValue",
    "PlanetState",
    "derive_planet_state",
    "classify_longitude",
    # catalogs
    "RASHI_CATALOG_VERSION",
    "RASHI_ORDER",
    "rashi_of",
    "degree_in_rashi",
    "NAKSHATRA_CATALOG_VERSION",
    "NAKSHATRA_ORDER",
    "nakshatra_of",
    "degree_in_nakshatra",
    "lord_of",
    "pada_of",
    # geometry
    "AspectKind",
    "ApplyingSeparating",
    "AspectRelationship",
    "PairGeometry",
    "ASPECT_IDEAL_ANGLES",
    "angular_separation_deg",
    "normalized_separation_deg",
    "pair_geometry",
    "all_pairs",
    # houses / lagna
    "HouseSystem",
    "HouseCuspProvider",
    "HouseCuspRegistry",
    "HouseCuspResult",
    "HouseProviderMetadata",
    "SWISSEPH_HOUSE_PROVIDER_ID",
    "whole_sign_cusps",
    "compute_bhavas",
    "bhava_containing_longitude",
    "Bhava",
    "LagnaState",
    "derive_lagna",
    "NatalChart",
    "BirthData",
    # transit
    "TransitEventKind",
    "TransitReferencePoint",
    "TransitEvent",
    "TransitThroughHouses",
    "HouseTransitEntry",
    "SearchMetadata",
    "ContinuousTransitEngine",
    "iso_utc_to_jd",
    "jd_to_iso_utc",
    # eclipse
    "EclipseKind",
    "EclipseClassification",
    "EclipseContact",
    "GeographicVisibility",
    "EclipseEvent",
    "EclipseProvider",
    "EclipseRegistry",
    "SWISSEPH_ECLIPSE_PROVIDER_ID",
    # serialization
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "birth_from_dict",
    "planetary_request_from_dict",
    "transit_query_from_dict",
    "eclipse_query_from_dict",
    # errors
    "JyotishError",
    "InvalidBirthDataError",
    "InvalidConfigError",
    "InvalidOrbError",
    "UnsupportedHouseSystemError",
    "UnsupportedReferencePointError",
    "TransitSearchError",
    "EclipseError",
    "ProviderCompatibilityError",
]
