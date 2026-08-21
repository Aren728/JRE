"""JRE-022 Synthesis (Verdict) Engine — deterministic rule-based
classical interpretation engine.

JRE-022 consumes the structural outputs of JRE-010 through JRE-021
and generates structured, rule-based classical interpretations (verdicts),
strictly as deterministic data points without probabilistic AI.

Strict Boundaries:
- IN SCOPE: src/synthesis/, config/synthesis.toml
- OUT OF SCOPE: No LLMs, no probabilistic AI, no free-text generation.
  No modification of JRE-002 through JRE-021.

Core Models:
- ``SynthesisCategory``: enum of life domains
- ``SynthesisRule``: category, condition_type, condition_params, weight
- ``Verdict``: category, score, strength, evidence_ids
- ``SynthesisReport``: verdicts, version

Service Interface:
- ``SynthesisService(config: SynthesisConfig)``
- ``generate_verdict(data, categories) -> SynthesisReport``
"""

from .config import load_config
from .errors import (
    InvalidSynthesisConfigError,
    InvalidSynthesisRequestError,
    SynthesisComputationError,
    SynthesisError,
)
from .models import (
    SYNTHESIS_VERSION,
    AshtakavargaIndicator,
    AvasthaIndicator,
    BalaIndicator,
    ConditionType,
    DashaIndicator,
    HouseIndicator,
    SynthesisCategory,
    SynthesisConfig,
    SynthesisInput,
    SynthesisReport,
    SynthesisRule,
    Verdict,
    VerdictStrength,
    YogaIndicator,
    classify_strength,
    compute_category_score,
    evaluate_condition,
    generate_verdicts,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    synthesis_config_from_dict,
)
from .service import SynthesisService

__version__ = SYNTHESIS_VERSION

__all__ = [
    # service
    "SynthesisService",
    # config
    "load_config",
    "SynthesisConfig",
    # models
    "SynthesisCategory",
    "SynthesisRule",
    "Verdict",
    "VerdictStrength",
    "SynthesisReport",
    "SynthesisInput",
    "ConditionType",
    # input indicators
    "YogaIndicator",
    "BalaIndicator",
    "DashaIndicator",
    "HouseIndicator",
    "AshtakavargaIndicator",
    "AvasthaIndicator",
    # derivation helpers
    "evaluate_condition",
    "compute_category_score",
    "classify_strength",
    "generate_verdicts",
    # constants
    "SYNTHESIS_VERSION",
    # errors
    "SynthesisError",
    "InvalidSynthesisConfigError",
    "InvalidSynthesisRequestError",
    "SynthesisComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "synthesis_config_from_dict",
]
