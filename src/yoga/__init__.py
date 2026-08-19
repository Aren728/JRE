"""JRE-013 Yoga (planetary combination) Engine — deterministic yoga identification.

JRE-013 identifies structural planetary combinations (classical Yogas)
from natal chart facts, Shadbala strengths, and Drik aspect graphs.
It performs NO predictive interpretation (e.g., "this yoga causes wealth").

Strict Boundaries:
- IN SCOPE: src/yoga/, config/yoga.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-012.

Core Models:
- ``YogaId``: GAJAKESARI, RAJA, DHANA, VIPARITA_RAJA
- ``YogaCondition``: the specific rule met
- ``YogaResult``: one yoga evaluation
- ``YogaReport``: complete chart yoga report

Service Interface:
- ``YogaService(config: YogaConfig)``
- ``identify_yogas(planet_states, lagna_sign, bala_report, drik_result) -> YogaReport``
"""

from .config import load_config
from .errors import (
    InvalidYogaConfigError,
    InvalidYogaRequestError,
    YogaComputationError,
    YogaError,
)
from .models import (
    YOGA_VERSION,
    ConnectionType,
    YogaCondition,
    YogaConfig,
    YogaId,
    YogaReport,
    YogaResult,
    YogaRuleType,
    validate,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    yoga_config_from_dict,
)
from .service import YogaService

__version__ = YOGA_VERSION

__all__ = [
    # service
    "YogaService",
    # config
    "load_config",
    "validate",
    "YogaConfig",
    # models
    "YogaId",
    "YogaRuleType",
    "ConnectionType",
    "YogaCondition",
    "YogaResult",
    "YogaReport",
    # constants
    "YOGA_VERSION",
    # errors
    "YogaError",
    "InvalidYogaConfigError",
    "InvalidYogaRequestError",
    "YogaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "yoga_config_from_dict",
]
