"""JRE Fact Engine — Extended Metrics Computation.

Computes traditional Vedic astrology metrics that are NOT part of the core
reasoning engine but enrich the JREFactPacket for reporting purposes:

- Full Divisional Matrix (D2, D3, D7, D12, D16, D30, D60)
- Strength Matrices (Shadbala simplified, Bhava Chalit)
- Ashtakavarga numeric bindu scores

NO engine logic — pure mathematical enrichment.
"""

from __future__ import annotations

from typing import Any

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════

_RASHI_ORDER: list[str] = [
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
]

_RASHI_NUM: dict[str, int] = {r: i + 1 for i, r in enumerate(_RASHI_ORDER)}

_SIGN_LORDS: dict[int, str] = {
    1: "MARS",
    2: "VENUS",
    3: "MERCURY",
    4: "MOON",
    5: "SUN",
    6: "MERCURY",
    7: "VENUS",
    8: "MARS",
    9: "JUPITER",
    10: "SATURN",
    11: "SATURN",
    12: "JUPITER",
}

_SIGN_EXALTATION: dict[str, int] = {
    "SUN": 1,
    "MOON": 2,
    "MARS": 10,
    "MERCURY": 6,
    "JUPITER": 4,
    "VENUS": 12,
    "SATURN": 7,
}

_SIGN_DEBILITATION: dict[str, int] = {
    "SUN": 7,
    "MOON": 8,
    "MARS": 4,
    "MERCURY": 12,
    "JUPITER": 10,
    "VENUS": 6,
    "SATURN": 1,
}

_SIGN_OWN: dict[str, list[int]] = {
    "SUN": [5],
    "MOON": [4],
    "MARS": [1, 8],
    "MERCURY": [3, 6],
    "JUPITER": [9, 12],
    "VENUS": [2, 7],
    "SATURN": [10, 11],
}

# Natural benefics/malefics
_BENEFICS = {"JUPITER", "VENUS", "MOON", "MERCURY"}
_MALEFICS = {"SUN", "MARS", "SATURN", "RAHU", "KETU"}

# Planet exaltation lagna strengths (simplified Shadbala in Rupas)
# Based on BPHS: functional strength from placement
_MOTHIYAMA_PLACEMENT: dict[int, float] = {
    # House → strength factor (out of 60 Rupas max)
    1: 1.0,
    2: 0.75,
    3: 0.6,
    4: 0.9,
    5: 0.8,
    6: 0.5,
    7: 0.85,
    8: 0.4,
    9: 0.95,
    10: 0.9,
    11: 0.7,
    12: 0.5,
}


# ══════════════════════════════════════════════════════════════════════════════
# Divisional Chart Computation
# ══════════════════════════════════════════════════════════════════════════════


def _compute_divisional_sign(longitude: float, division: int) -> str:
    """Compute which rashi a planet falls in for a given divisional chart.

    For division Dn, each rashi (30°) is divided into n parts of (30/n)°.
    The divisional sign index = floor(longitude / (30/n)) % 12.

    Args:
        longitude: Sidereal longitude in degrees [0, 360).
        division: Division number (2=Hora, 3=Dreshkana, etc.)

    Returns:
        Rashi name string (e.g., "MESHA").
    """
    sign_idx = int(longitude / 30.0)  # which rashi
    deg_in_sign = longitude - (sign_idx * 30.0)  # degree within rashi
    division_size = 30.0 / division
    division_within_sign = int(deg_in_sign / division_size)
    # Map to rashi: for odd signs (0-indexed even), start from sign itself
    # for even signs (0-indexed odd), start from sign+5
    is_odd_sign = sign_idx % 2 == 0  # Mesha, Mithuna, Simha... are "odd"
    if is_odd_sign:
        target = (sign_idx + division_within_sign) % 12
    else:
        target = (sign_idx + 5 + division_within_sign) % 12
    return _RASHI_ORDER[target]


def _compute_hora(longitude: float) -> str:
    """D2 — Hora chart. Sun/Moon hora alternation."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    # Odd signs (0,2,4...): 0-15° = Leo (Sun hora), 15-30° = Cancer (Moon hora)
    # Even signs (1,3,5...): 0-15° = Cancer (Moon hora), 15-30° = Leo (Sun hora)
    if sign_idx % 2 == 0:  # Odd rashi
        return "SIMHA" if deg_in_sign < 15 else "KARKA"
    else:  # Even rashi
        return "KARKA" if deg_in_sign < 15 else "SIMHA"


def compute_all_divisional_charts(jre_facts: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Compute divisional charts D2, D3, D7, D12, D16, D30, D60 for all planets.

    Args:
        jre_facts: JRE facts with 'planets' containing longitude data.

    Returns:
        Dict mapping division name → {planet → rashi}.
    """
    planets = jre_facts.get("planets", {})
    charts: dict[str, dict[str, str]] = {}

    divisions = {
        "D2_HORA": 2,
        "D3_DRESHKANA": 3,
        "D7_SAPTAMSHA": 7,
        "D12_DVADASAMSHA": 12,
        "D16_SHODASHAMSHA": 16,
        "D30_TRISHAMSHA": 30,
        "D60_SHASHTIAMSHA": 60,
    }

    for div_name, div_num in divisions.items():
        chart: dict[str, str] = {}
        for pname, pdata in planets.items():
            longitude = pdata.get("longitude", 0.0)
            if div_num == 2:
                chart[pname] = _compute_hora(longitude)
            else:
                chart[pname] = _compute_divisional_sign(longitude, div_num)
        charts[div_name] = chart

    # Also add D9 (Navamsha) from existing data if available
    d9 = jre_facts.get("planet_d9_sign", {})
    if d9:
        charts["D9_NAVAMSHA"] = d9

    return charts


# ══════════════════════════════════════════════════════════════════════════════
# Strength Matrices
# ══════════════════════════════════════════════════════════════════════════════


def compute_shadbala(jre_facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Compute simplified Shadbala (six-fold strength) for each planet.

    Full Shadbala includes: Sthana Bala, Dig Bala, Kala Bala, Naisargika Bala,
    Drik Bala, and Chesta Bala. Here we compute a practical subset using
    available data: placement strength, dignity, and combustion modifiers.

    Args:
        jre_facts: JRE facts with planet data.

    Returns:
        Dict mapping planet → {placement_rupas, dignity_modifier, total_rupas, grade}.
    """
    planets = jre_facts.get("planets", {})
    dignity_map = jre_facts.get("dignity_map", {})
    lagna_sign = jre_facts.get("lagna_sign", 1)

    result: dict[str, dict[str, Any]] = {}

    for pname, pdata in planets.items():
        house = pdata.get("house", 1)
        rashi_num = pdata.get("rashi_num", 0)
        is_combust = pdata.get("combust", False)
        is_debilitated = pdata.get("debilitated", False)
        is_retrograde = pdata.get("retrograde", False)

        # Sthana Bala (Placement strength) — simplified to Rupas
        placement = _MOTHIYAMA_PLACEMENT.get(house, 0.5) * 60.0

        # Dignity modifier
        dignity = dignity_map.get(pname, "Neutral")
        dignity_mod = {
            "Exalted": 1.5,
            "Moolatrikona": 1.3,
            "Own Sign": 1.2,
            "Friendly": 1.1,
            "Neutral": 1.0,
            "Enemy": 0.8,
            "Debilitated": 0.5,
        }.get(dignity, 1.0)

        # Combustion penalty
        if is_combust:
            placement *= 0.6

        # Debilitation penalty
        if is_debilitated:
            placement *= 0.5

        # Retrograde adds strength to natural malefics, reduces benefics
        if is_retrograde:
            if pname in _MALEFICS:
                placement *= 1.15
            else:
                placement *= 0.9

        total = placement * dignity_mod
        total = min(total, 60.0)  # Cap at 60 Rupas

        # Grade
        if total >= 50:
            grade = "Uttama (Excellent)"
        elif total >= 40:
            grade = "Good"
        elif total >= 30:
            grade = "Average"
        elif total >= 20:
            grade = "Weak"
        else:
            grade = "Very Weak"

        result[pname] = {
            "placement_rupas": round(placement, 2),
            "dignity_modifier": dignity_mod,
            "total_rupas": round(total, 2),
            "grade": grade,
        }

    return result


def compute_bhava_chalit(jre_facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Compute Bhava Chalit (true house cusps) — simplified whole-sign variant.

    In the absence of exact birth time for Placidus cusps, we compute
    which house each planet occupies in the Bhava Chalit chart. This
    differs from the Rashi chart when planets are near house cusps.

    For our purposes, we use the Whole-Sign system already computed
    and add the Placidus approximation based on degree within sign:
    - 0-10°: previous house
    - 10-20°: current house
    - 20-30°: next house

    Args:
        jre_facts: JRE facts with planet data.

    Returns:
        Dict mapping planet → {rashi_house, bhava_house, degree_in_sign}.
    """
    planets = jre_facts.get("planets", {})
    lagna_sign = jre_facts.get("lagna_sign", 1)

    result: dict[str, dict[str, Any]] = {}

    for pname, pdata in planets.items():
        house = pdata.get("house", 1)
        rashi = pdata.get("rashi", "")
        rashi_num = _RASHI_NUM.get(rashi, 1)
        longitude = pdata.get("longitude", 0.0)

        deg_in_sign = longitude - ((rashi_num - 1) * 30.0)
        if deg_in_sign < 0:
            deg_in_sign += 30.0

        # Placidus-like approximation
        if deg_in_sign < 10:
            bhava_house = (house - 1 - 1) % 12 + 1  # previous house
        elif deg_in_sign > 20:
            bhava_house = (house - 1 + 1) % 12 + 1  # next house
        else:
            bhava_house = house  # stays in current house

        result[pname] = {
            "rashi_house": house,
            "bhava_house": bhava_house,
            "degree_in_sign": round(deg_in_sign, 2),
        }

    return result


def compute_drishti_matrix(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute Graha Drishti (planetary aspects) with exact degrees.

    Classical Vedic aspects:
    - All planets aspect the 7th house (180°)
    - Mars also aspects 4th (90°) and 8th (210°)
    - Jupiter also aspects 5th (120°) and 9th (240°)
    - Saturn also aspects 3rd (60°) and 10th (270°)

    Args:
        jre_facts: JRE facts with planet data.

    Returns:
        List of aspect dicts with source, target, aspect_type, degrees.
    """
    planets = jre_facts.get("planets", {})
    aspects: list[dict[str, Any]] = []

    # Classical aspect rules: planet → [(target_house_offset, aspect_degrees)]
    _ASPECT_RULES: dict[str, list[tuple[int, float]]] = {
        "SUN": [(7, 180)],
        "MOON": [(7, 180)],
        "MERCURY": [(7, 180)],
        "VENUS": [(7, 180)],
        "RAHU": [(7, 180)],
        "KETU": [(7, 180)],
        "MARS": [(4, 90), (7, 180), (8, 210)],
        "JUPITER": [(5, 120), (7, 180), (9, 240)],
        "SATURN": [(3, 60), (7, 180), (10, 270)],
    }

    # Compute longitudes for all planets
    longitudes: dict[str, float] = {}
    for pname, pdata in planets.items():
        longitudes[pname] = pdata.get("longitude", 0.0)

    for source, rules in _ASPECT_RULES.items():
        if source not in longitudes:
            continue
        source_house = planets[source].get("house", 1)
        for target_offset, aspect_deg in rules:
            target_house = ((source_house - 1 + target_offset - 1) % 12) + 1
            # Find planets in target house
            for target, tdata in planets.items():
                if target == source:
                    continue
                if tdata.get("house") == target_house:
                    # Compute actual angular separation
                    sep = abs(longitudes[source] - longitudes[target])
                    if sep > 180:
                        sep = 360 - sep
                    aspects.append(
                        {
                            "source": source,
                            "target": target,
                            "aspect_type": f"classical_{target_offset}",
                            "nominal_degrees": aspect_deg,
                            "actual_separation": round(sep, 2),
                            "source_house": source_house,
                            "target_house": target_house,
                        }
                    )

    return aspects


# ══════════════════════════════════════════════════════════════════════════════
# Ashtakavarga
# ══════════════════════════════════════════════════════════════════════════════


def compute_ashtakavarga(jre_facts: dict[str, Any]) -> dict[str, Any]:
    """Compute Sarva-Ashtakavarga (SAV) and Bhinna-Ashtakavarga (BAV) tables.

    Each planet contributes points (0 or 1) to each house based on
    its relationship with the house lord and occupants.

    Simplified classical rules:
    - Planet gives 1 point to houses it owns, occupies, aspects, and friendly houses
    - Rahu/Ketu follow Saturn's rules
    - Benefics add 1 extra point to houses 3, 6, 10, 11

    Args:
        jre_facts: JRE facts with planet and house lord data.

    Returns:
        Dict with 'bav' (per-planet tables), 'sav' (total per house),
        and 'rekhankedaka' (table-based scoring).
    """
    planets = jre_facts.get("planets", {})
    house_lords = jre_facts.get("house_lords", {})
    lagna_sign = jre_facts.get("lagna_sign", 1)

    _CLASSICAL_ASPECTS = {
        "SUN": [7],
        "MOON": [7],
        "MERCURY": [7],
        "VENUS": [7],
        "RAHU": [7],
        "KETU": [7],
        "MARS": [4, 7, 8],
        "JUPITER": [5, 7, 9],
        "SATURN": [3, 7, 10],
    }

    bav: dict[str, dict[int, int]] = {}
    classical_planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]

    for pname in classical_planets:
        if pname not in planets:
            continue
        scores: dict[int, int] = {h: 0 for h in range(1, 13)}
        p_house = planets[pname].get("house", 1)
        p_rashi = planets[pname].get("rashi", "")
        p_sign_num = _RASHI_NUM.get(p_rashi, 1)

        # Rule 1: Planet aspects (gives 1 point to aspected houses)
        for offset in _CLASSICAL_ASPECTS.get(pname, []):
            aspected = ((p_house - 1 + offset - 1) % 12) + 1
            scores[aspected] += 1

        # Rule 2: Planet's own sign houses
        own_signs = _SIGN_OWN.get(pname, [])
        for h in range(1, 13):
            lord = house_lords.get(h, "")
            if lord == pname:
                scores[h] += 1

        # Rule 3: Planet occupies its own house
        scores[p_house] += 1

        # Rule 4: Friendly sign in each house
        for h in range(1, 13):
            house_lord = house_lords.get(h, "")
            if house_lord in _BENEFICS and pname in _BENEFICS:
                scores[h] += 1
            elif house_lord in _MALEFICS and pname in _MALEFICS:
                scores[h] += 1

        # Rule 5: Benefics add to upachaya houses (3, 6, 10, 11)
        if pname in _BENEFICS:
            for h in [3, 6, 10, 11]:
                scores[h] += 1

        bav[pname] = scores

    # Sarva-Ashtakavarga (total across all planets per house)
    sav: dict[int, int] = {h: 0 for h in range(1, 13)}
    for pname, scores in bav.items():
        for h, s in scores.items():
            sav[h] += s

    return {
        "bav": bav,
        "sav": sav,
        "total_bindus": sum(sav.values()),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Master Enrichment Function
# ══════════════════════════════════════════════════════════════════════════════


class ExtendedMetrics:
    """Computes all extended metrics and returns enriched facts dict."""

    @staticmethod
    def enrich(jre_facts: dict[str, Any]) -> dict[str, Any]:
        """Enrich JRE facts with all extended metrics.

        Args:
            jre_facts: Base JRE facts dictionary.

        Returns:
            Extended facts with divisional charts, strengths, aspects, av.
        """
        enriched = dict(jre_facts)

        try:
            enriched["divisional_charts"] = compute_all_divisional_charts(jre_facts)
        except Exception:
            enriched["divisional_charts"] = {}

        try:
            enriched["shadbala"] = compute_shadbala(jre_facts)
        except Exception:
            enriched["shadbala"] = {}

        try:
            enriched["bhava_chalit"] = compute_bhava_chalit(jre_facts)
        except Exception:
            enriched["bhava_chalit"] = {}

        try:
            enriched["drishti_matrix"] = compute_drishti_matrix(jre_facts)
        except Exception:
            enriched["drishti_matrix"] = []

        try:
            enriched["ashtakavarga"] = compute_ashtakavarga(jre_facts)
        except Exception:
            enriched["ashtakavarga"] = {}

        return enriched
