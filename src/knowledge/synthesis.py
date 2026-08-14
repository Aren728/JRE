"""Synthesis engine: query -> ordered ResolvedRules + conflicts + provenance.

Implements the ``synthesize`` pipeline (SPEC §11) and snapshot normalization
(SPEC §6.3): JRE-003 public outputs → the canonical ``fact_snapshot`` dict.
The engine is pure and deterministic — identical inputs yield bit-identical
output (SPEC §16); no clocks, randomness, or network.

Import graph (one-way, acyclic): ``synthesis -> schema, rules, traditions,
resolution, precedence, provenance, sources, errors, models`` and the
``jyotish`` public API (for normalization only — ADR-007).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from jyotish import (
    EclipseEvent,
    NatalChart,
    PairGeometry,
    PlanetState,
    TransitEvent,
)

from . import precedence, schema
from . import provenance as prov
from . import resolution as reso
from .errors import SynthesisError
from .facts import FactsRegistry, enrich_snapshot
from .models import (
    KnowledgeConfig,
    ResolvedRule,
    Rule,
    RuleDomain,
    RuleQuery,
    RuleStatus,
    SearchMetadata,
    SynthesisResult,
    TraditionProfile,
)
from .rules import RuleRegistry
from .sources import SourceRegistry
from .traditions import ProfileRegistry

ALGORITHM_NAME = "profile-precedence-order"


# --------------------------------------------------------------------------- #
# Snapshot normalization (SPEC §6.3)
# --------------------------------------------------------------------------- #


def _planet_entry(state: PlanetState) -> dict[str, Any]:
    return {
        "body": state.body.value,
        "rashi": state.rashi.value,
        "nakshatra": state.nakshatra.value,
        "pada": state.pada.value,
        "degree_in_rashi": state.degree_in_rashi,
        "retrograde": state.retrograde.value,
    }


def _pair_entry(pair: PairGeometry) -> dict[str, Any]:
    return {
        "first": pair.first.value,
        "second": pair.second.value,
        "conjunction": pair.conjunction,
        "separation_deg": pair.separation_deg,
        "aspects": [rel.kind.value for rel in pair.aspects if rel.within_orb],
    }


def _bhava_entry(bhava: Any) -> dict[str, Any]:
    return {
        "house_number": bhava.house_number,
        "house_lord": bhava.house_lord.value,
        "occupants": [body.value for body in bhava.occupants],
    }


def _relative_houses(chart: NatalChart) -> dict[str, dict[str, int]]:
    """Natal house of each body per reference (FACT_VOCABULARY v1.1.0).

    Computed from the chart's bhavas (occupancy) for every body in the
    ``relative_house`` reference set (ADR-012): ``LAGNA``/``ASC`` plus all
    nine grahas. ``ASC`` equals ``LAGNA`` in the whole-sign frame used by the
    snapshot (a cusp-frame anchor is a future additive vocabulary addition).
    Any body not placed in a bhava falls back to its whole-sign house from
    the lagna rashi. A reference body absent from the chart yields no map for
    that reference (a ``relative_house(<BODY>, <REF>)`` atom then reads
    **False** — never an exception).
    """
    house_of: dict[str, int] = {}
    for bhava in chart.bhavas:
        for body in bhava.occupants:
            house_of.setdefault(body.value, bhava.house_number)
    lagna_index = schema.RASHI_IDS.index(chart.lagna.rashi.value)

    def whole_sign_house(rashi: str) -> int:
        return ((schema.RASHI_IDS.index(rashi) - lagna_index) % 12) + 1

    def house_of_body(body: str, rashi: str) -> int:
        return house_of.get(body) or whole_sign_house(rashi)

    lagna_map: dict[str, int] = {}
    for state in chart.planet_states:
        lagna_map[state.body.value] = house_of_body(state.body.value, state.rashi.value)
    for placed_body, house_number in house_of.items():
        lagna_map.setdefault(placed_body, house_number)

    def rel_map(anchor: int) -> dict[str, int]:
        return {
            body: ((house_number - anchor) % 12) + 1 for body, house_number in lagna_map.items()
        }

    result: dict[str, dict[str, int]] = {"LAGNA": dict(lagna_map), "ASC": dict(lagna_map)}
    for ref in schema.RELATIVE_HOUSE_REFS:
        if ref in ("LAGNA", "ASC"):
            continue
        anchor_house = lagna_map.get(ref)
        if anchor_house is not None:
            result[ref] = rel_map(anchor_house)
    return result


def normalize_snapshot(
    outputs: object,
    pairs: object = None,
    facts: FactsRegistry | None = None,
) -> dict[str, Any]:
    """Normalize JRE-003 public outputs into a canonical ``fact_snapshot``.

    Accepts (SPEC §6.3, ADR-012): a pre-built dict (returned as-is, opaque
    round-trip); a single ``PlanetState`` / ``PairGeometry`` / ``NatalChart`` /
    ``TransitEvent`` / ``EclipseEvent``; or a tuple/list mixing any of them;
    plus an optional ``pairs=`` sequence of ``PairGeometry``. Mixed input is
    validated; unknown object types raise ``SynthesisError``.

    When ``facts`` (a ``FactsRegistry``) is provided, the v1.1.0 derived
    facts are added in place: ``nature``/``dignity``/``combusted`` on planet
    entries and ``aspect_strength`` on pair entries (ADR-012). The
    ``relative_houses`` section always spans every body reference when a
    ``NatalChart`` is present.
    """
    if isinstance(outputs, dict):
        snapshot_echo = dict(outputs)
        if facts is not None:
            enrich_snapshot(snapshot_echo, facts)
        return snapshot_echo

    planets: list[dict[str, Any]] = []
    pair_entries: list[dict[str, Any]] = []
    bhavas: list[dict[str, Any]] = []
    lagna: dict[str, Any] | None = None
    chart: NatalChart | None = None
    transits: dict[str, list[str]] = {}
    eclipse_kinds: list[str] = []
    eclipse_classifications: list[str] = []

    def ingest(item: object) -> None:
        nonlocal lagna, chart
        if isinstance(item, PlanetState):
            planets.append(_planet_entry(item))
        elif isinstance(item, PairGeometry):
            pair_entries.append(_pair_entry(item))
        elif isinstance(item, NatalChart):
            if chart is not None:
                raise SynthesisError("multiple NatalChart objects in one snapshot")
            chart = item
            lagna = {
                "rashi": item.lagna.rashi.value,
                "nakshatra": item.lagna.nakshatra.value,
                "pada": item.lagna.pada.value,
            }
            bhavas.extend(_bhava_entry(bhava) for bhava in item.bhavas)
            planets.extend(_planet_entry(state) for state in item.planet_states)
        elif isinstance(item, TransitEvent):
            transits.setdefault(item.body.value, []).append(item.kind.value)
        elif isinstance(item, EclipseEvent):
            eclipse_kinds.append(item.kind.value)
            eclipse_classifications.append(item.classification.value)
        else:
            raise SynthesisError(f"cannot normalize snapshot object of type {type(item).__name__}")

    if isinstance(outputs, (PlanetState, PairGeometry, NatalChart, TransitEvent, EclipseEvent)):
        ingest(outputs)
    elif isinstance(outputs, (tuple, list)):
        for item in outputs:
            ingest(item)
    else:
        raise SynthesisError(f"cannot normalize snapshot input of type {type(outputs).__name__}")
    if pairs is not None:
        if not isinstance(pairs, (tuple, list)):
            raise SynthesisError(
                f"pairs must be a sequence of PairGeometry, got {type(pairs).__name__}"
            )
        for pair in pairs:
            if not isinstance(pair, PairGeometry):
                raise SynthesisError(f"pairs must be PairGeometry, got {type(pair).__name__}")
            pair_entries.append(_pair_entry(pair))

    snapshot: dict[str, Any] = {}
    if planets:
        snapshot["planets"] = planets
    if pair_entries:
        snapshot["pairs"] = pair_entries
    if lagna is not None:
        snapshot["lagna"] = lagna
    if bhavas:
        snapshot["bhavas"] = bhavas
    if chart is not None:
        snapshot["relative_houses"] = _relative_houses(chart)
    if transits:
        snapshot["transits"] = transits
    if eclipse_kinds or eclipse_classifications:
        snapshot["eclipses"] = {
            "kinds": _dedupe(eclipse_kinds),
            "classifications": _dedupe(eclipse_classifications),
        }
    if facts is not None:
        enrich_snapshot(snapshot, facts)
    return snapshot


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


# --------------------------------------------------------------------------- #
# Query validation (SPEC §6.4, §11 step 2)
# --------------------------------------------------------------------------- #


def _in_scope(
    rule: Rule,
    profile: TraditionProfile,
    query_domain: RuleDomain | None,
    source_registry: SourceRegistry,
) -> bool:
    """Profile + query filter for candidate rules (§11 step 3)."""
    if rule.status is not RuleStatus.ACTIVE:
        return False
    if query_domain is not None and rule.domain is not query_domain:
        return False
    if profile.domains is not None and rule.domain not in profile.domains:
        return False
    if rule.provenance.source_id not in profile.included_sources:
        return False
    tags = set(rule.tradition_tags)
    if tags:
        allowed: set[str] = set()
        for source_id in profile.included_sources:
            if source_registry.has(source_id):
                allowed.update(source_registry.get(source_id).lineage)
        if not (tags & allowed):
            return False
    return True


def domains_in_scope(
    query: RuleQuery,
    profile: TraditionProfile,
    rule_registry: RuleRegistry,
    source_registry: SourceRegistry,
) -> set[RuleDomain]:
    """Domains whose requirements the snapshot must satisfy (§6.4)."""
    if query.domain is not None:
        return {query.domain}
    if profile.domains is not None:
        return set(profile.domains)
    return {
        rule.domain
        for rule in rule_registry.all()
        if _in_scope(rule, profile, None, source_registry)
    }


def require_sections(snapshot: dict[str, Any], domains: set[RuleDomain]) -> None:
    """Raise ``SynthesisError`` when a domain-required section is missing."""
    missing = schema.missing_sections(snapshot, domains)
    if missing:
        domain_labels = ", ".join(sorted(domain.value for domain in domains))
        raise SynthesisError(
            f"fact_snapshot misses section(s) {missing} required by domain(s) {domain_labels}"
        )


# --------------------------------------------------------------------------- #
# The pipeline (§11)
# --------------------------------------------------------------------------- #


def synthesize(
    query: RuleQuery,
    profile: TraditionProfile,
    *,
    rule_registry: RuleRegistry,
    source_registry: SourceRegistry,
    profile_registry: ProfileRegistry,
    facts_registry: FactsRegistry,
    config: KnowledgeConfig,
) -> SynthesisResult:
    """Run the deterministic synthesis pipeline over a resolved profile."""
    snapshot = query.fact_snapshot
    if not isinstance(snapshot, dict):
        raise SynthesisError(
            "RuleQuery.fact_snapshot must be a normalized dict (use normalize_snapshot)"
        )

    # step 2 — validate domain-section requirements
    domains = domains_in_scope(query, profile, rule_registry, source_registry)
    require_sections(snapshot, domains)

    # step 3-4 — filter ACTIVE rules and evaluate every condition
    candidates = [
        rule
        for rule in rule_registry.all()
        if _in_scope(rule, profile, query.domain, source_registry)
    ]
    matched: list[Rule] = [rule for rule in candidates if schema.evaluate(rule.condition, snapshot)]

    def key_fn(rule: Rule) -> tuple[object, ...]:
        return precedence.precedence_key(rule, profile)

    # ascending key sort yields higher-first (SPEC §8)
    matched_ordered = sorted(matched, key=key_fn)

    # step 5 — exceptions first, then conflicts, per profile policy
    policy = profile.conflict_policy
    exception_resolution = reso.resolve_exceptions(matched_ordered, key_fn=key_fn, policy=policy)
    remaining = [
        rule for rule in matched_ordered if rule.rule_id not in exception_resolution.suppressed_ids
    ]
    pairs = reso.conflict_pairs(remaining)
    conflict_suppressed, conflict_records = reso.apply_conflict_policy(
        pairs, key_fn=key_fn, policy=policy
    )

    final_matched = [rule for rule in remaining if rule.rule_id not in conflict_suppressed]
    if len(final_matched) > config.max_rules_per_synthesis:
        final_matched = final_matched[: config.max_rules_per_synthesis]

    # status notes (SPEC §3.3)
    notes: dict[str, str] = {}
    for base_id, winner_id in exception_resolution.overrides.items():
        notes[base_id] = f"overridden by exception {winner_id}"
    for record in exception_resolution.records:
        if record.resolution == "exception" and "loses to" in record.reason:
            notes[record.rule_b_id] = f"exception conflict: overridden by {record.rule_a_id}"
    for record in conflict_records:
        if record.resolution == "first wins":
            notes[record.rule_b_id] = f"suppressed by {record.rule_a_id}"

    suppressed_ids = set(exception_resolution.suppressed_ids) | set(conflict_suppressed)
    suppressed_rules = tuple(rule for rule in matched_ordered if rule.rule_id in suppressed_ids)

    # step 6 — ResolvedRule metadata (SPEC §3.3, §10)
    resolved = [
        ResolvedRule(
            rule=rule,
            precedence_key=precedence.precedence_key(rule, profile),
            effective_weight=precedence.effective_weight(rule, profile, config),
            credibility=precedence.credibility(rule, config),
            applicability=True,
            status_note=notes.get(rule.rule_id),
        )
        for rule in final_matched
    ]

    # step 7 — provenance index, search metadata, echo
    # (SPEC §16: catalogs echoes all versions incl. the fact vocabulary)
    provenance_index = prov.provenance_index(tuple(matched), source_registry)
    credibilities = [item.credibility for item in resolved]
    catalogs = {
        "fact_vocabulary": schema.FACT_VOCABULARY_VERSION,
        "sources": source_registry.catalog_version,
        "profiles": profile_registry.catalog_version,
        "facts": facts_registry.catalog_version,
        **rule_registry.catalog_versions(),
    }
    metadata = SearchMetadata(
        algorithm=ALGORITHM_NAME,
        catalogs=catalogs,
        rules_evaluated=len(candidates),
        rules_matched=len(resolved),
        credibility_summary=precedence.credibility_summary(credibilities),
    )
    suppressed_resolved = tuple(
        ResolvedRule(
            rule=rule,
            precedence_key=precedence.precedence_key(rule, profile),
            effective_weight=precedence.effective_weight(rule, profile, config),
            credibility=precedence.credibility(rule, config),
            applicability=True,
            status_note=notes.get(rule.rule_id),
        )
        for rule in suppressed_rules
    )
    return SynthesisResult(
        query=query,
        profile=profile,
        matched_rules=tuple(resolved),
        suppressed_rules=suppressed_resolved if query.include_suppressed else (),
        conflicts=(*exception_resolution.records, *conflict_records),
        provenance_index=provenance_index,
        config=config,
        search_metadata=metadata,
    )
