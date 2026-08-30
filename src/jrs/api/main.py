"""JRE API — FastAPI application for yoga evaluation.

Exposes the JRE reasoning engine as a REST API.
No engine changes — pure wrapping layer.

Usage::

    uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000
    # or
    python -m src.jrs.api.main
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException

from .dependencies import (
    _PROJECT_ROOT,
    build_jre_facts,
    compute_chart_from_birth_data,
    compute_chart_from_fixture,
    get_yoga_evaluator,
    list_fixtures,
    load_fixture,
)
from .schemas import (
    BirthDataInput,
    EvaluationResponse,
    FixtureInput,
    HealthResponse,
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
) -> EvaluationResponse:
    """Run the yoga evaluation pipeline and format the response.

    Args:
        chart: NatalChart object (for lagna/nakshatra extraction).
        jre_facts: JRE facts dictionary.
        subject: Subject name for the response.

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
        ))

    elapsed_ms = (time.perf_counter() - start) * 1000

    lagna_rashi = chart.lagna.rashi.value
    moon_nak = ""
    for ps in chart.planet_states:
        if ps.body.value == "MOON":
            moon_nak = ps.nakshatra.value
            break

    return EvaluationResponse(
        subject=subject,
        lagna=lagna_rashi,
        moon_nakshatra=moon_nak,
        yogas=yoga_results,
        yoga_count=len(yoga_results),
        formed_count=formed_count,
        processing_time_ms=round(elapsed_ms, 2),
    )


# ── Endpoints ───────────────────────────────────────────────────────────────


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/api/v1/fixtures", tags=["Fixtures"])
async def list_available_fixtures() -> dict[str, Any]:
    """List all available chart fixtures."""
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
async def evaluate_fixture(input_data: FixtureInput) -> EvaluationResponse:
    """Evaluate yogas for a pre-computed chart fixture.

    Loads the fixture by ID, computes the natal chart, and runs
    the full JRS evaluation pipeline.
    """
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

    return _run_evaluation(chart, jre_facts, subject=subject)


@app.post(
    "/api/v1/evaluate/custom",
    response_model=EvaluationResponse,
    tags=["Evaluation"],
)
async def evaluate_custom(input_data: BirthDataInput) -> EvaluationResponse:
    """Evaluate yogas for custom birth data.

    Computes the natal chart from the provided birth data and runs
    the full JRS evaluation pipeline.
    """
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

    return _run_evaluation(chart, jre_facts, subject="Custom")


# ── Report Endpoint ────────────────────────────────────────────────────────


@app.post(
    "/api/v1/report/fixture",
    tags=["Report"],
)
async def generate_report(
    input_data: FixtureInput,
    format: str = "markdown",
) -> dict[str, Any]:
    """Generate a human-readable astrological report for a chart fixture.

    Args:
        input_data: FixtureInput with fixture_id.
        format: Output format — 'markdown' (default) or 'html'.

    Returns:
        Dictionary with 'format' and 'content' keys.
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

    response = _run_evaluation(chart, jre_facts, subject=subject)

    # Generate report
    generator = ReportGenerator(response)
    if format == "html":
        content = generator.generate_html()
    else:
        content = generator.generate_markdown()

    return {
        "format": format,
        "subject": subject,
        "content": content,
    }


# ── Feedback Endpoint ───────────────────────────────────────────────────────


@app.post(
    "/api/v1/feedback",
    tags=["Feedback"],
)
async def submit_feedback(
    fixture_id: str = "",
    event_date: str = "",
    expected_outcome: str = "",
    actual_outcome: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Submit beta tester feedback.

    Appends the feedback to reports/beta_feedback_log.jsonl for later analysis.

    Args:
        fixture_id: Chart fixture identifier.
        event_date: Date of the event being evaluated.
        expected_outcome: What the tester expected.
        actual_outcome: What the engine predicted.
        notes: Additional notes or category (false_negative, false_positive, etc.).
    """
    import json
    from datetime import datetime, timezone

    feedback_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fixture_id": fixture_id,
        "event_date": event_date,
        "expected_outcome": expected_outcome,
        "actual_outcome": actual_outcome,
        "notes": notes,
    }

    # Write to JSONL file
    feedback_dir = _PROJECT_ROOT / "reports"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_path = feedback_dir / "beta_feedback_log.jsonl"

    try:
        with feedback_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry) + "\n")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {e}",
        )

    return {
        "status": "recorded",
        "message": "Feedback saved successfully",
        "entry_count": _count_feedback_entries(feedback_path),
    }


def _count_feedback_entries(path: Path) -> int:
    """Count existing feedback entries."""
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


# ── Entry Point ─────────────────────────────────────────────────────────────

def main() -> None:
    """Run the API server directly."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
