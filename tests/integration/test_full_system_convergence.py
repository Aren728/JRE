"""Full System Integration & Convergence Validation (JRS-084).

Tests the complete multi-system pipeline (Vedic + Western + Numerology)
combined with the Yoga Domain, asserting:
- All three system assessments are present
- Multi-System Independence Score is calculated
- Yoga Domain output contains 4-fold distinction
"""

from __future__ import annotations

import pytest

from jrs.cli import (
    _build_cross_system_result,
    _run_multi_system,
    _run_assessment,
)
from jrs.domains.yoga.service import YogaDomainService
from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
    compute_independence_score,
)
from jrs.multisystem.service import IndependenceAnalyzer


# ── Mock Birth Chart ─────────────────────────────────────────────────────────

MOCK_CHART = {
    "birth_date": "28-09-1979",
    "birth_time": "18:24",
    "place": "Mumbai, India",
    "latitude": 19.076,
    "longitude": 72.8777,
    "birth_name": "Raj Kumar Singh",
    "query": "career",
    "domain_key": "career",
    "facts": {
        "10th_lord_in_kendra_or_trikona": True,
        "sun_strong": True,
        "sun_10th_connection": True,
    },
    "outcome_taxonomy": "CAREER_ASCENT",
}


# ── Yoga Domain Facts ────────────────────────────────────────────────────────

YOGA_FACTS = {
    "lagna": "MESHA",
    "planets": {
        "SUN": {"rashi": "MAKARA", "house": 10, "combust": False, "debilitated": False},
        "SATURN": {"rashi": "MESHA", "house": 1, "combust": False, "debilitated": False},
    },
    "active_dasha_lord": "SATURN",
    "transit_planet": "JUPITER",
}


# ── Helper Functions ─────────────────────────────────────────────────────────


def _run_full_pipeline(
    systems: list[str],
) -> dict[str, object]:
    """Run the full multi-system pipeline and return structured results.

    Returns a dict containing:
    - system_assessments: tuple of SystemAssessment objects
    - cross_system: dict with independence_score and convergence metrics
    - vedic_assessment: dict from the Vedic domain assessment
    - yoga_assessment: DomainAssessment from the Yoga domain
    """
    assessments = _run_multi_system(
        query=MOCK_CHART["query"],
        domain_key=MOCK_CHART["domain_key"],
        facts=MOCK_CHART["facts"],
        outcome_taxonomy=MOCK_CHART["outcome_taxonomy"],
        event_windows=(),
        systems=systems,
        birth_date=MOCK_CHART["birth_date"],
        birth_time=MOCK_CHART["birth_time"],
        latitude=MOCK_CHART["latitude"],
        longitude=MOCK_CHART["longitude"],
        birth_name=MOCK_CHART["birth_name"],
    )

    cross_system = _build_cross_system_result(assessments)

    vedic_assessment = None
    for sa in assessments:
        if sa.system_type is SystemType.VEDIC:
            vedic_assessment = _run_assessment(
                domain_key=MOCK_CHART["domain_key"],
                facts=MOCK_CHART["facts"],
                outcome_taxonomy=MOCK_CHART["outcome_taxonomy"],
                event_windows=(),
            )
            break

    yoga_svc = YogaDomainService()
    yoga_assessment = yoga_svc.assess(YOGA_FACTS)

    return {
        "system_assessments": assessments,
        "cross_system": cross_system,
        "vedic_assessment": vedic_assessment,
        "yoga_assessment": yoga_assessment,
    }


# ── Test Class ───────────────────────────────────────────────────────────────


class TestFullSystemIntegration:
    """Full system integration test: Vedic + Western + Numerology + Yoga."""

    def test_all_three_system_assessments_present(self) -> None:
        """Vedic, Western, and Numerology assessments must be present."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        assessments = result["system_assessments"]
        system_types = {a.system_type for a in assessments}

        assert SystemType.VEDIC in system_types, "Vedic assessment missing"
        assert SystemType.WESTERN in system_types, "Western assessment missing"
        assert SystemType.NUMEROLOGY in system_types, "Numerology assessment missing"
        assert len(assessments) == 3

    def test_cross_system_independence_score_calculated(self) -> None:
        """Multi-System Independence Score must be calculated and present."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        cross_system = result["cross_system"]

        assert "independence_score" in cross_system, (
            "independence_score not in cross_system output"
        )
        independence = cross_system["independence_score"]
        assert isinstance(independence, (int, float))
        assert 0.0 <= independence <= 1.0, (
            f"independence_score out of range: {independence}"
        )

    def test_cross_system_convergence_score_calculated(self) -> None:
        """Adjusted convergence score must be calculated."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        cross_system = result["cross_system"]

        assert "adjusted_convergence" in cross_system
        assert "raw_convergence" in cross_system
        assert cross_system["adjusted_convergence"] <= cross_system["raw_convergence"]

    def test_yoga_domain_output_has_four_fold_distinction(self) -> None:
        """Yoga Domain output must contain the 4-fold distinction:
        Formation, Strength, Manifestation, Outcome.
        """
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        yoga = result["yoga_assessment"]

        yoga_dict = yoga.to_dict()

        # 1. Formation: check outcome_taxonomy indicates yoga formation
        assert "outcome_taxonomy" in yoga_dict, (
            "Yoga output missing outcome_taxonomy (Formation)"
        )
        assert yoga_dict["outcome_taxonomy"] == "YOGA_FORMATION"

        # 2. Strength: check overall_evidence_strength
        assert "overall_evidence_strength" in yoga_dict, (
            "Yoga output missing overall_evidence_strength (Strength)"
        )
        valid_strengths = {"STRONG", "MODERATE", "WEAK"}
        assert yoga_dict["overall_evidence_strength"] in valid_strengths, (
            f"Invalid strength: {yoga_dict['overall_evidence_strength']}"
        )

        # 3. Manifestation: check timing_status indicates manifestation
        assert "timing_status" in yoga_dict, (
            "Yoga output missing timing_status (Manifestation)"
        )
        valid_timing = {"CONVERGENT", "DIVERGENT", "INACTIVE"}
        assert yoga_dict["timing_status"] in valid_timing, (
            f"Invalid timing_status: {yoga_dict['timing_status']}"
        )

        # 4. Outcome: check assessment_status
        assert "assessment_status" in yoga_dict, (
            "Yoga output missing assessment_status (Outcome)"
        )
        valid_outcomes = {
            "STRONGLY_SUPPORTED", "SUPPORTED", "WEAKLY_SUPPORTED",
            "NEUTRAL", "CONTRADICTED", "STRONGLY_CONTRADICTED",
        }
        assert yoga_dict["assessment_status"] in valid_outcomes, (
            f"Invalid assessment_status: {yoga_dict['assessment_status']}"
        )

    def test_yoga_domain_dimensions_present(self) -> None:
        """Yoga Domain must produce evidence dimensions."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        yoga = result["yoga_assessment"]
        yoga_dict = yoga.to_dict()

        assert "dimensions" in yoga_dict
        dims = yoga_dict["dimensions"]
        assert "supporting_count" in dims
        assert "independent_channels" in dims
        assert "contradicting_count" in dims

    def test_vedic_assessment_included_in_cross_system(self) -> None:
        """Vedic assessment must be included in cross-system convergence."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        cross_system = result["cross_system"]

        assert "individual_assessments" in cross_system
        assert "VEDIC" in cross_system["individual_assessments"]

    def test_independence_analyzer_accepts_all_provenances(self) -> None:
        """IndependenceAnalyzer must accept provenances from all three systems."""
        analyzer = IndependenceAnalyzer()
        provenances = [
            EvidenceProvenance(
                system_type=SystemType.VEDIC,
                source_tradition="BPHS",
            ),
            EvidenceProvenance(
                system_type=SystemType.WESTERN,
                source_tradition="LILLY",
            ),
            EvidenceProvenance(
                system_type=SystemType.NUMEROLOGY,
                source_tradition="PYTHAGOREAN",
            ),
        ]
        collective = analyzer.calculate_collective_independence(provenances)
        assert 0.0 <= collective <= 1.0

    def test_convergence_score_mathematical_invariant(self) -> None:
        """Adjusted convergence must never exceed raw convergence."""
        result = _run_full_pipeline(
            systems=["vedic", "western", "numerology"],
        )
        cross_system = result["cross_system"]

        assert cross_system["adjusted_convergence"] <= cross_system["raw_convergence"]

    def test_yoga_assessment_deterministic(self) -> None:
        """Yoga Domain assessment must be deterministic across runs."""
        yoga_svc = YogaDomainService()
        y1 = yoga_svc.assess(YOGA_FACTS)
        y2 = yoga_svc.assess(YOGA_FACTS)
        assert y1.to_dict() == y2.to_dict()

    def test_vedic_only_pipeline_still_includes_yoga(self) -> None:
        """Even Vedic-only pipeline should include Yoga assessment."""
        result = _run_full_pipeline(systems=["vedic"])
        yoga = result["yoga_assessment"]
        assert yoga.to_dict()["outcome_taxonomy"] == "YOGA_FORMATION"
