"""JRE-017 Tajika (Varshaphala / annual chart) Engine — deterministic annual chart computation.

JRE-017 computes the Muntha, Varsheshwar, and classical Sahams for
a given Solar Return chart, strictly as structural data points without
predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/tajika/, config/tajika.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-016.

Core Models:
- ``MunthaResult``: rashi, house, lord
- ``VarsheshwarResult``: planet, basis
- ``SahamResult``: saham_name, rashi, degree
- ``TajikaReport``: muntha, varsheshwar, sahams

Service Interface:
- ``TajikaService(config: TajikaConfig)``
- ``calculate_tajika(...) -> TajikaReport``
"""

from .config import load_config
from .errors import (
    InvalidTajikaConfigError,
    InvalidTajikaRequestError,
    TajikaComputationError,
    TajikaError,
)
from .models import (
    TAJIKA_VERSION,
    MunthaResult,
    SahamResult,
    SahamType,
    TajikaConfig,
    TajikaReport,
    VarsheshwarBasis,
    VarsheshwarResult,
    compute_muntha_lord,
    compute_muntha_rashi,
    compute_saham_longitude,
    compute_varsheshwar,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    tajika_config_from_dict,
)
from .service import TajikaService

__version__ = TAJIKA_VERSION

__all__ = [
    # service
    "TajikaService",
    # config
    "load_config",
    "TajikaConfig",
    # models
    "MunthaResult",
    "VarsheshwarResult",
    "SahamResult",
    "SahamType",
    "VarsheshwarBasis",
    "TajikaReport",
    # derivation helpers
    "compute_muntha_rashi",
    "compute_muntha_lord",
    "compute_varsheshwar",
    "compute_saham_longitude",
    # constants
    "TAJIKA_VERSION",
    # errors
    "TajikaError",
    "InvalidTajikaConfigError",
    "InvalidTajikaRequestError",
    "TajikaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "tajika_config_from_dict",
]
