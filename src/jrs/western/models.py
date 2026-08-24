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

# Planetary Joys — classical house assignments
# Source: Ptolemy Tetrabiblos III.13, Lilly CA Ch. 21
# Sun = 9th, Moon = 3rd, Mercury = 1st, Venus = 5th,
# Mars = 6th, Jupiter = 11th, Saturn = 12th
PLANETARY_JOYS: dict[WesternPlanet, int] = {
    WesternPlanet.SUN: 9,
    WesternPlanet.MOON: 3,
    WesternPlanet.MERCURY: 1,
    WesternPlanet.VENUS: 5,
    WesternPlanet.MARS: 6,
    WesternPlanet.JUPITER: 11,
    WesternPlanet.SATURN: 12,
}

# Egyptian Terms/Bounds — each 30° sign divided into 5 bounds.
# Each bound has a ruling planet and an end degree within the sign.
# Source: Dorotheus of Sidon C.I.14, Lilly CA Ch. 32.
# Format: sign_index -> list of (end_degree, ruling_planet)
# The end_degree is exclusive upper bound within the sign (0-30).
_EGYPTIAN_TERMS: dict[int, list[tuple[float, WesternPlanet]]] = {
    0: [  # Aries
        (6.0, WesternPlanet.JUPITER),
        (14.0, WesternPlanet.VENUS),
        (22.0, WesternPlanet.MERCURY),
        (26.0, WesternPlanet.MARS),
        (30.0, WesternPlanet.SATURN),
    ],
    1: [  # Taurus
        (8.0, WesternPlanet.VENUS),
        (15.0, WesternPlanet.MERCURY),
        (24.0, WesternPlanet.JUPITER),
        (30.0, WesternPlanet.SATURN),
    ],
    2: [  # Gemini
        (6.0, WesternPlanet.MERCURY),
        (12.0, WesternPlanet.JUPITER),
        (18.0, WesternPlanet.VENUS),
        (24.0, WesternPlanet.MARS),
        (30.0, WesternPlanet.SATURN),
    ],
    3: [  # Cancer
        (7.0, WesternPlanet.MARS),
        (13.0, WesternPlanet.JUPITER),
        (20.0, WesternPlanet.MERCURY),
        (26.0, WesternPlanet.VENUS),
        (30.0, WesternPlanet.SATURN),
    ],
    4: [  # Leo
        (6.0, WesternPlanet.JUPITER),
        (12.0, WesternPlanet.VENUS),
        (18.0, WesternPlanet.SATURN),
        (24.0, WesternPlanet.MERCURY),
        (30.0, WesternPlanet.MARS),
    ],
    5: [  # Virgo
        (7.0, WesternPlanet.MERCURY),
        (14.0, WesternPlanet.VENUS),
        (20.0, WesternPlanet.JUPITER),
        (26.0, WesternPlanet.MARS),
        (30.0, WesternPlanet.SATURN),
    ],
    6: [  # Libra
        (6.0, WesternPlanet.SATURN),
        (11.0, WesternPlanet.JUPITER),
        (19.0, WesternPlanet.VENUS),
        (24.0, WesternPlanet.MERCURY),
        (30.0, WesternPlanet.MARS),
    ],
    7: [  # Scorpio
        (7.0, WesternPlanet.MARS),
        (11.0, WesternPlanet.JUPITER),
        (19.0, WesternPlanet.VENUS),
        (24.0, WesternPlanet.MERCURY),
        (30.0, WesternPlanet.SATURN),
    ],
    8: [  # Sagittarius
        (12.0, WesternPlanet.JUPITER),
        (18.0, WesternPlanet.VENUS),
        (24.0, WesternPlanet.MERCURY),
        (26.0, WesternPlanet.MARS),
        (30.0, WesternPlanet.SATURN),
    ],
    9: [  # Capricorn
        (7.0, WesternPlanet.SATURN),
        (14.0, WesternPlanet.MERCURY),
        (22.0, WesternPlanet.JUPITER),
        (30.0, WesternPlanet.VENUS),
    ],
    10: [  # Aquarius
        (7.0, WesternPlanet.SATURN),
        (14.0, WesternPlanet.MERCURY),
        (22.0, WesternPlanet.JUPITER),
        (30.0, WesternPlanet.VENUS),
    ],
    11: [  # Pisces
        (12.0, WesternPlanet.JUPITER),
        (18.0, WesternPlanet.VENUS),
        (24.0, WesternPlanet.MERCURY),
        (26.0, WesternPlanet.MARS),
        (30.0, WesternPlanet.SATURN),
    ],
}

# Combustion thresholds (degrees from Sun)
# Source: Lilly CA Ch. 22, Ptolemy Tetrabiblos II.9
_CAZIMI_THRESHOLD = 0.5  # Within 0°17' of Sun center = cazimi
_UNDER_BEAMS_THRESHOLD = 17.0  # Within 17° of Sun = under the beams
_COMBUST_THRESHOLD = 8.5  # Within 8°30' of Sun = combust


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

    Extracts:
    - House positions (sun_house, moon_house, etc.)
    - Essential dignities (sun_dignity, moon_dignity, etc.)
    - Aspects (aspect_sun_trine_jupiter, etc.)
    - Sect (chart_sect = DIURNAL | NOCTURNAL)
    - Planetary joys (planet_X_in_joy_house = true)
    - Egyptian terms/bounds (planet_X_term_ruler = PLANET)
    - Mutual receptions (mutual_reception_X_Y = true)
    - Accidental dignities (planet_X_cazimi, planet_X_combust, planet_X_under_beams)

    Args:
        chart: A WesternChart from JRE-066.

    Returns:
        A dictionary of fact_key -> value pairs.
    """
    facts: dict[str, Any] = {}

    # Build a lookup: planet -> house_number from house cusps
    planet_houses: dict[WesternPlanet, int] = {}
    for pp in chart.planet_positions:
        house_num = _determine_house(pp.longitude, chart)
        if house_num is not None:
            planet_houses[pp.planet] = house_num

    # ── House positions ──────────────────────────────────────────────
    for planet, key in _PLANET_HOUSE_KEYS.items():
        if planet in planet_houses:
            facts[key] = str(planet_houses[planet])

    # ── Essential dignities ──────────────────────────────────────────
    for planet, key in _PLANET_DIGNITY_KEYS.items():
        if planet in chart.dignities:
            facts[key] = chart.dignities[planet].value

    # ── Aspects ──────────────────────────────────────────────────────
    for aspect in chart.aspects:
        key = _aspect_key(aspect.planet_a, aspect.aspect_type, aspect.planet_b)
        facts[key] = "true"

    # ── Sect ─────────────────────────────────────────────────────────
    facts["chart_sect"] = chart.sect.value

    # ── Planetary Joys ───────────────────────────────────────────────
    for planet, joy_house in PLANETARY_JOYS.items():
        if planet in planet_houses and planet_houses[planet] == joy_house:
            pname = planet.value.lower()
            facts[f"{pname}_joy"] = "true"

    # ── Egyptian Terms/Bounds ────────────────────────────────────────
    for pp in chart.planet_positions:
        sign_idx = int(pp.longitude / 30.0) % 12
        deg_in_sign = pp.longitude % 30.0
        bounds = _EGYPTIAN_TERMS.get(sign_idx, ())
        for end_deg, ruler in bounds:
            if deg_in_sign <= end_deg:
                pname = pp.planet.value.lower()
                facts[f"{pname}_term_ruler"] = ruler.value
                break

    # ── Mutual Receptions (by domicile) ──────────────────────────────
    _extract_mutual_receptions_domicile(chart, planet_houses, facts)

    # ── Accidental Dignities ─────────────────────────────────────────
    _extract_accidental_dignities(chart, facts)

    return facts


def _extract_mutual_receptions_domicile(
    chart: WesternChart,
    planet_houses: dict[WesternPlanet, int],  # noqa: ARG001
    facts: dict[str, Any],
) -> None:
    """Extract mutual reception by domicile.

    A mutual reception occurs when two planets are in each other's
    domicile sign.  E.g., Venus in Aries (Mars's domicile) and
    Mars in Taurus (Venus's domicile).

    Source: Lilly CA Ch. 26, Dorotheus C.I.14.
    """
    classical_planets = [
        WesternPlanet.MERCURY,
        WesternPlanet.VENUS,
        WesternPlanet.MARS,
        WesternPlanet.JUPITER,
        WesternPlanet.SATURN,
    ]
    from western.models import DOMICILE_SIGNS, SECONDARY_DOMICILE

    # Build planet -> sign_index lookup
    planet_signs: dict[WesternPlanet, int] = {}
    for pp in chart.planet_positions:
        planet_signs[pp.planet] = int(pp.longitude / 30.0) % 12

    for i, pa in enumerate(classical_planets):
        for pb in classical_planets[i + 1 :]:
            # Check: pa in pb's domicile AND pb in pa's domicile
            pa_sign = planet_signs.get(pa)
            pb_sign = planet_signs.get(pb)
            if pa_sign is None or pb_sign is None:
                continue

            # Get domicile sign for each planet
            pa_dom = DOMICILE_SIGNS.get(pa)
            pa_sec = SECONDARY_DOMICILE.get(pa)
            pb_dom = DOMICILE_SIGNS.get(pb)
            pb_sec = SECONDARY_DOMICILE.get(pb)

            pa_in_pb_domicile = (
                pb_sign == pa_dom
                or (pa_sec is not None and pb_sign == pa_sec)
                or (pb_dom is not None and pa_sign == pb_dom)
                or (pb_sec is not None and pa_sign == pb_sec)
            )

            pb_in_pa_domicile = (
                pa_sign == pb_dom
                or (pb_sec is not None and pa_sign == pb_sec)
                or (pa_dom is not None and pb_sign == pa_dom)
                or (pa_sec is not None and pb_sign == pa_sec)
            )

            if pa_in_pb_domicile and pb_in_pa_domicile:
                pa_name = pa.value.lower()
                pb_name = pb.value.lower()
                # Deterministic key ordering
                if pa_name < pb_name:
                    key = f"mutual_reception_{pa_name}_{pb_name}"
                else:
                    key = f"mutual_reception_{pb_name}_{pa_name}"
                facts[key] = "true"


def _extract_accidental_dignities(
    chart: WesternChart,
    facts: dict[str, Any],
) -> None:
    """Extract accidental dignity facts from chart.

    Checks for:
    - Cazimi: planet within 0°30' of Sun center
    - Combust: planet within 8°30' of Sun
    - Under the beams: planet within 17° of Sun

    Source: Lilly CA Ch. 22, Ptolemy Tetrabiblos II.9.
    """
    sun = next(
        (pp for pp in chart.planet_positions if pp.planet == WesternPlanet.SUN),
        None,
    )
    if sun is None:
        return

    for pp in chart.planet_positions:
        if pp.planet == WesternPlanet.SUN:
            continue
        pname = pp.planet.value.lower()
        angular_dist = abs(pp.longitude - sun.longitude) % 360.0
        if angular_dist > 180.0:
            angular_dist = 360.0 - angular_dist

        if angular_dist <= _CAZIMI_THRESHOLD:
            facts[f"{pname}_cazimi"] = "true"
        elif angular_dist <= _COMBUST_THRESHOLD:
            facts[f"{pname}_combust"] = "true"
        elif angular_dist <= _UNDER_BEAMS_THRESHOLD:
            facts[f"{pname}_under_beams"] = "true"


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
