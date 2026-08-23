"""JRS-067: Western Astrology Interpretation Layer.

Consumes JRE-066 WesternChart facts and outputs SystemAssessment
objects with SystemType.WESTERN provenance.
"""

from __future__ import annotations

from .errors import InvalidWesternConfigError
from .models import (
    WesternConfig,
    WesternOutcomeTaxonomy,
    WesternRule,
    WesternRuleCatalog,
)
from .service import WesternDomainService

__all__ = [
    "InvalidWesternConfigError",
    "WesternConfig",
    "WesternDomainService",
    "WesternOutcomeTaxonomy",
    "WesternRule",
    "WesternRuleCatalog",
]
