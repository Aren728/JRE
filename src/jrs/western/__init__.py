"""JRS-067: Western Astrology Interpretation Layer.

Consumes JRE-066 WesternChart facts and outputs SystemAssessment
objects with SystemType.WESTERN provenance.

Also re-exports the JRE-066 calculation service (``WesternCalculationService``)
so the API/CLI can import everything western-related strictly from the
``jrs.western`` unified wrapper.
"""

from __future__ import annotations

from .errors import InvalidWesternConfigError
from .models import (
    WesternConfig,
    WesternOutcomeTaxonomy,
    WesternRule,
    WesternRuleCatalog,
)
from .service import WesternCalculationService, WesternDomainService

__all__ = [
    "InvalidWesternConfigError",
    "WesternCalculationService",
    "WesternConfig",
    "WesternDomainService",
    "WesternOutcomeTaxonomy",
    "WesternRule",
    "WesternRuleCatalog",
]
