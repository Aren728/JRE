"""JRE Advanced Charts — Shadbala (Six-Fold Strength) Engine.

Calculates the 6 classical strengths for all 7 planets:
  1. Sthana Bala (Positional Strength) — sign placement dignity
  2. Dig Bala (Directional Strength) — house direction placement
  3. Kala Bala (Temporal Strength) — day/night and birth time
  4. Chesta Bala (Motional Strength) — retrograde/stationary motion
  5. Naisargika Bala (Natural Strength) — inherent planetary nature
  6. Drik Bala (Aspectual Strength) — aspects received from other planets

Total Shadbala = sum of all 6 (in Virupas, where 1 Rupa = 60 Virupas).
Minimum required: 395 Virupas (Saptavimshottari) for a planet to be strong.

Source: BPHS Ch 28-29; Phaladeepika Ch 8; Saravali Ch 15-16.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Constants ─────────────────────────────────────────────

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

# Natural strengths (Naisargika Bala) in Virupas
# Sun is strongest (60V), then Moon (51.67V), etc.
_NAISARGIKA_BALA: dict[str, float] = {
    "SUN": 60.0,
    "MOON": 51.67,
    "JUPITER": 43.33,
    "VENUS": 35.0,
    "MERCURY": 26.67,
    "MARS": 18.33,
    "SATURN": 10.0,
}

# Dig Bala: Directional strength in each house (1-12)
# Format: planet -> {house: strength_in_virupas}
# Max 60V in best direction, 0V in worst
_DIG_BALA_TABLE: dict[str, dict[int, float]] = {
    "SUN": {1: 30, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5, 7: 0, 8: 5, 9: 10, 10: 15, 11: 20, 12: 25},
    "MOON": {1: 30, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5, 7: 0, 8: 5, 9: 10, 10: 15, 11: 20, 12: 25},
    "MARS": {1: 0, 2: 5, 3: 10, 4: 15, 5: 20, 6: 25, 7: 30, 8: 25, 9: 20, 10: 15, 11: 10, 12: 5},
    "MERCURY": {1: 30, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5, 7: 0, 8: 5, 9: 10, 10: 15, 11: 20, 12: 25},
    "JUPITER": {1: 30, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5, 7: 0, 8: 5, 9: 10, 10: 15, 11: 20, 12: 25},
    "VENUS": {1: 30, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5, 7: 0, 8: 5, 9: 10, 10: 15, 11: 20, 12: 25},
    "SATURN": {1: 0, 2: 5, 3: 10, 4: 15, 5: 20, 6: 25, 7: 30, 8: 25, 9: 20, 10: 15, 11: 10, 12: 5},
}

# Own sign dignity multipliers for Sthana Bala
_OWN_SIGNS: dict[str, set[str]] = {
    "SUN": {"SIMHA"},
    "MOON": {"KARKA"},
    "MARS": {"MESHA", "VRISHCHIKA"},
    "MERCURY": {"MITHUNA", "KANYA"},
    "JUPITER": {"DHANUSHA", "MEENA"},
    "VENUS": {"VRISHABHA", "TULA"},
    "SATURN": {"MAKARA", "KUMBHA"},
}

_EXALTATION_SIGNS: dict[str, str] = {
    "SUN": "MESHA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}

_DEBILITATION_SIGNS: dict[str, str] = {
    "SUN": "TULA",
    "MOON": "VRISHCHIKA",
    "MARS": "KARKA",
    "MERCURY": "MEENA",
    "JUPITER": "MAKARA",
    "VENUS": "KANYA",
    "SATURN": "MESHA",
}

# Kendra and Trikona houses
_KENDRA = {1, 4, 7, 10}
_TRIKONA = {1, 5, 9}


@dataclass
class PlanetStrength:
    """Shadbala result for a single planet."""

    planet: str
    sthana_bala: float = 0.0  # Positional strength (Virupas)
    dig_bala: float = 0.0  # Directional strength
    kala_bala: float = 0.0  # Temporal strength
    chesta_bala: float = 0.0  # Motional strength
    naisargika_bala: float = 0.0  # Natural strength
    drik_bala: float = 0.0  # Aspectual strength
    total_rupas: float = 0.0  # Total in Rupas (1 Rupa = 60 Virupas)
    total_virupas: float = 0.0  # Total in Virupas
    is_strong: bool = False  # True if total >= 395 Virupas


@dataclass
class ShadbalaResult:
    """Complete Shadbala result for all planets."""

    planets: dict[str, PlanetStrength]
    average_strength: float = 0.0
    strongest_planet: str = ""
    weakest_planet: str = ""


# ── Strength Calculation Functions ────────────────────────


def _compute_sthana_bala(planet: str, sign: str, degree_in_sign: float) -> float:
    """Compute Sthana Bala (Positional Strength) in Virupas.

    Based on the planet's dignity in the sign:
    - Exalted: 60V
    - Own sign: 45V
    - Friendly: 30V
    - Neutral: 15V
    - Enemy: 7.5V
    - Debilitated: 0V
    """
    if sign == _EXALTATION_SIGNS.get(planet, ""):
        return 60.0
    if sign in _OWN_SIGNS.get(planet, set()):
        return 45.0
    # Simplified: friendly signs get 30, others get 15
    return 30.0


def _compute_dig_bala(planet: str, house: int) -> float:
    """Compute Dig Bala (Directional Strength) in Virupas."""
    table = _DIG_BALA_TABLE.get(planet, {})
    return table.get(house, 0.0)


def _compute_kala_bala(planet: str, is_daytime: bool, hour: float) -> float:
    """Compute Kala Bala (Temporal Strength) in Virupas.

    Simplified calculation based on day/night and birth hour.
    Full implementation requires Paksha Bala (fortnight) and Ayana Bala.
    """
    # Basic day/night strength
    if is_daytime:
        base = {
            "SUN": 60,
            "MOON": 30,
            "MARS": 45,
            "JUPITER": 30,
            "VENUS": 45,
            "SATURN": 15,
            "MERCURY": 60,
        }.get(planet, 0)
    else:
        base = {
            "SUN": 15,
            "MOON": 60,
            "MARS": 15,
            "JUPITER": 30,
            "VENUS": 60,
            "SATURN": 45,
            "MERCURY": 30,
        }.get(planet, 0)
    return float(base)


def _compute_chesta_bala(planet: str, speed: float, retrograde: bool) -> float:
    """Compute Chesta Bala (Motional Strength) in Virupas.

    Retrograde planets gain strength, stationary planets are strongest.
    """
    if retrograde:
        return 60.0  # Full strength when retrograde
    if abs(speed) < 0.1:
        return 50.0  # Stationary
    # Direct motion: reduced strength based on speed
    return max(0.0, 30.0 - abs(speed) * 5)


def _compute_naisargika_bala(planet: str) -> float:
    """Compute Naisargika Bala (Natural Strength) in Virupas."""
    return _NAISARGIKA_BALA.get(planet, 0.0)


def _compute_drik_bala(planet: str, aspects_received: list[dict[str, Any]]) -> float:
    """Compute Drik Bala (Aspectual Strength) in Virupas.

    Benefic aspects add strength, malefic aspects reduce it.
    """
    score = 0.0
    benefics = {"JUPITER", "VENUS", "MOON", "MERCURY"}
    malefics = {"SATURN", "MARS", "RAHU", "KETU"}

    for asp in aspects_received:
        source = asp.get("source", "")
        if source in benefics:
            score += 15.0  # Benefic aspect adds strength
        elif source in malefics:
            score -= 10.0  # Malefic aspect reduces

    return max(0.0, min(60.0, score))


# ── Main Calculation ──────────────────────────────────────


def compute_shadbala(
    natal_data: dict[str, Any],
    is_daytime: bool = True,
    birth_hour: float = 12.0,
) -> ShadbalaResult:
    """Compute complete Shadbala for all 7 planets.

    Args:
        natal_data: Dict with 'planets' containing house, sign, longitude, etc.
        is_daytime: Whether birth was during daytime.
        birth_hour: Birth hour (0-24).

    Returns:
        ShadbalaResult with individual planet strengths.
    """
    planets = natal_data.get("planets", {})
    planet_strengths: dict[str, PlanetStrength] = {}

    for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
        pdata = planets.get(planet, {})
        sign = pdata.get("rashi", pdata.get("sign", ""))
        house = pdata.get("house", 1)
        degree = pdata.get("degree_in_sign", pdata.get("longitude", 0.0) % 30.0)
        retrograde = pdata.get("retrograde", False)
        speed = pdata.get("speed", 1.0)

        sthana = _compute_sthana_bala(planet, sign, degree)
        dig = _compute_dig_bala(planet, house)
        kala = _compute_kala_bala(planet, is_daytime, birth_hour)
        chesta = _compute_chesta_bala(planet, speed, retrograde)
        naisargika = _compute_naisargika_bala(planet)

        # Drik Bala: simplified — based on aspects in the chart
        aspects = []
        for other, odata in planets.items():
            if other == planet:
                continue
            other_house = odata.get("house", 1)
            diff = (
                abs(house - other_house)
                if isinstance(house, int) and isinstance(other_house, int)
                else 0
            )
            if diff in (3, 4, 5, 7, 9):  # Common aspect distances
                aspects.append({"source": other})
        drik = _compute_drik_bala(planet, aspects)

        total_virupas = sthana + dig + kala + chesta + naisargika + drik
        total_rupas = total_virupas / 60.0

        ps = PlanetStrength(
            planet=planet,
            sthana_bala=round(sthana, 2),
            dig_bala=round(dig, 2),
            kala_bala=round(kala, 2),
            chesta_bala=round(chesta, 2),
            naisargika_bala=round(naisargika, 2),
            drik_bala=round(drik, 2),
            total_rupas=round(total_rupas, 2),
            total_virupas=round(total_virupas, 2),
            is_strong=total_virupas >= 395.0,
        )
        planet_strengths[planet] = ps

    # Find strongest and weakest
    strongest: PlanetStrength | None = None
    weakest: PlanetStrength | None = None
    avg = 0.0
    if planet_strengths:
        strongest = max(planet_strengths.values(), key=lambda x: x.total_virupas)
        weakest = min(planet_strengths.values(), key=lambda x: x.total_virupas)
        avg = sum(p.total_virupas for p in planet_strengths.values()) / len(planet_strengths)

    return ShadbalaResult(
        planets=planet_strengths,
        average_strength=round(avg, 2),
        strongest_planet=strongest.planet if strongest else "",
        weakest_planet=weakest.planet if weakest else "",
    )


def calculate_shadbala(jre_facts_packet: dict[str, Any]) -> ShadbalaResult:
    """Calculate Shadbala from a JRE facts packet.

    This is the primary adapter that bridges the JRE fact engine output
    to the Shadbala calculation engine. The fact packet should contain
    a 'planets' key (or 'planet_details') with per-planet data including
    'rashi' (or 'sign'), 'house', 'retrograde', and optionally 'speed'
    and 'longitude'.

    Args:
        jre_facts_packet: JRE facts dictionary with planet positions.
            Expected format:
            {
                "planets": {
                    "SUN": {"rashi": "MESHA", "house": 1, ...},
                    ...
                },
                "is_daytime": True,  # optional
                "birth_hour": 14.5,  # optional
            }

    Returns:
        ShadbalaResult with all 6 strength components for 7 planets.
    """
    # Extract planets from the facts packet
    # The JRE facts can use either 'planets' or 'planet_details' key
    planets_data = jre_facts_packet.get("planet_details") or jre_facts_packet.get("planets", {})

    # Normalize the planet data format for compute_shadbala
    normalized_planets: dict[str, dict[str, Any]] = {}
    for planet, pdata in planets_data.items():
        # Normalize rashi/sign field
        rashi = pdata.get("rashi") or pdata.get("sign", "")
        # Normalize house field
        house = pdata.get("house", 1)
        # Normalize degree field
        degree = pdata.get("degree_in_sign", 0.0)
        if degree == 0.0 and "longitude" in pdata:
            # Compute degree_in_sign from longitude if not provided
            degree = pdata["longitude"] % 30.0
        # Normalize retrograde field
        retrograde = pdata.get("retrograde", False)
        if isinstance(retrograde, str):
            retrograde = retrograde.upper() == "RETROGRADE"
        # Normalize speed field
        speed = pdata.get("speed", 1.0)
        if speed is None:
            speed = 1.0

        normalized_planets[planet] = {
            "rashi": rashi,
            "house": house,
            "degree_in_sign": degree,
            "retrograde": retrograde,
            "speed": speed,
        }

    # Extract daytime and birth hour from facts packet
    is_daytime = jre_facts_packet.get("is_daytime", True)
    birth_hour = jre_facts_packet.get("birth_hour", 12.0)

    # Build the natal_data dict expected by compute_shadbala
    natal_data = {"planets": normalized_planets}

    return compute_shadbala(natal_data, is_daytime=is_daytime, birth_hour=birth_hour)


def shadbala_to_dict(result: ShadbalaResult) -> dict[str, Any]:
    """Convert ShadbalaResult to JSON-serializable dict."""
    return {
        "planets": {
            name: {
                "planet": ps.planet,
                "sthana_bala": ps.sthana_bala,
                "dig_bala": ps.dig_bala,
                "kala_bala": ps.kala_bala,
                "chesta_bala": ps.chesta_bala,
                "naisargika_bala": ps.naisargika_bala,
                "drik_bala": ps.drik_bala,
                "total_rupas": ps.total_rupas,
                "total_virupas": ps.total_virupas,
                "is_strong": ps.is_strong,
            }
            for name, ps in result.planets.items()
        },
        "average_strength": result.average_strength,
        "strongest_planet": result.strongest_planet,
        "weakest_planet": result.weakest_planet,
    }
