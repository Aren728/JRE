"""JRE-015 Avastha (Planetary States) Engine — deterministic state assignment.

JRE-015 assigns classical Jagradadi, Deeptadi, and Baladi states to
planets based on their natal positions, computing composite strength
multipliers without predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/avastha/, config/avastha.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-014.

Core Models:
- ``JagradadiState``: JAGRAT, SWAPNA, SUSHUPTI
- ``DeeptadiState``: DEEPTA, SWASTHA, PRASANTA, DEENA, KSHUDHITA, KSHOBHITA
- ``BaladiState``: BALA, KUMARA, YUVA, VRIDDHA, MRITA
- ``AvasthaResult``: per-planet state with multiplier
- ``AvasthaReport``: complete state report

Service Interface:
- ``AvasthaService(config: AvasthaConfig)``
- ``calculate_avasthas(planet_states) -> AvasthaReport``
"""

from .config import load_config
from .errors import (
    AvasthaComputationError,
    AvasthaError,
    InvalidAvasthaConfigError,
    InvalidAvasthaRequestError,
)
from .models import (
    AVASTHA_VERSION,
    AvasthaConfig,
    AvasthaReport,
    AvasthaResult,
    BaladiState,
    DeeptadiState,
    JagradadiState,
    compute_deeptadi,
    compute_jagradadi,
    validate,
)
from .serialize import (
    avastha_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import AvasthaService

__version__ = AVASTHA_VERSION

__all__ = [
    # service
    "AvasthaService",
    # config
    "load_config",
    "validate",
    "AvasthaConfig",
    # models
    "JagradadiState",
    "DeeptadiState",
    "BaladiState",
    "AvasthaResult",
    "AvasthaReport",
    # derivation helpers
    "compute_jagradadi",
    "compute_deeptadi",
    # constants
    "AVASTHA_VERSION",
    # errors
    "AvasthaError",
    "InvalidAvasthaConfigError",
    "InvalidAvasthaRequestError",
    "AvasthaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "avastha_config_from_dict",
]
