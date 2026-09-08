"""JRE Parihara — Remedies Engine.

Generates deterministic, classical Vedic remedies based on planetary
afflictions detected in the natal chart. Uses a strict JSON lookup table
for consistency and classical accuracy.

Source: BPHS Ch 40-45; Phaladeepika Ch 25-27; Saravali Ch 35.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Load Remedy Data ──────────────────────────────────────

_REMEDY_DATA_PATH = Path(__file__).parent / "remedy_data.json"


def _load_remedy_data() -> dict[str, Any]:
    """Load the deterministic remedy lookup table."""
    with _REMEDY_DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


_REMEDY_DATA: dict[str, Any] = _load_remedy_data()

# ── Affliction Detection Constants ────────────────────────

_DEBILITATION_SIGNS: dict[str, str] = {
    "SUN": "TULA",
    "MOON": "VRISHCHIKA",
    "MARS": "KARKA",
    "MERCURY": "MEENA",
    "JUPITER": "MAKARA",
    "VENUS": "KANYA",
    "SATURN": "MESHA",
}

_ENEMY_SIGNS: dict[str, set[str]] = {
    "SUN": {"KANYA", "MEENA"},
    "MOON": {"KANYA", "TULA"},
    "MARS": {"MESHA", "VRISHCHIKA"},
    "MERCURY": {"MESHA", "SIMHA"},
    "JUPITER": {"MESHA", "VRISHABHA"},
    "VENUS": {"KARKA", "SIMHA"},
    "SATURN": {"MESHA", "SIMHA"},
}

_MALEFIC_PLANETS = {"SUN", "MARS", "SATURN", "RAHU", "KETU"}

# ── Data Structures ───────────────────────────────────────


@dataclass
class PlanetRemedy:
    """Remedy package for a single planet."""

    planet: str
    affliction: str
    severity: str  # "high", "medium", "low"
    mantra: dict[str, Any] = field(default_factory=dict)
    gemstone: dict[str, Any] = field(default_factory=dict)
    temple: dict[str, Any] = field(default_factory=dict)
    charity: dict[str, Any] = field(default_factory=dict)
    color_therapy: dict[str, Any] = field(default_factory=dict)
    fasting: dict[str, Any] = field(default_factory=dict)
    lifestyle: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemedyResult:
    """Complete remedy result for all afflictions."""

    afflicted_planets: list[PlanetRemedy]
    doshas: list[dict[str, Any]]
    general_remedies: dict[str, Any]
    overall_assessment: str
    disclaimer: str


# ── Affliction Detection ─────────────────────────────────


def _detect_afflictions(planet_details: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect planetary afflictions from planet details.

    Args:
        planet_details: Dict of planet -> {sign, dignity, house, ...}

    Returns:
        List of affliction dicts with planet, type, and severity.
    """
    afflictions: list[dict[str, Any]] = []

    for planet, pdata in planet_details.items():
        if planet in ("RAHU", "KETU"):
            # Nodes have their own remedy section, skip general afflictions
            continue

        dignity = pdata.get("dignity", "").lower()
        sign = pdata.get("sign", "")
        combust = pdata.get("combust", False)

        # Check for debilitation
        if "debil" in dignity:
            afflictions.append(
                {
                    "planet": planet,
                    "type": "debilitated",
                    "severity": "high",
                    "description": f"{planet} is debilitated in {sign}",
                }
            )

        # Check for enemy sign
        elif "enemy" in dignity or "inimical" in dignity:
            afflictions.append(
                {
                    "planet": planet,
                    "type": "enemy_sign",
                    "severity": "medium",
                    "description": f"{planet} is in enemy sign {sign}",
                }
            )

        # Check for combustion
        elif combust:
            afflictions.append(
                {
                    "planet": planet,
                    "type": "combust",
                    "severity": "medium",
                    "description": f"{planet} is combust (too close to Sun)",
                }
            )

        # Check for malefic in malefic houses (simplified)
        if planet in _MALEFIC_PLANETS and "malefic" in dignity.lower():
            # Already captured above
            pass

    return afflictions


def _detect_doshas(
    planet_details: dict[str, Any],
    jre_facts: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect specific Doshas from the chart with definitive DETECTED/NOT DETECTED.

    Args:
        planet_details: Dict of planet -> details
        jre_facts: Full JRE facts packet

    Returns:
        List of all Doshas with status (DETECTED or NOT DETECTED).
    """
    doshas: list[dict[str, Any]] = []
    signs_order = [
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

    # ── 1. Manglik Dosha (Mars in houses 1, 2, 4, 7, 8, 12) ──
    mars_house = planet_details.get("MARS", {}).get("house", 0)
    manglik_houses = {1, 2, 4, 7, 8, 12}
    if mars_house in manglik_houses:
        severity = "high" if mars_house in {1, 4, 7, 8} else "medium"
        remedy = (
            "Perform Hanuman Chalisa daily, visit Mars temples on Tuesdays, "
            "donate red lentils and copper items. Marriage matching with "
            "another Manglik partner neutralizes the dosha. Recite Subramanya Bhujangam."
        )
        doshas.append(
            {
                "name": "Manglik Dosha",
                "status": "DETECTED",
                "severity": severity,
                "description": f"Mars occupies House {mars_house} from Lagna, creating Manglik Dosha. This affects marital harmony and requires careful matching or remedial measures.",
                "remedy": remedy,
            }
        )
    else:
        doshas.append(
            {
                "name": "Manglik Dosha",
                "status": "NOT DETECTED",
                "severity": "none",
                "description": "Mars does not occupy houses 1, 2, 4, 7, 8, or 12 from Lagna. No Manglik affliction present.",
                "remedy": "",
            }
        )

    # ── 2. Kaal Sarp Dosha (all planets between Rahu-Ketu axis) ──
    rahu_sign = planet_details.get("RAHU", {}).get("sign", "")
    ketu_sign = planet_details.get("KETU", {}).get("sign", "")
    kaal_sarp_detected = False
    if rahu_sign in signs_order and ketu_sign in signs_order:
        rahu_idx = signs_order.index(rahu_sign)
        ketu_idx = signs_order.index(ketu_sign)
        between_count = 0
        total_planets = 0
        for p, pd in planet_details.items():
            if p in ("RAHU", "KETU"):
                continue
            p_sign = pd.get("sign", "")
            if p_sign in signs_order:
                total_planets += 1
                p_idx = signs_order.index(p_sign)
                if rahu_idx < ketu_idx:
                    if rahu_idx < p_idx < ketu_idx:
                        between_count += 1
                else:
                    if p_idx > rahu_idx or p_idx < ketu_idx:
                        between_count += 1
        if between_count == total_planets and total_planets >= 5:
            kaal_sarp_detected = True

    if kaal_sarp_detected:
        doshas.append(
            {
                "name": "Kaal Sarp Dosha",
                "status": "DETECTED",
                "severity": "high",
                "description": f"All planets lie between Rahu ({rahu_sign}) and Ketu ({ketu_sign}) axis. This creates karmic debt from past lives, causing delays and obstacles in all areas of life.",
                "remedy": "Perform Kaal Sarp Dosha Nivaran Puja at Trimbakeshwar or Kalahasti. Visit Rahu/Ketu temples during Rahu Kaal. Donate black sesame seeds and blue cloth on Saturdays. Recite Maha Mrityunjaya Mantra 108 times daily.",
            }
        )
    else:
        doshas.append(
            {
                "name": "Kaal Sarp Dosha",
                "status": "NOT DETECTED",
                "severity": "none",
                "description": "Not all planets are confined between the Rahu-Ketu axis. No Kaal Sarp affliction present.",
                "remedy": "",
            }
        )

    # ── 3. Pitra Dosha (Sun/Rahu conjunction or Sun affliction) ──
    sun_sign = planet_details.get("SUN", {}).get("sign", "")
    pitra_detected = False
    if rahu_sign and sun_sign and rahu_sign == sun_sign:
        pitra_detected = True
    if not pitra_detected and rahu_sign in signs_order and sun_sign in signs_order:
        rahu_h = planet_details.get("RAHU", {}).get("house", 0)
        sun_h = planet_details.get("SUN", {}).get("house", 0)
        if rahu_h and sun_h and abs(rahu_h - sun_h) in (1, 11):
            pitra_detected = True

    if pitra_detected:
        doshas.append(
            {
                "name": "Pitra Dosha",
                "status": "DETECTED",
                "severity": "medium",
                "description": "Sun is afflicted by Rahu (conjunction or close aspect). This indicates unresolved ancestral karmas requiring remedial measures for ancestral peace.",
                "remedy": "Perform Pitra Tarpanam during Amavasya (new moon). Offer water mixed with sesame seeds to ancestors. Feed crows regularly. Donate food to Brahmins on Sundays. Visit Pitra Dosha Nivaran temples.",
            }
        )
    else:
        doshas.append(
            {
                "name": "Pitra Dosha",
                "status": "NOT DETECTED",
                "severity": "none",
                "description": "Sun is not afflicted by Rahu. No Pitra Dosha present.",
                "remedy": "",
            }
        )

    # ── 4. Sadhe Sati (Saturn transiting 12th, 1st, 2nd from Moon) ──
    saturn_house = planet_details.get("SATURN", {}).get("house", 0)
    moon_house = planet_details.get("MOON", {}).get("house", 0)
    sadhe_sati_detected = False
    if saturn_house and moon_house:
        diff = (saturn_house - moon_house) % 12
        if diff in (11, 0, 1):  # 12th, 1st, or 2nd from Moon
            sadhe_sati_detected = True

    if sadhe_sati_detected:
        doshas.append(
            {
                "name": "Sadhe Sati",
                "status": "DETECTED",
                "severity": "high",
                "description": f"Saturn transits near the natal Moon (House {saturn_house} from Moon). This 7.5-year period brings transformation through challenges, discipline, and karmic lessons.",
                "remedy": "Wear blue sapphire (after testing) on middle finger. Feed crows on Saturdays. Donate blankets and black items. Recite Shani Mantra: Om Sham Shanicharaya Namaha. Visit Shani temples on Saturdays.",
            }
        )
    else:
        doshas.append(
            {
                "name": "Sadhe Sati",
                "status": "NOT DETECTED",
                "severity": "none",
                "description": "Saturn is not transiting near the natal Moon. No Sadhe Sati period active.",
                "remedy": "",
            }
        )

    # ── 5. Weak Moon Dosha ──
    moon_dignity = planet_details.get("MOON", {}).get("dignity", "").lower()
    weak_moon = "debil" in moon_dignity
    if not weak_moon:
        moon_house = planet_details.get("MOON", {}).get("house", 0)
        if moon_house in (6, 8, 12):
            weak_moon = True
    if not weak_moon:
        for p in ["SATURN", "RAHU", "MARS"]:
            p_house = planet_details.get(p, {}).get("house", 0)
            if p_house and moon_house and p_house == moon_house:
                weak_moon = True
                break

    if weak_moon:
        doshas.append(
            {
                "name": "Weak Moon Dosha",
                "status": "DETECTED",
                "severity": "medium",
                "description": "Moon is weakened by debilitation, placement in dusthana, or conjunction with malefics. This affects emotional stability, mental peace, and relationships with mother.",
                "remedy": "Wear pearl (Moti) on little finger on Monday morning. Drink water stored in silver vessel. Worship Lord Shiva with milk and water. Chant Moon Mantra: Om Somaya Namaha. Meditate during full moon.",
            }
        )
    else:
        doshas.append(
            {
                "name": "Weak Moon Dosha",
                "status": "NOT DETECTED",
                "severity": "none",
                "description": "Moon is well-placed and strong. No Moon affliction present.",
                "remedy": "",
            }
        )

    # ── 6. Chandra Manglik Dosha ──
    if mars_house and moon_house:
        mars_moon_diff = abs(mars_house - moon_house)
        if mars_moon_diff in (2, 4, 6, 8, 12, 0):
            doshas.append(
                {
                    "name": "Chandra Manglik Dosha",
                    "status": "DETECTED",
                    "severity": "medium",
                    "description": f"Mars and Moon are in conflicting houses ({mars_house} and {moon_house}). This creates emotional volatility and relationship challenges.",
                    "remedy": "Perform Chandra Manglik Dosha Nivaran. Wear pearl and coral together. Worship Lord Shiva and Goddess Durga. Donate rice and red sweets on Mondays.",
                }
            )
        else:
            doshas.append(
                {
                    "name": "Chandra Manglik Dosha",
                    "status": "NOT DETECTED",
                    "severity": "none",
                    "description": "Mars and Moon do not create Chandra Manglik conflict.",
                    "remedy": "",
                }
            )

    print(
        f"DOSHA ENGINE DEBUG: Checked 6 Doshas — "
        + ", ".join(f"{d['name']}: {d['status']}" for d in doshas)
    )
    return doshas


# ── Remedy Generation ─────────────────────────────────────


def _get_planet_remedy(
    planet: str,
    affliction_type: str,
    severity: str,
) -> PlanetRemedy:
    """Get the complete remedy package for an afflicted planet.

    Args:
        planet: Planet name (e.g., "SUN")
        affliction_type: Type of affliction (e.g., "debilitated")
        severity: Severity level ("high", "medium", "low")

    Returns:
        PlanetRemedy with all remedy categories.
    """
    planet_data = _REMEDY_DATA.get("planets", {}).get(planet, {})

    return PlanetRemedy(
        planet=planet,
        affliction=affliction_type,
        severity=severity,
        mantra=planet_data.get("mantra", {}),
        gemstone=planet_data.get("gemstone", {}),
        temple=planet_data.get("temple", {}),
        charity=planet_data.get("charity", {}),
        color_therapy=planet_data.get("color_therapy", {}),
        fasting=planet_data.get("fasting", {}),
        lifestyle=planet_data.get("lifestyle", {}),
    )


def _generate_dosha_remedies(doshas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate remedies for detected Doshas.

    Args:
        doshas: List of detected Doshas.

    Returns:
        List of Dosha remedy dicts.
    """
    remedy_doshas = _REMEDY_DATA.get("doshas", {})
    remedies = []

    for dosha in doshas:
        dosha_name = dosha.get("name", "")
        remedy_info = remedy_doshas.get(dosha_name, {})
        if remedy_info:
            remedies.append(
                {
                    "dosha": dosha_name,
                    "severity": dosha.get("severity", "medium"),
                    "description": dosha.get("description", ""),
                    "mantra": remedy_info.get("mantra", ""),
                    "charity": remedy_info.get("charity", ""),
                    "temple": remedy_info.get("temple", ""),
                    "remedy": remedy_info.get("remedy", ""),
                }
            )

    return remedies


def _assess_overall(afflictions: list[dict[str, Any]], doshas: list[dict[str, Any]]) -> str:
    """Assess overall chart balance.

    Args:
        afflictions: List of detected afflictions.
        doshas: List of detected Doshas.

    Returns:
        Overall assessment string.
    """
    high_severity = sum(1 for a in afflictions if a.get("severity") == "high")
    medium_severity = sum(1 for a in afflictions if a.get("severity") == "medium")
    dosha_count = len(doshas)

    if high_severity == 0 and medium_severity == 0 and dosha_count == 0:
        return "excellent"
    elif high_severity == 0 and medium_severity <= 2:
        return "good"
    elif high_severity <= 1 and medium_severity <= 3:
        return "moderate"
    elif high_severity <= 2:
        return "challenging"
    else:
        return "difficult"


# ── Main Function ─────────────────────────────────────────


def generate_remedies(jre_facts_packet: dict[str, Any]) -> RemedyResult:
    """Generate classical Vedic remedies from JRE facts packet.

    This is the primary entry point for the Remedies Engine. It analyzes
    planetary afflictions and Doshas, then returns structured remedy
    recommendations using a deterministic lookup table.

    Args:
        jre_facts_packet: JRE facts dictionary with planet positions.
            Expected format:
            {
                "planet_details": {
                    "SUN": {"sign": "MESHA", "dignity": "Friendly", ...},
                    ...
                },
                "planets": { ... }  # optional fallback
            }

    Returns:
        RemedyResult with all remedy categories for afflicted planets.
    """
    # Extract planet details from facts packet
    planet_details = jre_facts_packet.get("planet_details") or jre_facts_packet.get("planets", {})

    # Detect afflictions
    afflictions = _detect_afflictions(planet_details)

    # Detect Doshas
    doshas = _detect_doshas(planet_details, jre_facts_packet)

    # Generate remedies for each affliction
    planet_remedies: list[PlanetRemedy] = []
    for affliction in afflictions:
        planet = affliction["planet"]
        remedy = _get_planet_remedy(
            planet=planet,
            affliction_type=affliction["type"],
            severity=affliction["severity"],
        )
        planet_remedies.append(remedy)

    # Generate Dosha remedies
    dosha_remedies = _generate_dosha_remedies(doshas)

    # Get general remedies
    general = _REMEDY_DATA.get("general_remedies", {}).get("for_balance", {})

    # Assess overall
    assessment = _assess_overall(afflictions, doshas)

    # Build disclaimer
    disclaimer = (
        "These are classical Vedic recommendations based on Parashari principles. "
        "Consult a qualified astrologer before wearing gemstones or performing "
        "major remedial measures. Gemstones should be tested for 3-7 days before "
        "wearing permanently."
    )

    return RemedyResult(
        afflicted_planets=planet_remedies,
        doshas=dosha_remedies,
        general_remedies=general,
        overall_assessment=assessment,
        disclaimer=disclaimer,
    )


def remedy_to_dict(result: RemedyResult) -> dict[str, Any]:
    """Convert RemedyResult to JSON-serializable dict.

    Args:
        result: RemedyResult from generate_remedies.

    Returns:
        JSON-serializable dictionary.
    """
    return {
        "afflicted_planets": [
            {
                "planet": pr.planet,
                "affliction": pr.affliction,
                "severity": pr.severity,
                "mantra": pr.mantra,
                "gemstone": pr.gemstone,
                "temple": pr.temple,
                "charity": pr.charity,
                "color_therapy": pr.color_therapy,
                "fasting": pr.fasting,
                "lifestyle": pr.lifestyle,
            }
            for pr in result.afflicted_planets
        ],
        "doshas": result.doshas,
        "general_remedies": result.general_remedies,
        "overall_assessment": result.overall_assessment,
        "disclaimer": result.disclaimer,
    }
