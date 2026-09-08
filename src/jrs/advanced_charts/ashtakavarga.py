"""JRE Advanced Charts — Ashtakavarga Engine.

Calculates Bhinna Ashtakavarga (BAV) and Sarva Ashtakavarga (SAV) bindus
for all 12 houses.

Bhinna Ashtakavarga (BAV): Individual planet's contribution to each house.
  - Each of the 7 planets (excluding nodes) assigns bindus (1-8) to houses.
  - A planet assigns a bindu to a house if another planet is in:
    Kendra (1/4/7/10), Trikona (1/5/9), or the same house as the giver.

Sarva Ashtakavarga (SAV): Sum of all BAVs for each house.
  - Strong houses have SAV >= 28 bindus.
  - Weak houses have SAV < 24 bindus.

Source: BPHS Ch 39; Phaladeepika Ch 9; Saravali Ch 33.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SIGN_ORDER = [
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

# Bindu assignment rules for each giver planet
# Based on the position of the receiver planet relative to the giver
# Positive houses: 1, 2, 4, 5, 7, 8, 10, 11 (get 1 bindu each)
# Negative houses: 3, 6, 9, 12 (get 0 bindus)
_BINDU_RULES: dict[str, list[int]] = {
    "SUN": [1, 2, 4, 5, 7, 8, 10, 11],  # Houses that get bindus from Sun
    "MOON": [1, 3, 6, 7, 8, 10, 11],
    "MARS": [1, 2, 4, 7, 8, 10, 11],
    "MERCURY": [1, 2, 4, 5, 6, 8, 10, 11],
    "JUPITER": [1, 2, 4, 5, 6, 7, 9, 10],
    "VENUS": [1, 2, 3, 4, 5, 7, 8, 9, 11],
    "SATURN": [1, 3, 4, 5, 6, 8, 9, 10, 11],
}


@dataclass
class BAVResult:
    """Bhinna Ashtakavarga result for a single planet."""

    planet: str
    bindus: dict[int, int]  # house number (1-12) -> bindu count (0-7)
    total_bindus: int  # Sum of all bindus


@dataclass
class AshtakavargaResult:
    """Complete Ashtakavarga result."""

    bav: dict[str, BAVResult]  # Per-planet BAV
    sav: dict[int, int]  # Sarva Ashtakavarga: house -> total bindus
    strongest_house: int  # House with highest SAV
    weakest_house: int  # House with lowest SAV
    average_sav: float  # Average SAV across houses


# ── Calculation ───────────────────────────────────────────


def _compute_bav(
    giver: str,
    giver_house: int,
    all_planets: dict[str, int],  # planet -> house
) -> BAVResult:
    """Compute Bhinna Ashtakavarga for a single giver planet.

    Args:
        giver: Giver planet name.
        giver_house: House where the giver is placed.
        all_planets: Dict of all planet names -> house numbers.

    Returns:
        BAVResult with bindus for each house.
    """
    bindus: dict[int, int] = {h: 0 for h in range(1, 13)}

    rules = _BINDU_RULES.get(giver, [])

    for receiver, receiver_house in all_planets.items():
        if receiver == giver:
            continue

        # Calculate relative house from giver to receiver
        relative_house = ((receiver_house - giver_house) % 12) + 1

        # Check if this relative house gets a bindu
        if relative_house in rules:
            # The bindu goes to the receiver's ACTUAL house
            bindus[receiver_house] = bindus.get(receiver_house, 0) + 1

    total = sum(bindus.values())
    return BAVResult(
        planet=giver,
        bindus=bindus,
        total_bindus=total,
    )


def compute_ashtakavarga(
    natal_data: dict[str, Any],
) -> AshtakavargaResult:
    """Compute complete Ashtakavarga for all 7 planets.

    Args:
        natal_data: Dict with 'planets' containing house positions.

    Returns:
        AshtakavargaResult with BAV and SAV.
    """
    planets = natal_data.get("planets", {})

    # Build planet -> house mapping
    all_planets: dict[str, int] = {}
    for pname, pdata in planets.items():
        if pname in ("RAHU", "KETU"):
            continue  # Nodes are excluded from Ashtakavarga
        house = pdata.get("house", 0)
        if isinstance(house, int) and 1 <= house <= 12:
            all_planets[pname] = house

    # Compute BAV for each giver
    bav_results: dict[str, BAVResult] = {}
    for giver in all_planets:
        bav_results[giver] = _compute_bav(giver, all_planets[giver], all_planets)

    # Compute SAV: sum BAVs for each house
    sav: dict[int, int] = {h: 0 for h in range(1, 13)}
    for bav in bav_results.values():
        for house, bindu in bav.bindus.items():
            sav[house] = sav.get(house, 0) + bindu

    # Find strongest and weakest houses
    if sav:
        strongest = max(sav, key=sav.get)
        weakest = min(sav, key=sav.get)
        avg = sum(sav.values()) / len(sav)
    else:
        strongest = weakest = 1
        avg = 0.0

    return AshtakavargaResult(
        bav=bav_results,
        sav=sav,
        strongest_house=strongest,
        weakest_house=weakest,
        average_sav=round(avg, 2),
    )


def calculate_ashtakavarga(jre_facts_packet: dict[str, Any]) -> AshtakavargaResult:
    """Calculate Ashtakavarga from a JRE facts packet.

    This is the primary adapter that bridges the JRE fact engine output
    to the Ashtakavarga calculation engine. The fact packet should contain
    a 'planets' key (or 'planet_details') with per-planet data including
    'house' positions.

    Args:
        jre_facts_packet: JRE facts dictionary with planet positions.
            Expected format:
            {
                "planets": {
                    "SUN": {"house": 1, ...},
                    ...
                }
            }
            OR:
            {
                "planet_details": {
                    "SUN": {"house": 1, ...},
                    ...
                }
            }

    Returns:
        AshtakavargaResult with BAV and SAV for all 7 planets.
    """
    # Extract planets from the facts packet
    # The JRE facts can use either 'planets' or 'planet_details' key
    planets_data = jre_facts_packet.get("planet_details") or jre_facts_packet.get("planets", {})

    # Normalize the planet data format for compute_ashtakavarga
    normalized_planets: dict[str, dict[str, Any]] = {}
    for planet, pdata in planets_data.items():
        # Skip nodes
        if planet in ("RAHU", "KETU"):
            continue
        # Normalize house field
        house = pdata.get("house", 0)
        if isinstance(house, int) and 1 <= house <= 12:
            normalized_planets[planet] = {"house": house}

    # Build the natal_data dict expected by compute_ashtakavarga
    natal_data = {"planets": normalized_planets}

    return compute_ashtakavarga(natal_data)


def ashtakavarga_to_dict(result: AshtakavargaResult) -> dict[str, Any]:
    """Convert AshtakavargaResult to JSON-serializable dict."""
    return {
        "bav": {
            name: {
                "planet": bav.planet,
                "bindus": {str(h): b for h, b in bav.bindus.items()},
                "total_bindus": bav.total_bindus,
            }
            for name, bav in result.bav.items()
        },
        "sav": {str(h): s for h, s in result.sav.items()},
        "strongest_house": result.strongest_house,
        "weakest_house": result.weakest_house,
        "average_sav": result.average_sav,
    }
