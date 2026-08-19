"""JRE-012 Drik (Aspect) Engine — deterministic classical aspect graph.

JRE-012 computes the classical Jyotish aspect graph from natal planet
positions.  It applies standard and special aspects (Mars 4/8, Jupiter
5/9, Saturn 3/10) and outputs a structured aspect graph without
predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/drik/, config/drik.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-011.

Core Models:
- ``AspectType``: STANDARD, MARS_SPECIAL, JUPITER_SPECIAL, SATURN_SPECIAL
- ``AspectRule``: source planet + target house offset + type
- ``AspectApplication``: computed aspect with orb and direction
- ``DrikResult``: complete aspect graph

Service Interface:
- ``DrikService(config: DrikConfig)``
- ``calculate_aspects(planet_states) -> DrikResult``
"""

from .config import load_config
from .errors import (
    DrikComputationError,
    DrikError,
    InvalidDrikConfigError,
    InvalidDrikRequestError,
)
from .models import (
    DRIK_VERSION,
    AspectApplication,
    AspectDirection,
    AspectRule,
    AspectType,
    DrikConfig,
    DrikResult,
    validate,
)
from .serialize import (
    drik_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import DrikService

__version__ = DRIK_VERSION

__all__ = [
    # service
    "DrikService",
    # config
    "load_config",
    "validate",
    "DrikConfig",
    # models
    "AspectType",
    "AspectDirection",
    "AspectRule",
    "AspectApplication",
    "DrikResult",
    # constants
    "DRIK_VERSION",
    # errors
    "DrikError",
    "InvalidDrikConfigError",
    "InvalidDrikRequestError",
    "DrikComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "drik_config_from_dict",
]
