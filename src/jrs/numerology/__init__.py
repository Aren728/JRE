"""JRS Numerology — Interpretation layer for numerology charts.

Also re-exports the calculation service (``NumerologyCalculationService``)
so the API/CLI can import everything numerology-related strictly from the
``jrs.numerology`` unified wrapper.
"""

from __future__ import annotations

from .service import NumerologyCalculationService, NumerologyDomainService

__all__ = [
    "NumerologyCalculationService",
    "NumerologyDomainService",
]
