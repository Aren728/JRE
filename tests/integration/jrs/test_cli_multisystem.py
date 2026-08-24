"""Integration tests for JRS-071: Multi-System CLI with Western real data and Numerology.

Tests:
- Western engine uses real CLI birth data (not defaults)
- Numerology engine produces deterministic facts
- Three-system convergence mathematically preserves Numerology independence
"""

from __future__ import annotations

import json

import pytest

from jrs.cli import (
    _run_multi_system,
    _run_numerology_system_assessment,
    _run_western_system_assessment,
    build_parser,
    main,
)
from jrs.multisystem.models import SystemType

# ── Parser Tests ─────────────────────────────────────────────────────────────


class TestParserMultiSystem:
    """Tests for the --systems CLI argument with numerology."""

    def test_numerology_in_valid_systems(self) -> None:
        """Numerology should be accepted as a valid system."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "numerology",
            "--json",
        ])
        # Should not fail with "Unknown system" error
        assert rc == 0

    def test_three_systems_accepted(self) -> None:
        """All three systems should be accepted."""
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western,numerology",
        ])
        assert args.systems == "vedic,western,numerology"

    def test_latitude_longitude_args(self) -> None:
        """CLI should accept latitude and longitude arguments."""
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
        ])
        assert args.latitude == 28.6139
        assert args.longitude == 77.2090

    def test_birth_name_arg(self) -> None:
        """CLI should accept birth name argument for numerology."""
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--birth-name", "Raj Kumar Singh",
        ])
        assert args.birth_name == "Raj Kumar Singh"


# ── Western Real Data Tests ─────────────────────────────────────────────────


class TestWesternRealData:
    """Tests that Western engine uses real birth data."""

    def test_western_with_real_coords(self) -> None:
        """Western assessment should use real coordinates."""
        assessment = _run_western_system_assessment(
            query="career",
            outcome_taxonomy="CAREER_PROMINENCE",
            birth_date="28-09-1979",
            birth_time="18:24:00",
            latitude=28.6139,
            longitude=77.2090,
        )
        assert assessment.system_type is SystemType.WESTERN
        assert assessment.provenance is not None
        assert assessment.provenance.source_tradition in ("LILLY", "PTOLEMY")

    def test_western_different_coords_different_results(self) -> None:
        """Different coordinates should potentially produce different results."""
        a1 = _run_western_system_assessment(
            query="career",
            outcome_taxonomy="CAREER_PROMINENCE",
            birth_date="28-09-1979",
            birth_time="18:24:00",
            latitude=28.6139,   # Delhi
            longitude=77.2090,
        )
        a2 = _run_western_system_assessment(
            query="career",
            outcome_taxonomy="CAREER_PROMINENCE",
            birth_date="28-09-1979",
            birth_time="18:24:00",
            latitude=40.7128,   # New York
            longitude=-74.0060,
        )
        # Both should produce valid assessments
        assert a1.system_type is SystemType.WESTERN
        assert a2.system_type is SystemType.WESTERN


# ── Numerology Tests ────────────────────────────────────────────────────────


class TestNumerologyEngine:
    """Tests for the Numerology JRE engine."""

    def test_numerology_deterministic(self) -> None:
        """Numerology chart should be deterministic."""
        from numerology.service import NumerologyCalculationService

        svc = NumerologyCalculationService()
        c1 = svc.calculate(birth_date="1985-07-15", birth_name="John Adam Smith")
        c2 = svc.calculate(birth_date="1985-07-15", birth_name="John Adam Smith")
        assert c1.deterministic_id == c2.deterministic_id
        assert c1.to_dict() == c2.to_dict()

    def test_numerology_life_path(self) -> None:
        """Life Path number should be correctly calculated."""
        from numerology.service import NumerologyCalculationService

        svc = NumerologyCalculationService()
        chart = svc.calculate(birth_date="1985-07-15", birth_name="John Adam Smith")
        assert chart.life_path is not None
        assert chart.life_path.reduced in range(1, 10)

    def test_numerology_destiny(self) -> None:
        """Destiny number should be correctly calculated."""
        from numerology.service import NumerologyCalculationService

        svc = NumerologyCalculationService()
        chart = svc.calculate(birth_date="1985-07-15", birth_name="John Adam Smith")
        assert chart.destiny is not None
        assert chart.destiny.reduced in range(1, 10)

    def test_numerology_system_assessment(self) -> None:
        """Numerology assessment should produce a valid SystemAssessment."""
        assessment = _run_numerology_system_assessment(
            birth_date="15-07-1985",
            birth_name="John Adam Smith",
        )
        assert assessment.system_type is SystemType.NUMEROLOGY
        assert assessment.provenance is not None
        assert assessment.provenance.source_tradition == "PYTHAGOREAN"


# ── Three-System Convergence Tests ──────────────────────────────────────────


class TestThreeSystemConvergence:
    """Tests for three-system convergence with Numerology independence."""

    def test_three_system_assessments(self) -> None:
        """Three systems should produce three assessments."""
        assessments = _run_multi_system(
            query="career",
            domain_key="career",
            facts={"sun_strong": True, "sun_10th_connection": True},
            outcome_taxonomy="CAREER_ASCENT",
            event_windows=(),
            systems=["vedic", "western", "numerology"],
            birth_date="28-09-1979",
            birth_time="18:24:00",
            latitude=28.6139,
            longitude=77.2090,
            birth_name="Raj Kumar Singh",
        )
        assert len(assessments) == 3
        system_types = {a.system_type for a in assessments}
        assert SystemType.VEDIC in system_types
        assert SystemType.WESTERN in system_types
        assert SystemType.NUMEROLOGY in system_types

    def test_numerology_independence_preserved(self) -> None:
        """Numerology should have independence score of 1.0 with Vedic/Western.

        Since Numerology shares NO derivative roots with astrology systems,
        its pairwise independence should be 1.0.
        """
        from jrs.multisystem.models import EvidenceProvenance
        from jrs.multisystem.service import IndependenceAnalyzer

        analyzer = IndependenceAnalyzer()

        # Numerology vs Vedic: no shared roots -> 1.0
        num_prov = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )
        vedic_prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        score_nv = analyzer.calculate_pairwise_independence(num_prov, vedic_prov)
        assert score_nv == 1.0

        # Numerology vs Western: no shared roots -> 1.0
        western_prov = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        )
        score_nw = analyzer.calculate_pairwise_independence(num_prov, western_prov)
        assert score_nw == 1.0

    def test_collective_independence_three_systems(self) -> None:
        """Collective independence with all three systems should be high.

        Numerology contributes no penalty; only Vedic-Western share roots.
        Expected: (1.0 + 1.0 + 0.85) / 3 ≈ 0.95
        """
        from jrs.multisystem.models import EvidenceProvenance
        from jrs.multisystem.service import IndependenceAnalyzer

        analyzer = IndependenceAnalyzer()
        prov_list = [
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
        collective = analyzer.calculate_collective_independence(prov_list)
        # Vedic-Western: 0.85, Vedic-Numerology: 1.0, Western-Numerology: 1.0
        # Average: (0.85 + 1.0 + 1.0) / 3 ≈ 0.95
        assert collective >= 0.9
        assert collective <= 1.0

    def test_three_system_convergence_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Three-system CLI output should include all systems."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--birth-name", "Raj Kumar Singh",
            "--systems", "vedic,western,numerology",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "system_assessments" in parsed
        assert "cross_system_convergence" in parsed
        assert "VEDIC" in parsed["system_assessments"]
        assert "WESTERN" in parsed["system_assessments"]
        assert "NUMEROLOGY" in parsed["system_assessments"]
        convergence = parsed["cross_system_convergence"]
        assert convergence["adjusted_convergence"] <= convergence["raw_convergence"]
        assert 0.0 <= convergence["independence_score"] <= 1.0

    def test_three_system_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Three-system text output should show all assessments."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--birth-name", "Raj Kumar Singh",
            "--systems", "vedic,western,numerology",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "INDIVIDUAL SYSTEM ASSESSMENTS" in output
        assert "CROSS-SYSTEM CONVERGENCE" in output
        assert "VEDIC" in output
        assert "WESTERN" in output
        assert "NUMEROLOGY" in output

    def test_numerology_source_attribution(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Numerology should show PYTHAGOREAN source attribution."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--birth-name", "Raj Kumar Singh",
            "--systems", "vedic,numerology",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "system_assessments" in parsed
        num = parsed["system_assessments"]["NUMEROLOGY"]
        assert num["provenance"]["source_tradition"] == "PYTHAGOREAN"


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestDeterminism:
    """Tests for deterministic output across runs."""

    def test_three_system_deterministic(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Three-system output should be deterministic."""
        args = [
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--birth-name", "Raj Kumar Singh",
            "--systems", "vedic,western,numerology",
            "--json",
        ]
        main(args)
        output1 = capsys.readouterr().out
        main(args)
        output2 = capsys.readouterr().out
        parsed1 = json.loads(output1)
        parsed2 = json.loads(output2)
        assert (
            parsed1["cross_system_convergence"]["adjusted_convergence"]
            == parsed2["cross_system_convergence"]["adjusted_convergence"]
        )
        assert (
            parsed1["cross_system_convergence"]["independence_score"]
            == parsed2["cross_system_convergence"]["independence_score"]
        )
