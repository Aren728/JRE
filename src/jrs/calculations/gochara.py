"""JRS Phase 5C: Gochara (Transit) Calculation Module.

Standalone, deterministic transit-fact and relationship generator per
``docs/validation/phase_5c_gochara_spec.md``:

- **Transit positions** — sidereal longitudes of the seven classical
  planets at a reference instant (``compute_transit_positions`` via the
  Swiss-Ephemeris-backed JyotishService), evaluated against natal
  Moon/Lagna anchors with whole-sign (rashi-relative) house counting.
- **Vedha (obstruction)** — the classical benefic-house obstruction
  table: a planet transiting a favorable house from the natal Moon loses
  its good effects when another (non-exempt) planet occupies the paired
  obstructing house. Exemptions: Saturn never obstructs the Sun (and
  vice versa); the Moon and Mercury never mutually afflict.
- **Kakshya** — each sign's eight 3°45′ divisions with the canonical
  lord sequence Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna.
- **TQS** — Transit Quality Score: the natal Shodhita SAV (fallback raw
  SAV, recorded via ``tqs_basis``) of the sign a planet transits, mapped
  through the frozen ``GOCHARA_BANDS`` multipliers; active Vedha applies
  the frozen ``VEDHA_MULTIPLIER`` dampening.

Every transit record emits a canonical ``FACT-GOCHARA-*`` provenance id
(e.g. ``FACT-GOCHARA-SATURN-MAKARA-K3``) and links to the natal
Moon/Lagna anchors over ``REL-GOCHARA-*`` edges when embedded in the
evidence graph (flag-on path only).

Determinism contract
--------------------
No wall-clock reads, no randomness, no unordered iteration. Transits are
always evaluated either at caller-supplied positions or at the pinned
``GOCHARA_TRANSIT_EPOCH`` — identical inputs yield byte-identical
reports, safe for the Stage 7 golden-state manifest.

Feature flag
------------
``gochara_scoring_enabled()`` (default **False**, env override
``JRS_GOCHARA_SCORING``) gates injection of the report into
``jre_facts``; the frozen benchmark baseline (Micro-F1 = 0.7435) cannot
silently regress.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

__all__ = [
    "GOCHARA_STAGE_VERSION",
    "GOCHARA_TRANSIT_EPOCH",
    "GOCHARA_BANDS",
    "VEDHA_MULTIPLIER",
    "VEDHA_TABLE",
    "VEDHA_EXEMPTIONS",
    "KAKSHYA_LORDS",
    "KAKSHYA_ARC_DEG",
    "RASHI_ORDER",
    "GOCHARA_PLANETS",
    "gochara_scoring_enabled",
    "compute_transit_positions",
    "house_from_anchor",
    "kakshya_of",
    "is_vedha_obstructed",
    "band_for_tqs",
    "compute_tqs",
    "compute_gochara",
    "gochara_to_dict",
]

#: Version of this calculation module (bump on semantic change).
GOCHARA_STAGE_VERSION = "1.0.0"

#: Pinned reference instant for golden-state transit evaluation.
#: Never wall-clock: identical to the Phase 2 dasha pinning discipline.
GOCHARA_TRANSIT_EPOCH = dt.datetime(2020, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)

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

#: The seven classical gochara planets (nodes excluded).
GOCHARA_PLANETS: tuple[str, ...] = (
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
)

# ── Frozen band multipliers (spec §3) ───────────────────────────────────────
#: (min_tqs, multiplier, label); first matching threshold wins.
GOCHARA_BANDS: tuple[tuple[int, float, str], ...] = (
    (30, 1.08, "SUPPORTIVE"),
    (25, 1.00, "NEUTRAL"),
    (18, 0.92, "MIXED"),
    (0, 0.80, "AFFLICTED"),
)

#: Multiplicative dampening applied when an active Vedha obstructs the
#: planet's current favorable transit house.
VEDHA_MULTIPLIER: float = 0.80

# ── Classical Vedha table (BPHS/Vashishta gochara rules) ────────────────────
#: VEDHA_TABLE[planet][favorable_house_from_moon] = obstructing_house.
#: A planet transiting the favorable house is obstructed when another
#: (non-exempt) planet transits the paired house from the natal Moon.
VEDHA_TABLE: dict[str, dict[int, int]] = {
    "SUN": {3: 9, 6: 12, 10: 4, 11: 5},
    "MOON": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "MARS": {3: 12, 6: 9, 11: 5},
    "MERCURY": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "JUPITER": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "VENUS": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    "SATURN": {3: 12, 6: 9, 11: 5},
}

#: Pairs that never mutually afflict (classical exemptions):
#: Saturn does not obstruct the Sun nor the Sun Saturn; Moon and Mercury
#: are never mutually afflictive.
VEDHA_EXEMPTIONS: frozenset[frozenset[str]] = frozenset(
    {frozenset({"SUN", "SATURN"}), frozenset({"MOON", "MERCURY"})}
)

# ── Kakshya (8-fold sign division) ──────────────────────────────────────────
#: Canonical kakshya lord sequence for every sign (BPHS; each division
#: spans 30/8 = 3°45′).
KAKSHYA_LORDS: tuple[str, ...] = (
    "SATURN",
    "JUPITER",
    "MARS",
    "SUN",
    "VENUS",
    "MERCURY",
    "MOON",
    "LAGNA",
)

#: Arc of one kakshya in degrees (30 / 8).
KAKSHYA_ARC_DEG: float = 3.75


# ── Feature flag ────────────────────────────────────────────────────────────
def gochara_scoring_enabled() -> bool:
    """Whether Gochara scoring facts are injected into ``jre_facts``.

    Default **False**: the frozen benchmark baseline (Micro-F1 = 0.7435)
    is unaffected. Set ``JRS_GOCHARA_SCORING=1`` (truthy) to enable.
    """
    return os.environ.get("JRS_GOCHARA_SCORING", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# ── Geometry helpers ────────────────────────────────────────────────────────
def _sign_index_of_longitude(longitude: float) -> int:
    return int((longitude % 360.0) / 30.0) % 12


def rashi_of_longitude(longitude: float) -> str:
    return RASHI_ORDER[_sign_index_of_longitude(longitude)]


def house_from_anchor(
    transit_longitude: float,
    natal_anchor_longitude: float,
) -> int:
    """Whole-sign house (1–12) of a transit longitude from a natal anchor.

    Classical gochara counts rashi-to-rashi (Janma Rashi counting), so
    the anchor is reduced to its sign: a planet in the anchor's own sign
    is in house 1, the next sign house 2, and so on.
    """
    transit_idx = _sign_index_of_longitude(transit_longitude)
    anchor_idx = _sign_index_of_longitude(natal_anchor_longitude)
    return ((transit_idx - anchor_idx) % 12) + 1


def kakshya_of(longitude: float) -> dict[str, Any]:
    """Kakshya (3°45′ division) of a sidereal longitude within its sign.

    Returns the 1-based index (1–8), the classical lord, and the span
    boundaries within the sign.
    """
    degree_in_sign = longitude % 30.0
    index = int(degree_in_sign / KAKSHYA_ARC_DEG) + 1
    start = (index - 1) * KAKSHYA_ARC_DEG
    return {
        "index": index,
        "lord": KAKSHYA_LORDS[index - 1],
        "start_deg": round(start, 2),
        "end_deg": round(start + KAKSHYA_ARC_DEG, 2),
    }


def is_vedha_obstructed(
    planet: str,
    house_from_moon: int,
    houses_from_moon: dict[str, int],
) -> tuple[bool, int | None]:
    """Evaluate the classical Vedha obstruction for one transiting planet.

    Args:
        planet: The transiting planet under evaluation.
        house_from_moon: Its current whole-sign house from the natal Moon.
        houses_from_moon: House-from-natal-Moon of every transiting planet
            (used to detect an occupant in the obstructing house).

    Returns:
        (obstructed, obstructing_house) — obstructing_house is the paired
        house from the Vedha table when obstruction is active, else None.
    """
    table = VEDHA_TABLE.get(planet, {})
    obstructing_house = table.get(house_from_moon)
    if obstructing_house is None:
        return False, None
    for other, other_house in houses_from_moon.items():
        if other == planet:
            continue
        if other_house != obstructing_house:
            continue
        if frozenset({planet, other}) in VEDHA_EXEMPTIONS:
            continue
        return True, obstructing_house
    return False, obstructing_house


def band_for_tqs(tqs: float) -> dict[str, Any]:
    """Map a TQS value to its frozen band entry."""
    for threshold, multiplier, label in GOCHARA_BANDS:
        if tqs >= threshold:
            return {
                "threshold": threshold,
                "multiplier": multiplier,
                "label": label,
            }
    # GOCHARA_BANDS ends with threshold 0 — unreachable, defensive only.
    raise ValueError(f"no GOCHARA band for TQS {tqs}")


def compute_tqs(
    sav_row: tuple[int, ...] | list[int],
    sign_index: int,
) -> int:
    """Transit Quality Score for one planet: the natal SAV of the sign it
    transits (callers pass the Shodhita row when available and record
    ``tqs_basis`` accordingly)."""
    if len(sav_row) != 12:
        raise ValueError("sav_row must have 12 entries")
    if not 0 <= sign_index < 12:
        raise ValueError(f"sign_index out of range: {sign_index}")
    return sav_row[sign_index]


# ── Ephemeris bridge ────────────────────────────────────────────────────────
def compute_transit_positions(
    date: str,
    time: str,
    timezone: str,
    latitude: float,
    longitude: float,
) -> dict[str, float]:
    """Sidereal longitudes of the seven gochara planets at an instant.

    Uses the Swiss-Ephemeris-backed JyotishService with the given
    date/time and location (the observer location affects only the Lagna,
    not planetary longitudes, but keeps the call signature chart-shaped).

    Raises:
        RuntimeError: If the ephemeris call fails — callers decide on
            fallbacks; this module never silently substitutes natal data.
    """
    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    svc = JyotishService()
    birth = BirthData(
        date=date,
        time=time,
        timezone=timezone,
        latitude=float(latitude),
        longitude=float(longitude),
    )
    chart = svc.chart(birth)
    positions: dict[str, float] = {}
    for ps in chart.planet_states:
        if ps.body.value in GOCHARA_PLANETS:
            positions[ps.body.value] = float(ps.longitude_used)
    missing = [p for p in GOCHARA_PLANETS if p not in positions]
    if missing:
        raise RuntimeError(f"ephemeris missing gochara planets: {missing}")
    return positions


# ── Report assembly ─────────────────────────────────────────────────────────
def _natal_anchor_signs(facts: dict[str, Any]) -> dict[str, str]:
    """Natal Moon and Lagna rashi names from JRE facts."""
    moon_sign = str(facts.get("planets", {}).get("MOON", {}).get("rashi", ""))
    lagna_sign = str(facts.get("lagna", ""))
    if moon_sign not in RASHI_ORDER:
        raise ValueError(f"natal facts missing MOON rashi: {moon_sign!r}")
    if lagna_sign not in RASHI_ORDER:
        raise ValueError(f"natal facts missing lagna rashi: {lagna_sign!r}")
    return {"MOON": moon_sign, "LAGNA": lagna_sign}


def _ashta_rows(
    facts: dict[str, Any],
) -> tuple[tuple[int, ...], tuple[int, ...], str]:
    """Natal SAV rows for TQS lookups: (sav, shodhita_sav, tqs_basis).

    Prefers the Phase 5B report embedded in the facts (flag-on path);
    otherwise computes the raw SAV inline (read-only, no facts mutation).
    """
    embedded = facts.get("ashtakavarga")
    if isinstance(embedded, dict):
        sav = tuple(embedded["sav"])
        shodhita = tuple(embedded["shodhita_sav"])
        return sav, shodhita, "shodhita_sav"
    from jrs.calculations.ashtakavarga import (
        compute_bav,
        compute_sav,
    )

    planets = facts.get("planets", {})
    anchor_signs = {
        "SUN": str(planets.get("SUN", {}).get("rashi", "")),
        "MOON": str(planets.get("MOON", {}).get("rashi", "")),
        "MARS": str(planets.get("MARS", {}).get("rashi", "")),
        "MERCURY": str(planets.get("MERCURY", {}).get("rashi", "")),
        "JUPITER": str(planets.get("JUPITER", {}).get("rashi", "")),
        "VENUS": str(planets.get("VENUS", {}).get("rashi", "")),
        "SATURN": str(planets.get("SATURN", {}).get("rashi", "")),
        "LAGNA": str(facts.get("lagna", "")),
    }
    from jrs.calculations.ashtakavarga import ANCHORS

    for anchor in ANCHORS:
        if anchor_signs[anchor] not in RASHI_ORDER:
            raise ValueError(f"ashtakavarga fallback missing rashi: {anchor}")
    bav = compute_bav(anchor_signs)
    return compute_sav(bav), compute_sav(bav), "sav"


def compute_gochara(
    facts: dict[str, Any],
    transit_positions: dict[str, float],
    epoch: dt.datetime | None = None,
) -> dict[str, Any]:
    """Full deterministic Gochara report for one natal chart.

    Args:
        facts: Natal JRE facts (planets rashi/longitude, lagna,
            ashtakavarga report when the 5B flag is on).
        transit_positions: Sidereal longitudes of the seven gochara
            planets at the evaluated instant (see
            :func:`compute_transit_positions`).
        epoch: The evaluated instant (for reporting only; defaults to the
            pinned ``GOCHARA_TRANSIT_EPOCH``).

    Returns:
        Report dict with per-planet transit facts (rashi, houses from
        natal Moon/Lagna, kakshya, vedha, TQS, band) and the aggregate
        mean TQS band, plus ``FACT-GOCHARA-*`` provenance ids.
    """
    instant = epoch or GOCHARA_TRANSIT_EPOCH
    anchors = _natal_anchor_signs(facts)
    sav, shodhita, tqs_basis = _ashta_rows(facts)

    missing = [p for p in GOCHARA_PLANETS if p not in transit_positions]
    if missing:
        raise ValueError(f"transit_positions missing planets: {missing}")

    # Whole-sign houses from both natal anchors.
    houses_from_moon: dict[str, int] = {}
    houses_from_lagna: dict[str, int] = {}
    for planet in GOCHARA_PLANETS:
        lon = float(transit_positions[planet])
        houses_from_moon[planet] = house_from_anchor(
            lon, RASHI_ORDER.index(anchors["MOON"]) * 30.0
        )
        houses_from_lagna[planet] = house_from_anchor(
            lon, RASHI_ORDER.index(anchors["LAGNA"]) * 30.0
        )

    planets_report: dict[str, dict[str, Any]] = {}
    tqs_values: list[int] = []
    for planet in GOCHARA_PLANETS:
        lon = float(transit_positions[planet])
        sign = rashi_of_longitude(lon)
        sign_idx = _sign_index_of_longitude(lon)
        kakshya = kakshya_of(lon)
        obstructed, obstructing_house = is_vedha_obstructed(
            planet, houses_from_moon[planet], houses_from_moon
        )
        tqs = compute_tqs(shodhita if tqs_basis == "shodhita_sav" else sav, sign_idx)
        tqs_values.append(tqs)
        band = band_for_tqs(tqs)
        effective = band["multiplier"] * (VEDHA_MULTIPLIER if obstructed else 1.0)
        planets_report[planet] = {
            "fact_id": f"FACT-GOCHARA-{planet}-{sign}-K{kakshya['index']}",
            "transit_longitude": round(lon, 6),
            "transit_rashi": sign,
            "house_from_moon": houses_from_moon[planet],
            "house_from_lagna": houses_from_lagna[planet],
            "kakshya": kakshya,
            "vedha_obstructed": obstructed,
            "vedha_house": obstructing_house,
            "tqs": tqs,
            "band": band,
            "effective_multiplier": round(effective, 6),
        }

    mean_tqs = sum(tqs_values) / len(tqs_values) if tqs_values else 0.0
    aggregate_band = band_for_tqs(mean_tqs)

    fact_ids: list[str] = [planets_report[p]["fact_id"] for p in GOCHARA_PLANETS]
    fact_ids.append("FACT-GOCHARA-MOON-NATAL")
    fact_ids.append("FACT-GOCHARA-LAGNA-NATAL")

    return {
        "version": GOCHARA_STAGE_VERSION,
        "epoch_utc": instant.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "natal_anchors": anchors,
        "tqs_basis": tqs_basis,
        "planets": planets_report,
        "mean_tqs": round(mean_tqs, 6),
        "aggregate_band": aggregate_band,
        "fact_ids": tuple(fact_ids),
    }


def gochara_to_dict(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize the report with JSON-safe types and canonical order."""
    return {
        "version": report["version"],
        "epoch_utc": report["epoch_utc"],
        "natal_anchors": dict(report["natal_anchors"]),
        "tqs_basis": report["tqs_basis"],
        "planets": {
            p: {
                "fact_id": report["planets"][p]["fact_id"],
                "transit_longitude": report["planets"][p]["transit_longitude"],
                "transit_rashi": report["planets"][p]["transit_rashi"],
                "house_from_moon": report["planets"][p]["house_from_moon"],
                "house_from_lagna": report["planets"][p]["house_from_lagna"],
                "kakshya": dict(report["planets"][p]["kakshya"]),
                "vedha_obstructed": report["planets"][p]["vedha_obstructed"],
                "vedha_house": report["planets"][p]["vedha_house"],
                "tqs": report["planets"][p]["tqs"],
                "band": dict(report["planets"][p]["band"]),
                "effective_multiplier": report["planets"][p]["effective_multiplier"],
            }
            for p in GOCHARA_PLANETS
        },
        "mean_tqs": report["mean_tqs"],
        "aggregate_band": dict(report["aggregate_band"]),
        "fact_ids": list(report["fact_ids"]),
    }
