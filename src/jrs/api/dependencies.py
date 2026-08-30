"""JRE API — Dependency injection for service initialization.

Services are initialized once at startup via FastAPI lifespan events
to avoid re-initializing the heavy pipeline on every request.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

# Ensure src/ is on the path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# ── Path Constants ──────────────────────────────────────────────────────────

FIXTURES_DIR = (
    _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"
)

# ── Lazy Service Singletons ─────────────────────────────────────────────────

_yoga_evaluator = None
_jyotish_service = None


def get_yoga_evaluator():
    """Get or initialize the YogaEvaluatorService singleton."""
    global _yoga_evaluator
    if _yoga_evaluator is None:
        from jrs.yoga_evaluator.service import YogaEvaluatorService
        _yoga_evaluator = YogaEvaluatorService()
    return _yoga_evaluator


def get_jyotish_service():
    """Get or initialize the JyotishService singleton."""
    global _jyotish_service
    if _jyotish_service is None:
        from jyotish.service import JyotishService
        _jyotish_service = JyotishService()
    return _jyotish_service


# ── Fixture Loading ─────────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def load_fixture(fixture_id: str) -> dict[str, Any]:
    """Load a chart fixture by ID (cached).

    Args:
        fixture_id: Fixture filename without .json extension.
                    e.g., "chart_001_pilot" or "chart_001_pilot.json"

    Returns:
        Parsed fixture dictionary.

    Raises:
        FileNotFoundError: If fixture file doesn't exist.
        ValueError: If fixture JSON is malformed.
    """
    # Normalize: strip .json if provided
    if fixture_id.endswith(".json"):
        fixture_id = fixture_id[:-5]

    fixture_path = FIXTURES_DIR / f"{fixture_id}.json"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {fixture_path}. "
            f"Available fixtures: {[f.stem for f in sorted(FIXTURES_DIR.glob('chart_*.json'))]}"
        )

    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)


def list_fixtures() -> list[str]:
    """List all available fixture IDs."""
    return sorted(f.stem for f in FIXTURES_DIR.glob("chart_*.json"))


# ── Chart Computation ───────────────────────────────────────────────────────

def compute_chart_from_fixture(fixture: dict[str, Any]) -> Any:
    """Compute a natal chart from fixture birth data.

    Args:
        fixture: Loaded fixture dictionary with raw_birth_data.

    Returns:
        NatalChart from JyotishService.
    """
    from jyotish.models import BirthData

    raw = fixture["raw_birth_data"]
    svc = get_jyotish_service()
    birth = BirthData(
        date=raw["date"],
        time=raw["time"],
        timezone=raw["timezone"],
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
    )
    return svc.chart(birth)


def compute_chart_from_birth_data(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str,
) -> Any:
    """Compute a natal chart from raw birth data.

    Args:
        date: ISO date string (YYYY-MM-DD).
        time: ISO time string (HH:MM:SS).
        latitude: Decimal degrees.
        longitude: Decimal degrees.
        timezone: IANA timezone string.

    Returns:
        NatalChart from JyotishService.
    """
    from jyotish.models import BirthData

    svc = get_jyotish_service()
    birth = BirthData(
        date=date,
        time=time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
    )
    return svc.chart(birth)


# ── JRE Facts Builder ───────────────────────────────────────────────────────

def build_jre_facts(chart: Any) -> dict[str, Any]:
    """Build JRE facts dictionary from a natal chart.

    This replicates the logic from blind_evaluation_cohort._build_jre_facts
    to avoid importing the script directly.
    """
    from jyotish.rashi import RASHI_ORDER as JYOTISH_RASHI_ORDER

    _RASHI_NUM: dict[str, int] = {
        "MESHA": 1, "VRISHABHA": 2, "MITHUNA": 3, "KARKA": 4,
        "SIMHA": 5, "KANYA": 6, "TULA": 7, "VRISHCHIKA": 8,
        "DHANUSHA": 9, "MAKARA": 10, "KUMBHA": 11, "MEENA": 12,
    }

    _SIGN_LORDS: dict[int, str] = {
        1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
        6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
        11: "SATURN", 12: "JUPITER",
    }

    _SIGN_TYPES: dict[int, str] = {
        0: "fire", 1: "earth", 2: "air", 3: "water",
        4: "fire", 5: "earth", 6: "air", 7: "water",
        8: "fire", 9: "earth", 10: "air", 11: "water",
    }

    _RASHI_ORDER_LIST: list[str] = [
        "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
        "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
    ]

    def _compute_d9_sign(longitude_used: float) -> str:
        sign_index = int(longitude_used / 30.0)
        degree_in_sign = longitude_used - (sign_index * 30.0)
        navamsha_within_sign = int(degree_in_sign / (30.0 / 9.0))
        sign_type = _SIGN_TYPES[sign_index]
        if sign_type == "fire":
            start = sign_index
        elif sign_type == "earth":
            start = (sign_index + 5) % 12
        elif sign_type == "air":
            start = (sign_index + 4) % 12
        else:
            start = (sign_index + 8) % 12
        return _RASHI_ORDER_LIST[(start + navamsha_within_sign) % 12]

    _DEBILITATION = {
        "SUN": 7, "MOON": 8, "MARS": 4, "MERCURY": 12,
        "JUPITER": 10, "VENUS": 6, "SATURN": 1,
    }

    lagna_rashi = chart.lagna.rashi.value
    lagna_sign_num = _RASHI_NUM.get(lagna_rashi, 1)
    lagna_longitude = chart.lagna.ascendant_longitude_deg

    lagna_idx = list(JYOTISH_RASHI_ORDER).index(chart.lagna.rashi)
    house_lords: dict[int, str] = {}
    for i in range(12):
        rashi_idx = (lagna_idx + i) % 12
        rashi_name = list(JYOTISH_RASHI_ORDER)[rashi_idx]
        house_lords[i + 1] = _SIGN_LORDS.get(_RASHI_NUM.get(rashi_name, rashi_idx + 1), "")

    planets: dict[str, dict[str, Any]] = {}
    moon_nakshatra = ""
    moon_nakshatra_degree = 0.0

    for ps in chart.planet_states:
        pname = ps.body.value
        planet_rashi = ps.rashi.value
        planet_rashi_idx = list(JYOTISH_RASHI_ORDER).index(ps.rashi)
        house_num = (planet_rashi_idx - lagna_idx) % 12 + 1
        rashi_num = _RASHI_NUM.get(planet_rashi, 0)

        sun_state = next((s for s in chart.planet_states if s.body.value == "SUN"), None)
        is_combust = False
        if sun_state and pname != "SUN":
            diff = abs(ps.longitude_used - sun_state.longitude_used)
            if diff > 180:
                diff = 360 - diff
            is_combust = diff < 8.0

        planets[pname] = {
            "house": house_num,
            "rashi": planet_rashi,
            "rashi_num": rashi_num,
            "combust": is_combust,
            "debilitated": rashi_num == _DEBILITATION.get(pname, -1),
            "retrograde": ps.retrograde.value == "RETROGRADE",
            "longitude": ps.longitude_used,
            "sign_lord": _SIGN_LORDS.get(rashi_num, ""),
        }

        if pname == "MOON":
            moon_nakshatra = ps.nakshatra.value
            moon_nakshatra_degree = ps.longitude_used

    planet_d9_house: dict[str, int] = {}
    planet_d9_sign: dict[str, str] = {}
    for ps in chart.planet_states:
        pname = ps.body.value
        planet_d9_sign[pname] = _compute_d9_sign(ps.longitude_used)
        planet_d9_house[pname] = (
            (_RASHI_ORDER_LIST.index(planet_d9_sign[pname])
             - _RASHI_ORDER_LIST.index(_compute_d9_sign(lagna_longitude))) % 12 + 1
        )

    moon_data = planets.get("MOON", {})
    natal_moon_house = moon_data.get("house", 1)

    return {
        "planets": planets,
        "house_lords": house_lords,
        "lagna_sign": lagna_sign_num,
        "lagna_house": 1,
        "planet_d9_house": planet_d9_house,
        "planet_d9_sign": planet_d9_sign,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_nakshatra_degree,
        "natal_moon_house": natal_moon_house,
    }
