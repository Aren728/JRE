"""JRE API — Dependency injection for service initialization.

Services are initialized once at startup via FastAPI lifespan events
to avoid re-initializing the heavy pipeline on every request.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jrs.calculations.ashtakavarga import ashta_scoring_enabled
from jrs.calculations.gochara import gochara_scoring_enabled

if TYPE_CHECKING:
    from jyotish.service import JyotishService
    from jrs.yoga_evaluator.service import YogaEvaluatorService

# Ensure src/ is on the path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# ── Path Constants ──────────────────────────────────────────────────────────

FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"
_MODERN_FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "modern_personalities"

# ── Lazy Service Singletons ─────────────────────────────────────────────────

_yoga_evaluator = None
_jyotish_service = None


def get_yoga_evaluator() -> YogaEvaluatorService:
    """Get or initialize the YogaEvaluatorService singleton."""
    global _yoga_evaluator
    if _yoga_evaluator is None:
        from jrs.yoga_evaluator.service import YogaEvaluatorService

        _yoga_evaluator = YogaEvaluatorService()
    return _yoga_evaluator


def get_jyotish_service() -> JyotishService:
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

    # Search validation_charts first, then modern_personalities
    fixture_path = FIXTURES_DIR / f"{fixture_id}.json"
    if not fixture_path.exists() and _MODERN_FIXTURES_DIR.exists():
        fixture_path = _MODERN_FIXTURES_DIR / f"{fixture_id}.json"
    if not fixture_path.exists():
        available = sorted(f.stem for f in FIXTURES_DIR.glob("chart_*.json"))
        if _MODERN_FIXTURES_DIR.exists():
            available += sorted(f.stem for f in _MODERN_FIXTURES_DIR.glob("chart_*.json"))
        raise FileNotFoundError(f"Fixture not found: {fixture_id}. Available fixtures: {available}")

    with fixture_path.open(encoding="utf-8") as f:
        loaded: dict[str, Any] = json.load(f)
        return loaded


def list_fixtures() -> list[str]:
    """List all available fixture IDs."""
    fixtures = sorted(f.stem for f in FIXTURES_DIR.glob("chart_*.json"))
    if _MODERN_FIXTURES_DIR.exists():
        fixtures += sorted(f.stem for f in _MODERN_FIXTURES_DIR.glob("chart_*.json"))
    return fixtures


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


# Time values that indicate unknown or missing birth time
_UNKNOWN_TIME_VALUES = ("", "00:00", "00:00:00", "unknown", "UNKNOWN", "12:00:00")


def is_unknown_time(time_str: str) -> bool:
    """Check if a time string represents an unknown or missing birth time.

    Args:
        time_str: The time string to check.

    Returns:
        True if the time is missing, zero, or explicitly marked unknown.
    """
    normalized = time_str.strip().lower()
    return normalized in _UNKNOWN_TIME_VALUES or normalized == ""


def normalize_time(time_str: str) -> str:
    """Normalize a birth time string, returning noon for unknown times.

    Args:
        time_str: The input time string.

    Returns:
        '12:00:00' if the time is unknown, otherwise the original value.
    """
    if is_unknown_time(time_str):
        return "12:00:00"
    return time_str


def compute_chart_from_birth_data(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str,
) -> Any:
    """Compute a natal chart from raw birth data.

    If the time is unknown, noon (12:00:00) is used as a computational
    default for planetary positions. The Lagna will be approximate.

    Args:
        date: ISO date string (YYYY-MM-DD).
        time: ISO time string (HH:MM:SS). Empty or 'unknown' → noon default.
        latitude: Decimal degrees.
        longitude: Decimal degrees.
        timezone: IANA timezone string.

    Returns:
        NatalChart from JyotishService.
    """
    from jyotish.models import BirthData

    effective_time = normalize_time(time)
    svc = get_jyotish_service()
    birth = BirthData(
        date=date,
        time=effective_time,
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

    _SIGN_TYPES: dict[int, str] = {
        0: "fire",
        1: "earth",
        2: "air",
        3: "water",
        4: "fire",
        5: "earth",
        6: "air",
        7: "water",
        8: "fire",
        9: "earth",
        10: "air",
        11: "water",
    }

    _RASHI_ORDER_LIST: list[str] = [
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
        "SUN": 7,
        "MOON": 8,
        "MARS": 4,
        "MERCURY": 12,
        "JUPITER": 10,
        "VENUS": 6,
        "SATURN": 1,
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
            # Per-planet nakshatra facts (computed by the jyotish position
            # layer for every body — exact, not degree-approximated).
            "nakshatra": ps.nakshatra.value,
            "nakshatra_lord": ps.nakshatra_lord.value,
            "nakshatra_pada": int(ps.pada),
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
            _RASHI_ORDER_LIST.index(planet_d9_sign[pname])
            - _RASHI_ORDER_LIST.index(_compute_d9_sign(lagna_longitude))
        ) % 12 + 1

    moon_data = planets.get("MOON", {})
    natal_moon_house = moon_data.get("house", 1)

    # ── Arudha Pada Ladder (A1–A12) ─────────────────────────────────────
    # Classical Parashari rule (BPHS: Arudha computation / Jaimini sutras):
    # count from the house to its sign lord, then the same count onward from
    # the lord. Exception: if the pada lands in the house itself or the 7th
    # from it, take the 10th sign from the lord instead. A12 = Upapada Lagna.
    arudha_padas: dict[str, str] = {}
    planet_rashi_by_name: dict[str, str] = {
        p: d["rashi"] for p, d in planets.items() if d.get("rashi")
    }
    for house_num in range(1, 13):
        house_sign_idx = (lagna_idx + house_num - 1) % 12
        house_sign = _RASHI_ORDER_LIST[house_sign_idx]
        house_lord = _SIGN_LORDS.get(_RASHI_NUM.get(house_sign, house_sign_idx + 1), "")
        lord_sign = planet_rashi_by_name.get(house_lord, "")
        if not lord_sign:
            # Lord body missing from ephemeris (e.g. outer bodies excluded):
            # no classical pada can be derived — leave empty, never guess.
            arudha_padas[f"A{house_num}"] = ""
            continue
        lord_idx = _RASHI_ORDER_LIST.index(lord_sign)
        dist = (lord_idx - house_sign_idx) % 12 + 1
        pada_idx = (lord_idx + dist - 1) % 12
        if dist in (1, 7):
            pada_idx = (lord_idx + 9) % 12
        arudha_padas[f"A{house_num}"] = _RASHI_ORDER_LIST[pada_idx]

    # ── Build raw facts dict ──
    facts: dict[str, Any] = {
        "planets": planets,
        "house_lords": house_lords,
        "lagna_sign": lagna_sign_num,
        "lagna_house": 1,
        "lagna": _RASHI_ORDER_LIST[lagna_sign_num - 1],
        "planet_d9_house": planet_d9_house,
        "planet_d9_sign": planet_d9_sign,
        # Exact navamsha (D9) lagna sign, derived from the ascendant longitude
        # via the same _compute_d9_sign rule used for the planets.
        "navamsha_lagna": _compute_d9_sign(lagna_longitude),
        # Full Arudha ladder A1–A12 (sign names). A12 = Upapada Lagna.
        # Empty string = lord body unavailable, pada not derived.
        "arudha_padas": arudha_padas,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_nakshatra_degree,
        "natal_moon_house": natal_moon_house,
    }

    # ── Enrich with elemental/dignity/aspect data (Phase I6) ──
    try:
        from jrs.fact_enrichment import enrich_jre_facts

        facts = enrich_jre_facts(facts)
    except Exception:
        # Graceful fallback — enrichment is non-critical
        pass

    # ── Phase 5B: Ashtakavarga scoring facts (feature-flagged) ──
    # Injected ONLY when ashta_scoring_enabled() is on, so the frozen
    # benchmark baseline (Micro-F1 = 0.7435) cannot silently regress.
    # The golden-state 'ashtakavarga' stage records the pure calculation
    # report independently of this flag.
    if ashta_scoring_enabled():
        from jrs.calculations.ashtakavarga import (
            ashtakavarga_to_dict,
            compute_full_ashtakavarga,
        )

        facts["ashtakavarga"] = ashtakavarga_to_dict(
            compute_full_ashtakavarga(facts)
        )

    # ── Phase 5C: Gochara transit facts (feature-flagged) ──
    # Same gating discipline as 5B: injected only when enabled, evaluated
    # at the pinned epoch so the report is deterministic.
    if gochara_scoring_enabled():
        from jrs.calculations.gochara import (
            GOCHARA_TRANSIT_EPOCH,
            compute_gochara,
            compute_transit_positions,
            gochara_to_dict,
        )

        transit_positions = compute_transit_positions(
            date=GOCHARA_TRANSIT_EPOCH.strftime("%Y-%m-%d"),
            time=GOCHARA_TRANSIT_EPOCH.strftime("%H:%M:%S"),
            timezone="UTC",
            latitude=0.0,
            longitude=0.0,
        )
        facts["gochara"] = gochara_to_dict(
            compute_gochara(facts, transit_positions, epoch=GOCHARA_TRANSIT_EPOCH)
        )

    return facts
