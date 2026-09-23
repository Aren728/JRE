"""
src/jrs/api/routes/predictions.py

FastAPI endpoints exposing the prediction_engine's gochar (transit) and
relationship analysis engines for the JRE frontend report tabs.

Response shapes match frontend/lib/api.ts:
  - GocharTransitResult       (/api/v1/predictions/gochar-transit)
  - RelationshipAnalysisResult (/api/v1/predictions/relationship)
  - DailyTransitAspect[]      (/api/v1/predictions/day-by-day-transit)

Each endpoint accepts either `fixture_id` or raw birth data
(date/time/latitude/longitude/timezone), mirroring /api/v1/evaluate/* and
/api/v1/advanced/*.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from jrs.api.auth import check_rate_limit, get_key_hash
from jrs.api.logging_config import log_request

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


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

    Mirrors the advanced_charts helper (kept local to avoid a circular
    router import). Raises HTTPException 422 on missing/invalid input.
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

    log_request(
        endpoint=endpoint,
        method="GET",
        status_code=200,
        latency_ms=0.0,
        key_hash=get_key_hash(request.headers.get("X-API-Key", "")),
        message="Predictions request completed",
    )
    return facts


def _natal_inputs(facts: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], str, str]:
    """Extract (planet_details, lagna, moon_sign) from the facts packet."""
    planet_details: dict[str, dict[str, Any]] = {}
    for pname, pdata in facts.get("planet_details", {}).items():
        natal = facts.get("planets", {}).get(pname, {})
        sign = pdata.get("sign") or natal.get("rashi", "")
        planet_details[pname] = {
            "sign": sign,
            "degree_in_sign": pdata.get("degree_in_sign", 0.0),
            "house": natal.get("house", pdata.get("house", 0)),
        }

    lagna = facts.get("lagna", "")
    moon_sign = ""
    for pname in ("MOON",):
        detail = planet_details.get(pname, {})
        moon_sign = detail.get("sign", "")
        if moon_sign:
            break
    return planet_details, lagna, moon_sign


# ── Gochar (Transit) Predictions ────────────────────────────────────────────


@router.get("/gochar-transit")
async def get_gochar_transit(
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> dict[str, Any]:
    """Live gochar transit predictions for the current sky.

    Requires API key. Accepts fixture_id or birth data.
    """
    from datetime import datetime as _dt

    from jrs.prediction_engine.gochar_transit import (
        SIGN_ORDER,
        compute_gochar_transits,
        compute_planetary_states_for_date,
        gochar_transit_to_dict,
    )

    facts = await _build_facts(
        request,
        "/api/v1/predictions/gochar-transit",
        fixture_id,
        date,
        time,
        latitude,
        longitude,
        timezone,
    )
    planet_details, lagna, moon_sign = _natal_inputs(facts)

    now = _dt.now()
    daily_states = compute_planetary_states_for_date(now.year, now.month, now.day)
    transit_positions: dict[str, dict[str, Any]] = {}
    for planet, state in daily_states.items():
        sign_idx = int(state.longitude // 30) % 12
        transit_positions[planet] = {
            "rashi": SIGN_ORDER[sign_idx],
            "degree_in_sign": round(state.longitude % 30, 2),
            "longitude": round(state.longitude, 4),
            "retrograde": state.is_retrograde,
            "combust": state.is_combust,
        }

    result = compute_gochar_transits(
        natal_lagna=lagna,
        transit_positions=transit_positions,
        moon_sign=moon_sign,
    )
    payload = gochar_transit_to_dict(result)

    # Frontend contract (GocharTransitResult.transit_positions) reads
    # {sign, degree} per planet — alias the engine-native rashi/degree keys.
    for _planet, _pos in payload.get("transit_positions", {}).items():
        _pos.setdefault("sign", _pos.get("rashi", ""))
        _pos.setdefault(
            "degree", _pos.get("degree_in_sign", 0.0)
        )
    return payload


# ── Relationship Analysis ───────────────────────────────────────────────────


@router.get("/relationship")
async def get_relationship_analysis(
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> dict[str, Any]:
    """Classical relationship (marriage mechanics) analysis from the natal chart.

    Requires API key. Accepts fixture_id or birth data.
    """
    from jrs.prediction_engine.relationship_analysis import (
        compute_relationship_analysis,
        relationship_analysis_to_dict,
    )

    facts = await _build_facts(
        request,
        "/api/v1/predictions/relationship",
        fixture_id,
        date,
        time,
        latitude,
        longitude,
        timezone,
    )
    planet_details, lagna, _moon_sign = _natal_inputs(facts)

    result = compute_relationship_analysis(
        planet_details=planet_details,
        lagna=lagna,
        aspects=facts.get("aspect_matrix", []),
        parivartana_yogas=facts.get("parivartana_yogas", []),
        yogas=[],
        dignity_map=facts.get("dignity_map", {}),
    )
    return relationship_analysis_to_dict(result)


# ── Day-by-Day Transit Forecast ─────────────────────────────────────────────


@router.get("/day-by-day-transit")
async def get_day_by_day_transits(
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
    fixture_id: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    days: int = Query(14, ge=1, le=60),
) -> list[dict[str, Any]]:
    """Day-by-day transit aspect forecast for the next N days.

    Requires API key. Accepts fixture_id or birth data.
    """
    from jrs.prediction_engine.gochar_transit import (
        compute_day_by_day_transits,
        daily_transit_to_dict,
    )

    facts = await _build_facts(
        request,
        "/api/v1/predictions/day-by-day-transit",
        fixture_id,
        date,
        time,
        latitude,
        longitude,
        timezone,
    )
    planet_details, lagna, moon_sign = _natal_inputs(facts)

    aspects = compute_day_by_day_transits(
        natal_planet_details=planet_details,
        natal_lagna=lagna,
        natal_moon_sign=moon_sign,
        days=days,
    )
    return daily_transit_to_dict(aspects)
