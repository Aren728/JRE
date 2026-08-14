"""JRE-005 Bhava / House engine — derived bhava/house computational state.

Consumes ONLY the ``jyotish`` public API and the standard library
(ADR-013). JRE-005 computes derived house facts (occupancy, lordship,
ownership, relative houses, categories, cusp proximity, geometric
aspect echoes, transit-house echoes) with full provenance
(ADR-016) — and performs NO interpretation: no yoga detection, no
benefic/malefic, no dasha, no drishti doctrine, no rule resolution,
no prediction. Those belong to JRE-004 and future engines.
"""

from .config import load_config
from .derive import (
    derive_house_analysis,
    derive_transit_analysis,
    house_categories,
    near_cusp,
    relative_house,
    shortest_arc_deg,
    whole_sign_house,
)
from .errors import (
    BhavaError,
    InconsistentChartError,
    InvalidAnalysisRequestError,
    InvalidBhavaConfigError,
    UnplacedBodyError,
    UnsupportedReferenceError,
)
from .models import (
    GOLDEN_VERSION,
    SIGN_GRID_FRAME_SUPPORTED,
    AspectToHouseFact,
    BhavaConfig,
    BoundaryKind,
    ChartEcho,
    DerivationBlock,
    DerivationId,
    DerivedHouseFact,
    FactFrame,
    HouseAnalysis,
    HouseAnalysisResult,
    HouseCategory,
    HouseOwnershipFact,
    OccupancyStatus,
    PlanetHouseFact,
    RelativeHouseFact,
    RelativeHouseFrame,
    TransitHouseAnalysis,
    TransitHouseFact,
    UnplacedBodyBehavior,
    validate,
)
from .serialize import (
    analysis_request_from_dict,
    result_to_dict,
    result_to_json,
    transit_request_from_dict,
)
from .service import BhavaService

__version__ = "0.2.0"

__all__ = [
    # service
    "BhavaService",
    # config
    "load_config",
    "validate",
    "BhavaConfig",
    # models
    "HouseAnalysisResult",
    "HouseAnalysis",
    "TransitHouseAnalysis",
    "DerivedHouseFact",
    "PlanetHouseFact",
    "HouseOwnershipFact",
    "RelativeHouseFact",
    "AspectToHouseFact",
    "TransitHouseFact",
    "DerivationBlock",
    "ChartEcho",
    # enums
    "OccupancyStatus",
    "BoundaryKind",
    "HouseCategory",
    "RelativeHouseFrame",
    "UnplacedBodyBehavior",
    "FactFrame",
    "DerivationId",
    # constants
    "SIGN_GRID_FRAME_SUPPORTED",
    "GOLDEN_VERSION",
    # derivation functions (SPEC §4/S8 — public, unit-testable)
    "shortest_arc_deg",
    "near_cusp",
    "house_categories",
    "relative_house",
    "whole_sign_house",
    "derive_house_analysis",
    "derive_transit_analysis",
    # errors
    "BhavaError",
    "InvalidAnalysisRequestError",
    "InvalidBhavaConfigError",
    "InconsistentChartError",
    "UnplacedBodyError",
    "UnsupportedReferenceError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "analysis_request_from_dict",
    "transit_request_from_dict",
]
