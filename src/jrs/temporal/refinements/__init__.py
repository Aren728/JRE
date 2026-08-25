"""JRS-073 Temporal Refinements — Dasha Sandhi & Eclipse Windows.

Public API
----------
- ``TemporalModifier``       – time-bound weight adjustment
- ``ModifierType``           – DASHA_SANDHI, ECLIPSE_WINDOW
- ``TemporalRefinementService`` – generates and applies modifiers
"""

from __future__ import annotations

from .models import ModifierType, TemporalModifier
from .service import TemporalRefinementService

__all__: tuple[str, ...] = (
    "ModifierType",
    "TemporalModifier",
    "TemporalRefinementService",
)
