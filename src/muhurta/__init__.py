"""JRE-020 Muhurta (Electional) Engine — deterministic time-window
structural fitness evaluation.

JRE-020 computes the Panchanga state and evaluates the structural
fitness of specific time windows for classical categories, strictly
as structural data points without predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/muhurta/, config/muhurta.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-019.

Core Models:
- ``PanchangaState``: tithi, vara, nakshatra, yoga, karana
- ``MuhurtaWindow``: start_utc, end_utc
- ``MuhurtaEvaluation``: window, panchanga, structural_flags, fitness_score

Service Interface:
- ``MuhurtaService(config: MuhurtaConfig)``
- ``evaluate_window(window, category, panchanga) -> MuhurtaEvaluation``
"""

from .config import load_config
from .errors import (
    InvalidMuhurtaConfigError,
    InvalidMuhurtaRequestError,
    MuhurtaComputationError,
    MuhurtaError,
)
from .models import (
    MUHURTA_VERSION,
    CategoryRule,
    Karana,
    MuhurtaCategory,
    MuhurtaConfig,
    MuhurtaEvaluation,
    MuhurtaWindow,
    PanchangaState,
    Tithi,
    Var,
    Yoga,
    compute_fitness_score,
    evaluate_panchanga,
)
from .serialize import (
    muhurta_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import MuhurtaService

__version__ = MUHURTA_VERSION

__all__ = [
    # service
    "MuhurtaService",
    # config
    "load_config",
    "MuhurtaConfig",
    # models
    "PanchangaState",
    "MuhurtaWindow",
    "MuhurtaEvaluation",
    "MuhurtaCategory",
    "CategoryRule",
    "Tithi",
    "Var",
    "Yoga",
    "Karana",
    # derivation helpers
    "evaluate_panchanga",
    "compute_fitness_score",
    # constants
    "MUHURTA_VERSION",
    # errors
    "MuhurtaError",
    "InvalidMuhurtaConfigError",
    "InvalidMuhurtaRequestError",
    "MuhurtaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "muhurta_config_from_dict",
]
