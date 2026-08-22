"""JRS Research Worker — Source-Pinned Classical Rule Citations.

Public API
----------
- ``RuleCitation``      – a single classical rule citation
- ``ResearchConfig``    – research configuration
- ``ResearchService``   – resolves rule IDs into human-readable citations
"""

from __future__ import annotations

from .models import ResearchConfig, RuleCitation
from .service import ResearchService

__all__: tuple[str, ...] = (
    "RuleCitation",
    "ResearchConfig",
    "ResearchService",
)
