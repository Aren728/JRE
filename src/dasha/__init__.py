"""JRE-010 Dasha / Planetary Period Engine — deterministic Dasha computation.

JRE-010 computes the Vimshottari Dasha timeline (Mahadasha, Antardasha,
Pratyantardasha) from the Moon's natal Nakshatra/Pada and defined period
lengths.  It performs NO prediction, interpretation, auspiciousness
judgment, or inference; NO position/ayanamsa recalculation; NO ephemeris
access.

Strict Boundaries:
- IN SCOPE: src/dasha/, config/dasha.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-009.

Core Models:
- ``DashaPeriod``: start_utc, end_utc, mahadasha_lord, antardasha_lord,
  pratyantardasha_lord
- ``DashaTimeline``: birth_nakshatra, birth_pada, balance_at_birth, periods
- ``DashaConfig``: default_system, max_depth, vimshottari_years

Service Interface:
- ``DashaService(config: DashaConfig)``
- ``generate_timeline(moon_state, birth_time, duration_years) -> DashaTimeline``
- ``get_lord_at(instant, timeline) -> dict[str, Planet | None]``
"""

from .config import load_config
from .errors import (
    DashaComputationError,
    DashaError,
    InvalidDashaConfigError,
    InvalidDashaRequestError,
)
from .models import (
    DASHA_VERSION,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN_DEG,
    VIMSHOTTARI_CYCLE_YEARS,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    DashaTimeline,
    compute_antardasha_order,
    compute_balance_at_birth,
    compute_balance_at_birth_from_state,
    validate,
)
from .serialize import (
    dasha_config_from_dict,
    dasha_period_from_dict,
    dasha_timeline_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import DashaService

__version__ = DASHA_VERSION

__all__ = [
    # service
    "DashaService",
    # config
    "load_config",
    "validate",
    "DashaConfig",
    # models
    "DashaPeriod",
    "DashaTimeline",
    "DashaSystem",
    # constants
    "DASHA_VERSION",
    "VIMSHOTTARI_CYCLE_YEARS",
    "VIMSHOTTARI_ORDER",
    "VIMSHOTTARI_YEARS",
    "NAKSHATRA_LORDS",
    "NAKSHATRA_SPAN_DEG",
    # derivation helpers (public, unit-testable)
    "compute_balance_at_birth",
    "compute_balance_at_birth_from_state",
    "compute_antardasha_order",
    # errors
    "DashaError",
    "InvalidDashaConfigError",
    "InvalidDashaRequestError",
    "DashaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "dasha_config_from_dict",
    "dasha_period_from_dict",
    "dasha_timeline_from_dict",
]
