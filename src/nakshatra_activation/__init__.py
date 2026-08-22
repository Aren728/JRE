"""JRE-026 Nakshatra Relationship & Activation Engine — deterministic fact layer.

Deterministic, interpretation-free nakshatra activation facts on top of
JRE-003 planet positions:

- Nakshatra occupancy activations (which planet occupies which nakshatra)
- Nakshatra lord activations (lord relationships between planets)
- Transit ingress activations (transit planets entering natal nakshatras)
- Mutual exchange activations (planets exchanging nakshatra lords)
- Dependency activations (planets sharing a nakshatra)

This engine performs NO interpretation: no predictions, no predictions,
no significance claims. Those belong to future engines.

Public API:
- NakshatraActivationService — the deterministic facade
- NakshatraActivation — a single activation fact
- NakshatraActivationReport — complete activation report
- NakshatraRelationshipType — classification enum
"""

from .errors import (
    ActivationComputationError,
    InvalidActivationConfigError,
    InvalidActivationRequestError,
    NakshatraActivationError,
)
from .models import (
    NAKSHATRA_ACTIVATION_VERSION,
    NakshatraActivation,
    NakshatraActivationReport,
    NakshatraRelationshipType,
    to_dict_value,
)
from .service import NakshatraActivationService

__version__ = NAKSHATRA_ACTIVATION_VERSION

__all__ = [
    # service
    "NakshatraActivationService",
    # models
    "NakshatraActivation",
    "NakshatraActivationReport",
    "NakshatraRelationshipType",
    "NAKSHATRA_ACTIVATION_VERSION",
    "to_dict_value",
    # errors
    "NakshatraActivationError",
    "InvalidActivationRequestError",
    "InvalidActivationConfigError",
    "ActivationComputationError",
]
