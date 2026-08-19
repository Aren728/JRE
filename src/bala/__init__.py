"""JRE-011 Bala (Shadbala) Engine — deterministic planetary strength.

JRE-011 computes the Shadbala (six-fold planetary strength) from
positional, temporal, directional, motional, natural, and aspectual
factors.  It produces deterministic numerical strength values without
any predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/bala/, config/bala.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-010.

Core Models:
- ``ShadbalaComponents``: six balas and sub-components
- ``ShadbalaResult``: per-planet strength result
- ``ShadbalaReport``: full report for all computed planets
- ``BalaConfig``: immutable configuration

Service Interface:
- ``BalaService(config: BalaConfig)``
- ``calculate_shadbala(planet_states, lagna_state) -> ShadbalaReport``
"""

from .config import load_config
from .errors import (
    BalaComputationError,
    BalaError,
    InvalidBalaConfigError,
    InvalidBalaRequestError,
)
from .models import (
    BALA_PLANETS,
    BALA_VERSION,
    BalaConfig,
    BalaSystem,
    IshtaKashtaPhala,
    KalaBalaComponents,
    ShadbalaComponents,
    ShadbalaReport,
    ShadbalaResult,
    SthanaBalaComponents,
    validate,
)
from .serialize import (
    bala_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import BalaService

__version__ = BALA_VERSION

__all__ = [
    # service
    "BalaService",
    # config
    "load_config",
    "validate",
    "BalaConfig",
    # models
    "ShadbalaComponents",
    "ShadbalaResult",
    "ShadbalaReport",
    "SthanaBalaComponents",
    "KalaBalaComponents",
    "IshtaKashtaPhala",
    "BalaSystem",
    # constants
    "BALA_VERSION",
    "BALA_PLANETS",
    # errors
    "BalaError",
    "InvalidBalaConfigError",
    "InvalidBalaRequestError",
    "BalaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "bala_config_from_dict",
]
