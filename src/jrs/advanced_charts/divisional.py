"""JRE Advanced Charts — Divisional Chart Engine (D1–D16).

Computes planetary positions for all major divisional charts (Vargas)
from natal longitudes using classical Vedic math.

Divisional charts map the same 360° zodiac into finer subdivisions,
each governing specific life domains:
  D1 (Rashi) — Self, physical body
  D2 (Hora) — Wealth
  D3 (Drekkana) — Siblings, courage
  D4 (Tritiya Dreshkan/Chaturthamsha) — Fortune, property
  D7 (Saptamamsha) — Progeny
  D9 (Navamsha) — Marriage, dharma, spiritual strength
  D10 (Dashamsha) — Career, profession
  D12 (Dwadashamsha) — Parents, inheritance
  D16 (Shodashamsha) — Vehicles, comforts, happiness

Source: BPHS Ch 6-7; Jataka Parijata Ch 2; Phaladeepika Ch 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# ── Sign Constants ────────────────────────────────────────

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

SIGN_NAMES: dict[str, str] = {
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

# Sign type classification (odd/even for D2/D3/D4 calculations)
_ODD_SIGNS = {"MESHA", "MITHUNA", "SIMHA", "TULA", "DHANUSHA", "KUMBHA"}
_EVEN_SIGNS = {"VRISHABHA", "KARKA", "KANYA", "VRISHCHIKA", "MAKARA", "MEENA"}


# ── Data Structures ───────────────────────────────────────


@dataclass
class DivisionalPlanet:
    """Planet position in a divisional chart."""

    planet: str
    longitude: float  # Full longitude in D1 (0-360)
    divisional_longitude: float  # Computed divisional longitude (0-360)
    rashi: str  # Rashi in the divisional chart
    rashi_index: int  # 0-11
    degree_in_sign: float  # 0-30
    house: int  # House number (1-12) from divisional lagna


@dataclass
class DivisionalChart:
    """Complete divisional chart result."""

    division: int  # D1, D2, D3, etc.
    name: str  # "Rashi", "Hora", etc.
    description: str  # Life domain governed
    planets: dict[str, DivisionalPlanet]
    lagna: str  # Lagna rashi in this division
    lagna_house: int  # Always 1
    vargottama_planets: tuple[str, ...] = ()  # Planets with same sign in D1 and this division


# ── Divisional Chart Metadata ─────────────────────────────

CHART_META: dict[int, dict[str, str]] = {
    1: {"name": "Rashi (D1)", "desc": "Self, physical body, overall life"},
    2: {"name": "Hora (D2)", "desc": "Wealth, financial fortune"},
    3: {"name": "Drekkana (D3)", "desc": "Siblings, courage, initiative"},
    4: {"name": "Chaturthamsha (D4)", "desc": "Fortune, property, mother"},
    7: {"name": "Saptamamsha (D7)", "desc": "Progeny, creativity, partnership"},
    9: {"name": "Navamsha (D9)", "desc": "Marriage, dharma, spiritual strength"},
    10: {"name": "Dashamsha (D10)", "desc": "Career, profession, public life"},
    12: {"name": "Dwadashamsha (D12)", "desc": "Parents, inheritance, ancestry"},
    16: {"name": "Shodashamsha (D16)", "desc": "Vehicles, comforts, happiness"},
    20: {"name": "Vimshamsha (D20)", "desc": "Spiritual practices, religious inclinations"},
    24: {"name": "Saptavimshamsha (D24)", "desc": "Education, learning, knowledge"},
    27: {"name": "Trimsamsha (D27)", "desc": "Strength, vigor, vitality"},
    30: {"name": "Trishamsha (D30)", "desc": "Misfortunes, obstacles, fears"},
    40: {"name": "Khavedamsha (D40)", "desc": "Maternal legacy, auspiciousness"},
    45: {"name": "Akshavedamsha (D45)", "desc": "Paternal legacy, overall fortune"},
    60: {"name": "Shashtiamsha (D60)", "desc": "Past life karma, overall destiny"},
}


# ── Divisional Calculation Functions ──────────────────────


def _d2_hora(longitude: float) -> float:
    """Calculate D2 (Hora) longitude.

    D2 splits each sign into two halves:
    - Odd signs (MESHA, MITHUNA, etc.): first half → MESHA, second half → VRISHABHA
    - Even signs (VRISHABHA, KARKA, etc.): first half → VRISHABHA, second half → MESHA

    Returns longitude in the Hora chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    sign_name = SIGN_ORDER[sign_idx % 12]

    # Each hora is 15° wide
    hora_in_sign = int(deg_in_sign / 15.0)

    if sign_name in _ODD_SIGNS:
        # Odd sign: first hora → MESHA (0°), second hora → VRISHABHA (30°)
        hora_sign = 0 if hora_in_sign == 0 else 1
    else:
        # Even sign: first hora → VRISHABHA (30°), second hora → MESHA (0°)
        hora_sign = 1 if hora_in_sign == 0 else 0

    return float(hora_sign * 30.0 + (deg_in_sign % 15.0) * 2.0)


def _d3_drekkana(longitude: float) -> float:
    """Calculate D3 (Drekkana) longitude.

    Each sign is divided into 3 equal parts of 10° each.
    - 1st drekkana: same sign
    - 2nd drekkana: 5th from that sign
    - 3rd drekkana: 9th from that sign

    Returns longitude in the Drekkana chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)

    drekkana_in_sign = int(deg_in_sign / 10.0)

    # Offset: 0, 4, 8 (for 1st, 2nd, 3rd drekkana)
    offset = drekkana_in_sign * 4
    result_sign = (sign_idx + offset) % 12
    result_deg = (deg_in_sign % 10.0) * 3.0  # Scale 0-10 to 0-30

    return float(result_sign * 30.0 + result_deg)


def _d4_chaturthamsha(longitude: float) -> float:
    """Calculate D4 (Chaturthamsha/Tritiya Dreshkan) longitude.

    Each sign is divided into 4 equal parts of 7.5° each.
    - 1st: same sign
    - 2nd: 4th from that sign
    - 3rd: 8th from that sign
    - 4th: 12th (same sign again, but 2nd half)

    Returns longitude in the Chaturthamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)

    dreshkan_in_sign = int(deg_in_sign / 7.5)
    offset = dreshkan_in_sign * 3
    result_sign = (sign_idx + offset) % 12
    result_deg = (deg_in_sign % 7.5) * 4.0  # Scale 0-7.5 to 0-30

    return float(result_sign * 30.0 + result_deg)


def _d7_saptamamsha(longitude: float) -> float:
    """Calculate D7 (Saptamamsha) longitude.

    The starting point depends on the sign:
    - Odd signs (MESHA, etc.): start from the sign itself
    - Even signs (VRISHABHA, etc.): start from the 7th from the sign

    Each portion is 30/7 ≈ 4.286°

    Returns longitude in the Saptamamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    sign_name = SIGN_ORDER[sign_idx % 12]

    portion_size = 30.0 / 7.0
    portion_in_sign = int(deg_in_sign / portion_size)

    if sign_name in _ODD_SIGNS:
        result_sign = (sign_idx + portion_in_sign) % 12
    else:
        result_sign = (sign_idx + 6 + portion_in_sign) % 12

    result_deg = (deg_in_sign % portion_size) * 7.0  # Scale to 0-30

    return float(result_sign * 30.0 + result_deg)


def _d9_navamsha(longitude: float) -> float:
    """Calculate D9 (Navamsha) longitude.

    Each sign is divided into 9 equal parts of 3°20' each.
    Starting sign depends on the sign type:
    - MESHA (odd): starts from MESHA
    - VRISHABHA (even): starts from TULA (7th)

    Returns longitude in the Navamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    sign_name = SIGN_ORDER[sign_idx % 12]

    navamsha_size = 30.0 / 9.0
    nav_in_sign = int(deg_in_sign / navamsha_size)

    if sign_name in _ODD_SIGNS:
        result_sign = (sign_idx + nav_in_sign) % 12
    else:
        result_sign = (sign_idx + 6 + nav_in_sign) % 12

    result_deg = (deg_in_sign % navamsha_size) * 9.0  # Scale to 0-30

    return float(result_sign * 30.0 + result_deg)


def _d10_dashamsha(longitude: float) -> float:
    """Calculate D10 (Dashamsha) longitude.

    Each sign is divided into 10 parts of 3° each.
    Starting point depends on the sign lord:
    - Sun/Leo signs: start from MESHA
    - Other signs: start from the 9th from the sign lord's sign

    Returns longitude in the Dashamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)

    dashamsha_size = 30.0 / 10.0
    dash_in_sign = int(deg_in_sign / dashamsha_size)

    # Simplified: start from the sign itself for all signs
    # Classical rules use sign lord, but this is a reasonable approximation
    result_sign = (sign_idx + dash_in_sign) % 12
    result_deg = (deg_in_sign % dashamsha_size) * 10.0

    return float(result_sign * 30.0 + result_deg)


def _d12_dwadashamsha(longitude: float) -> float:
    """Calculate D12 (Dwadashamsha) longitude.

    Each sign is divided into 12 equal parts of 2°30' each.
    Each portion maps to the same sign (MESHA→MESHA, VRISHABHA→VRISHABHA, etc.)

    Returns longitude in the Dwadashamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)

    dwad_size = 30.0 / 12.0
    dwad_in_sign = int(deg_in_sign / dwad_size)

    result_sign = (sign_idx + dwad_in_sign) % 12
    result_deg = (deg_in_sign % dwad_size) * 12.0

    return float(result_sign * 30.0 + result_deg)


def _d16_shodashamsha(longitude: float) -> float:
    """Calculate D16 (Shodashamsha) longitude.

    Each sign is divided into 16 parts of 1°52'30" each.
    Starting point depends on sign position (odd/even within odd/even quadrant).

    Returns longitude in the Shodashamsha chart (0-360).
    """
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)

    shodash_size = 30.0 / 16.0
    shodash_in_sign = int(deg_in_sign / shodash_size)

    # Simplified mapping
    result_sign = (sign_idx + shodash_in_sign // 4) % 12
    result_deg = (deg_in_sign % shodash_size) * 16.0

    return float(result_sign * 30.0 + result_deg)


def _d20_vimshamsha(longitude: float) -> float:
    """Calculate D20 (Vimshamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 20.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 20.0
    return float(result_sign * 30.0 + result_deg)


def _d24_saptavimshamsha(longitude: float) -> float:
    """Calculate D24 (Saptavimshamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 24.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 24.0
    return float(result_sign * 30.0 + result_deg)


def _d27_trimsamsha(longitude: float) -> float:
    """Calculate D27 (Trimsamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 27.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 27.0
    return float(result_sign * 30.0 + result_deg)


def _d30_trishamsha(longitude: float) -> float:
    """Calculate D30 (Trishamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 30.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 30.0
    return float(result_sign * 30.0 + result_deg)


def _d40_khavedamsha(longitude: float) -> float:
    """Calculate D40 (Khavedamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 40.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 40.0
    return float(result_sign * 30.0 + result_deg)


def _d45_akshavedamsha(longitude: float) -> float:
    """Calculate D45 (Akshavedamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 45.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 45.0
    return float(result_sign * 30.0 + result_deg)


def _d60_shashtiamsha(longitude: float) -> float:
    """Calculate D60 (Shashtiamsha) longitude."""
    sign_idx = int(longitude / 30.0)
    deg_in_sign = longitude - (sign_idx * 30.0)
    size = 30.0 / 60.0
    part = int(deg_in_sign / size)
    result_sign = (sign_idx + part) % 12
    result_deg = (deg_in_sign % size) * 60.0
    return float(result_sign * 30.0 + result_deg)


# ── Divisional Calculator Map ─────────────────────────────

_DIVISION_CALCULATORS: dict[int, Callable[[float], float]] = {
    2: _d2_hora,
    3: _d3_drekkana,
    4: _d4_chaturthamsha,
    7: _d7_saptamamsha,
    9: _d9_navamsha,
    10: _d10_dashamsha,
    12: _d12_dwadashamsha,
    16: _d16_shodashamsha,
    20: _d20_vimshamsha,
    24: _d24_saptavimshamsha,
    27: _d27_trimsamsha,
    30: _d30_trishamsha,
    40: _d40_khavedamsha,
    45: _d45_akshavedamsha,
    60: _d60_shashtiamsha,
}


def compute_divisional_chart(
    natal_longitudes: dict[str, float],
    lagna_longitude: float,
    division: int,
) -> DivisionalChart:
    """Compute a divisional chart from natal longitudes.

    Args:
        natal_longitudes: Dict of planet name -> ecliptic longitude (0-360).
        lagna_longitude: Lagna (ascendant) longitude.
        division: Division number (1, 2, 3, 4, 7, 9, 10, 12, 16, etc.).

    Returns:
        DivisionalChart with all planet positions in the division.
    """
    meta = CHART_META.get(
        division, {"name": f"D{division}", "desc": f"Divisional Chart {division}"}
    )

    # D1 is just the natal chart
    if division == 1:
        planets = {}
        for planet, lon in natal_longitudes.items():
            sign_idx = int(lon / 30.0)
            rashi = SIGN_ORDER[sign_idx % 12]
            deg_in_sign = lon - (sign_idx * 30.0)
            lagna_sign_idx = int(lagna_longitude / 30.0)
            house = ((sign_idx - lagna_sign_idx) % 12) + 1

            planets[planet] = DivisionalPlanet(
                planet=planet,
                longitude=lon,
                divisional_longitude=lon,
                rashi=rashi,
                rashi_index=sign_idx % 12,
                degree_in_sign=round(deg_in_sign, 2),
                house=house,
            )

        lagna_sign_idx = int(lagna_longitude / 30.0)
        return DivisionalChart(
            division=1,
            name=meta["name"],
            description=meta["desc"],
            planets=planets,
            lagna=SIGN_ORDER[lagna_sign_idx % 12],
            lagna_house=1,
        )

    # Get the calculator for this division
    calc_func = _DIVISION_CALCULATORS.get(division)
    if not calc_func:
        raise ValueError(f"Divisional chart D{division} not yet implemented")

    # Calculate divisional longitudes
    div_longitudes = {}
    for planet, lon in natal_longitudes.items():
        div_longitudes[planet] = calc_func(lon)

    # Calculate divisional lagna
    div_lagna = calc_func(lagna_longitude)

    # Build planet positions
    planets = {}
    d1_signs = {}  # Track D1 signs for vargottama detection

    for planet, div_lon in div_longitudes.items():
        natal_lon = natal_longitudes[planet]
        sign_idx = int(div_lon / 30.0)
        rashi = SIGN_ORDER[sign_idx % 12]
        deg_in_sign = div_lon - (sign_idx * 30.0)

        # House from divisional lagna
        lagna_sign_idx = int(div_lagna / 30.0)
        house = ((sign_idx - lagna_sign_idx) % 12) + 1

        # D1 sign for vargottama
        d1_sign_idx = int(natal_lon / 30.0)
        d1_signs[planet] = SIGN_ORDER[d1_sign_idx % 12]

        planets[planet] = DivisionalPlanet(
            planet=planet,
            longitude=natal_lon,
            divisional_longitude=round(div_lon, 4),
            rashi=rashi,
            rashi_index=sign_idx % 12,
            degree_in_sign=round(deg_in_sign, 2),
            house=house,
        )

    # Detect vargottama planets (same sign in D1 and this division)
    vargottama = tuple(p for p, dp in planets.items() if dp.rashi == d1_signs.get(p))

    lagna_sign = SIGN_ORDER[int(div_lagna / 30.0) % 12]

    return DivisionalChart(
        division=division,
        name=meta["name"],
        description=meta["desc"],
        planets=planets,
        lagna=lagna_sign,
        lagna_house=1,
        vargottama_planets=vargottama,
    )


def compute_all_divisional_charts(
    natal_longitudes: dict[str, float],
    lagna_longitude: float,
    divisions: list[int] | None = None,
) -> dict[int, DivisionalChart]:
    """Compute multiple divisional charts at once.

    Args:
        natal_longitudes: Dict of planet name -> ecliptic longitude.
        lagna_longitude: Lagna longitude.
        divisions: List of division numbers to compute (default: all supported).

    Returns:
        Dict of division number -> DivisionalChart.
    """
    if divisions is None:
        divisions = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    charts = {}
    for div in divisions:
        try:
            charts[div] = compute_divisional_chart(natal_longitudes, lagna_longitude, div)
        except (ValueError, KeyError):
            continue  # Skip unsupported divisions

    return charts


def calculate_divisional_positions(
    jre_facts_packet: dict[str, Any],
    divisional_type: str,
) -> DivisionalChart:
    """Calculate divisional chart positions from a JRE facts packet.

    This is the primary adapter that bridges the JRE fact engine output
    to the Divisional Chart calculation engine. The fact packet should contain
    planet longitudes (or 'planet_details' with longitude data).

    Args:
        jre_facts_packet: JRE facts dictionary with planet positions.
            Expected format:
            {
                "planets": {
                    "SUN": {"longitude": 15.0, ...},
                    ...
                },
                "lagna_longitude": 100.0  # optional, computed from lagna
            }
            OR:
            {
                "planet_details": {
                    "SUN": {"longitude": 15.0, ...},
                    ...
                }
            }

        divisional_type: Division identifier as string (e.g., "D9", "D1", "D10").
            Supports: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27,
            D30, D40, D45, D60.

    Returns:
        DivisionalChart with all planet positions in the requested division.

    Raises:
        ValueError: If divisional_type is invalid or not supported.
    """
    # Parse divisional type (e.g., "D9" -> 9, "9" -> 9, "D10" -> 10)
    division_str = divisional_type.upper().strip()
    if division_str.startswith("D"):
        division_str = division_str[1:]
    try:
        division = int(division_str)
    except ValueError:
        raise ValueError(
            f"Invalid divisional type: {divisional_type}. Use format like 'D9', '9', 'D10', etc."
        )

    if division not in CHART_META:
        supported = sorted(CHART_META.keys())
        raise ValueError(
            f"Divisional chart D{division} not supported. Supported divisions: {supported}"
        )

    # Extract planet longitudes from the facts packet
    # Priority: planets (raw with longitude) > planet_details (enriched)
    planets_data = jre_facts_packet.get("planets") or jre_facts_packet.get("planet_details", {})

    # Build natal longitudes dict
    natal_longitudes: dict[str, float] = {}
    for planet, pdata in planets_data.items():
        if planet in ("RAHU", "KETU"):
            continue  # Skip nodes for divisional charts
        longitude = pdata.get("longitude")
        if longitude is not None:
            natal_longitudes[planet] = float(longitude)

    if not natal_longitudes:
        raise ValueError(
            "No planet longitudes found in the facts packet. Ensure planets have 'longitude' field."
        )

    # Extract lagna longitude
    lagna_longitude = jre_facts_packet.get("lagna_longitude")
    if lagna_longitude is None:
        # Try to compute from lagna_sign if available
        lagna_sign = jre_facts_packet.get("lagna_sign")
        if lagna_sign is not None:
            # Map sign number to approximate longitude (midpoint)
            if isinstance(lagna_sign, int):
                lagna_longitude = (lagna_sign - 1) * 30.0 + 15.0
            elif isinstance(lagna_sign, str):
                # Map sign name to index
                sign_idx = SIGN_ORDER.index(lagna_sign) if lagna_sign in SIGN_ORDER else 0
                lagna_longitude = sign_idx * 30.0 + 15.0

    if lagna_longitude is None:
        # Default to 0° Aries if no lagna info
        lagna_longitude = 0.0

    return compute_divisional_chart(natal_longitudes, lagna_longitude, division)


def divisional_chart_to_dict(chart: DivisionalChart) -> dict[str, Any]:
    """Convert DivisionalChart to a JSON-serializable dictionary."""
    return {
        "division": chart.division,
        "name": chart.name,
        "description": chart.description,
        "lagna": chart.lagna,
        "lagna_name": SIGN_NAMES.get(chart.lagna, chart.lagna),
        "vargottama_planets": list(chart.vargottama_planets),
        "planets": {
            name: {
                "planet": p.planet,
                "natal_longitude": round(p.longitude, 4),
                "divisional_longitude": round(p.divisional_longitude, 4),
                "rashi": p.rashi,
                "rashi_name": SIGN_NAMES.get(p.rashi, p.rashi),
                "degree_in_sign": p.degree_in_sign,
                "house": p.house,
            }
            for name, p in chart.planets.items()
        },
    }
