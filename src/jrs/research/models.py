"""Research module data models — rule citations and configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleCitation:
    """A single classical rule citation linking a rule ID to its source.

    This is a read-only, source-pinned record. It does not alter any
    deterministic JRE calculations — it provides human-readable context
    for evidence records produced by domain rule catalogs.
    """

    rule_id: str
    source: str
    source_full: str
    location: str
    claim: str
    evidence_class: str
    modern_normalization: str
    domain: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rule_id": self.rule_id,
            "source": self.source,
            "source_full": self.source_full,
            "location": self.location,
            "claim": self.claim,
            "evidence_class": self.evidence_class,
            "modern_normalization": self.modern_normalization,
            "domain": self.domain,
        }

    def to_citation_string(self) -> str:
        """Return a human-readable citation string."""
        return f"{self.source_full}, {self.location}: {self.claim}"


@dataclass(frozen=True)
class ResearchConfig:
    """Configuration for the research module."""

    version: str = "1.0"
