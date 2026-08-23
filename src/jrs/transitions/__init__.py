"""JRS Advanced Temporal / Transition Reasoning Engine — deterministic fact calculation.

Calculates exact transition EVENTS as deterministic facts.
Does NOT interpret what these transitions mean for the user.

Consumes existing Dasha, Transit, and Ephemeris facts.  Does not
recalculate planetary positions.

Public API
----------
- ``TransitionService``      – transition calculation from ephemeris + dasha data
- ``TransitionEvent``        – a single deterministic transition fact
- ``TransitionType``         – classification of transition kinds
"""

from __future__ import annotations

from .errors import (
    InvalidTransitionInputError,
    TransitionComputationError,
    TransitionsError,
)
from .models import (
    TransitionEvent,
    TransitionType,
    compute_deterministic_id,
)
from .service import TransitionService

__all__: tuple[str, ...] = (
    # Errors
    "TransitionsError",
    "InvalidTransitionInputError",
    "TransitionComputationError",
    # Enums
    "TransitionType",
    # Models
    "TransitionEvent",
    "compute_deterministic_id",
    # Service
    "TransitionService",
)
