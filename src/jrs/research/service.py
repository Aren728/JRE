"""Research service — resolves rule IDs into human-readable citations."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import CitationNotFoundError, InvalidResearchConfigError
from .models import ResearchConfig, RuleCitation

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "config" / "research_sources.toml"
)


class ResearchService:
    """Research service: loads citations and resolves rule IDs.

    This service is strictly read-only. It structures knowledge and
    provides human-readable context; it does not alter deterministic
    JRE calculations.

    Usage::

        svc = ResearchService()
        citation = svc.get_citation("R-BPHS-14-05")
        print(citation.to_citation_string())
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the research service.

        Args:
            config_path: Optional path to the TOML config file.
        """
        self._config_path = config_path or _CONFIG_PATH
        self._citations: dict[str, RuleCitation] | None = None
        self._config = ResearchConfig()

    def _load_citations(self) -> dict[str, RuleCitation]:
        """Load citations from the TOML config."""
        if self._citations is not None:
            return self._citations

        config_path = self._config_path
        if not config_path.exists():
            raise InvalidResearchConfigError(
                f"Research config not found: {config_path}",
            )

        try:
            with config_path.open("rb") as f:
                raw: dict[str, Any] = tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            raise InvalidResearchConfigError(f"Invalid TOML: {exc}") from exc

        section = raw.get("research")
        if not isinstance(section, dict):
            raise InvalidResearchConfigError(
                "Missing top-level [research] section",
            )

        rules_raw = section.get("rules", [])
        if not isinstance(rules_raw, list):
            raise InvalidResearchConfigError("rules must be a list")

        loaded: list[RuleCitation] = []
        for rule_data in rules_raw:
            citation = self._parse_citation(rule_data)
            loaded.append(citation)

        self._citations = {c.rule_id: c for c in loaded}
        return self._citations

    def _parse_citation(self, data: dict[str, Any]) -> RuleCitation:
        """Parse a single citation from TOML data."""
        rule_id = data.get("rule_id", "")
        if not rule_id:
            raise InvalidResearchConfigError("rule_id must not be empty")

        return RuleCitation(
            rule_id=rule_id,
            source=data.get("source", ""),
            source_full=data.get("source_full", ""),
            location=data.get("location", ""),
            claim=data.get("claim", ""),
            evidence_class=data.get("evidence_class", ""),
            modern_normalization=data.get("modern_normalization", ""),
            domain=data.get("domain", ""),
        )

    def get_citation(self, rule_id: str) -> RuleCitation:
        """Resolve a rule ID into a human-readable citation.

        Args:
            rule_id: The rule ID to look up (e.g., "R-BPHS-14-05").

        Returns:
            A RuleCitation with the full source information.

        Raises:
            CitationNotFoundError: If the rule_id has no matching citation.
        """
        citations = self._load_citations()
        if rule_id not in citations:
            raise CitationNotFoundError(
                f"No citation found for rule_id: {rule_id}",
            )
        return citations[rule_id]

    def get_citations_for_domain(
        self,
        domain: str,
    ) -> tuple[RuleCitation, ...]:
        """Get all citations for a specific domain.

        Args:
            domain: The domain to filter by (e.g., "wealth", "career").

        Returns:
            A tuple of matching RuleCitation objects.
        """
        citations = self._load_citations()
        return tuple(
            c for c in citations.values() if c.domain == domain
        )

    def get_all_citations(self) -> tuple[RuleCitation, ...]:
        """Get all loaded citations.

        Returns:
            A tuple of all RuleCitation objects.
        """
        citations = self._load_citations()
        return tuple(citations.values())

    def get_citation_ids(self) -> tuple[str, ...]:
        """Get all loaded citation rule IDs.

        Returns:
            A tuple of rule_id strings.
        """
        citations = self._load_citations()
        return tuple(sorted(citations.keys()))

    @property
    def config(self) -> ResearchConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def citation_count(self) -> int:
        """Return the number of loaded citations."""
        citations = self._load_citations()
        return len(citations)
