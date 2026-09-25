"""JRS Phase 5D: Multi-Varga Calculation Module.

Exact planetary placements across the four vargas the deliverable
requires (D1 Rasi, D9 Navamsha, D10 Dashamsha, D60 Shashtiamsha) plus
the classical cross-varga evaluations:

- **Vargottama** — the planet occupies the same sign in D1 and D9
  (reinforced placement, classically rated as strong as exaltation).
- **Navamsha dignity** — exalted / own / neutral / debilitated in D9
  (the D9 tests what a rasi placement is really worth).
- **D10 career-anchor strength** — dignity of Sun and Saturn (the
  natural career significators: authority and work) in the Dashamsha.

Divisional counting rules (source-verified, BPHS varga definitions):

=========== ==== ==================================== =====================
Varga       Arc  Counting rule                        Verification
=========== ==== ==================================== =====================
D1          30°  sign itself                          natal positions
D9      3°20′  element-quadrant starts (see note)    500/500 golden
                                                      fixtures; equals repo
                                                      ``_compute_d9_sign``
D10         3°   odd: self; even: 9th from it         BPHS example: 17°20′
                                                      Leo (6th part) →
                                                      Capricorn
D60        30′   continuous from the sign             repo ``_d60``
                                                      convention; classical
                                                      named-amsa lords noted
                                                      as a future extension
=========== ==== ==================================== =====================

D9 note: the count for a sign begins at the movable sign given by the
repo's golden-verified element scheme — fire signs count from
themselves, earth from the 6th sign (inclusive), air from the 5th,
water from the 9th. This reproduces all 500 hand-verified
``expected_canonical_facts.d9_sign`` cases across the golden corpus and
matches ``jrs.api.dependencies._compute_d9_sign`` exactly. Textbook
variants (continuous-from-Aries, or the movable/fixed/dual modality
rule) place roughly two thirds of the zodiac differently and are
therefore NOT used here; this module follows the codebase's validated
convention.

Every placement emits a canonical ``FACT-VARGA-<DIV>-<BODY>`` provenance
id, vargottama placements add ``FACT-VARGA-VARGOTTAMA-<BODY>``, and
cross-varga relations emit ``REL-VARGA-SUPPORTS`` / ``REL-VARGA-DAMPENS``
edges linking the D9 fact to the D1 fact (flag-on path only, see
``jrs.prediction_engine.provenance``).

Determinism contract
--------------------
Pure arithmetic over caller-supplied longitudes: no I/O, no ephemeris,
no wall-clock, no unordered iteration. Identical inputs yield
byte-identical reports, safe for the Stage 8 golden-state manifest.

Feature flag
------------
``varga_scoring_enabled()`` (default **False**, env override
``JRS_VARGA_SCORING``) gates injection of the report into
``jre_facts``; the frozen benchmark baseline (Micro-F1 = 0.7435) cannot
silently regress.
"""

from __future__ import annotations

import os
from typing import Any

__all__ = [
    "VARGA_STAGE_VERSION",
    "VARGA_DIVISIONS",
    "DIGNITY_EXALTATION",
    "DIGNITY_OWN_SIGNS",
    "CAREER_ANCHOR_PLANETS",
    "DIGNITY_SCORES",
    "RASHI_ORDER",
    "varga_scoring_enabled",
    "varga_sign_index",
    "varga_placement",
    "dignity_of",
    "compute_multi_varga",
    "multi_varga_to_dict",
]

#: Version of this calculation module (bump on semantic change).
VARGA_STAGE_VERSION = "1.0.0"

#: The vargas this module computes: division -> arc of one part in degrees.
VARGA_DIVISIONS: dict[str, tuple[int, float]] = {
    "D1": (1, 30.0),
    "D9": (9, 30.0 / 9.0),
    "D10": (10, 3.0),
    "D60": (60, 0.5),
}

RASHI_ORDER: tuple[str, ...] = (
    "MESHA",
    "VRISHABHA",
    "MITHUNA",
    "KARKA",
    "SIMHA",
    "KANYA",
    "TULA",
    "VRISHCHIKA",
    "DHANUSHA",
    "MAKARA",
    "KUMBHA",
    "MEENA",
)

#: Bodies evaluated (seven planets; the Lagna is evaluated separately
#: when its longitude is available).
VARGA_PLANETS: tuple[str, ...] = (
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
)

# ── Dignity tables (classical) ──────────────────────────────────────────────
#: Exaltation sign index per planet; debilitation is the 7th from it.
DIGNITY_EXALTATION: dict[str, int] = {
    "SUN": 0,  # MESHA
    "MOON": 1,  # VRISHABHA
    "MARS": 9,  # MAKARA
    "MERCURY": 5,  # KANYA
    "JUPITER": 3,  # KARKA
    "VENUS": 11,  # MEENA
    "SATURN": 6,  # TULA
}

#: Moolatrikona/own signs per planet.
DIGNITY_OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "SUN": (4,),  # SIMHA
    "MOON": (3,),  # KARKA
    "MARS": (0, 7),  # MESHA, VRISHCHIKA
    "MERCURY": (2, 5),  # MITHUNA, KANYA
    "JUPITER": (8, 11),  # DHANUSHA, MEENA
    "VENUS": (1, 6),  # VRISHABHA, TULA
    "SATURN": (9, 10),  # MAKARA, KUMBHA
}

#: D10 career anchors: the natural significators of authority and work.
CAREER_ANCHOR_PLANETS: tuple[str, ...] = ("SUN", "SATURN")

#: Dignity -> strength score used by the D10 career-anchor evaluation.
DIGNITY_SCORES: dict[str, float] = {
    "EXALTED": 1.0,
    "OWN": 0.75,
    "NEUTRAL": 0.5,
    "DEBILITATED": 0.25,
}


# ── Feature flag ────────────────────────────────────────────────────────────
def varga_scoring_enabled() -> bool:
    """Whether multi-varga scoring facts are injected into ``jre_facts``.

    Default **False**: the frozen benchmark baseline (Micro-F1 = 0.7435)
    is unaffected. Set ``JRS_VARGA_SCORING=1`` (truthy) to enable.
    """
    return os.environ.get("JRS_VARGA_SCORING", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# ── Divisional arithmetic ───────────────────────────────────────────────────
def varga_sign_index(longitude: float, division: str) -> int:
    """Sign index (0–11, Mesha = 0) of a longitude in one varga.

    Args:
        longitude: Sidereal longitude (0–360).
        division: One of ``VARGA_DIVISIONS`` keys ("D1", "D9", "D10",
            "D60").

    Raises:
        ValueError: On an unknown division key.
    """
    if division not in VARGA_DIVISIONS:
        raise ValueError(f"unknown varga division: {division!r}")
    n, arc = VARGA_DIVISIONS[division]
    lon = longitude % 360.0
    sign_idx = int(lon / 30.0)
    degree_in_sign = lon - sign_idx * 30.0
    part = int(degree_in_sign / arc)

    if division in ("D1", "D60"):
        # Continuous count from the sign itself.
        start = sign_idx
    elif division == "D9":
        # Element-quadrant starts (golden-verified, matches
        # _compute_d9_sign exactly): fire counts from itself, earth from
        # +5, air from +4, water from +8 (exclusive offsets).
        element = sign_idx % 4
        if element == 0:  # fire
            start = sign_idx
        elif element == 1:  # earth
            start = (sign_idx + 5) % 12
        elif element == 2:  # air
            start = (sign_idx + 4) % 12
        else:  # water
            start = (sign_idx + 8) % 12
    else:  # D10
        # Odd signs count from themselves; even signs from the 9th from
        # it (inclusive), i.e. an offset of +8 signs.
        start = sign_idx if sign_idx % 2 == 0 else (sign_idx + 8) % 12
    return (start + part) % 12


def varga_placement(longitude: float, division: str) -> dict[str, Any]:
    """Full placement record for one longitude in one varga."""
    n, arc = VARGA_DIVISIONS[division]
    sign_idx = varga_sign_index(longitude, division)
    degree_in_sign = (longitude % 360.0) % 30.0
    part = int(degree_in_sign / arc) + 1  # 1-based division number
    return {
        "sign": RASHI_ORDER[sign_idx],
        "sign_index": sign_idx,
        "division_part": part,
        "degree_in_division": round(
            (degree_in_sign % arc) * n, 6
        ),
    }


def dignity_of(planet: str, sign_index: int) -> str:
    """Classical dignity of a planet in a sign (EXALTED/OWN/NEUTRAL/
    DEBILITATED). Unknown planets are NEUTRAL by definition."""
    exalt = DIGNITY_EXALTATION.get(planet)
    if exalt is not None:
        if sign_index == exalt:
            return "EXALTED"
        if sign_index == (exalt + 6) % 12:
            return "DEBILITATED"
    if sign_index in DIGNITY_OWN_SIGNS.get(planet, ()):
        return "OWN"
    return "NEUTRAL"


# ── Report assembly ─────────────────────────────────────────────────────────
def _body_longitudes(facts: dict[str, Any]) -> dict[str, float]:
    """Natal sidereal longitudes of the seven planets from JRE facts."""
    planets = facts.get("planets", {})
    longitudes: dict[str, float] = {}
    for planet in VARGA_PLANETS:
        pdata = planets.get(planet, {})
        lon = pdata.get("longitude")
        if not isinstance(lon, (int, float)):
            raise ValueError(f"varga input missing longitude: {planet}")
        longitudes[planet] = float(lon)
    return longitudes


def compute_multi_varga(
    facts: dict[str, Any],
    lagna_longitude: float | None = None,
) -> dict[str, Any]:
    """Full deterministic multi-varga report.

    Args:
        facts: Natal JRE facts (``planets[name]["longitude"]``).
        lagna_longitude: Optional ascendant longitude; when provided, the
            Lagna is evaluated across the vargas too (including
            Lagna-vargottama). Never read from ``facts`` to avoid
            mutating or depending on enrichment behavior.

    Returns:
        Report dict with placements per body per division, cross-varga
        evaluations (vargottama, navamsha dignity, D10 career anchor),
        and ``FACT-VARGA-*`` provenance ids.
    """
    longitudes = _body_longitudes(facts)
    bodies: dict[str, float] = dict(longitudes)
    if lagna_longitude is not None:
        bodies["LAGNA"] = float(lagna_longitude)

    placements: dict[str, dict[str, dict[str, Any]]] = {}
    for body, lon in bodies.items():
        placements[body] = {
            div: varga_placement(lon, div) for div in VARGA_DIVISIONS
        }

    # Cross-varga evaluations.
    vargottama: dict[str, bool] = {}
    navamsha_dignity: dict[str, str] = {}
    d10_dignity: dict[str, str] = {}
    for body in bodies:
        d1_idx = placements[body]["D1"]["sign_index"]
        d9_idx = placements[body]["D9"]["sign_index"]
        vargottama[body] = d1_idx == d9_idx
        if body != "LAGNA":
            navamsha_dignity[body] = dignity_of(body, d9_idx)
            d10_dignity[body] = dignity_of(body, placements[body]["D10"]["sign_index"])

    # D10 career-anchor strength over SUN and SATURN.
    anchor_scores = {
        p: DIGNITY_SCORES[d10_dignity.get(p, "NEUTRAL")]
        for p in CAREER_ANCHOR_PLANETS
    }
    best_anchor = max(
        CAREER_ANCHOR_PLANETS,
        key=lambda p: (anchor_scores[p], -CAREER_ANCHOR_PLANETS.index(p)),
    )
    career_anchor = {
        "planet": best_anchor,
        "dignity": d10_dignity.get(best_anchor, "NEUTRAL"),
        "strength": round(anchor_scores[best_anchor], 6),
        "scores": {p: anchor_scores[p] for p in CAREER_ANCHOR_PLANETS},
    }

    # Provenance ids: D1/D9/D10/D60 facts per body + vargottama facts.
    fact_ids: list[str] = []
    for body in bodies:
        for div in VARGA_DIVISIONS:
            fact_ids.append(f"FACT-VARGA-{div}-{body}")
    for body in bodies:
        if vargottama[body]:
            fact_ids.append(f"FACT-VARGA-VARGOTTAMA-{body}")
    fact_ids.append("FACT-VARGA-D10-CAREER-ANCHOR")

    return {
        "version": VARGA_STAGE_VERSION,
        "placements": placements,
        "vargottama": vargottama,
        "navamsha_dignity": navamsha_dignity,
        "d10_dignity": d10_dignity,
        "career_anchor": career_anchor,
        "lagna_evaluated": lagna_longitude is not None,
        "fact_ids": tuple(fact_ids),
    }


def multi_varga_to_dict(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize the report with JSON-safe types and canonical order."""
    bodies = list(report["placements"])
    return {
        "version": report["version"],
        "placements": {
            body: {
                div: dict(report["placements"][body][div])
                for div in ("D1", "D9", "D10", "D60")
            }
            for body in bodies
        },
        "vargottama": {b: report["vargottama"][b] for b in bodies},
        "navamsha_dignity": {
            b: report["navamsha_dignity"][b]
            for b in bodies
            if b in report["navamsha_dignity"]
        },
        "d10_dignity": {
            b: report["d10_dignity"][b]
            for b in bodies
            if b in report["d10_dignity"]
        },
        "career_anchor": dict(report["career_anchor"]),
        "lagna_evaluated": report["lagna_evaluated"],
        "fact_ids": list(report["fact_ids"]),
    }
