"""``KnowledgeService`` — the deterministic facade (ADR-011).

The sole consumer surface for future engines: registry queries
(``sources``/``profiles``/``get_profile``) and ``synthesize``. Catalogs load
once at construction (checksummed, version-pinned, immutable). The service
never interprets results — it returns rules, provenance, and metadata.

Import direction is one-way: ``service -> everything below``.
"""

from __future__ import annotations

from .config import load_config
from .errors import UnknownProfileError
from .facts import FactsRegistry, load_facts
from .models import (
    KnowledgeConfig,
    RuleQuery,
    Source,
    SynthesisResult,
    TraditionProfile,
)
from .rules import RuleRegistry, load_rule_catalogs
from .sources import SourceRegistry, load_sources
from .synthesis import synthesize
from .traditions import ProfileRegistry, load_profiles


class KnowledgeService:
    """Immutable knowledge engine wired to the committed, checksummed catalogs."""

    def __init__(self, config: KnowledgeConfig | None = None) -> None:
        self._config = config if config is not None else load_config()
        self._sources: SourceRegistry = load_sources(
            verify_checksums=self._config.verify_checksums,
            pin=self._config.source_catalog_version,
        )
        self._profiles: ProfileRegistry = load_profiles(
            sources=self._sources,
            verify_checksums=self._config.verify_checksums,
            pin=self._config.profile_catalog_version,
        )
        if not self._profiles.has(self._config.default_profile_id):
            raise UnknownProfileError(
                f"default_profile_id {self._config.default_profile_id!r} is not "
                "registered in the profile catalog"
            )
        self._facts: FactsRegistry = load_facts(
            verify_checksums=self._config.verify_checksums,
            pin=self._config.facts_catalog_version,
        )
        self._rules: RuleRegistry = load_rule_catalogs(
            registry=self._sources,
            verify_checksums=self._config.verify_checksums,
            enforce_provenance=self._config.enforce_provenance,
            pins=self._config.rule_catalog_versions,
        )

    def sources(self) -> tuple[Source, ...]:
        """All registered sources (registry query)."""
        return self._sources.all()

    def profiles(self) -> tuple[TraditionProfile, ...]:
        """All registered tradition profiles (registry query)."""
        return self._profiles.all()

    def get_profile(self, profile_id: str) -> TraditionProfile:
        """Resolve a profile; raises ``UnknownProfileError`` otherwise."""
        return self._profiles.get(profile_id)

    def synthesize(self, query: RuleQuery) -> SynthesisResult:
        """Run the deterministic synthesis pipeline (SPEC §11)."""
        profile_id = query.profile_id or self._config.default_profile_id
        profile = self._profiles.get(profile_id)
        return synthesize(
            query,
            profile,
            rule_registry=self._rules,
            source_registry=self._sources,
            profile_registry=self._profiles,
            facts_registry=self._facts,
            config=self._config,
        )

    def rule_catalog_versions(self) -> dict[str, str]:
        """``{catalog_id: version}`` of every loaded rule catalog (echo)."""
        return self._rules.catalog_versions()

    @property
    def facts(self) -> FactsRegistry:
        """The loaded classical-facts registry (ADR-012)."""
        return self._facts
