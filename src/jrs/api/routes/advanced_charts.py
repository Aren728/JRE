"""
src/jrs/api/routes/advanced_charts.py

FastAPI endpoints exposing the Advanced Charts engines (divisional vargas,
Shadbala, Ashtakavarga) for the JRE frontend report tabs.

Response shapes match frontend/lib/api.ts:
  - DivisionalChartResponse  (division, name, description, lagna, lagna_name,
    vargottama_planets, planets{planet: DivisionalPlanetData})
  - ShadbalaResponse         (planets{PlanetStrength}, average_strength,
    strongest_planet, weakest_planet)
  - AshtakavargaResponse     (bav{BAVData}, sav, strongest_house,
    weakest_house, average_sav)

Each endpoint accepts either `fixture_id` or raw birth data
(date/time/latitude/longitude/timezone), mirroring /api/v1/evaluate/*.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, Depends

from jrs.api.auth import check_rate_limit, get_key_hash
from jrs.api.logging_config import log_request
from jrs.advanced_charts.ashtakavarga import (
    ashtakavarga_to_dict,
    calculate_ashtakavarga,
)
from jrs.advanced_charts.divisional import (
    calculate_divisional_positions,
    divisional_chart_to_dict,
)
from jrs.advanced_charts.shadbala import (
    calculate_shadbala,
    shadbala_to_dict,
)

router = APIRouter(prefix="/api/v1/advanced", tags=["Advanced Charts"])

# All 16 classical vargas supported by the divisional engine (D1–D60).
SUPPORTED_DIVISIONS = (1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)


# ── Shared helpers ──────────────────────────────────────────────────────────


async def _build_facts(
    request: Request,
    endpoint: str,
    fixture_id: Optional[str],
    date: Optional[str],
    time: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> dict[str, Any]:
    """Build the JRE facts packet from fixture_id or raw birth data.

    Raises HTTPException 422 with a helpful message when inputs are missing
    or chart computation fails. Also injects lagna longitude and daytime
    context used by the Shadbala engine.
    """
    from jrs.api.dependencies import (
        build_jre_facts,
        compute_chart_from_birth_data,
        compute_chart_from_fixture,
        is_unknown_time,
        load_fixture,
    )

    try:
        if fixture_id:
            fixture = load_fixture(fixture_id)
            chart = compute_chart_from_fixture(fixture)
        elif date and latitude is not None and longitude is not None and timezone:
            effective_time = time or ""
            if is_unknown_time(effective_time):
                effective_time = "12:00:00"
            chart = compute_chart_from_birth_data(
                date=date,
                time=effective_time,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Provide either fixture_id or full birth data "
                    "(date, time, latitude, longitude, timezone)."
                ),
            )
        facts = build_jre_facts(chart)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Chart computation failed: {e}")

    # Enrich with data the advanced engines read but build_jre_facts omits.
    # Exact lagna longitude avoids the sign-midpoint approximation.
    facts.setdefault("lagna_longitude", float(chart.lagna.ascendant_longitude_deg))

    # Daytime context for Kala Bala: sunrise/sunset approximated at 6am/6pm
    # (documented simplification; classical Kala Bala uses exact sunrise).
    birth_time = time or "12:00:00"
    try:
        hour = float(birth_time.split(":")[0])
        minute = float(birth_time.split(":")[1]) if ":" in birth_time else 0.0
    except (ValueError, IndexError):
        hour, minute = 12.0, 0.0
    decimal_hour = hour + minute / 60.0
    facts.setdefault("is_daytime", 6.0 <= decimal_hour < 18.0)
    facts.setdefault("birth_hour", decimal_hour)

    # PII-safe request log consistent with other endpoints
    log_request(
        endpoint=endpoint,
        method="GET",
        status_code=200,
        latency_ms=0.0,
        key_hash=get_key_hash(request.headers.get("X-API-Key", "")),
        message="Advanced charts request completed",
    )
    return facts


# ── Divisional (Varga) Charts ───────────────────────────────────────────────


@router.get("/divisional")
async def get_divisional_chart(
    request: Request,
    division: str,
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Compute one divisional chart (D1–D60) for a fixture or birth data."""
    facts = await _build_facts(
        request, "/api/v1/advanced/divisional",
        fixture_id, date, time, latitude, longitude, timezone,
    )

    division_clean = division.upper().strip().lstrip("D")
    try:
        division_num = int(division_clean)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid division {division!r}. Use D1…D60 (e.g. D9).",
        )
    if division_num not in SUPPORTED_DIVISIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Division D{division_num} not supported. Supported: {list(SUPPORTED_DIVISIONS)}",
        )

    try:
        chart = calculate_divisional_positions(facts, f"D{division_num}")
        return divisional_chart_to_dict(chart)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── Shadbala (Six-Fold Strength) ────────────────────────────────────────────


@router.get("/shadbala")
async def get_shadbala(
    request: Request,
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Compute 6-fold planetary strength (Shadbala) for a fixture or birth data."""
    facts = await _build_facts(
        request, "/api/v1/advanced/shadbala",
        fixture_id, date, time, latitude, longitude, timezone,
    )
    return shadbala_to_dict(calculate_shadbala(facts))


# ── Ashtakavarga (Bindu Points) ─────────────────────────────────────────────


@router.get("/ashtakavarga")
async def get_ashtakavarga(
    request: Request,
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Compute Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV) bindus."""
    facts = await _build_facts(
        request, "/api/v1/advanced/ashtakavarga",
        fixture_id, date, time, latitude, longitude, timezone,
    )
    return ashtakavarga_to_dict(calculate_ashtakavarga(facts))
