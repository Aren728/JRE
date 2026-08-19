"""JRE-016 Ashtakavarga (eight-fold strength) Engine — deterministic bindu computation.

JRE-016 computes Bhinnashtakavarga (individual planet points) and
Sarvashtakavarga (total points) for all 12 rashis, strictly without
predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/ashtakavarga/, config/ashtakavarga.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-015.

Core Models:
- ``PlanetAshtakavarga``: per-planet bindu scores
- ``Sarvashtakavarga``: total bindu scores
- ``AshtakavargaReport``: complete report

Service Interface:
- ``AshtakavargaService(config: AshtakavargaConfig)``
- ``calculate_ashtakavarga(planet_states) -> AshtakavargaReport``
"""

from .config import load_config
from .errors import (
    AshtakavargaComputationError,
    AshtakavargaError,
    InvalidAshtakavargaConfigError,
    InvalidAshtakavargaRequestError,
)
from .models import (
    ASHTAKAVARGA_VERSION,
    AshtakavargaConfig,
    AshtakavargaReport,
    PlanetAshtakavarga,
    Sarvashtakavarga,
    compute_planet_bindus,
    compute_sarvashtakavarga,
)
from .serialize import (
    ashtakavarga_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import AshtakavargaService

__version__ = ASHTAKAVARGA_VERSION

__all__ = [
    # service
    "AshtakavargaService",
    # config
    "load_config",
    "AshtakavargaConfig",
    # models
    "PlanetAshtakavarga",
    "Sarvashtakavarga",
    "AshtakavargaReport",
    # derivation helpers
    "compute_planet_bindus",
    "compute_sarvashtakavarga",
    # constants
    "ASHTAKAVARGA_VERSION",
    # errors
    "AshtakavargaError",
    "InvalidAshtakavargaConfigError",
    "InvalidAshtakavargaRequestError",
    "AshtakavargaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "ashtakavarga_config_from_dict",
]
