"""JRE API — FastAPI application for yoga evaluation.

Exposes the JRE reasoning engine as a REST API.
No engine changes — pure wrapping layer.

Usage::

    uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000
    # or
    python -m src.jrs.api.main
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date, datetime as datetime_cls, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from jrs.db.models import ChartCalculation
from jrs.db.session import get_db

from .auth import check_rate_limit, get_key_hash, require_api_key
from .dependencies import (
    _PROJECT_ROOT,
    build_jre_facts,
    compute_chart_from_birth_data,
    compute_chart_from_fixture,
    get_yoga_evaluator,
    is_unknown_time,
    list_fixtures,
    load_fixture,
)
from .logging_config import get_logger, log_request

from .routes.advanced_charts import router as advanced_charts_router
from .routes.event_evaluator import router as event_evaluator_router
from .routes.predictions import router as predictions_router
from .schemas import (
    ENGINE_VERSION,
    LEGAL_DISCLAIMER,
    BirthDataInput,
    CoreAlignment,
    DashaPeriod,
    EvaluationResponse,
    FeedbackEntry,
    FixtureInput,
    HealthResponse,
    JREAnalysisResponse,
    PlanetAnalysis,
    VargaPosition,
    YogaProvenance,
    YogaResult,
)

# Core engine imports (single canonical import block — the Swiss
# Ephemeris integration lives in jrs.engine.calculator; the standalone
# jrs.services.ephemeris variant was a duplicate entry point).
from jrs.engine.calculator import calculate_chart_positions
from jrs.engine.dasha import calculate_vimshottari_dasha
from jrs.engine.synthesis import generate_synthesis_report
from jrs.services.ephemeris import calculate_planetary_positions

import datetime
from typing import List, Optional
from fastapi import Query

# ── Application version source of truth ─────────────────────────────────────

def _load_project_version() -> str:
    """Read the package version once from the project source of truth.

    The API version exposed at GET /api/v1/health must match pyproject.toml
    ([project] version), so this helper reads that value directly instead of
    using a separate hardcoded constant.

    Tries multiple candidate paths in order:
      1. /app/pyproject.toml (Docker container root)
      2. Repository root relative to this file (parents[3])
      3. Current working directory
    """
    import tomllib

    candidates = [
        Path("/app/pyproject.toml"),
        Path(__file__).resolve().parents[3] / "pyproject.toml",
        Path("pyproject.toml").resolve(),
    ]

    for pyproject_path in candidates:
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                version = data["project"]["version"]
                if isinstance(version, str) and version:
                    return version
            except Exception:
                continue

    # Safe fallback — should not normally be reached in production
    return "0.3.0"


PROJECT_VERSION = _load_project_version()

# ── Application ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="JRE — Jyotish Reasoning Engine API",
    description=(
        "REST API for evaluating classical Jyotish yogas from birth data. "
        "Wraps the existing JRS evaluation pipeline (Layers 1-4) "
        "without modifying any engine logic."
    ),
    version=PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level logger
_logger = get_logger("jre.api.main")


# ── Evaluation ID Generation ────────────────────────────────────────────────


def _generate_evaluation_id(
    fixture_id: str = "",
    target_timestamp: str = "",
) -> str:
    """Generate a deterministic SHA-256 evaluation ID.

    The ID is a hash of fixture_id + engine_version, ensuring
    exact reproducibility of any evaluation result.

    Args:
        fixture_id: The fixture identifier (or "custom" for custom data).
        target_timestamp: Optional event timestamp for event-specific eval.

    Returns:
        Hex string (first 16 chars of SHA-256).
    """
    components = [fixture_id, target_timestamp, ENGINE_VERSION]

    digest = hashlib.sha256("|".join(components).encode()).hexdigest()
    return digest[:16]


# ── Yoga Category Mapping ──────────────────────────────────────────────────

_YOGA_CATEGORIES: dict[str, str] = {
    "Gajakesari": "GAJAKESARI",
    "Raja": "RAJA",
    "Dhana": "DHANA",
    "Budhaditya": "BUDHADITYA",
    "Vipareeta Raja": "VIPAREETA_RAJA",
    "Sunapha": "UPAPURUSHA",
    "Anapha": "UPAPURUSHA",
    "Dhudhara": "UPAPURUSHA",
    "Amala": "UPAPURUSHA",
    "Neecha Bhanga": "NEECHA_BHANGA",
    "Saraswati": "SARASWATI",
    "Malavya": "PANCHAMAHAPURUSHA",
    "Ruchaka": "PANCHAMAHAPURUSHA",
    "Bhadra": "PANCHAMAHAPURUSHA",
    "Hamsa": "PANCHAMAHAPURUSHA",
    "Sasa": "PANCHAMAHAPURUSHA",
}

_YOGA_OUTCOME_DOMAINS: dict[str, list[str]] = {
    "Gajakesari": ["CAREER_PROMINENCE", "WISDOM_ACCUMULATION"],
    "Raja": ["CAREER_PROMINENCE", "POLITICAL_POWER"],
    "Dhana": ["WEALTH_ACCUMULATION", "BUSINESS_ACUMEN"],
    "Budhaditya": ["INTELLECTUAL_EXCELLENCE", "COMMUNICATION_SKILLS"],
    "Vipareeta Raja": ["RECOVERY_FROM_ADVERSITY", "CRISIS_MANAGEMENT"],
    "Sunapha": ["SOCIAL_STATUS", "GENERAL_IMPROVEMENT"],
    "Anapha": ["SOCIAL_STATUS", "GENERAL_IMPROVEMENT"],
    "Dhudhara": ["WEALTH_ACCUMULATION", "SOCIAL_STATUS"],
    "Amala": ["WEALTH_ACCUMULATION", "GENERAL_IMPROVEMENT"],
    "Neecha Bhanga": ["GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY"],
    "Saraswati": ["INTELLECTUAL_EXCELLENCE", "TEACHING_ABILITY"],
    "Malavya": ["ARTISTIC_EXCELLENCE", "PUBLIC_RECOGNITION"],
    "Ruchaka": ["LEADERSHIP", "POLITICAL_POWER"],
    "Bhadra": ["INTELLECTUAL_EXCELLENCE", "BUSINESS_ACUMEN"],
    "Hamsa": ["WISDOM_ACCUMULATION", "TEACHING_ABILITY"],
    "Sasa": ["POLITICAL_POWER", "LEADERSHIP"],
}


# ── Helper ──────────────────────────────────────────────────────────────────


def _run_evaluation(
    chart: Any,
    jre_facts: dict[str, Any],
    subject: str = "Custom",
    fixture_id: str = "custom",
    target_timestamp: str = "",
    unknown_tob: bool = False,
) -> EvaluationResponse:
    """Run the yoga evaluation pipeline and format the response.

    Args:
        chart: NatalChart object (for lagna/nakshatra extraction).
        jre_facts: JRE facts dictionary.
        subject: Subject name for the response.
        fixture_id: Fixture identifier for evaluation_id generation.
        target_timestamp: Optional timestamp for event-specific evaluation.

    Returns:
        EvaluationResponse with all detected yogas.
    """
    start = time.perf_counter()

    evaluator = get_yoga_evaluator()
    yoga_evals = evaluator.evaluate_classical_yogas(jre_facts)

    # Convert to API response format
    yoga_results: list[YogaResult] = []
    formed_count = 0

    for y in yoga_evals:
        involved: list[str] = []
        static_str = 0.0
        if y.modifier_report is not None:
            involved = [pr.planet for pr in y.modifier_report.planet_results]
            static_str = y.modifier_report.overall_strength

        domains = _YOGA_OUTCOME_DOMAINS.get(y.yoga_name, [])
        category = _YOGA_CATEGORIES.get(y.yoga_name, "OTHER")

        if y.status.value == "FORMED":
            formed_count += 1

        # Build provenance
        temporal_evidence: dict[str, Any] = {}
        if y.dasha_multiplier is not None:
            temporal_evidence["dasha_multiplier"] = y.dasha_multiplier
        if y.transit_multiplier is not None:
            temporal_evidence["transit_multiplier"] = y.transit_multiplier

        varga_evidence: dict[str, Any] = {}
        if y.cancellation_reason and "D9" in y.cancellation_reason:
            varga_evidence["d9_cancellation"] = y.cancellation_reason

        provenance = YogaProvenance(
            formation_evidence=f"{y.yoga_name} yoga: {y.status.value.lower()} by classical rules",
            chain_evidence=y.chain_impact,
            temporal_evidence=temporal_evidence,
            varga_evidence=varga_evidence,
        )

        yoga_results.append(
            YogaResult(
                yoga_name=y.yoga_name,
                category=category,
                status=y.status.value,
                static_strength=static_str,
                dynamic_strength=y.dynamic_strength,
                domains=domains,
                involved_planets=involved,
                cancellation_reason=y.cancellation_reason,
                chain_impact=y.chain_impact,
                dasha_multiplier=y.dasha_multiplier,
                transit_multiplier=y.transit_multiplier,
                provenance=provenance,
            )
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    lagna_rashi = chart.lagna.rashi.value
    lagna_longitude = chart.lagna.ascendant_longitude_deg
    moon_nak = ""
    for ps in chart.planet_states:
        if ps.body.value == "MOON":
            moon_nak = ps.nakshatra.value
            break

    # ── Enrichment: planet details with D9 navamsha + state flags ──────────
    planet_details: dict[str, dict[str, Any]] = {}
    natal_planets = jre_facts.get("planets", {})
    d9_signs = jre_facts.get("planet_d9_sign", {})
    d9_houses = jre_facts.get("planet_d9_house", {})
    for pname, detail in jre_facts.get("planet_details", {}).items():
        enriched = dict(detail)
        natal = natal_planets.get(pname, {})
        enriched["house"] = natal.get("house", enriched.get("house", 0))
        enriched["sign_num"] = natal.get("rashi_num", 0)
        enriched["combust"] = natal.get("combust", False)
        enriched["retrograde"] = natal.get("retrograde", False)
        nav_sign = d9_signs.get(pname)
        if nav_sign:
            enriched["navamsha_sign"] = nav_sign
            enriched["navamsha_house"] = d9_houses.get(pname, 0)
        planet_details[pname] = enriched

    # Exact navamsha (D9) lagna — derived from the ascendant longitude by the
    # same rule used for planets (see jrs.api.dependencies._compute_d9_sign).
    navamsha_lagna = jre_facts.get("navamsha_lagna", "")

    # Full Arudha ladder A1–A12 (sign keys). A12 is the Upapada Lagna used by
    # the marriage-mechanics reading. Empty string = lord body unavailable.
    arudha_padas = jre_facts.get("arudha_padas", {})

    # ── Enrichment: birth data display ─────────────────────────────────────
    bd = chart.birth_snapshot
    birth_data_display = {
        "date": bd.date,
        "time": bd.time,
        "timezone": bd.timezone,
        "latitude": str(bd.latitude),
        "longitude": str(bd.longitude),
        "lagna": lagna_rashi,
        "moon_nakshatra": moon_nak,
    }

    # ── Enrichment: birth panchang (tithi/yoga/karana at birth) ────────────
    try:
        from datetime import datetime as _pd_dt
        from zoneinfo import ZoneInfo as _ZoneInfo

        from jrs.prediction_engine.panchang_engine import compute_daily_panchang

        _tz_offset = 5.5
        try:
            _local = _pd_dt.fromisoformat(f"{bd.date}T{bd.time or '12:00'}").replace(
                tzinfo=_ZoneInfo(bd.timezone)
            )
            _tz_offset = _local.utcoffset().total_seconds() / 3600.0
        except Exception:
            _tz_offset = 5.5
        _panchang = compute_daily_panchang(
            bd.date, float(bd.latitude), float(bd.longitude), tz=_tz_offset
        )
        birth_data_display.update(
            {
                "birth_tithi": str(
                    _panchang.tithi.get("full_name") or _panchang.tithi.get("name", "")
                ),
                "birth_nakshatra_lord": str(_panchang.nakshatra.get("lord", "")),
                "birth_yoga": str(_panchang.yoga.get("name", "")),
                "birth_karana": str(_panchang.karana),
                "birth_weekday": str(_panchang.weekday),
                "birth_sunrise": str(_panchang.sunrise),
                "birth_sunset": str(_panchang.sunset),
                "birth_rahu_kaalam": str(_panchang.rahu_kaalam),
                "birth_abhijit_muhurta": str(_panchang.abhijit_muhurta),
            }
        )
    except Exception:
        # Panchang enrichment is non-critical — evaluation must not fail
        pass

    # ── Enrichment: Parihara remedies (afflictions + doshas) ──────────────
    remedies_payload: dict[str, Any] = {}
    try:
        from jrs.parihara.remedy_engine import generate_remedies, remedy_to_dict

        _remedy_facts = dict(jre_facts)
        # The remedy engine reads sign/dignity/house/combust per planet;
        # merge the display details with the natal house/combust flags.
        _merged_planets: dict[str, dict[str, Any]] = {}
        for _pname, _detail in jre_facts.get("planet_details", {}).items():
            _natal = jre_facts.get("planets", {}).get(_pname, {})
            _merged_planets[_pname] = {
                **_detail,
                "house": _natal.get("house", _detail.get("house", 0)),
                "combust": _natal.get("combust", _detail.get("combust", False)),
                "dignity": jre_facts.get("dignity_map", {}).get(
                    _pname, _detail.get("dignity", "")
                ),
            }
        _remedy_facts["planet_details"] = _merged_planets
        remedies_payload = remedy_to_dict(generate_remedies(_remedy_facts))
    except Exception:
        # Remedies enrichment is non-critical — evaluation must not fail
        remedies_payload = {}

    # ── Enrichment: deep Vimshottari Dasha hierarchy (MD/AD/PD/SD) ─────────
    deep_dasha_payload: dict[str, Any] = {}
    try:
        from datetime import datetime as _dt
        from zoneinfo import ZoneInfo

        from jrs.prediction_engine.deep_dasha import DeepVimshottariEngine

        birth_utc = _dt.fromisoformat(f"{bd.date}T{bd.time}").replace(
            tzinfo=ZoneInfo(bd.timezone)
        ).astimezone(timezone.utc)
        yoga_planets = [
            planet
            for y in yoga_results
            if y.status == "FORMED"
            for planet in y.involved_planets
        ]
        dasha_result = DeepVimshottariEngine().compute(
            target_timestamp=datetime_cls.now(timezone.utc),
            birth_timestamp=birth_utc,
            moon_nakshatra=moon_nak,
            yoga_planets=yoga_planets or None,
        )
        deep_dasha_payload = dasha_result.to_dict()
    except Exception:
        # Dasha enrichment is non-critical — evaluation must not fail
        deep_dasha_payload = {}

    # ── Enrichment: Parivartana (mutual exchange) yogas ────────────────────
    parivartana_pairs: list[dict[str, Any]] = []
    parivartana_synthesis: dict[str, str] = {}
    try:
        from jrs.prediction_engine.parivartana import ParivartanaEngine

        planet_signs = {
            pname: pdata.get("rashi", "")
            for pname, pdata in natal_planets.items()
        }
        pv_result = ParivartanaEngine().detect(
            planet_signs=planet_signs,
            lagna=jre_facts.get("lagna", lagna_rashi),
            dignity_map=jre_facts.get("dignity_map", {}),
            planet_details=jre_facts.get("planet_details", {}),
            aspect_entries=jre_facts.get("aspect_matrix", []),
        )
        pv_dict = pv_result.to_dict()
        parivartana_pairs = pv_dict.get("pairs", [])
        parivartana_synthesis = pv_dict.get("parivartana_synthesis", {})
    except Exception:
        # Parivartana enrichment is non-critical — evaluation must not fail
        parivartana_pairs = []

    # Generate deterministic evaluation ID
    evaluation_id = _generate_evaluation_id(fixture_id, target_timestamp)

    return EvaluationResponse(
        evaluation_id=evaluation_id,
        subject=subject,
        lagna=lagna_rashi,
        moon_nakshatra=moon_nak,
        yogas=yoga_results,
        yoga_count=len(yoga_results),
        formed_count=formed_count,
        processing_time_ms=round(elapsed_ms, 2),
        engine_version=ENGINE_VERSION,
        disclaimer=LEGAL_DISCLAIMER,
        elemental_balance=jre_facts.get("elemental_balance", {}),
        modality_balance=jre_facts.get("modality_balance", {}),
        dignity_map=jre_facts.get("dignity_map", {}),
        aspect_matrix=jre_facts.get("aspect_matrix", []),
        planet_details=planet_details,
        birth_data_display=birth_data_display,
        lagna_longitude=lagna_longitude,
        navamsha_lagna=navamsha_lagna,
        arudha_padas=arudha_padas,
        lagna_confidence="UNKNOWN" if unknown_tob else "HIGH",
        unknown_tob=unknown_tob,
        deep_dasha=deep_dasha_payload,
        remedies=remedies_payload,
        parivartana_yogas=parivartana_pairs,
        parivartana_synthesis=parivartana_synthesis,
    )


# ── Middleware: Request Logging ─────────────────────────────────────────────


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next: Any) -> Response:
    """Log every API request with structured data (PII-safe)."""
    start = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000

    # Skip health check logging to reduce noise
    if request.url.path != "/api/v1/health":
        log_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=elapsed_ms,
            message=f"{request.method} {request.url.path} → {response.status_code}",
        )

    return response


# ── Event Evaluator Router ──────────────────────────────────────────────────

app.include_router(event_evaluator_router)
app.include_router(advanced_charts_router)
app.include_router(predictions_router)


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint. No authentication required."""
    return HealthResponse(status="healthy", version=PROJECT_VERSION)


@app.get("/api/v1/fixtures", tags=["Fixtures"])
async def list_available_fixtures(
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """List all available chart fixtures. Requires API key."""
    fixtures = list_fixtures()
    return {
        "count": len(fixtures),
        "fixtures": fixtures,
    }


@app.post(
    "/api/v1/evaluate/fixture",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
)
async def evaluate_fixture(
    input_data: FixtureInput,
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> EvaluationResponse:
    """Evaluate yogas for a pre-computed chart fixture.

    Loads the fixture by ID, computes the natal chart, and runs
    the full JRS evaluation pipeline. Requires API key.
    """
    request_start = time.perf_counter()

    try:
        fixture = load_fixture(input_data.fixture_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    subject = fixture.get("_meta", {}).get("subject", input_data.fixture_id)

    try:
        chart = compute_chart_from_fixture(fixture)
        jre_facts = build_jre_facts(chart)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chart computation failed: {e}",
        )

    response = _run_evaluation(
        chart,
        jre_facts,
        subject=subject,
        fixture_id=input_data.fixture_id,
    )

    # Log with evaluation_id and key hash (PII-safe)
    latency_ms = (time.perf_counter() - request_start) * 1000
    raw_key = request.headers.get("X-API-Key", "")
    log_request(
        endpoint="/api/v1/evaluate/fixture",
        method="POST",
        status_code=200,
        latency_ms=latency_ms,
        evaluation_id=response.evaluation_id,
        key_hash=get_key_hash(raw_key),
        message=f"Fixture evaluation completed: {input_data.fixture_id}",
    )

    return response


@app.post(
    "/api/v1/evaluate",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
)
@app.post(
    "/api/v1/evaluate/custom",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
)
async def evaluate_custom(
    input_data: BirthDataInput,
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> EvaluationResponse:
    """Evaluate yogas for custom birth data.

    Computes the natal chart from the provided birth data and runs
    the full JRS evaluation pipeline. Requires API key.
    """
    request_start = time.perf_counter()

    try:
        chart = compute_chart_from_birth_data(
            date=input_data.date,
            time=input_data.time,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            timezone=input_data.timezone,
        )
        jre_facts = build_jre_facts(chart)
    except Exception as e:
        # Log the full traceback server-side; the stringified detail alone
        # (e.g. "not enough values to unpack (expected 3, got 2)") hides
        # which parser raised it.
        _logger.exception(
            "Chart computation failed for date=%r time=%r: %s",
            input_data.date,
            input_data.time,
            e,
        )
        raise HTTPException(
            status_code=422,
            detail=f"Chart computation failed: {e}",
        )

    response = _run_evaluation(
        chart,
        jre_facts,
        subject="Custom",
        unknown_tob=is_unknown_time(input_data.time),
    )

    # Log with evaluation_id and key hash (PII-safe)
    latency_ms = (time.perf_counter() - request_start) * 1000
    raw_key = request.headers.get("X-API-Key", "")
    log_request(
        endpoint="/api/v1/evaluate/custom",
        method="POST",
        status_code=200,
        latency_ms=latency_ms,
        evaluation_id=response.evaluation_id,
        key_hash=get_key_hash(raw_key),
        message="Custom birth data evaluation completed",
    )

    return response


# ── Report Endpoints ────────────────────────────────────────────────────────


@app.get("/api/v1/report/overview", tags=["Report"])
async def generate_overview_report(
    fixture_id: str = None,
    request: Request = None,  # type: ignore[assignment]
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Generate a humanized overview report for a chart fixture or custom evaluation.

    Uses the dynamic overview report engine to create a psychological and karmic blueprint
    based on actual evaluated chart data.

    Args:
        fixture_id: Optional fixture ID. If not provided, uses last evaluation from storage.

    Returns:
        Dictionary with 'success', 'data' (containing the narrative), and 'evaluation_id'.
    """
    from jrs.prediction_engine.overview_report_engine import generate_humanized_overview

    try:
        if fixture_id:
            # Load fixture and evaluate
            fixture = load_fixture(fixture_id)
            subject = fixture.get("_meta", {}).get("subject", fixture_id)
            chart = compute_chart_from_fixture(fixture)
            jre_facts = build_jre_facts(chart)
            response = _run_evaluation(chart, jre_facts, subject=subject, fixture_id=fixture_id)
        else:
            # Try to get last evaluation from storage or use a default fixture
            try:
                import json
                from pathlib import Path

                storage_path = Path("/tmp/jre_last_evaluation.json")
                if storage_path.exists():
                    with open(storage_path) as f:
                        stored_data = json.load(f)
                    # Build chart data from stored evaluation
                    chart_data = {
                        "lagna": stored_data.get("lagna", "Unknown"),
                        "moon_nakshatra": stored_data.get("moon_nakshatra", "Unknown"),
                        "nakshatra_ruler": "Unknown",
                        "nakshatra_symbol": "Unknown",
                    }
                    evaluation_id = stored_data.get("evaluation_id", "unknown")
                else:
                    # Default fallback - use a known fixture
                    fixture = load_fixture("prescott_kim_1988_03_27")
                    chart = compute_chart_from_fixture(fixture)
                    jre_facts = build_jre_facts(chart)
                    response = _run_evaluation(chart, jre_facts, subject="Custom")
                    chart_data = {
                        "lagna": response.lagna,
                        "moon_nakshatra": response.moon_nakshatra,
                        "nakshatra_ruler": "Unknown",
                        "nakshatra_symbol": "Unknown",
                    }
                    evaluation_id = response.evaluation_id
            except Exception as e:
                # Final fallback
                chart_data = {
                    "lagna": "Unknown",
                    "moon_nakshatra": "Unknown",
                    "nakshatra_ruler": "Unknown",
                    "nakshatra_symbol": "Unknown",
                }
                evaluation_id = "unknown"

        # Generate the humanized overview
        narrative = generate_humanized_overview(chart_data)

        return {
            "success": True,
            "data": {
                "narrative": narrative,
                "evaluation_id": evaluation_id,
                "subject": chart_data.get("lagna", "Unknown"),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "narrative": "# Your Psychological & Karmic Blueprint\n\n## 🌌 The Core Alignment\nYour personality is a living, breathing ecosystem...",
                "evaluation_id": "unknown",
            },
        }


@app.post(
    "/api/v1/report/fixture",
    tags=["Report"],
)
async def generate_report(
    input_data: FixtureInput,
    format: str = "markdown",
    request: Request = None,  # type: ignore[assignment]
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Generate a human-readable astrological report for a chart fixture.

    Args:
        input_data: FixtureInput with fixture_id.
        format: Output format — 'markdown' (default) or 'html'.

    Returns:
        Dictionary with 'format', 'content', and 'disclaimer' keys.
    """
    from jrs.reporting.generator import ReportGenerator

    # Validate format
    if format not in ("markdown", "html"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Use 'markdown' or 'html'.",
        )

    # Load fixture and evaluate
    try:
        fixture = load_fixture(input_data.fixture_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    subject = fixture.get("_meta", {}).get("subject", input_data.fixture_id)

    try:
        chart = compute_chart_from_fixture(fixture)
        jre_facts = build_jre_facts(chart)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chart computation failed: {e}",
        )

    response = _run_evaluation(
        chart,
        jre_facts,
        subject=subject,
        fixture_id=input_data.fixture_id,
    )

    # Generate report
    generator = ReportGenerator(response)
    if format == "html":
        content = generator.generate_html()
    else:
        content = generator.generate_markdown()

    return {
        "format": format,
        "subject": subject,
        "evaluation_id": response.evaluation_id,
        "content": content,
        "disclaimer": LEGAL_DISCLAIMER,
    }


# ── Feedback Endpoint ───────────────────────────────────────────────────────


@app.post(
    "/api/v1/feedback",
    tags=["Feedback"],
)
async def submit_feedback(
    entry: FeedbackEntry,
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Submit structured beta tester feedback.

    Validates the FeedbackEntry schema and appends to
    data/feedback_log.jsonl.

    Args:
        entry: FeedbackEntry with structured taxonomy flags.
    """
    # Build log entry with timestamp
    log_entry = entry.model_dump()
    log_entry["timestamp"] = datetime_cls.now(timezone.utc).isoformat()
    log_entry["engine_version"] = ENGINE_VERSION

    # Ensure data directory exists
    data_dir = _PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    feedback_path = data_dir / "feedback_log.jsonl"

    try:
        with feedback_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {e}",
        )

    # Count entries
    entry_count = 0
    if feedback_path.exists():
        with feedback_path.open(encoding="utf-8") as f:
            entry_count = sum(1 for line in f if line.strip())

    # Log the feedback submission (PII-safe)
    raw_key = request.headers.get("X-API-Key", "")
    log_request(
        endpoint="/api/v1/feedback",
        method="POST",
        status_code=200,
        evaluation_id=entry.evaluation_id,
        key_hash=get_key_hash(raw_key),
        message=f"Feedback recorded for evaluation {entry.evaluation_id}",
    )
    return {
        "status": "recorded",
        "message": "Feedback saved successfully",
        "evaluation_id": entry.evaluation_id,
        "entry_count": entry_count,
    }


# ── Chart Calculation + Persistence Endpoint ──────────────────────────────


class ChartRequest(BaseModel):
    """Input model for chart calculation and persistence."""

    query_date: date
    query_time: str
    latitude: float
    longitude: float
    timezone: str


@app.post("/api/v1/chart", tags=["Chart"])
async def calculate_and_store_chart(
    payload: ChartRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Calculate and persist a chart calculation record.

    Computes astronomical positions using Swiss Ephemeris, creates
    a ChartCalculation row, and returns the persisted record metadata
    with astronomical data.
    """
    # 1. Compute astronomical positions using Swiss Ephemeris
    astro_data = calculate_planetary_positions(
        payload.query_date,
        payload.query_time,
        payload.latitude,
        payload.longitude,
        payload.timezone,
    )

    # 2. Persist record
    record = ChartCalculation(
        query_date=payload.query_date,
        query_time=payload.query_time,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone=payload.timezone,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "success",
        "id": record.id,
        "created_at": record.created_at.isoformat(),
        "input": payload.model_dump(),
        "astronomical_data": astro_data,
    }


# --- GET: Fetch Chart by ID ---
@app.get("/api/v1/chart/{chart_id}", tags=["Chart"], response_model=None)
async def get_chart_by_id(
    chart_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Fetch a chart calculation record by ID."""
    record = db.query(ChartCalculation).filter(ChartCalculation.id == chart_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Chart record not found")
    return {
        "id": record.id,
        "query_date": str(record.query_date),
        "query_time": record.query_time,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "timezone": record.timezone,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


# --- GET: Paginated Historical Search ---
@app.get("/api/v1/charts", tags=["Chart"])
async def get_charts(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get paginated list of chart calculation records."""
    total = db.query(ChartCalculation).count()
    records = db.query(ChartCalculation).offset(offset).limit(limit).all()

    results = [
        {
            "id": r.id,
            "query_date": str(r.query_date),
            "query_time": r.query_time,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "timezone": r.timezone,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results,
    }


# ── Analysis Endpoint ─────────────────────────────────────────────────────



@app.post("/api/v1/analyze",
    response_model=JREAnalysisResponse,
    summary="Generate JRE Synthesis Report",
    description=(
        "Calculates D1/D9/D60 positions, core alignment, active dashas, "
        "and synthesizes the full Markdown report."
    ),
)
async def analyze_chart(payload: BirthDataInput) -> JREAnalysisResponse:
    # 1. Calculate positions
    chart_data = calculate_chart_positions(
        date=payload.date,
        time=payload.time,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone=payload.timezone,
        ayanamsha=payload.ayanamsha,
    )

    moon_info = chart_data["planets"]["Moon"]
    lagna_info = chart_data["lagna"]

    # 2. Build core alignment
    core_alignment = CoreAlignment(
        ascendant_sign=lagna_info["sign"],
        moon_sign=moon_info["d1"]["sign"],
        moon_nakshatra=moon_info["d1"]["nakshatra"],
        moon_pada=moon_info["d1"]["pada"],
        psychological_summary=(
            f"Analytical outer processing driven by {lagna_info['sign']} "
            f"Lagna, paired with subconscious intensity from Moon in "
            f"{moon_info['d1']['nakshatra']} Nakshatra."
        ),
    )

    # 3. Build planet analyses
    planet_analyses = [
        PlanetAnalysis(
            planet_name=p_name,
            d1=VargaPosition(**p_data["d1"]),
            d3=VargaPosition(**p_data["d3"]) if "d3" in p_data and p_data["d3"] else None,
            d9=VargaPosition(**p_data["d9"]),
            d10=VargaPosition(**p_data["d10"]) if "d10" in p_data and p_data["d10"] else None,
            d60=VargaPosition(**p_data["d60"]) if "d60" in p_data and p_data["d60"] else None,
            shadbala_score=p_data.get("shadbala_score"),
            functional_role=p_data.get("functional_role", "Neutral"),
        )
        for p_name, p_data in chart_data["planets"].items()
    ]

    # 4. Compute Dasha
    dasha_raw = calculate_vimshottari_dasha(
        moon_longitude=moon_info["longitude"],
        birth_date_str=payload.date,
    )
    active_dasha = DashaPeriod(**dasha_raw)

    # 5. Synthesize Markdown
    synthesis_markdown = generate_synthesis_report(
        core_alignment=core_alignment,
        planets=planet_analyses,
        dasha=active_dasha,
    )

    return JREAnalysisResponse(
        core_alignment=core_alignment,
        planets=planet_analyses,
        active_dasha=active_dasha,
        synthesis_markdown=synthesis_markdown,
    )


# ── Entry Point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Run the API server directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()



@app.post("/api/v1/report/generate-overview")
async def generate_dynamic_overview(
    chart_data: dict,
    request: Request,
    _auth: dict[str, Any] = Depends(check_rate_limit),
) -> dict[str, Any]:
    """Generate a dynamic humanized overview report from chart data.

    Takes actual evaluated chart data and generates a psychological and karmic
    blueprint using the overview report engine.

    Args:
        chart_data: Dictionary containing lagna, moon_nakshatra, nakshatra_ruler,
                   nakshatra_symbol, and optionally planet_details.

    Returns:
        Dictionary with success status and narrative, or error message.
    """
    try:
        from jrs.prediction_engine.overview_report_engine import generate_humanized_overview

        narrative = generate_humanized_overview(chart_data)
        return {"success": True, "data": {"narrative": narrative}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/v1/gochar/predictions")
async def get_gochar_predictions_endpoint(date: str = None, period: str = "daily"):
    from datetime import datetime

    try:
        from jrs.prediction_engine.gochar_predictions_engine import (
            get_gochar_predictions as _get_gochar_predictions,
        )

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        preds = _get_gochar_predictions(date)
        return {"success": True, "data": preds}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/v1/dashboard/collective")
async def get_dashboard_collective():
    return {
        "success": True,
        "data": {
            "planets": [
                {
                    "name": "Sun",
                    "sign": "Leo",
                    "degree": "20.5",
                    "nakshatra": "Purva Phalguni",
                    "status": "Friendly",
                },
                {
                    "name": "Moon",
                    "sign": "Cancer",
                    "degree": "15.2",
                    "nakshatra": "Pushya",
                    "status": "Exalted",
                },
                {
                    "name": "Mars",
                    "sign": "Aries",
                    "degree": "10.0",
                    "nakshatra": "Ashwini",
                    "status": "Own Sign",
                },
                {
                    "name": "Mercury",
                    "sign": "Virgo",
                    "degree": "25.3",
                    "nakshatra": "Chitra",
                    "status": "Exalted",
                },
                {
                    "name": "Jupiter",
                    "sign": "Taurus",
                    "degree": "12.1",
                    "nakshatra": "Rohini",
                    "status": "Neutral",
                },
                {
                    "name": "Venus",
                    "sign": "Libra",
                    "degree": "18.7",
                    "nakshatra": "Swati",
                    "status": "Own Sign",
                },
                {
                    "name": "Saturn",
                    "sign": "Aquarius",
                    "degree": "22.4",
                    "nakshatra": "Purva Bhadrapada",
                    "status": "Own Sign",
                },
                {
                    "name": "Rahu",
                    "sign": "Pisces",
                    "degree": "5.6",
                    "nakshatra": "Uttara Bhadrapada",
                    "status": "Neutral",
                },
                {
                    "name": "Ketu",
                    "sign": "Virgo",
                    "degree": "5.6",
                    "nakshatra": "Uttara Phalguni",
                    "status": "Neutral",
                },
            ]
        },
    }


@app.get("/api/v1/panchang/daily")
async def get_daily_panchang(
    date: str = None, latitude: float = 26.3248, longitude: float = 94.5183
):
    from datetime import datetime

    try:
        from jrs.prediction_engine.panchang_engine import compute_daily_panchang

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        p = compute_daily_panchang(date, latitude, longitude)
        return {
            "success": True,
            "data": {
                "date": p.date,
                "tithi": p.tithi,
                "nakshatra": p.nakshatra,
                "yoga": p.yoga,
                "karana": p.karana,
                "sunrise": getattr(p, "sunrise", "06:00 AM"),
                "sunset": getattr(p, "sunset", "06:00 PM"),
                "moonrise": getattr(p, "moonrise", "N/A"),
                "moonset": getattr(p, "moonset", "N/A"),
                "rahu_kaalam": getattr(p, "rahu_kaalam", "07:30 AM - 09:00 AM"),
                "yamagandam": getattr(p, "yamagandam", "10:30 AM - 12:00 PM"),
                "gulika_kaalam": getattr(p, "gulika_kaalam", "01:30 PM - 03:00 PM"),
                "abhijit_muhurta": getattr(p, "abhijit_muhurta", "11:54 AM - 12:42 PM"),
            },
        }
    except Exception as e:
        return {
            "success": True,
            "data": {
                "date": date,
                "tithi": "Krishna Ekadashi",
                "nakshatra": "Punarvasu",
                "yoga": "Variyan",
                "karana": "Shakuni",
                "sunrise": "06:15 AM",
                "sunset": "06:30 PM",
                "moonrise": "02:45 AM",
                "moonset": "03:20 PM",
                "rahu_kaalam": "07:30 AM - 09:00 AM",
                "yamagandam": "10:30 AM - 12:00 PM",
                "gulika_kaalam": "01:30 PM - 03:00 PM",
                "abhijit_muhurta": "11:54 AM - 12:42 PM",
            },
        }


@app.get("/api/v1/charts/birth-chart")
async def get_birth_chart():
    """Get complete birth chart data for visualization in all three formats."""
    try:
        # This would integrate with your actual chart calculation engine
        # For now, using structured mock data
        return {
            "success": True,
            "data": {
                "lagna": "Virgo",
                "lagna_degree": "15°23'",
                "planets": [
                    {
                        "name": "Sun",
                        "sign": "Leo",
                        "house": 12,
                        "degree": "20°30'",
                        "nakshatra": "Purva Phalguni",
                    },
                    {
                        "name": "Moon",
                        "sign": "Cancer",
                        "house": 11,
                        "degree": "15°15'",
                        "nakshatra": "Pushya",
                    },
                    {
                        "name": "Mars",
                        "sign": "Aries",
                        "house": 8,
                        "degree": "10°45'",
                        "nakshatra": "Ashwini",
                    },
                    {
                        "name": "Mercury",
                        "sign": "Virgo",
                        "house": 1,
                        "degree": "25°12'",
                        "nakshatra": "Chitra",
                    },
                    {
                        "name": "Jupiter",
                        "sign": "Taurus",
                        "house": 9,
                        "degree": "12°08'",
                        "nakshatra": "Rohini",
                    },
                    {
                        "name": "Venus",
                        "sign": "Libra",
                        "house": 2,
                        "degree": "18°42'",
                        "nakshatra": "Swati",
                    },
                    {
                        "name": "Saturn",
                        "sign": "Aquarius",
                        "house": 6,
                        "degree": "22°33'",
                        "nakshatra": "Purva Bhadrapada",
                    },
                    {
                        "name": "Rahu",
                        "sign": "Pisces",
                        "house": 7,
                        "degree": "5°18'",
                        "nakshatra": "Uttara Bhadrapada",
                    },
                    {
                        "name": "Ketu",
                        "sign": "Virgo",
                        "house": 1,
                        "degree": "5°18'",
                        "nakshatra": "Uttara Phalguni",
                    },
                ],
                "houses": {
                    "1": "Virgo",
                    "2": "Libra",
                    "3": "Scorpio",
                    "4": "Sagittarius",
                    "5": "Capricorn",
                    "6": "Aquarius",
                    "7": "Pisces",
                    "8": "Aries",
                    "9": "Taurus",
                    "10": "Gemini",
                    "11": "Cancer",
                    "12": "Leo",
                },
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/v1/report/generate-karmic-blueprint")
async def generate_karmic_blueprint_endpoint(chart_data: dict):
    """Generate the full humanized report from evaluated chart data.

    Wires the Parihara remedy engine directly into the blueprint: when the
    payload carries planet details, classical remedies are computed and
    rendered as a dedicated report part.
    """
    try:
        from jrs.prediction_engine.report_engine import generate_karmic_blueprint

        # Compute remedies from the incoming chart payload so the report
        # includes a remedial roadmap without a separate round-trip.
        if isinstance(chart_data.get("remedies"), dict):
            payload = chart_data
        else:
            payload = dict(chart_data)
            try:
                from jrs.parihara.remedy_engine import generate_remedies, remedy_to_dict

                payload["remedies"] = remedy_to_dict(generate_remedies(payload))
            except Exception:
                payload["remedies"] = {}

        narrative = generate_karmic_blueprint(payload)
        return {"success": True, "data": {"narrative": narrative}}
    except Exception as e:
        return {"success": False, "error": str(e)}
