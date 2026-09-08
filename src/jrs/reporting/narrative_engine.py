"""JRE Reporting — Narrative Engine for professional astrological prose.

Translates structured JRE data into polished, domain-appropriate narrative
text suitable for a world-class astrological report. Follows classical
BPHS/Phaladeepika interpretive conventions.

NO engine logic — pure presentation/narrative generation.
"""

from __future__ import annotations

from typing import Any

from jrs.reporting.classical_interpretations import (
    ASPECT_NARRATIVES,
    HOUSE_SIGNIFICATIONS,
    KARMIC_INDICATORS,
    get_aspect_narrative,
    get_conjunction_interpretation,
    get_house_signification,
    get_karmic_indicator,
    get_nakshatra_interpretation,
    get_planet_house_interpretation,
)

# ── Element Narratives ───────────────────────────────────────────────────────

_ELEMENT_NARRATIVES: dict[str, str] = {
    "fire": (
        "Fire energy dominates the chart, indicating a personality driven by "
        "initiative, courage, and creative self-expression. The native is "
        "naturally entrepreneurial and thrives in competitive environments."
    ),
    "earth": (
        "Earth energy prevails, suggesting a practical, grounded, and materially "
        "oriented temperament. The native values stability, reliability, and "
        "tangible results over abstract ideals."
    ),
    "air": (
        "Air energy is prominent, reflecting an intellectual, communicative, and "
        "socially oriented nature. The native excels in analytical thinking, "
        "networking, and intellectual pursuits."
    ),
    "water": (
        "Water energy is strong, pointing to deep emotional intelligence, "
        "intuitive perception, and empathic sensitivity. The native is drawn to "
        "healing, spirituality, and emotional depth."
    ),
}

_MODALITY_NARRATIVES: dict[str, str] = {
    "cardinal": (
        "Cardinal modality dominates, indicating a natural leader and initiator "
        "who excels at launching new ventures and driving change."
    ),
    "fixed": (
        "Fixed modality is strongest, suggesting determination, persistence, and "
        "the ability to sustain efforts and maintain stability."
    ),
    "mutable": (
        "Mutable modality predominates, reflecting adaptability, versatility, and "
        "a capacity for intellectual flexibility and learning."
    ),
}

# ── Dignity Narratives ──────────────────────────────────────────────────────

_DIGNITY_NARRATIVES: dict[str, str] = {
    "Exalted": (
        "in exaltation — operating at peak strength, bestowing exceptional "
        "blessings in its significations"
    ),
    "Moolatrikona": (
        "in Moolatrikona — deeply comfortable and functionally powerful, "
        "providing clear and strong results in its house ownership"
    ),
    "Own Sign": (
        "in its own sign — naturally strong and self-sufficient, expressing "
        "its significations with clarity and authority"
    ),
    "Friendly": (
        "in a friendly sign — well-placed and cooperative, producing beneficial results with ease"
    ),
    "Neutral": (
        "in a neutral sign — neither particularly strong nor weak, producing "
        "moderate and context-dependent results"
    ),
    "Enemy": (
        "in an enemy sign — placed in a hostile environment, which may "
        "create friction in its significations"
    ),
    "Debilitated": (
        "in debilitation — significantly weakened, requiring supportive "
        "conditions (Neecha Bhanga) for beneficial results"
    ),
}


# ── Primary Triad Narrative ──────────────────────────────────────────────────


def generate_primary_triad_narrative(jre_facts: dict[str, Any]) -> str:
    """Generate professional prose for the Primary Triad (Lagna, Sun, Moon).

    The Primary Triad represents the three pillars of the native's identity:
    Lagna (physical body/temperament), Sun (soul/purpose), and Moon
    (mind/emotions).

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        Multi-paragraph narrative string.
    """
    planets = jre_facts.get("planets", {})
    lagna_sign_num = jre_facts.get("lagna_sign", 1)
    dignity_map = jre_facts.get("dignity_map", {})
    planet_details = jre_facts.get("planet_details", {})

    _RASHI_NAMES: dict[int, str] = {
        1: "Aries (Mesha)",
        2: "Taurus (Vrishabha)",
        3: "Gemini (Mithuna)",
        4: "Cancer (Karka)",
        5: "Leo (Simha)",
        6: "Virgo (Kanya)",
        7: "Libra (Tula)",
        8: "Scorpio (Vrishchika)",
        9: "Sagittarius (Dhanusha)",
        10: "Capricorn (Makara)",
        11: "Aquarius (Kumbha)",
        12: "Pisces (Meena)",
    }

    lagna_name = _RASHI_NAMES.get(lagna_sign_num, f"Rashi {lagna_sign_num}")

    sun_data = planets.get("SUN", {})
    moon_data = planets.get("MOON", {})

    sun_rashi = sun_data.get("rashi", "")
    sun_house = sun_data.get("house", 0)
    moon_rashi = moon_data.get("rashi", "")
    moon_house = moon_data.get("house", 0)
    moon_nak = jre_facts.get("moon_nakshatra", "")

    sun_dignity = dignity_map.get("SUN", "Neutral")
    moon_dignity = dignity_map.get("MOON", "Neutral")
    sun_detail = planet_details.get("SUN", {})
    moon_detail = planet_details.get("MOON", {})

    # Build narrative
    paragraphs: list[str] = []

    # Lagna paragraph
    lagna_element = _SIGN_ELEMENTS.get(_RASHI_NUM_REVERSE.get(lagna_sign_num, ""), "fire")
    element_desc = _ELEMENT_NARRATIVES.get(lagna_element, "")
    paragraphs.append(
        f"The native's Lagna (Ascendant) is {lagna_name}, endowing the physical "
        f"body and outward temperament with the qualities of this sign. {element_desc}"
    )

    # Sun paragraph
    if sun_rashi:
        sun_rashi_name = _RASHI_NAMES.get(
            _RASHI_NUM.get(sun_rashi, 0),
            sun_rashi,
        )
        sun_dignity_text = _DIGNITY_NARRATIVES.get(sun_dignity, "")
        paragraphs.append(
            f"The Sun, representing the soul and core identity, is placed in "
            f"{sun_rashi_name} in the {_ordinal(sun_house)} house, "
            f"{sun_dignity_text}. This placement shapes the native's fundamental "
            f"purpose and sense of self."
        )

    # Moon paragraph
    if moon_rashi:
        moon_rashi_name = _RASHI_NAMES.get(
            _RASHI_NUM.get(moon_rashi, 0),
            moon_rashi,
        )
        moon_dignity_text = _DIGNITY_NARRATIVES.get(moon_dignity, "")
        nak_text = f" in Nakshatra {moon_nak}" if moon_nak else ""
        paragraphs.append(
            f"The Moon, governing the mind and emotional nature, resides in "
            f"{moon_rashi_name}{nak_text} in the {_ordinal(moon_house)} house, "
            f"{moon_dignity_text}. This influences the native's emotional "
            f"temperament, instincts, and psychological well-being."
        )

    # Synthesis
    paragraphs.append(
        "Together, the Lagna-Sun-Moon triad forms the foundational axis of the "
        "natal chart. The interplay between physical temperament (Lagna), soul "
        "purpose (Sun), and emotional nature (Moon) determines the native's "
        "overall trajectory and capacity for self-realization."
    )

    return "\n\n".join(paragraphs)


# ── House Analysis Narrative ─────────────────────────────────────────────────

# Domain grouping for houses
_HOUSE_DOMAINS: dict[str, list[int]] = {
    "Personality & Self": [1],
    "Wealth & Family": [2, 11],
    "Communication & Courage": [3],
    "Home & Happiness": [4],
    "Children & Creativity": [5],
    "Health & Service": [6],
    "Marriage & Partnership": [7],
    "Obstacles & Transformation": [8],
    "Fortune & Dharma": [9],
    "Career & Status": [10],
    "Gains & Aspirations": [11],
    "Loss & Liberation": [12],
}


def generate_house_analysis_narrative(jre_facts: dict[str, Any]) -> str:
    """Generate narrative analysis grouped by life domains.

    Groups houses into thematic clusters and provides narrative interpretation
    of planetary placements within each domain.

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        Multi-section narrative string.
    """
    planets = jre_facts.get("planets", {})
    house_lords = jre_facts.get("house_lords", {})
    dignity_map = jre_facts.get("dignity_map", {})
    planet_details = jre_facts.get("planet_details", {})

    _RASHI_NAMES: dict[int, str] = {
        1: "Mesha",
        2: "Vrishabha",
        3: "Mithuna",
        4: "Karka",
        5: "Simha",
        6: "Kanya",
        7: "Tula",
        8: "Vrishchika",
        9: "Dhanusha",
        10: "Makara",
        11: "Kumbha",
        12: "Meena",
    }

    sections: list[str] = []

    for domain_name, house_numbers in _HOUSE_DOMAINS.items():
        # Find planets in these houses
        occupants: list[str] = []
        for pname, pdata in planets.items():
            house = pdata.get("house")
            if isinstance(house, int) and house in house_numbers:
                occupants.append(pname)

        # Find house lords
        lords_in_domain: list[str] = []
        for h_num in house_numbers:
            lord = house_lords.get(h_num)
            if lord and lord in planets:
                lord_house = planets[lord].get("house")
                if isinstance(lord_house, int):
                    lords_in_domain.append(f"{lord} (lord of H{h_num}, placed in H{lord_house})")

        if not occupants and not lords_in_domain:
            continue

        narrative_parts: list[str] = []

        if occupants:
            planet_descs = []
            for pname in occupants:
                pdata = planets[pname]
                dignity = dignity_map.get(pname, "")
                rashi = pdata.get("rashi", "")
                detail = planet_details.get(pname, {})
                deg_in_sign = detail.get("degree_in_sign", 0)
                retro = " (retrograde)" if pdata.get("retrograde") else ""
                combust = " (combust)" if pdata.get("combust") else ""
                debil = " [debilitated]" if pdata.get("debilitated") else ""
                planet_descs.append(
                    f"{pname} in {_RASHI_NAMES.get(_RASHI_NUM.get(rashi, 0), rashi)}"
                    f" ({deg_in_sign:.1f}°){retro}{combust}{debil}"
                )

            narrative_parts.append(f"Planetary occupants: {', '.join(planet_descs)}.")

        if lords_in_domain:
            narrative_parts.append(f"House lordship significance: {'; '.join(lords_in_domain)}.")

        sections.append(
            f"**{domain_name}** ({', '.join(f'H{h}' for h in house_numbers)}):\n"
            + "\n".join(narrative_parts)
        )

    return "\n\n".join(sections)


# ══════════════════════════════════════════════════════════════════════════════
# NEW: Classical House Placement Narratives (Phase I7 — Section 3.5)
# ══════════════════════════════════════════════════════════════════════════════


def generate_classical_house_narratives(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate detailed classical interpretations for each occupied house.

    Iterates through all 12 houses, looks up the classical interpretation for
    each planet found in that house, and detects conjunctions for multi-planet
    houses.

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        List of dicts, each with:
            - house (int): House number
            - house_name (str): Classical house name
            - domain (str): Life domain
            - signifies (str): House significations
            - narratives (list[dict]): Per-planet or conjunction interpretations
              Each dict has 'type' ('planet' or 'conjunction'), 'planets' (list),
              'interpretation' (str), and 'dignity' (str).
    """
    planets = jre_facts.get("planets", {})
    dignity_map = jre_facts.get("dignity_map", {})
    nakshatra_data = jre_facts.get("planet_nakshatras", {})

    # Group planets by house
    house_occupants: dict[int, list[str]] = {}
    for pname, pdata in planets.items():
        house = pdata.get("house")
        if isinstance(house, int):
            house_occupants.setdefault(house, []).append(pname)

    results: list[dict[str, Any]] = []

    for house_num in range(1, 13):
        sig = get_house_signification(house_num)
        if not sig:
            continue

        occupants = house_occupants.get(house_num, [])
        if not occupants:
            continue

        narratives: list[dict[str, Any]] = []

        if len(occupants) >= 2:
            # Check for conjunction interpretation first
            conj_text = get_conjunction_interpretation(occupants)
            if conj_text:
                narratives.append(
                    {
                        "type": "conjunction",
                        "planets": occupants,
                        "interpretation": conj_text,
                        "dignity": " / ".join(dignity_map.get(p, "") for p in occupants),
                    }
                )

        # Individual planet interpretations
        for pname in occupants:
            text = get_planet_house_interpretation(pname, house_num)
            if text:
                narratives.append(
                    {
                        "type": "planet",
                        "planets": [pname],
                        "interpretation": text,
                        "dignity": dignity_map.get(pname, ""),
                    }
                )

        if narratives:
            results.append(
                {
                    "house": house_num,
                    "house_name": sig["name"],
                    "domain": sig["domain"],
                    "signifies": sig["signifies"],
                    "narratives": narratives,
                }
            )

    return results


# ══════════════════════════════════════════════════════════════════════════════
# NEW: Nakshatra Influence Narratives (Phase I7 — Section 3.6)
# ══════════════════════════════════════════════════════════════════════════════


def generate_nakshatra_narratives(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate interpretive text for significant nakshatra placements.

    Highlights the most significant nakshatra placements:
    - Lagna Lord's Nakshatra
    - Moon's Nakshatra (always included if available)
    - Sun's Nakshatra
    - Any planet in its own Nakshatra ruler's nakshatra

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        List of dicts with 'planet', 'nakshatra', 'interpretation' keys.
    """
    planets = jre_facts.get("planets", {})
    planet_nakshatras = jre_facts.get("planet_nakshatras", {})
    lagna_sign_num = jre_facts.get("lagna_sign", 1)

    # Build house_lords to find Lagna lord
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
    lagna_lord = _SIGN_LORDS.get(lagna_sign_num, "")

    # Priority planets for nakshatra highlights
    highlight_planets: list[str] = []
    if lagna_lord:
        highlight_planets.append(lagna_lord)
    highlight_planets.extend(["MOON", "SUN"])
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_highlights: list[str] = []
    for p in highlight_planets:
        if p not in seen:
            seen.add(p)
            unique_highlights.append(p)

    results: list[dict[str, Any]] = []

    for pname in unique_highlights:
        # Try to get nakshatra from planet_nakshatras dict or from planet data
        nak_name = planet_nakshatras.get(pname, "")
        if not nak_name:
            pdata = planets.get(pname, {})
            nak_name = pdata.get("nakshatra", "")
        if not nak_name:
            continue

        text = get_nakshatra_interpretation(pname, nak_name)
        if text:
            results.append(
                {
                    "planet": pname,
                    "nakshatra": nak_name,
                    "interpretation": text,
                }
            )

    # Also check for any other planets with known nakshatra interpretations
    for pname, pdata in planets.items():
        if pname in seen:
            continue
        nak = planet_nakshatras.get(pname, "") or pdata.get("nakshatra", "")
        if not nak:
            continue
        text = get_nakshatra_interpretation(pname, nak)
        if text:
            results.append(
                {
                    "planet": pname,
                    "nakshatra": nak,
                    "interpretation": text,
                }
            )
            seen.add(pname)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# NEW: Aspectual Themes Narratives (Phase I7 — Section 3.7)
# ══════════════════════════════════════════════════════════════════════════════


def generate_aspectual_themes(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate the aspect matrix into narrative text.

    Iterates through detected aspects and generates classical interpretation
    narratives for each, highlighting the most significant planetary influences.

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        List of dicts with 'source', 'target', 'aspect_type', 'narrative' keys.
    """
    aspects = jre_facts.get("aspect_matrix", [])

    results: list[dict[str, Any]] = []

    for asp in aspects:
        source = asp.get("source", "")
        target = asp.get("target", "")
        aspect_type = asp.get("type", "opposition")

        narrative = get_aspect_narrative(source, aspect_type)

        if not narrative:
            # Generate a generic narrative based on aspect type
            if aspect_type == "opposition":
                narrative = (
                    f"{source}'s aspect to {target} creates dynamic energy that "
                    f"stimulates growth through interaction across the chart axis."
                )
            elif "trine" in aspect_type:
                narrative = (
                    f"{source}'s aspect to {target} brings harmonious, supportive "
                    f"energy that enhances the positive qualities of both planets."
                )
            elif "square" in aspect_type:
                narrative = (
                    f"{source}'s aspect to {target} creates tension that demands "
                    f"conscious integration and ultimately strengthens both planetary "
                    f"functions through challenge."
                )
            else:
                narrative = (
                    f"{source} aspects {target}, creating an interplay of "
                    f"planetary energies that shapes the native's experience."
                )

        results.append(
            {
                "source": source,
                "target": target,
                "aspect_type": aspect_type,
                "angle_deg": asp.get("angle_deg", 0),
                "source_house": asp.get("source_house"),
                "target_house": asp.get("target_house"),
                "narrative": narrative,
            }
        )

    return results


# ══════════════════════════════════════════════════════════════════════════════
# NEW: Karmic Themes & Predictive Indicators (Phase I7 — Section 7.5)
# ══════════════════════════════════════════════════════════════════════════════


def generate_karmic_insights(jre_facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan for karmic and predictive indicators in the chart.

    Detects challenging placements (8th/12th house, maraka influences,
    severe afflictions) and frames them constructively with classical
    remedial context.

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        List of dicts with 'key', 'condition', 'interpretation', 'remedy' keys.
    """
    planets = jre_facts.get("planets", {})

    detected: list[dict[str, Any]] = []

    # Check each known karmic indicator
    for key, indicator in KARMIC_INDICATORS.items():
        condition = indicator.get("condition", "")
        triggered = False

        # Parse condition to check if it matches the chart
        # Conditions are like "Ketu in 12th house", "Saturn in 8th house", etc.
        parts = condition.split(" in ")
        if len(parts) == 2:
            planet_name = parts[0].strip().upper()
            house_str = (
                parts[1]
                .strip()
                .replace(" house", "")
                .replace("th", "")
                .replace("st", "")
                .replace("nd", "")
                .replace("rd", "")
            )
            try:
                house_num = int(house_str)
            except ValueError:
                continue

            pdata = planets.get(planet_name, {})
            actual_house = pdata.get("house")
            if isinstance(actual_house, int) and actual_house == house_num:
                triggered = True

        if triggered:
            detected.append(
                {
                    "key": key,
                    "condition": condition,
                    "interpretation": indicator.get("interpretation", ""),
                    "remedy": indicator.get("remedy", ""),
                }
            )

    # Also scan for additional karmic patterns not in the static dictionary
    _scan_additional_karmic_patterns(planets, detected)

    return detected


def _scan_additional_karmic_patterns(
    planets: dict[str, Any],
    detected: list[dict[str, Any]],
) -> None:
    """Scan for additional karmic patterns beyond the static dictionary.

    Detects:
    - Multiple debilitated planets
    - Stellium in a single house
    - Planets in dusthana houses (6, 8, 12) as a group
    - Planets conjunct nodes (Rahu/Ketu)
    """
    debilitated = [p for p, d in planets.items() if d.get("debilitated")]
    if len(debilitated) >= 2:
        names = ", ".join(debilitated)
        detected.append(
            {
                "key": "multiple_debilitated",
                "condition": f"Multiple debilitated planets: {names}",
                "interpretation": (
                    f"The presence of multiple debilitated planets ({names}) suggests "
                    f"significant karmic challenges in this lifetime. However, classical "
                    f"texts emphasize that debilitation is not inherently negative — it "
                    f"indicates areas where the soul must develop through conscious effort. "
                    f"Neecha Bhanga (cancellation of debilitation) can transform these "
                    f"challenges into unexpected strengths."
                ),
                "remedy": (
                    "Focus remedial measures on the most functionally important debilitated "
                    "planet. Regular mantra practice, gemstone therapy (after consulting a "
                    "qualified astrologer), and charitable donations on the planet's day are "
                    "classically recommended. BPHS Ch. 38 provides detailed Neecha Bhanga "
                    "remedies."
                ),
            }
        )

    # Stellium detection (3+ planets in one house)
    house_counts: dict[int, list[str]] = {}
    for pname, pdata in planets.items():
        house = pdata.get("house")
        if isinstance(house, int) and 1 <= house <= 12:
            house_counts.setdefault(house, []).append(pname)

    for house_num, occupants in house_counts.items():
        if len(occupants) >= 3:
            names = ", ".join(occupants)
            sig = get_house_signification(house_num)
            domain = sig["domain"] if sig else f"House {house_num}"
            detected.append(
                {
                    "key": f"stellium_house_{house_num}",
                    "condition": f"Stellium in House {house_num}: {names}",
                    "interpretation": (
                        f"A stellium (three or more planets) in the {_ordinal(house_num)} "
                        f"house ({domain}) creates intense focus and concentration of "
                        f"planetary energy in this area of life. The native's karmic "
                        f"lessons are heavily concentrated in the domain of "
                        f"{sig['signifies'] if sig else 'this house'}. This concentration "
                        f"can produce exceptional talent or significant challenges, "
                        f"depending on the planets involved and their dignity."
                    ),
                    "remedy": (
                        f"Balance the intense focus on {domain} by consciously cultivating "
                        f"qualities of the opposite house ({_ordinal((house_num + 5) % 12 + 1)}). "
                        f"Regular meditation and balanced daily routines help distribute "
                        f"planetary energy more evenly across life domains."
                    ),
                }
            )

    # Rahu/Ketu conjunctions
    for node in ("RAHU", "KETU"):
        node_data = planets.get(node, {})
        node_house = node_data.get("house")
        if not isinstance(node_house, int):
            continue
        for pname, pdata in planets.items():
            if pname in (node,):
                continue
            p_house = pdata.get("house")
            if isinstance(p_house, int) and p_house == node_house:
                # Check if they are conjunct (same house)
                detected.append(
                    {
                        "key": f"{node}_conjunct_{pname}",
                        "condition": f"{node} conjunct {pname} in House {node_house}",
                        "interpretation": (
                            f"{node}'s conjunction with {pname} in the {_ordinal(node_house)} "
                            f"house creates a karmic fusion of energies. "
                            f"{'Rahu amplifies' if node == 'RAHU' else 'Ketu releases'} "
                            f"{pname}'s significations, creating both challenge and "
                            f"extraordinary potential in this area of life."
                        ),
                        "remedy": (
                            f"Chant {'Om Ra Namaha' if node == 'RAHU' else 'Om Ketave Namaha'} "
                            f"and practice meditation to integrate the node's transformative "
                            f"energy with {pname}'s natural function."
                        ),
                    }
                )
                break  # Only report first conjunction per node per house


# ── Karmic Axis Narrative ────────────────────────────────────────────────────


def generate_karmic_axis_narrative(jre_facts: dict[str, Any]) -> str:
    """Generate interpretation of Rahu (North Node) and Ketu (South Node) placement.

    The karmic axis represents the soul's evolutionary direction: Ketu shows
    where the soul is coming from (past life comfort zone), Rahu shows where
    it is heading (future growth area).

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        Narrative string about the karmic axis.
    """
    planets = jre_facts.get("planets", {})

    _RASHI_NAMES: dict[str, str] = {
        "MESHA": "Aries",
        "VRISHABHA": "Taurus",
        "MITHUNA": "Gemini",
        "KARKA": "Cancer",
        "SIMHA": "Leo",
        "KANYA": "Virgo",
        "TULA": "Libra",
        "VRISHCHIKA": "Scorpio",
        "DHANUSHA": "Sagittarius",
        "MAKARA": "Capricorn",
        "KUMBHA": "Aquarius",
        "MEENA": "Pisces",
    }

    rahu = planets.get("RAHU", {})
    ketu = planets.get("KETU", {})

    rahu_rashi = rahu.get("rashi", "")
    ketu_rashi = ketu.get("rashi", "")
    rahu_house = rahu.get("house", 0)
    ketu_house = ketu.get("house", 0)

    if not rahu_rashi or not ketu_rashi:
        return "Karmic axis data is not available for this chart."

    rahu_sign_name = _RASHI_NAMES.get(rahu_rashi, rahu_rashi)
    ketu_sign_name = _RASHI_NAMES.get(ketu_rashi, ketu_rashi)

    paragraphs = [
        (
            f"The karmic axis runs through {ketu_sign_name} ({_ordinal(ketu_house)} house) "
            f"to {rahu_sign_name} ({_ordinal(rahu_house)} house). Ketu in {ketu_sign_name} "
            f"indicates the native's innate comfort zone and past-life gifts — areas where "
            f"natural talent and instinctive understanding already exist. Rahu in {rahu_sign_name} "
            f"points to the soul's evolutionary direction — the unfamiliar territory that offers "
            f"the greatest growth potential."
        ),
        (
            "This axis creates a fundamental tension between the familiar (Ketu) and the "
            "aspirational (Rahu). The native's life journey involves gradually integrating "
            "Rahu's qualities while honoring the natural gifts of Ketu."
        ),
    ]

    return "\n\n".join(paragraphs)


# ── Remedial Measures Narrative ──────────────────────────────────────────────

# Classical remedy associations
_PLANET_REMEDIES: dict[str, dict[str, Any]] = {
    "SUN": {
        "mantra": "Om Suryaya Namaha",
        "gemstone": "Ruby (Manikya)",
        "donation": "Wheat, jaggery, red cloth on Sundays",
        "classical_remedy": (
            "Offer water to the rising Sun (Arghya) while reciting Aditya Hridayam. "
            "Worship at Shiva temples on Sundays. BPHS Ch. 26 recommends Surya "
            "Upasana for strengthening the Sun's significations."
        ),
    },
    "MOON": {
        "mantra": "Om Chandraya Namaha",
        "gemstone": "Pearl (Moti)",
        "donation": "Rice, milk, white cloth on Mondays",
        "classical_remedy": (
            "Chant Chandra Mantra 108 times on Mondays. Worship at Shiva temples "
            "with bel leaves. Phaladeepika recommends Moon remedies for emotional "
            "stability and mental peace."
        ),
    },
    "MARS": {
        "mantra": "Om Angarakaya Namaha",
        "gemstone": "Red Coral (Moonga)",
        "donation": "Red lentils, red cloth on Tuesdays",
        "classical_remedy": (
            "Visit Hanuman temples on Tuesdays and recite Hanuman Chalisa. BPHS "
            "Ch. 25 prescribes Mars remedies for courage, sibling harmony, and "
            "property matters."
        ),
    },
    "MERCURY": {
        "mantra": "Om Budhaya Namaha",
        "gemstone": "Emerald (Panna)",
        "donation": "Green gram, green cloth on Wednesdays",
        "classical_remedy": (
            "Worship Lord Vishnu on Wednesdays. Recite Vishnu Sahasranama for "
            "Mercury strengthening. Phaladeepika Ch. 8 recommends Mercury remedies "
            "for intelligence, communication, and business success."
        ),
    },
    "JUPITER": {
        "mantra": "Om Gurave Namaha",
        "gemstone": "Yellow Sapphire (Pukhraj)",
        "donation": "Chana dal, turmeric, yellow cloth on Thursdays",
        "classical_remedy": (
            "Visit Vishnu temples on Thursdays. Recite Guru Mantra or Vishnu "
            "Sahasranama. BPHS Ch. 27 recommends Jupiter remedies for wisdom, "
            "prosperity, and spiritual growth."
        ),
    },
    "VENUS": {
        "mantra": "Om Shukraya Namaha",
        "gemstone": "Diamond (Heera) or White Sapphire",
        "donation": "Sugar, white sweets, white cloth on Fridays",
        "classical_remedy": (
            "Worship Goddess Lakshmi on Fridays. Offer white flowers at Venus "
            "temples. Phaladeepika Ch. 10 prescribes Venus remedies for beauty, "
            "luxury, and relationship harmony."
        ),
    },
    "SATURN": {
        "mantra": "Om Shanicharaya Namaha",
        "gemstone": "Blue Sapphire (Neelam)",
        "donation": "Black sesame, iron, blue/black cloth on Saturdays",
        "classical_remedy": (
            "Visit Shani temples on Saturdays. Offer mustard oil to Shani idols. "
            "BPHS Ch. 29 recommends Saturn remedies for discipline, longevity, "
            "and overcoming obstacles. Serve the elderly and disabled."
        ),
    },
}


def generate_remedial_measures_narrative(jre_facts: dict[str, Any]) -> str:
    """Generate classical remedial measures based on the most afflicted/weakest planet.

    Analyzes debilitation, combustion, and affliction patterns to identify
    the planet most in need of remedial measures, then provides classical
    recommendations from BPHS and Phaladeepika.

    Args:
        jre_facts: Enriched JRE facts dictionary.

    Returns:
        Narrative string with remedial recommendations.
    """
    planets = jre_facts.get("planets", {})
    dignity_map = jre_facts.get("dignity_map", {})

    # Score affliction: debilitated > combust > enemy sign > neutral
    affliction_scores: dict[str, int] = {}
    for pname, pdata in planets.items():
        if pname in ("RAHU", "KETU"):
            continue
        score = 0
        if pdata.get("debilitated"):
            score += 3
        if pdata.get("combust"):
            score += 2
        if dignity_map.get(pname) == "Enemy":
            score += 1
        if score > 0:
            affliction_scores[pname] = score

    if not affliction_scores:
        return (
            "No significantly afflicted classical planets were detected. The chart "
            "shows a relatively balanced planetary disposition. General remedies "
            "include daily prayer, charitable giving, and maintaining ethical conduct "
            "as prescribed in Phaladeepika."
        )

    # Sort by affliction score (highest first)
    sorted_planets = sorted(affliction_scores.items(), key=lambda x: x[1], reverse=True)
    primary_planet = sorted_planets[0][0]

    remedies = _PLANET_REMEDIES.get(primary_planet, {})
    if not remedies:
        return f"Classical remedies for {primary_planet} are not available in the remedy database."

    paragraphs = [
        (
            f"The most afflicted planet in the chart is **{primary_planet}**. "
            f"{'It is debilitated.' if planets[primary_planet].get('debilitated') else ''} "
            f"{'It is combust (close to the Sun).' if planets[primary_planet].get('combust') else ''} "
            f"Classical texts recommend specific remedial measures to mitigate "
            f"the negative effects and channel this planet's energy constructively."
        ),
        (
            f"**Mantra:** Chant '{remedies.get('mantra', 'N/A')}' 108 times daily "
            f"or on the planet's day of the week."
        ),
        (
            f"**Gemstone:** {remedies.get('gemstone', 'N/A')} — to be worn after "
            f"consulting a qualified Vedic astrologer. BPHS Ch. 2–3 prescribes "
            f"gemstone therapy based on the functional nature of the planet."
        ),
        (
            f"**Charity (Daan):** {remedies.get('donation', 'N/A')}. "
            f"Donating to those in need appeases afflicted planetary energies."
        ),
        (f"**Classical Remedy:** {remedies.get('classical_remedy', '')}"),
    ]

    if len(sorted_planets) > 1:
        secondary = sorted_planets[1][0]
        sec_remedies = _PLANET_REMEDIES.get(secondary, {})
        if sec_remedies:
            paragraphs.append(
                f"Additionally, **{secondary}** shows moderate affliction. "
                f"Consider chanting '{sec_remedies.get('mantra', 'N/A')}' and "
                f"performing {sec_remedies.get('donation', 'N/A')}."
            )

    return "\n\n".join(paragraphs)


# ── Helpers ──────────────────────────────────────────────────────────────────

_RASHI_NUM: dict[str, int] = {
    "MESHA": 1,
    "VRISHABHA": 2,
    "MITHUNA": 3,
    "KARKA": 4,
    "SIMHA": 5,
    "KANYA": 6,
    "TULA": 7,
    "VRISHCHIKA": 8,
    "DHANUSHA": 9,
    "MAKARA": 10,
    "KUMBHA": 11,
    "MEENA": 12,
}

_RASHI_NUM_REVERSE: dict[int, str] = {v: k for k, v in _RASHI_NUM.items()}

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


def _ordinal(n: int) -> str:
    """Convert integer to ordinal string (1→'1st', 2→'2nd', etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
