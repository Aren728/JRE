"""Pure data model for the Classical Knowledge & Rule Engine (JRE-004).

This module contains ONLY data definitions: enums, immutable dataclasses and
pure catalog-integrity helpers. It imports nothing beyond the standard
library (same rule as JRE-002/JRE-003), so consumers can rely on it without
coupling. The field-level contract is defined in
``docs/architecture/JRE-004-DATA-CONTRACT.md`` (v0.3.0) and refined by the
Specialist spec (v0.4.0).

Deliberate inclusions beyond bare data (still stdlib-only):

- ``PASSTHROUGH_FIELD_VALUES`` — the pinned allow-list for
  ``TraditionProfile.passthrough_config`` (SPEC §14). These values mirror
  the ``jyotish``/``astronomy`` enums; they are pinned data here so the
  knowledge layer validates profiles without importing those layers.
- Catalog-integrity helpers (``read_catalog_file``, ``canonical_catalog_json``,
  ``sha256_hex``). They live here (rather than in ``provenance.py``) so that
  ``sources.py``/``rules.py``/``traditions.py`` can verify checksums without
  an import cycle — the import graph stays one-way and acyclic (ADR-007).

The engine never evaluates, scores, or interprets rule conclusions here;
``RuleConclusion.structured`` is opaque data (ADR-009).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Enums (string values are the JSON values) — DATA-CONTRACT §1
# --------------------------------------------------------------------------- #


class SourceStatus(StrEnum):
    """Classification of a classical source in the registry (SPEC §4)."""

    CANONICAL = "CANONICAL"
    SUPPLEMENTAL = "SUPPLEMENTAL"
    REGIONAL = "REGIONAL"
    HISTORICAL = "HISTORICAL"


class RuleStatus(StrEnum):
    """Lifecycle status of an authored rule (SPEC §3.1).

    ``INACTIVE`` marks authored rules held as unresolved research records
    (NEEDS-RESEARCH per the recovery reconciliation): they load and validate
    (provenance intact) but are never matched by synthesis — the ``_in_scope``
    filter excludes every non-``ACTIVE`` status.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"
    SUPERSEDED = "SUPERSEDED"


class RuleDomain(StrEnum):
    """Consumption group for rules; a catalog label, never engine behavior.

    New values are additive, versioned enum additions (SPEC §7.1) — a new
    value requires a ``DOMAIN_REQUIREMENTS`` entry and a spec bump.
    """

    KARAKA = "KARAKA"
    BHAVA_MEANING = "BHAVA_MEANING"
    DRISHTI = "DRISHTI"
    YOGA_DEFINITION = "YOGA_DEFINITION"
    NAKSHATRA_CHARACTER = "NAKSHATRA_CHARACTER"
    DASHA_APPLICATION = "DASHA_APPLICATION"
    GOCHAR_SIGNIFICATION = "GOCHAR_SIGNIFICATION"
    ECLIPSE_SIGNIFICATION = "ECLIPSE_SIGNIFICATION"
    GENERAL = "GENERAL"


class ConflictPolicy(StrEnum):
    """Explicit policy for same-priority disagreements (ADR-010)."""

    FIRST_WINS = "FIRST_WINS"
    REPORT_ALL = "REPORT_ALL"


class ConditionOp(StrEnum):
    """Typed predicate operators for rule condition atoms (SPEC §3.2)."""

    EQ = "EQ"
    NEQ = "NEQ"
    LT = "LT"
    LTE = "LTE"
    GT = "GT"
    GTE = "GTE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    EXISTS = "EXISTS"


class ConditionCombiner(StrEnum):
    """Combiners for recursive condition trees (SPEC §3.2)."""

    ALL = "ALL"
    ANY = "ANY"
    NOT = "NOT"


# --------------------------------------------------------------------------- #
# Pure catalog-integrity helpers (see module docstring)
# --------------------------------------------------------------------------- #


def canonical_catalog_json(document: dict[str, Any]) -> str:
    """Deterministic JSON serialization of a catalog document.

    Used as the checksum input so the digest does not depend on key order or
    whitespace. Matches the authoring-time canonicalization.
    """
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    """SHA-256 digest of ``text`` (hex)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_catalog_file(path: Path) -> tuple[dict[str, Any], str]:
    """Read a catalog JSON file.

    Returns ``(document, digest)`` where ``digest`` is the SHA-256 of the
    document with the ``checksum_sha256`` field removed (canonical form).
    The caller compares ``digest`` against the stored field and raises
    ``CatalogIntegrityError`` on mismatch (SPEC §5.2). Raises ``OSError`` or
    ``ValueError`` (invalid JSON) for the caller to wrap.
    """
    raw = path.read_text(encoding="utf-8")
    document = json.loads(raw)
    body = {key: value for key, value in document.items() if key != "checksum_sha256"}
    return document, sha256_hex(canonical_catalog_json(body))


# --------------------------------------------------------------------------- #
# Passthrough configuration allow-list (SPEC §14)
# --------------------------------------------------------------------------- #

#: Pinned mirror of the ``jyotish``/``astronomy`` enums allowed in
#: ``TraditionProfile.passthrough_config``. Values are validated at profile
#: load; unknown field or bad value raises ``InvalidConfigError``. The
#: passthrough is echoed, never interpreted, by the engine.
PASSTHROUGH_FIELD_VALUES: dict[str, frozenset[str]] = {
    "ayanamsa": frozenset({"LAHIRI", "RAMAN", "FAGAN_BRADLEY"}),
    "house_system": frozenset(
        {"WHOLE_SIGN", "EQUAL", "PLACIDUS", "KOCH", "REGIOMONTANUS", "CAMPANUS"}
    ),
    "node_model": frozenset({"MEAN", "TRUE"}),
    "zodiac_mode": frozenset({"SIDEREAL", "TROPICAL"}),
    "position_type": frozenset({"APPARENT", "TRUE"}),
}

# --------------------------------------------------------------------------- #
# Configuration — DATA-CONTRACT §2
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class KnowledgeConfig:
    """Immutable snapshot of every setting that can change synthesis output.

    Echoed in every ``SynthesisResult``. The credibility/weight coefficients
    and provenance-completeness levels are configuration (SPEC §10,
    supersession #7): tuning them is a versioned config decision and never
    affects rule *selection* (selection is condition matching + precedence).
    """

    default_profile_id: str = "bphs-classical"
    default_conflict_policy: ConflictPolicy = ConflictPolicy.FIRST_WINS
    source_catalog_version: str | None = None
    rule_catalog_versions: dict[str, str] = field(default_factory=dict)
    profile_catalog_version: str | None = None
    facts_catalog_version: str | None = None
    enforce_provenance: bool = True
    verify_checksums: bool = True
    max_rules_per_synthesis: int = 200
    #: deterministic metadata coefficients (SPEC §10) — never selection inputs
    weight_authority_coeff: float = 1.0
    weight_specificity_coeff: float = 0.5
    weight_source_rank_coeff: float = 0.05
    credibility_authority_weight: float = 0.55
    credibility_provenance_weight: float = 0.30
    credibility_specificity_weight: float = 0.15
    provenance_completeness: dict[str, float] = field(
        default_factory=lambda: {
            "full": 1.0,
            "verse": 0.85,
            "chapter": 0.7,
            "source": 0.5,
        }
    )


# --------------------------------------------------------------------------- #
# Source registry — DATA-CONTRACT §3
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Edition:
    """One bibliographic edition/translation record (ADR-008)."""

    edition_id: str
    title: str
    translator: str | None
    publisher: str | None
    year: str | None
    language: str
    notes: str | None


@dataclass(frozen=True)
class Source:
    """A classical source entry: bibliographic provenance, never prose."""

    source_id: str
    canonical_name: str
    common_name: str
    author: str | None
    period: str | None
    language: str
    lineage: tuple[str, ...]
    status: SourceStatus
    editions: tuple[Edition, ...]
    catalog_version: str


# --------------------------------------------------------------------------- #
# Rules — DATA-CONTRACT §4–§5
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProvenanceRef:
    """A citation locus: source → chapter → verse → edition (ADR-008)."""

    source_id: str
    chapter: str | None = None
    verse_start: str | None = None
    verse_end: str | None = None
    edition_id: str | None = None
    commentary: str | None = None


def provenance_completeness_level(ref: ProvenanceRef) -> str:
    """Bibliographic completeness level of a ref (SPEC §5.1).

    Levels: ``full`` = source+chapter+verse+edition; ``verse`` =
    source+chapter+verse; ``chapter`` = source+chapter; ``source`` = source
    only. (In valid catalogs ``edition_id`` is mandatory whenever chapter or
    verse is set, so ``verse`` is defensive-only.)
    """
    if ref.chapter is None:
        return "source"
    if ref.verse_start is None:
        return "chapter"
    if ref.edition_id is None:
        return "verse"
    return "full"


@dataclass(frozen=True)
class RuleConclusion:
    """Structured, machine-readable conclusion content (opaque to the engine)."""

    kind: str
    statement: str
    structured: dict[str, Any]


@dataclass(frozen=True)
class RuleCondition:
    """Recursive typed predicate tree over the pinned fact vocabulary.

    Atom: ``combiner is None``, ``op``/``path`` set, ``children == ()``.
    Combiner: ``op``/``path`` None, ``children != ()``; ``NOT`` has exactly
    one child. ``EXISTS`` has ``value is None`` (presence test only).
    """

    combiner: ConditionCombiner | None
    op: ConditionOp | None
    path: str | None
    value: object | None
    children: tuple[RuleCondition, ...] = ()


@dataclass(frozen=True)
class Rule:
    """One authored classical rule (SPEC §3.1). Rules are data, never code."""

    rule_id: str
    domain: RuleDomain
    summary: str
    condition: RuleCondition
    conclusion: RuleConclusion
    provenance: ProvenanceRef
    supporting_refs: tuple[ProvenanceRef, ...]
    conflicts_with: tuple[str, ...]
    exception_for: tuple[str, ...]
    authority_tier: int
    status: RuleStatus
    tradition_tags: tuple[str, ...]
    rule_version: str


@dataclass(frozen=True)
class ResolvedRule:
    """A matched/suppressed rule with its deterministic metadata (SPEC §3.3)."""

    rule: Rule
    precedence_key: tuple[object, ...]
    effective_weight: float
    credibility: float
    applicability: bool
    status_note: str | None


# --------------------------------------------------------------------------- #
# Tradition profiles — DATA-CONTRACT §6
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TraditionProfile:
    """A named, versioned bundle of sources with an explicit priority order."""

    profile_id: str
    name: str
    version: str
    description: str
    included_sources: tuple[str, ...]
    source_priority: tuple[str, ...]
    conflict_policy: ConflictPolicy
    domains: tuple[RuleDomain, ...] | None
    passthrough_config: dict[str, Any]


# --------------------------------------------------------------------------- #
# Query / result — DATA-CONTRACT §7
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RuleQuery:
    """Synthesis input: domain, fact snapshot, optional profile override."""

    domain: RuleDomain | None
    fact_snapshot: dict[str, Any]
    profile_id: str | None = None
    include_suppressed: bool = False


@dataclass(frozen=True)
class ConflictRecord:
    """Every suppression / disagreement / exception override (never silent)."""

    rule_a_id: str
    rule_b_id: str
    reason: str
    resolution: str
    policy: ConflictPolicy


@dataclass(frozen=True)
class SearchMetadata:
    """Determinism echo: algorithm, catalog versions, counts, summary."""

    algorithm: str
    catalogs: dict[str, str]
    rules_evaluated: int
    rules_matched: int
    credibility_summary: dict[str, float | int | None]


@dataclass(frozen=True)
class SynthesisResult:
    """Complete, self-describing synthesis envelope (ADR-011)."""

    query: RuleQuery
    profile: TraditionProfile
    matched_rules: tuple[ResolvedRule, ...]
    suppressed_rules: tuple[ResolvedRule, ...]
    conflicts: tuple[ConflictRecord, ...]
    provenance_index: dict[str, tuple[str, ...]]
    config: KnowledgeConfig
    search_metadata: SearchMetadata


# --------------------------------------------------------------------------- #
# Generic serialization helper — DATA-CONTRACT §0 conventions
# --------------------------------------------------------------------------- #


def model_to_dict(value: Any) -> Any:
    """Serialize a frozen dataclass: enums -> values, tuples -> lists.

    ``None`` stays ``null``; ``-0.0`` normalizes to ``0.0``; floats use
    Python's round-trip repr via ``json.dumps`` downstream. ``fact_snapshot``
    is opaque: dicts/lists pass through (tuples become lists so the JSON
    round-trip is byte-stable for the canonical snapshot form).
    """
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {model_to_dict(key): model_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [model_to_dict(item) for item in value]
    if isinstance(value, float) and value == 0.0:
        return 0.0
    if hasattr(value, "__dataclass_fields__"):
        return {key: model_to_dict(item) for key, item in value.__dict__.items()}
    return value
