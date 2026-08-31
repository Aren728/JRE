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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response

from .auth import check_rate_limit, get_key_hash, require_api_key
from .dependencies import (
    _PROJECT_ROOT,
    build_jre_facts,
    compute_chart_from_birth_data,
    compute_chart_from_fixture,
    get_yoga_evaluator,
    list_fixtures,
    load_fixture,
)
from .logging_config import get_logger, log_request
from .schemas import (
    ENGINE_VERSION,
    LEGAL_DISCLAIMER,
    BirthDataInput,
    EvaluationResponse,
    FeedbackEntry,
    FixtureInput,
    HealthResponse,
    YogaProvenance,
    YogaResult,
)

# ── Application ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="JRE — Jyotish Reasoning Engine API",
    description=(
        "REST API for evaluating classical Jyotish yogas from birth data. "
        "Wraps the existing JRS evaluation pipeline (Layers 1–4) without "
        "modifying any engine logic."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

        yoga_results.append(YogaResult(
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
        ))

    elapsed_ms = (time.perf_counter() - start) * 1000

    lagna_rashi = chart.lagna.rashi.value
    moon_nak = ""
    for ps in chart.planet_states:
        if ps.body.value == "MOON":
            moon_nak = ps.nakshatra.value
            break

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


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint. No authentication required."""
    return HealthResponse(status="healthy", version="1.0.0")


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
        chart, jre_facts, subject=subject,
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
        raise HTTPException(
            status_code=422,
            detail=f"Chart computation failed: {e}",
        )

    response = _run_evaluation(chart, jre_facts, subject="Custom")

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


# ── Report Endpoint ────────────────────────────────────────────────────────


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
        chart, jre_facts, subject=subject,
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
    log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
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


# ── Entry Point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Run the API server directly."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
