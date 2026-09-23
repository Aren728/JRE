"""JRE Fact Enrichment — Lightweight aggregators for enriched JREFactPacket.

Adds elemental/modality counters, dignity labels, and aspect matrix
WITHOUT changing core reasoning logic.

NO engine logic — pure data aggregation on top of existing facts.
"""

from __future__ import annotations

from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────

# Sign → element mapping (sidereal zodiac order)
_SIGN_ELEMENTS: dict[str, str] = {
    "MESHA": "fire",
    "VRISHABHA": "earth",
    "MITHUNA": "air",
    "KARKA": "water",
    "SIMHA": "fire",
    "KANYA": "earth",
    "TULA": "air",
    "VRISHCHIKA": "water",
    "DHANUSHA": "fire",
    "MAKARA": "earth",
    "KUMBHA": "air",
    "MEENA": "water",
}

# Sign → modality mapping
_SIGN_MODALITIES: dict[str, str] = {
    "MESHA": "cardinal",
    "VRISHABHA": "fixed",
    "MITHUNA": "mutable",
    "KARKA": "cardinal",
    "SIMHA": "fixed",
    "KANYA": "mutable",
    "TULA": "cardinal",
    "VRISHCHIKA": "fixed",
    "DHANUSHA": "mutable",
    "MAKARA": "cardinal",
    "KUMBHA": "fixed",
    "MEENA": "mutable",
}

# Classical dignities
_EXALTATION: dict[str, str] = {
    "SUN": "MESHA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}

_DEBILITATION: dict[str, str] = {
    "SUN": "TULA",
    "MOON": "VRISHCHIKA",
    "MARS": "KARKA",
    "MERCURY": "MEENA",
    "JUPITER": "MAKARA",
    "VENUS": "KANYA",
    "SATURN": "MESHA",
}

# Moolatrikona signs (simplified: use start degree ranges)
_MOOLATRIKONA: dict[str, tuple[str, float, float]] = {
    "SUN": ("SIMHA", 0.0, 20.0),  # Leo 0°-20°
    "MOON": ("VRISHABHA", 0.0, 3.0),  # Taurus 0°-3°
    "MARS": ("MESHA", 0.0, 12.0),  # Aries 0°-12°
    "MERCURY": ("VIRISHABHA", 16.0, 20.0),  # Virgo 15°-20°
    "JUPITER": ("SAGITTARIUS", 0.0, 10.0),  # Sag 0°-10°
    "VENUS": ("LIBRA", 0.0, 15.0),  # Libra 0°-15°
    "SATURN": ("AQUARIUS", 0.0, 20.0),  # Aquarius 0°-20°
}

# Extended Moolatrikona using correct sign names
_MOOLATRIKONA_SIGNS: dict[str, str] = {
    "SUN": "SIMHA",
    "MOON": "VRISHABHA",
    "MARS": "MESHA",
    "MERCURY": "KANYA",
    "JUPITER": "DHANUSHA",
    "VENUS": "TULA",
    "SATURN": "KUMBHA",
}

# Sign lordship
_SIGN_LORDS: dict[str, str] = {
    "MESHA": "MARS",
    "VRISHABHA": "VENUS",
    "MITHUNA": "MERCURY",
    "KARKA": "MOON",
    "SIMHA": "SUN",
    "KANYA": "MERCURY",
    "TULA": "VENUS",
    "VRISHCHIKA": "MARS",
    "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN",
    "KUMBHA": "SATURN",
    "MEENA": "JUPITER",
}

# Friendly signs per planet (simplified)
_FRIENDSIGNS: dict[str, set[str]] = {
    "SUN": {"MESHA", "VRISHCHIKA", "DHANUSHA", "MEENA", "KARKA"},
    "MOON": {"MESHA", "VRISHABHA", "KANYA", "TULA", "DHANUSHA", "MEENA"},
    "MARS": {"MESHA", "VRISHCHIKA", "KARKA", "VRISHABHA", "SIMHA", "DHANUSHA"},
    "MERCURY": {"MITHUNA", "KANYA", "TULA", "KUMBHA", "MESHA", "VRISHABHA"},
    "JUPITER": {"MESHA", "VRISHCHIKA", "KARKA", "SIMHA", "DHANUSHA", "MEENA"},
    "VENUS": {"MITHUNA", "KANYA", "TULA", "KUMBHA", "MAKARA", "VRISHABHA"},
    "SATURN": {"TULA", "KUMBHA", "MAKARA", "VRISHABHA", "MITHUNA"},
}

# Enemy signs per planet
_ENEMY_SIGNS: dict[str, set[str]] = {
    "SUN": {"TULA", "KUMBHA", "KANYA", "VRISHABHA"},
    "MOON": {"VRISHCHIKA"},
    "MARS": {"TULA", "KARKA", "KANYA", "MEENA"},
    "MERCURY": {"KARKA", "SIMHA", "MEENA"},
    "JUPITER": {"MITHUNA", "KANYA"},
    "VENUS": {"MESHA", "VRISHCHIKA", "KARKA"},
    "SATURN": {"MESHA", "SIMHA", "VRISHCHIKA"},
}

# Aspect rules: planet → list of (target_offset, exact_angle_deg)
# Vedic aspects: all planets aspect 7th house; special aspects for Mars/Jupiter/Saturn
_CLASSICAL_ASPECTS: dict[str, list[tuple[int, float]]] = {
    # All planets aspect 7th
    "SUN": [(7, 180.0)],
    "MOON": [(7, 180.0)],
    "MERCURY": [(7, 180.0)],
    "VENUS": [(7, 180.0)],
    "RAHU": [(7, 180.0)],
    "KETU": [(7, 180.0)],
    # Mars also aspects 4th and 8th
    "MARS": [(4, 90.0), (7, 180.0), (8, 210.0)],
    # Jupiter also aspects 5th and 9th
    "JUPITER": [(5, 120.0), (7, 180.0), (9, 240.0)],
    # Saturn also aspects 3rd and 10th
    "SATURN": [(3, 60.0), (7, 180.0), (10, 270.0)],
}

# Planets used for aspect calculations (classical 7 + nodes)
_CLASSICAL_PLANETS = [
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
    "RAHU",
    "KETU",
]


# ── Enrichment Functions ─────────────────────────────────────────────────────


def _evaluate_dignity(
    planet: str,
    rashi: str,
    degree_in_sign: float,
) -> str:
    """Evaluate a planet's classical dignity based on its sign placement.

    Returns one of: Exalted, Moolatrikona, Own Sign, Friendly, Neutral,
    Enemy, or Debilitated.
    """
    if planet in _EXALTATION and rashi == _EXALTATION[planet]:
        return "Exalted"

    if planet in _DEBILITATION and rashi == _DEBILITATION[planet]:
        return "Debilitated"

    # Moolatrikona check
    mt_sign = _MOOLATRIKONA_SIGNS.get(planet)
    if rashi == mt_sign:
        # Additional degree check for precision
        return "Moolatrikona"

    # Own sign check
    if _SIGN_LORDS.get(rashi) == planet:
        return "Own Sign"

    # Friendly / Enemy / Neutral
    if planet in _FRIENDSIGNS and rashi in _FRIENDSIGNS[planet]:
        return "Friendly"
    if planet in _ENEMY_SIGNS and rashi in _ENEMY_SIGNS[planet]:
        return "Enemy"

    return "Neutral"


def _detect_aspects(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect Vedic aspects between planets based on house positions.

    Uses classical Vedic aspect rules: all planets aspect the 7th house,
    Mars aspects 4th and 8th, Jupiter aspects 5th and 9th, Saturn aspects
    3rd and 10th.

    Args:
        jre_facts: JRE facts with planets data.

    Returns:
        List of aspect dictionaries with source, target, type, and orb info.
    """
    planets = jre_facts.get("planets", {})
    aspects: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for source_planet, aspects_list in _CLASSICAL_ASPECTS.items():
        source_data = planets.get(source_planet)
        if not source_data:
            continue
        source_house = source_data.get("house")
        if not isinstance(source_house, int):
            continue

        for target_offset, angle in aspects_list:
            target_house = ((source_house - 1 + target_offset) % 12) + 1

            # Find which planet(s) are in the target house
            for target_name, target_data in planets.items():
                if target_name == source_planet:
                    continue
                if target_data.get("house") == target_house:
                    pair = tuple(sorted([source_planet, target_name]))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)

                    # Determine aspect type
                    if target_offset == 7:
                        aspect_type = "opposition"
                    elif target_offset in (4,):
                        aspect_type = "square"
                    elif target_offset in (8,):
                        aspect_type = "trine_special"
                    elif target_offset in (3,):
                        aspect_type = "sextile_special"
                    elif target_offset in (5, 9):
                        aspect_type = "trine_special"
                    elif target_offset in (10,):
                        aspect_type = "square_special"
                    else:
                        aspect_type = "opposition"

                    aspects.append(
                        {
                            "source": source_planet,
                            "target": target_name,
                            "type": aspect_type,
                            "angle_deg": angle,
                            "source_house": source_house,
                            "target_house": target_house,
                        }
                    )

    return aspects


def enrich_jre_facts(jre_facts: dict[str, Any]) -> dict[str, Any]:
    """Enrich JRE facts with elemental counters, dignity labels, and aspect matrix.

    This function adds three new top-level keys to the facts dictionary:
    - 'elemental_balance': counts of planets in fire/earth/air/water
    - 'modality_balance': counts of planets in cardinal/fixed/mutable
    - 'dignity_map': planet → dignity label
    - 'aspect_matrix': list of detected aspects
    - 'planet_degrees': planet → {sign, degree_in_sign, element, modality}

    Args:
        jre_facts: Existing JRE facts dictionary.

    Returns:
        Enriched facts dictionary (mutates in place for efficiency).
    """
    planets = jre_facts.get("planets", {})

    # ── Elemental & Modality Counters ──
    elemental = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modality = {"cardinal": 0, "fixed": 0, "mutable": 0}
    planet_details: dict[str, dict[str, Any]] = {}

    for pname, pdata in planets.items():
        rashi = pdata.get("rashi", "")
        longitude = pdata.get("longitude", 0.0)

        element = _SIGN_ELEMENTS.get(rashi, "fire")
        mod = _SIGN_MODALITIES.get(rashi, "cardinal")

        elemental[element] = elemental.get(element, 0) + 1
        modality[mod] = modality.get(mod, 0) + 1

        # Compute degree within sign
        sign_idx = (
            [
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
            ].index(rashi)
            if rashi in _SIGN_ELEMENTS
            else 0
        )
        deg_in_sign = longitude - (sign_idx * 30.0)
        if deg_in_sign < 0:
            deg_in_sign += 360.0

        # Evaluate dignity
        dignity = _evaluate_dignity(pname, rashi, deg_in_sign)

        planet_details[pname] = {
            "sign": rashi,
            "element": element,
            "modality": mod,
            "dignity": dignity,
            "degree_in_sign": round(deg_in_sign, 2),
            "house": pdata.get("house", 0),
            # Per-planet nakshatra facts propagated from the position layer.
            "nakshatra": pdata.get("nakshatra", ""),
            "nakshatra_lord": pdata.get("nakshatra_lord", ""),
            "nakshatra_pada": pdata.get("nakshatra_pada", 0),
        }

    # ── Aspect Matrix ──
    aspects = _detect_aspects(jre_facts)

    # ── Dignity Summary ──
    dignity_map = {p: d["dignity"] for p, d in planet_details.items()}

    # ── Apply to facts ──
    jre_facts["elemental_balance"] = elemental
    jre_facts["modality_balance"] = modality
    jre_facts["dignity_map"] = dignity_map
    jre_facts["aspect_matrix"] = aspects
    jre_facts["planet_details"] = planet_details

    return jre_facts
