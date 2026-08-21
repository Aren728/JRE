"""JRE-019 Prashna (Horary) Engine — deterministic query chart casting
and structural house mapping.

JRE-019 computes the Query Ascendant (Prashna Lagna) and maps the
relevant houses for a specific inquiry based on the exact time of
the query, strictly as structural data points without predictive
interpretation.

Strict Boundaries:
- IN SCOPE: src/prashna/, config/prashna.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-018.

Core Models:
- ``QueryLocation``: latitude, longitude
- ``PrashnaChart``: query_time_utc, query_location, prashna_lagna, query_moon_rashi
- ``PrashnaHouseMapping``: query_category, primary_house, secondary_house
- ``PrashnaReport``: chart, house_mapping

Service Interface:
- ``PrashnaService(config: PrashnaConfig)``
- ``cast_prashna(query_time_utc, query_location, query_category, planet_states) -> PrashnaReport``
"""

from .config import load_config
from .errors import (
    InvalidPrashnaConfigError,
    InvalidPrashnaRequestError,
    PrashnaComputationError,
    PrashnaError,
)
from .models import (
    PRASHNA_VERSION,
    PrashnaCategory,
    PrashnaChart,
    PrashnaConfig,
    PrashnaHouseMapping,
    PrashnaReport,
    QueryLocation,
    compute_prashna_lagna,
    resolve_house_mapping,
)
from .serialize import (
    prashna_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import PrashnaService

__version__ = PRASHNA_VERSION

__all__ = [
    # service
    "PrashnaService",
    # config
    "load_config",
    "PrashnaConfig",
    # models
    "PrashnaChart",
    "PrashnaHouseMapping",
    "PrashnaReport",
    "PrashnaCategory",
    "QueryLocation",
    # derivation helpers
    "compute_prashna_lagna",
    "resolve_house_mapping",
    # constants
    "PRASHNA_VERSION",
    # errors
    "PrashnaError",
    "InvalidPrashnaConfigError",
    "InvalidPrashnaRequestError",
    "PrashnaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "prashna_config_from_dict",
]
