"""Calibration pipeline — batch fixture runner.

Loads all validation fixtures from each domain, runs each through the
full JRS pipeline (Facts → Evidence → Temporal → Convergence), and
compares the generated DomainAssessment against ground truth.

Supports optional multi-system calibration (Vedic + Western + Numerology)
with independence-adjusted convergence scoring.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from jrs.convergence.service import ConvergenceService
from jrs.evidence.models import EvidenceRecord
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
)
from jrs.multisystem.service import IndependenceAnalyzer
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger
from western.models import WesternHouseSystem
from western.service import WesternCalculationService

from .metrics import (
    CalibrationReport,
    ComparativeCalibrationReport,
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
    "yoga_domain": "yoga",
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
    "yoga": "YogaDomainService",
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
    if domain == "yoga":
        from jrs.domains.yoga.service import YogaDomainService
        return YogaDomainService()
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

    # Handle Yoga domain specially — its assess() returns DomainAssessment directly
    if domain == "yoga" and domain_svc is not None and hasattr(domain_svc, "assess"):
        assessment = domain_svc.assess(facts)
        return assessment.to_dict()

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


# ── Western System Assessment ────────────────────────────────────────────────


def _run_western_assessment(
    chart: dict[str, Any],
    outcome_taxonomy: str,
) -> SystemAssessment:
    """Run the Western pipeline using fixture birth data.

    Computes a WesternChart from the fixture's birth_data coordinates
    using WesternCalculationService, then evaluates it through
    WesternDomainService.
    """
    from jrs.western.service import WesternDomainService

    birth_data = chart.get("birth_data", {})
    date_str = birth_data.get("date", "1980-01-01")
    time_str = birth_data.get("time", "12:00:00")
    latitude = float(birth_data.get("latitude", 19.076))
    longitude = float(birth_data.get("longitude", 72.8777))

    # Parse birth date and time
    time_parts = time_str.split(":")
    parsed_time = dt.time(
        int(time_parts[0]),
        int(time_parts[1]),
        int(time_parts[2]) if len(time_parts) > 2 else 0,
    )

    western_calc = WesternCalculationService()
    western_chart = western_calc.calculate(
        birth_date=dt.date.fromisoformat(date_str),
        birth_time=parsed_time,
        latitude=latitude,
        longitude=longitude,
        house_system=WesternHouseSystem.PLACIDUS,
    )

    western_svc = WesternDomainService()
    return western_svc.assess_chart(western_chart)


# ── Numerology System Assessment ─────────────────────────────────────────────


def _run_numerology_assessment(
    chart: dict[str, Any],
    outcome_taxonomy: str,
) -> SystemAssessment:
    """Run the Numerology pipeline using fixture birth data.

    Computes a NumerologyChart from the fixture's birth_data, then
    evaluates it through NumerologyDomainService.
    """
    from jrs.numerology.service import NumerologyDomainService
    from numerology.service import NumerologyCalculationService

    birth_data = chart.get("birth_data", {})
    date_str = birth_data.get("date", "1980-01-01")
    # Use a default name for numerology since fixtures may not have one
    birth_name = chart.get("birth_name", "Default Test Name")

    num_calc = NumerologyCalculationService()
    num_chart = num_calc.calculate(
        birth_date=date_str,
        birth_name=birth_name,
    )

    num_svc = NumerologyDomainService()
    return num_svc.assess_chart(num_chart)


# ── Multi-System Pipeline ────────────────────────────────────────────────────


def run_multi_system_assessment(
    chart: dict[str, Any],
    domain: str,
    outcome_taxonomy: str,
    convergence_svc: ConvergenceService,
    systems: tuple[str, ...] = ("vedic",),
) -> dict[str, Any]:
    """Run the multi-system pipeline for a single outcome.

    Runs the requested systems in parallel (Vedic, Western, Numerology)
    and feeds their SystemAssessments into the IndependenceAnalyzer
    for cross-system convergence analysis.

    Args:
        chart: The validation fixture dict.
        domain: The domain name (e.g., "marriage").
        outcome_taxonomy: The outcome taxonomy string.
        convergence_svc: The ConvergenceService instance.
        systems: Tuple of system names to run.

    Returns:
        A dict with single_system_assessment, system_assessments,
        cross_system_convergence, and timing_match.
    """
    # Get the Vedic (single-system) assessment as baseline
    vedic_assessment = run_single_assessment(
        chart, domain, outcome_taxonomy, convergence_svc,
    )

    # Run each requested system
    system_assessments: dict[str, SystemAssessment] = {}
    system_assessments_list: list[SystemAssessment] = []

    if "vedic" in systems:
        # Build a SystemAssessment from the Vedic DomainAssessment
        vedic_sa = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy=outcome_taxonomy,
            assessment_status=vedic_assessment.get(
                "assessment_status", "NEUTRAL"
            ),
            timing_status=vedic_assessment.get(
                "timing_status", "INACTIVE"
            ),
            provenance=EvidenceProvenance(
                system_type=SystemType.VEDIC,
                source_tradition="BPHS",
            ),
        )
        system_assessments[SystemType.VEDIC.value] = vedic_sa
        system_assessments_list.append(vedic_sa)

    if "western" in systems:
        try:
            western_sa = _run_western_assessment(
                chart, outcome_taxonomy,
            )
            system_assessments[SystemType.WESTERN.value] = western_sa
            system_assessments_list.append(western_sa)
        except Exception:
            # Western assessment may fail for some fixtures
            pass

    if "numerology" in systems:
        try:
            num_sa = _run_numerology_assessment(
                chart, outcome_taxonomy,
            )
            system_assessments[SystemType.NUMEROLOGY.value] = num_sa
            system_assessments_list.append(num_sa)
        except Exception:
            pass

    # Compute cross-system convergence if multiple systems
    cross_system: dict[str, Any] = {}
    if len(system_assessments_list) >= 2:
        analyzer = IndependenceAnalyzer()
        provenances = [
            sa.provenance
            for sa in system_assessments_list
            if sa.provenance is not None
        ]
        raw_convergence = compute_convergence_score(system_assessments)
        independence = analyzer.calculate_collective_independence(
            provenances
        )
        adjusted_convergence = raw_convergence * independence

        cross_system = {
            "raw_convergence": round(raw_convergence, 6),
            "independence_score": round(independence, 6),
            "adjusted_convergence": round(adjusted_convergence, 6),
            "systems": [
                sa.system_type.value for sa in system_assessments_list
            ],
        }

    return {
        "single_system_assessment": vedic_assessment,
        "system_assessments": {
            k: v.to_dict() for k, v in system_assessments.items()
        },
        "cross_system_convergence": cross_system,
        "assessment_status": vedic_assessment.get(
            "assessment_status", "NEUTRAL"
        ),
        "timing_status": vedic_assessment.get(
            "timing_status", "INACTIVE"
        ),
    }


# ── Calibration Runner ───────────────────────────────────────────────────────


def _run_single_system_calibration(
    systems: tuple[str, ...],
) -> CalibrationReport:
    """Run calibration for a specific system configuration.

    Args:
        systems: Tuple of system names (e.g., ("vedic",) or
            ("vedic", "western", "numerology")).

    Returns:
        A CalibrationReport with per-domain and per-outcome metrics.
    """
    from datetime import UTC, datetime

    convergence_svc = ConvergenceService()
    all_domain_metrics: list[DomainMetrics] = []

    fixture_map = discover_fixtures()
    is_multi = len(systems) > 1

    for domain, fixture_paths in sorted(fixture_map.items()):
        all_outcome_metrics: list[OutcomeMetrics] = []

        for fixture_path in fixture_paths:
            chart = load_fixture(fixture_path)
            expected = chart.get("expected_assessments", {})

            for outcome, ground_truth in expected.items():
                gt_status = ground_truth.get(
                    "assessment_status", "NEUTRAL"
                )
                gt_timing = ground_truth.get(
                    "timing_status", "INACTIVE"
                )

                if is_multi:
                    result = run_multi_system_assessment(
                        chart, domain, outcome,
                        convergence_svc, systems,
                    )
                    pred_status = result.get(
                        "assessment_status", "NEUTRAL"
                    )
                    pred_timing = result.get(
                        "timing_status", "INACTIVE"
                    )
                else:
                    predicted = run_single_assessment(
                        chart, domain, outcome, convergence_svc,
                    )
                    pred_status = predicted.get(
                        "assessment_status", "NEUTRAL"
                    )
                    pred_timing = predicted.get(
                        "timing_status", "INACTIVE"
                    )

                timing_match = compute_timing_overlap(
                    gt_timing, pred_timing,
                )

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


def run_calibration() -> CalibrationReport:
    """Run single-system calibration (Vedic only) across all domains.

    Returns:
        A CalibrationReport with per-domain and per-outcome metrics.
    """
    return _run_single_system_calibration(systems=("vedic",))


def run_multi_system_calibration(
    systems: tuple[str, ...] = ("vedic", "western", "numerology"),
) -> CalibrationReport:
    """Run multi-system calibration across all domains.

    Args:
        systems: Tuple of system names to include.

    Returns:
        A CalibrationReport with per-domain and per-outcome metrics.
    """
    return _run_single_system_calibration(systems=systems)


def run_comparative_calibration(
    single_systems: tuple[str, ...] = ("vedic",),
    multi_systems: tuple[str, ...] = (
        "vedic", "western", "numerology",
    ),
) -> ComparativeCalibrationReport:
    """Run comparative calibration: single vs multi-system.

    Produces two CalibrationReports and compares them.

    Args:
        single_systems: Systems for the single-system baseline.
        multi_systems: Systems for the multi-system run.

    Returns:
        A ComparativeCalibrationReport with deltas and verdict.
    """
    single_report = _run_single_system_calibration(single_systems)
    multi_report = _run_single_system_calibration(multi_systems)

    mode = f"{'+'.join(single_systems)}_vs_{'+'.join(multi_systems)}"
    return ComparativeCalibrationReport(
        single_system_report=single_report,
        multi_system_report=multi_report,
        comparison_mode=mode,
    )
