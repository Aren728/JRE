"""JRS-067 Western Astrology interpretation models.

Defines the outcome taxonomy, rule catalog, and fact extraction logic
for the Western interpretation layer.  Consumes JRE-066 WesternChart
facts and produces EvidenceRecord objects that can be wrapped in
SystemAssessment objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from jrs.evidence.models import (
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
)
from western.models import (
    WesternAspectType,
    WesternChart,
    WesternPlanet,
)

# ── Outcome Taxonomy ─────────────────────────────────────────────────────────


class WesternOutcomeTaxonomy(Enum):
    """Western astrological outcome categories.

    Derived from classical house significations (Ptolemy, Lilly)
    and aspect-based judgments.
    """

    CAREER_PROMINENCE = "CAREER_PROMINENCE"
    RELATIONSHIP_HARMONY = "RELATIONSHIP_HARMONY"
    EMOTIONAL_TENSION = "EMOTIONAL_TENSION"
    FINANCIAL_GAIN = "FINANCIAL_GAIN"
    INTELLECTUAL_CAPACITY = "INTELLECTUAL_CAPACITY"
    LEADERSHIP_AUTHORITY = "LEADERSHIP_AUTHORITY"
    SOCIAL_INFLUENCE = "SOCIAL_INFLUENCE"
    PHILOSOPHICAL_DEPTH = "PHILOSOPHICAL_DEPTH"
    CREATIVE_TALENT = "CREATIVE_TALENT"
    DOMESTIC_PROMINENCE = "DOMESTIC_PROMINENCE"


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WesternRule:
    """A single classical Western rule mapping chart facts to an outcome."""

    rule_id: str
    description: str
    condition_facts: tuple[str, ...]
    outcome: WesternOutcomeTaxonomy
    direction: EvidenceDirection
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    source_id: str = "PTOLEMY"
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "condition_facts": list(self.condition_facts),
            "outcome": self.outcome.value,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "source_id": self.source_id,
            "location": self.location,
        }


@dataclass(frozen=True)
class WesternRuleCatalog:
    """Complete catalog of Western domain rules."""

    rules: tuple[WesternRule, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "rule_count": len(self.rules),
        }

    def get_rules_by_outcome(
        self, outcome: WesternOutcomeTaxonomy
    ) -> tuple[WesternRule, ...]:
        """Get all rules for a specific outcome taxonomy."""
        return tuple(r for r in self.rules if r.outcome is outcome)


@dataclass(frozen=True)
class WesternConfig:
    """Configuration metadata for the Western domain."""

    version: str = "1.0"
    source_id: str = "PTOLEMY"
    default_strength: str = "MODERATE"


# ── Fact Extraction from WesternChart ────────────────────────────────────────

# Mapping from planet to its house position key
_PLANET_HOUSE_KEYS: dict[WesternPlanet, str] = {
    WesternPlanet.SUN: "sun_house",
    WesternPlanet.MOON: "moon_house",
    WesternPlanet.MERCURY: "mercury_house",
    WesternPlanet.VENUS: "venus_house",
    WesternPlanet.MARS: "mars_house",
    WesternPlanet.JUPITER: "jupiter_house",
    WesternPlanet.SATURN: "saturn_house",
    WesternPlanet.URANUS: "uranus_house",
    WesternPlanet.NEPTUNE: "neptune_house",
    WesternPlanet.PLUTO: "pluto_house",
}

# Mapping from planet to its dignity key
_PLANET_DIGNITY_KEYS: dict[WesternPlanet, str] = {
    WesternPlanet.SUN: "sun_dignity",
    WesternPlanet.MOON: "moon_dignity",
    WesternPlanet.MERCURY: "mercury_dignity",
    WesternPlanet.VENUS: "venus_dignity",
    WesternPlanet.MARS: "mars_dignity",
    WesternPlanet.JUPITER: "jupiter_dignity",
    WesternPlanet.SATURN: "saturn_dignity",
}

# Aspect key templates: "aspect_{planet_a}_{aspect_type}_{planet_b}"
# Normalized to lowercase with underscores


def _aspect_key(
    planet_a: WesternPlanet,
    aspect_type: WesternAspectType,
    planet_b: WesternPlanet,
) -> str:
    """Generate a deterministic fact key for an aspect."""
    a_name = planet_a.value.lower()
    b_name = planet_b.value.lower()
    atype = aspect_type.value.lower()
    # Alphabetical ordering for deterministic keys
    if a_name > b_name:
        a_name, b_name = b_name, a_name
    return f"aspect_{a_name}_{atype}_{b_name}"


def extract_facts_from_chart(chart: WesternChart) -> dict[str, Any]:
    """Extract a flat fact dictionary from a WesternChart for rule evaluation.

    The fact dictionary maps condition strings (as used in TOML rules)
    to their values from the chart.

    Args:
        chart: A WesternChart from JRE-066.

    Returns:
        A dictionary of fact_key -> value pairs.
    """
    facts: dict[str, Any] = {}

    # Extract house positions
    # Build a lookup: planet -> house_number from house cusps
    planet_houses: dict[WesternPlanet, int] = {}
    for pp in chart.planet_positions:
        # Determine which house each planet falls in
        house_num = _determine_house(pp.longitude, chart)
        if house_num is not None:
            planet_houses[pp.planet] = house_num

    for planet, key in _PLANET_HOUSE_KEYS.items():
        if planet in planet_houses:
            facts[key] = str(planet_houses[planet])

    # Extract dignities
    for planet, key in _PLANET_DIGNITY_KEYS.items():
        if planet in chart.dignities:
            facts[key] = chart.dignities[planet].value

    # Extract aspects
    for aspect in chart.aspects:
        key = _aspect_key(aspect.planet_a, aspect.aspect_type, aspect.planet_b)
        facts[key] = "true"

    return facts


def _determine_house(
    longitude: float, chart: WesternChart
) -> int | None:
    """Determine which house a planet falls in based on house cusps.

    Uses the standard method: a planet is in house N if its longitude
    is between house cusp N and cusp N+1 (wrapping around the zodiac).
    """
    if not chart.house_cusps:
        return None

    cusps = [hc.longitude for hc in chart.house_cusps]
    n = len(cusps)

    for i in range(n):
        cusp_start = cusps[i]
        cusp_end = cusps[(i + 1) % n]

        if cusp_start < cusp_end:
            # Normal case: cusp_start < longitude <= cusp_end
            if cusp_start < longitude <= cusp_end:
                return i + 1
        else:
            # Wrap-around case (e.g., cusp at 350° wraps to 10°)
            if longitude > cusp_start or longitude <= cusp_end:
                return i + 1

    # If no cusp matches (shouldn't happen), return None
    return None


# ── Condition Evaluation ─────────────────────────────────────────────────────


def evaluate_condition(condition: str, facts: dict[str, Any]) -> bool:
    """Evaluate a single condition against the facts dictionary.

    Supports:
    - ``fact_name=value``: equality check
    - ``fact_name=true``: truthy check

    Args:
        condition: The condition string to evaluate.
        facts: The facts dictionary.

    Returns:
        True if the condition is satisfied.
    """
    condition = condition.strip()

    if "=" in condition:
        parts = condition.split("=", 1)
        fact_name = parts[0].strip()
        target = parts[1].strip().strip("'\"")
        fact_val = facts.get(fact_name)
        if fact_val is None:
            return False
        return str(fact_val).lower() == target.lower()

    # Truthy check
    fact_val = facts.get(condition)
    return bool(fact_val) if fact_val is not None else False


def evaluate_rule(
    rule: WesternRule, facts: dict[str, Any]
) -> EvidenceRecord | None:
    """Evaluate a single rule against facts and produce an EvidenceRecord.

    All condition_facts must be satisfied (AND logic).

    Args:
        rule: The Western rule to evaluate.
        facts: The facts dictionary from the chart.

    Returns:
        An EvidenceRecord if all conditions are met, None otherwise.
    """
    if not rule.condition_facts:
        return None

    for condition in rule.condition_facts:
        if not evaluate_condition(condition, facts):
            return None

    return EvidenceRecord(
        evidence_id=f"{rule.rule_id}-auto",
        outcome_taxonomy=rule.outcome.value,
        supporting_fact_type=",".join(rule.condition_facts),
        rule_id=rule.rule_id,
        source_id=rule.source_id,
        location=rule.location,
        direction=rule.direction,
        strength=rule.strength,
    )


def evaluate_facts(
    rules: tuple[WesternRule, ...], facts: dict[str, Any]
) -> tuple[EvidenceRecord, ...]:
    """Evaluate all rules against facts and return matching EvidenceRecords.

    Args:
        rules: The tuple of Western rules.
        facts: The facts dictionary from the chart.

    Returns:
        A tuple of EvidenceRecord objects for all rules that fired.
    """
    records: list[EvidenceRecord] = []
    for rule in rules:
        record = evaluate_rule(rule, facts)
        if record is not None:
            records.append(record)
    return tuple(records)
