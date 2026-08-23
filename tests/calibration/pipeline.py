"""Calibration pipeline — batch fixture runner.

Loads all validation fixtures from each domain, runs each through the
full JRS pipeline (Facts → Evidence → Temporal → Convergence), and
compares the generated DomainAssessment against ground truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jrs.convergence.service import ConvergenceService
from jrs.evidence.models import EvidenceRecord
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger

from .metrics import (
    CalibrationReport,
    DomainMetrics,
    OutcomeMetrics,
    compute_outcome_metrics,
    compute_timing_overlap,
)

# ── Fixture Discovery ────────────────────────────────────────────────────────

_FIXTURES_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / "tests" / "fixtures" / "validation_charts"
)

# Domain directory names → display names
_DOMAIN_DIRS: dict[str, str] = {
    "marriage_domain": "marriage",
    "career_domain": "career",
    "wealth_domain": "wealth",
    "education_domain": "education",
    "health_domain": "health",
    "business_domain": "business",
    "litigation_domain": "litigation",
    "property_domain": "property",
    "spirituality_domain": "spirituality",
    "transitions_domain": "transitions",
    "migration_domain": "migration",
    "assets_domain": "assets",
    "progeny_domain": "progeny",
}


def discover_fixtures() -> dict[str, list[Path]]:
    """Discover all validation fixture files organized by domain.

    Returns:
        A dict mapping domain display names to lists of fixture file paths.
    """
    domains: dict[str, list[Path]] = {}
    for dir_name, display_name in _DOMAIN_DIRS.items():
        domain_dir = _FIXTURES_ROOT / dir_name
        if not domain_dir.exists():
            continue
        fixtures = sorted(domain_dir.glob("chart_*.json"))
        if fixtures:
            domains[display_name] = fixtures
    return domains


def load_fixture(path: Path) -> dict[str, Any]:
    """Load a single validation fixture from a JSON file."""
    with path.open() as f:
        return json.load(f)


# ── Pipeline Execution ───────────────────────────────────────────────────────

# Domain directory → service class name mapping for dynamic dispatch
_DOMAIN_SERVICES: dict[str, str] = {
    "marriage": "MarriageDomainService",
    "career": "CareerDomainService",
    "wealth": "WealthDomainService",
    "education": "EducationDomainService",
    "health": "HealthDomainService",
    "business": "BusinessDomainService",
    "litigation": "LitigationDomainService",
    "property": "PropertyDomainService",
    "spirituality": "SpiritualityDomainService",
    "transitions": "TransitionsDomainService",
    "migration": "MigrationDomainService",
    "assets": "AssetsDomainService",
    "progeny": "ProgenyDomainService",
}


def _get_domain_service(domain: str) -> Any:
    """Dynamically import and instantiate the domain service."""
    if domain == "marriage":
        from jrs.domains.marriage.service import MarriageDomainService
        return MarriageDomainService()
    if domain == "career":
        from jrs.domains.career.service import CareerDomainService
        return CareerDomainService()
    if domain == "wealth":
        from jrs.domains.wealth.service import WealthDomainService
        return WealthDomainService()
    if domain == "education":
        from jrs.domains.education.service import EducationDomainService
        return EducationDomainService()
    if domain == "health":
        from jrs.domains.health.service import HealthDomainService
        return HealthDomainService()
    if domain == "business":
        from jrs.domains.business.service import BusinessDomainService
        return BusinessDomainService()
    if domain == "litigation":
        from jrs.domains.litigation.service import LitigationDomainService
        return LitigationDomainService()
    if domain == "property":
        from jrs.domains.property.service import PropertyDomainService
        return PropertyDomainService()
    if domain == "spirituality":
        from jrs.domains.spirituality.service import SpiritualityDomainService
        return SpiritualityDomainService()
    if domain == "transitions":
        from jrs.domains.transitions.service import TransitionsDomainService
        return TransitionsDomainService()
    if domain == "migration":
        from jrs.domains.migration.service import MigrationDomainService
        return MigrationDomainService()
    if domain == "assets":
        from jrs.domains.assets.service import AssetsDomainService
        return AssetsDomainService()
    if domain == "progeny":
        from jrs.domains.progeny.service import ProgenyDomainService
        return ProgenyDomainService()
    return None


def _evaluate_domain_facts(
    domain_svc: Any,
    facts: dict[str, Any],
) -> tuple[EvidenceRecord, ...]:
    """Evaluate natal facts through the domain service.

    Handles the different method names across domain services.
    """
    # All domain services expose an evaluate_*_facts method
    for attr_name in dir(domain_svc):
        if attr_name.startswith("evaluate_") and attr_name.endswith("_facts"):
            method = getattr(domain_svc, attr_name)
            return method(facts)
    return ()


def _extract_event_windows(
    chart: dict[str, Any],
    outcome_taxonomy: str,
) -> tuple[EventWindow, ...]:
    """Extract event windows from chart dasha and transit periods."""
    windows: list[EventWindow] = []

    for period_type in ("dasha_periods", "transits"):
        periods = chart.get(period_type, [])
        for p in periods:
            trigger = TemporalTrigger(
                activation_type=ActivationType(p["activation_type"]),
                triggering_planet=p.get("triggering_planet", ""),
                activation_start_utc=p.get("activation_start_utc", ""),
                activation_end_utc=p.get("activation_end_utc", ""),
                strength=float(p.get("strength", 1.0)),
            )
            windows.append(EventWindow(
                candidate_event_taxonomy=outcome_taxonomy,
                triggers=(trigger,),
            ))

    return tuple(windows)


def run_single_assessment(
    chart: dict[str, Any],
    domain: str,
    outcome_taxonomy: str,
    convergence_svc: ConvergenceService,
) -> dict[str, Any]:
    """Run the full JRS pipeline for a single outcome on a single chart.

    Steps:
        1. Extract natal_facts from chart
        2. Evaluate facts through domain service → EvidenceRecords
        3. Extract temporal windows from dasha/transits
        4. Assess convergence → DomainAssessment

    Returns:
        The DomainAssessment as a dict.
    """
    facts = chart.get("natal_facts", {})
    domain_svc = _get_domain_service(domain)

    evidence_records: tuple[EvidenceRecord, ...] = ()
    if domain_svc is not None:
        evidence_records = _evaluate_domain_facts(domain_svc, facts)

    event_windows = _extract_event_windows(chart, outcome_taxonomy)

    assessment = convergence_svc.assess_domain(
        outcome_taxonomy,
        evidence_records=evidence_records,
        event_windows=event_windows,
    )
    return assessment.to_dict()


# ── Calibration Runner ───────────────────────────────────────────────────────


def run_calibration() -> CalibrationReport:
    """Run calibration across all domains and fixtures.

    Returns:
        A CalibrationReport with per-domain and per-outcome metrics.
    """
    from datetime import UTC, datetime

    convergence_svc = ConvergenceService()
    all_domain_metrics: list[DomainMetrics] = []

    fixture_map = discover_fixtures()

    for domain, fixture_paths in sorted(fixture_map.items()):
        all_outcome_metrics: list[OutcomeMetrics] = []

        for fixture_path in fixture_paths:
            chart = load_fixture(fixture_path)
            expected = chart.get("expected_assessments", {})

            for outcome, ground_truth in expected.items():
                gt_status = ground_truth.get("assessment_status", "NEUTRAL")
                gt_timing = ground_truth.get("timing_status", "INACTIVE")

                predicted = run_single_assessment(
                    chart, domain, outcome, convergence_svc,
                )
                pred_status = predicted.get("assessment_status", "NEUTRAL")
                pred_timing = predicted.get("timing_status", "INACTIVE")

                timing_match = compute_timing_overlap(gt_timing, pred_timing)

                metrics = compute_outcome_metrics(
                    outcome=outcome,
                    ground_truth_status=gt_status,
                    predicted_status=pred_status,
                    timing_match=timing_match,
                )
                all_outcome_metrics.append(metrics)

        domain_metrics = DomainMetrics(
            domain=domain,
            outcome_metrics=tuple(all_outcome_metrics),
            total_charts=len(fixture_paths),
        )
        all_domain_metrics.append(domain_metrics)

    report = CalibrationReport(
        domain_metrics=tuple(all_domain_metrics),
        timestamp=datetime.now(UTC).isoformat(),
    )
    return report
