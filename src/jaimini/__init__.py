"""JRE-018 Jaimini (Chara Dasha / Argala) Engine — deterministic sign-based
dasha and planetary intervention computation.

JRE-018 computes the Chara Dasha sequence (sign-based periods) and
Argala (planetary interventions) for a given natal chart, strictly
as structural data points without predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/jaimini/, config/jaimini.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-017.

Core Models:
- ``CharaDashaPeriod``: rashi, start_utc, end_utc, lord
- ``ArgalaResult``: target_rashi, intervening_planets, obstructing_planets
- ``JaiminiReport``: chara_dasha, argala

Service Interface:
- ``JaiminiService(config: JaiminiConfig)``
- ``calculate_jaimini(lagna_rashi, planet_states) -> JaiminiReport``
"""

from .config import load_config
from .errors import (
    InvalidJaiminiConfigError,
    InvalidJaiminiRequestError,
    JaiminiComputationError,
    JaiminiError,
)
from .models import (
    JAIMINI_VERSION,
    ArgalaResult,
    CharaDashaPeriod,
    JaiminiConfig,
    JaiminiReport,
    LagnaNature,
    classify_lagna_nature,
    compute_argala,
    compute_chara_dasha_sequence,
    compute_starting_sign,
)
from .serialize import (
    jaimini_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import JaiminiService

__version__ = JAIMINI_VERSION

__all__ = [
    # service
    "JaiminiService",
    # config
    "load_config",
    "JaiminiConfig",
    # models
    "CharaDashaPeriod",
    "ArgalaResult",
    "JaiminiReport",
    "LagnaNature",
    # derivation helpers
    "classify_lagna_nature",
    "compute_starting_sign",
    "compute_chara_dasha_sequence",
    "compute_argala",
    # constants
    "JAIMINI_VERSION",
    # errors
    "JaiminiError",
    "InvalidJaiminiConfigError",
    "InvalidJaiminiRequestError",
    "JaiminiComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "jaimini_config_from_dict",
]
