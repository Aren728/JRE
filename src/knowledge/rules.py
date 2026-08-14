"""Rule catalogs: load, validate, version, and register rules.

Implements SPEC §7. Rules are authored JSON data under
``datasets/knowledge/rules/``; each catalog is checksummed and versioned, and
every rule is schema-validated (condition grammar + fact vocabulary),
provenance-validated (ADR-008), and cross-validated: ``conflicts_with``
symmetry, ``exception_for`` target/domain checks and cycle rejection
(SPEC §7, §9.2). Invalid or unprovenanced rules fail loudly — never silently
skipped.

Import direction is one-way: ``rules -> models, schema, provenance, errors``
(``sources`` is imported only for the registry type under TYPE_CHECKING).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .errors import (
    CatalogIntegrityError,
    ConflictResolutionError,
    ProvenanceError,
    RuleSchemaError,
)
from .models import (
    ConditionCombiner,
    ConditionOp,
    ProvenanceRef,
    Rule,
    RuleConclusion,
    RuleCondition,
    RuleDomain,
    RuleStatus,
    read_catalog_file,
)
from .schema import validate_condition

if TYPE_CHECKING:
    from .sources import SourceRegistry

logger = logging.getLogger("knowledge.rules")

DEFAULT_RULES_DIR: Path = Path("datasets/knowledge/rules")

RULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


class RuleRegistry:
    """Immutable registry of all loaded rules + catalog versions."""

    def __init__(self, rules: tuple[Rule, ...], catalog_versions: dict[str, str]) -> None:
        self._rules = rules
        self._by_id = {rule.rule_id: rule for rule in rules}
        self._catalog_versions = dict(catalog_versions)

    def all(self) -> tuple[Rule, ...]:
        """All loaded rules (catalog order)."""
        return self._rules

    def get(self, rule_id: str) -> Rule | None:
        """Rule by id, or ``None`` if not loaded."""
        return self._by_id.get(rule_id)

    def by_id(self) -> dict[str, Rule]:
        """Copy of the id → rule map (deterministic)."""
        return dict(self._by_id)

    def catalog_versions(self) -> dict[str, str]:
        """``{catalog_id: version}`` for every loaded rule catalog."""
        return dict(self._catalog_versions)

    def domains(self) -> tuple[RuleDomain, ...]:
        """Distinct domains present in the registry (sorted by value)."""
        return tuple(sorted({rule.domain for rule in self._rules}, key=lambda d: d.value))


# --------------------------------------------------------------------------- #
# Dict -> model parsing
# --------------------------------------------------------------------------- #


def _condition_from_dict(data: Any) -> RuleCondition:
    if not isinstance(data, dict):
        raise RuleSchemaError(f"condition must be an object, got {data!r}")
    try:
        combiner_raw = data.get("combiner")
        op_raw = data.get("op")
        path_raw = data.get("path")
        value = data.get("value")
        children_raw = data.get("children")
        combiner = None if combiner_raw is None else ConditionCombiner(str(combiner_raw))
        op = None if op_raw is None else ConditionOp(str(op_raw))
        children_raw_list = children_raw if isinstance(children_raw, list) else []
        children = tuple(_condition_from_dict(child) for child in children_raw_list)
    except (ValueError, TypeError) as exc:
        raise RuleSchemaError(f"malformed condition: {exc!r}") from exc
    condition = RuleCondition(
        combiner=combiner,
        op=op,
        path=None if path_raw is None else str(path_raw),
        value=value,
        children=children,
    )
    validate_condition(condition)
    return condition


def _ref_from_dict(data: Any) -> ProvenanceRef:
    if not isinstance(data, dict):
        raise RuleSchemaError(f"provenance ref must be an object, got {data!r}")
    try:
        source_id = str(data["source_id"])
    except (KeyError, TypeError) as exc:
        raise RuleSchemaError(f"provenance ref missing source_id: {exc!r}") from exc

    def _opt(key: str) -> str | None:
        raw = data.get(key)
        return None if raw is None else str(raw)

    return ProvenanceRef(
        source_id=source_id,
        chapter=_opt("chapter"),
        verse_start=_opt("verse_start"),
        verse_end=_opt("verse_end"),
        edition_id=_opt("edition_id"),
        commentary=_opt("commentary"),
    )


def _rule_from_dict(data: Any, catalog_id: str) -> Rule:
    if not isinstance(data, dict):
        raise RuleSchemaError(f"rule entry in {catalog_id!r} must be an object")
    try:
        rule_id = str(data["rule_id"])
        domain = RuleDomain(str(data["domain"]))
        summary = str(data["summary"])
        condition = _condition_from_dict(data["condition"])
        conclusion_raw = data["conclusion"]
        if not isinstance(conclusion_raw, dict):
            raise RuleSchemaError(f"rule {rule_id!r}: conclusion must be an object")
        conclusion = RuleConclusion(
            kind=str(conclusion_raw["kind"]),
            statement=str(conclusion_raw["statement"]),
            structured=conclusion_raw.get("structured") or {},
        )
        provenance = _ref_from_dict(data["provenance"])
        supporting = tuple(_ref_from_dict(ref) for ref in data.get("supporting_refs", []))
        conflicts = tuple(str(item) for item in data.get("conflicts_with", []))
        exceptions = tuple(str(item) for item in data.get("exception_for", []))
        authority_tier = int(data["authority_tier"])
        status = RuleStatus(str(data["status"]))
        tags = tuple(str(item) for item in data.get("tradition_tags", []))
        version = str(data["rule_version"])
    except (KeyError, ValueError, TypeError) as exc:
        raise RuleSchemaError(f"malformed rule in catalog {catalog_id!r}: {exc!r}") from exc

    if RULE_ID_RE.match(rule_id) is None:
        raise RuleSchemaError(f"invalid rule_id {rule_id!r}")
    if not summary:
        raise RuleSchemaError(f"rule {rule_id!r} has an empty summary")
    if not 1 <= authority_tier <= 5:
        raise RuleSchemaError(f"rule {rule_id!r} authority_tier must be 1..5, got {authority_tier}")
    if SEMVER_RE.match(version) is None:
        raise RuleSchemaError(f"rule {rule_id!r} rule_version {version!r} is not semver")
    return Rule(
        rule_id=rule_id,
        domain=domain,
        summary=summary,
        condition=condition,
        conclusion=conclusion,
        provenance=provenance,
        supporting_refs=supporting,
        conflicts_with=conflicts,
        exception_for=exceptions,
        authority_tier=authority_tier,
        status=status,
        tradition_tags=tags,
        rule_version=version,
    )


# --------------------------------------------------------------------------- #
# Cross-rule validation
# --------------------------------------------------------------------------- #


def _validate_ref(rule: Rule, ref: ProvenanceRef, registry: SourceRegistry, enforce: bool) -> None:
    """Provenance integrity for one ref (SPEC §4/§5.2)."""
    if registry.has(ref.source_id):
        source = registry.get(ref.source_id)
        if not source.editions:
            raise ProvenanceError(
                f"rule {rule.rule_id!r} cites source {ref.source_id!r} which has no edition records"
            )
        if ref.chapter is not None or ref.verse_start is not None:
            if ref.edition_id is None:
                raise ProvenanceError(
                    f"rule {rule.rule_id!r} must pin edition_id when chapter/verse "
                    "is set (source {ref.source_id!r})"
                )
            registry.resolve_edition(ref.source_id, ref.edition_id)  # UnknownEditionError
        return
    if enforce:
        raise ProvenanceError(f"rule {rule.rule_id!r} cites unknown source {ref.source_id!r}")
    # enforce_provenance=False allows explicit-None refs only (SPEC §5.2)
    if ref.chapter is not None or ref.verse_start is not None or ref.edition_id is not None:
        raise ProvenanceError(
            f"rule {rule.rule_id!r} cites unknown source {ref.source_id!r} "
            "with a non-None ref; only whole-source (explicit-None) refs allowed"
        )


def _check_exception_cycles(rules: tuple[Rule, ...]) -> None:
    by_id = {rule.rule_id: rule for rule in rules}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(rule_id: str, path: list[str]) -> None:
        if rule_id in visiting:
            cycle = " -> ".join(path + [rule_id])
            raise ConflictResolutionError(f"exception_for cycle detected: {cycle}")
        if rule_id in visited:
            return
        visiting.add(rule_id)
        for target in by_id[rule_id].exception_for:
            visit(target, path + [rule_id])
        visiting.remove(rule_id)
        visited.add(rule_id)

    for rule in rules:
        visit(rule.rule_id, [])


def _warn_structural_contradictions(rules: tuple[Rule, ...]) -> None:
    """Load-time warning only; never auto-suppresses (SPEC §9.1)."""
    for index, rule in enumerate(rules):
        for other in rules[index + 1 :]:
            if (
                rule.domain is other.domain
                and rule.condition == other.condition
                and rule.conclusion.structured != other.conclusion.structured
            ):
                logger.warning(
                    "structural contradiction at load: %r and %r share a "
                    "condition with different conclusions",
                    rule.rule_id,
                    other.rule_id,
                )


def _validate_catalog(
    rules: tuple[Rule, ...],
    registry: SourceRegistry,
    enforce_provenance: bool,
) -> None:
    by_id = {rule.rule_id: rule for rule in rules}
    if len(by_id) != len(rules):
        raise RuleSchemaError("duplicate rule_id across catalogs")

    for rule in rules:
        _validate_ref(rule, rule.provenance, registry, enforce_provenance)
        for ref in rule.supporting_refs:
            _validate_ref(rule, ref, registry, enforce_provenance)

    for rule in rules:
        for other_id in rule.conflicts_with:
            if other_id == rule.rule_id:
                raise ConflictResolutionError(
                    f"rule {rule.rule_id!r} declares a conflict with itself"
                )
            other = by_id.get(other_id)
            if other is None:
                raise ConflictResolutionError(
                    f"rule {rule.rule_id!r} declares conflict with unknown rule {other_id!r}"
                )
            if rule.rule_id not in other.conflicts_with:
                raise ConflictResolutionError(
                    f"asymmetric conflicts_with: {rule.rule_id!r} lists "
                    f"{other_id!r} but not vice versa"
                )
        for target_id in rule.exception_for:
            target = by_id.get(target_id)
            if target is None:
                raise RuleSchemaError(
                    f"rule {rule.rule_id!r} exception_for unknown rule {target_id!r}"
                )
            if target.domain is not rule.domain:
                raise RuleSchemaError(
                    f"rule {rule.rule_id!r} exception_for {target_id!r} has a different domain"
                )
    _check_exception_cycles(rules)
    _warn_structural_contradictions(rules)


# --------------------------------------------------------------------------- #
# Catalog loading
# --------------------------------------------------------------------------- #


def _read_catalog(path: Path, verify_checksums: bool) -> dict[str, Any]:
    try:
        document, digest = read_catalog_file(path)
    except OSError as exc:
        raise CatalogIntegrityError(f"cannot read catalog {path}: {exc}") from exc
    except ValueError as exc:
        raise CatalogIntegrityError(f"invalid JSON in catalog {path}: {exc}") from exc
    if verify_checksums:
        expected = document.get("checksum_sha256")
        if expected != digest:
            raise CatalogIntegrityError(
                f"checksum mismatch for {path}: expected {expected!r}, got {digest!r}"
            )
    if not document.get("catalog_id") or not document.get("catalog_version"):
        raise CatalogIntegrityError(f"catalog {path} is missing catalog_id/catalog_version")
    return document


def load_rule_catalogs(
    paths: list[str | Path] | None = None,
    *,
    registry: SourceRegistry,
    verify_checksums: bool = True,
    enforce_provenance: bool = True,
    pins: dict[str, str] | None = None,
) -> RuleRegistry:
    """Load and validate all rule catalogs (checksummed, versioned).

    ``registry`` resolves every cited source (provenance enforcement).
    ``pins`` maps ``catalog_id`` → expected version (exact match).
    """
    catalog_paths: list[Path] = (
        [Path(item) for item in paths]
        if paths is not None
        else sorted(DEFAULT_RULES_DIR.glob("*.json"))
    )
    all_rules: list[Rule] = []
    versions: dict[str, str] = {}
    for path in catalog_paths:
        document = _read_catalog(path, verify_checksums)
        catalog_id = str(document["catalog_id"])
        version = str(document["catalog_version"])
        if pins is not None and catalog_id in pins and pins[catalog_id] != version:
            raise CatalogIntegrityError(
                f"version-pin mismatch for {path}: expected {pins[catalog_id]!r}, got {version!r}"
            )
        entries = document.get("entries", [])
        if not isinstance(entries, list) or not entries:
            raise CatalogIntegrityError(f"catalog {path} has no rule entries")
        for entry in entries:
            all_rules.append(_rule_from_dict(entry, catalog_id))
        versions[catalog_id] = version
    rules = tuple(all_rules)
    _validate_catalog(rules, registry, enforce_provenance)
    return RuleRegistry(rules, versions)
