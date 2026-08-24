"""Integration tests for JRS-070: Multi-System CLI Integration.

Tests the --systems argument, individual SystemAssessment display,
Cross-System Convergence section, source attributions, and
deterministic output.
"""

from __future__ import annotations

import json

import pytest

from jrs.cli import (
    _build_cross_system_result,
    _run_multi_system,
    build_parser,
    main,
)
from jrs.multisystem.models import SystemAssessment, SystemType

# ── Parser Tests ─────────────────────────────────────────────────────────────


class TestParserMultiSystem:
    """Tests for the --systems CLI argument."""

    def test_default_systems(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
        ])
        assert args.systems == "vedic"

    def test_multi_systems_argument(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western",
        ])
        assert args.systems == "vedic,western"

    def test_western_only(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "western",
        ])
        assert args.systems == "western"

    def test_invalid_system_rejected(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "invalid_system",
        ])
        assert rc == 1
        captured = capsys.readouterr()
        assert "Unknown system" in captured.err


# ── Pipeline Function Tests ──────────────────────────────────────────────────


class TestMultiSystemPipeline:
    """Tests for _run_multi_system pipeline."""

    def test_returns_vedic_and_western(self) -> None:
        assessments = _run_multi_system(
            query="career",
            domain_key="career",
            facts={"sun_strong": True, "sun_10th_connection": True},
            outcome_taxonomy="CAREER_ASCENT",
            event_windows=(),
            systems=["vedic", "western"],
        )
        assert len(assessments) == 2
        system_types = {a.system_type for a in assessments}
        assert SystemType.VEDIC in system_types
        assert SystemType.WESTERN in system_types

    def test_vedic_only(self) -> None:
        assessments = _run_multi_system(
            query="career",
            domain_key="career",
            facts={"sun_strong": True},
            outcome_taxonomy="CAREER_ASCENT",
            event_windows=(),
            systems=["vedic"],
        )
        assert len(assessments) == 1
        assert assessments[0].system_type is SystemType.VEDIC

    def test_western_only(self) -> None:
        assessments = _run_multi_system(
            query="career",
            domain_key="career",
            facts={"sun_strong": True},
            outcome_taxonomy="CAREER_ASCENT",
            event_windows=(),
            systems=["western"],
        )
        assert len(assessments) == 1
        assert assessments[0].system_type is SystemType.WESTERN

    def test_all_assessments_have_provenance(self) -> None:
        assessments = _run_multi_system(
            query="wealth",
            domain_key="wealth",
            facts={"2nd_lord_in_11th": True},
            outcome_taxonomy="WEALTH_ACCUMULATION",
            event_windows=(),
            systems=["vedic", "western"],
        )
        for a in assessments:
            assert a.provenance is not None
            assert a.provenance.system_type is a.system_type


class TestCrossSystemResult:
    """Tests for _build_cross_system_result."""

    def test_returns_empty_for_single_system(self) -> None:
        assessment = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
        )
        result = _build_cross_system_result((assessment,))
        assert result == {}

    def test_returns_convergence_for_two_systems(self) -> None:
        vedic = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
            provenance=None,
        )
        western = SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
            provenance=None,
        )
        result = _build_cross_system_result((vedic, western))
        assert "raw_convergence" in result
        assert "independence_score" in result
        assert "adjusted_convergence" in result
        assert "individual_assessments" in result

    def test_adjusted_leq_raw_convergence(self) -> None:
        """Proving the independence penalty is displayed."""
        vedic = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
        )
        western = SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
        )
        result = _build_cross_system_result((vedic, western))
        assert result["adjusted_convergence"] <= result["raw_convergence"]

    def test_independence_score_is_valid(self) -> None:
        vedic = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
        )
        western = SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="CAREER_ASCENT",
            assessment_status="SUPPORTED",
        )
        result = _build_cross_system_result((vedic, western))
        assert 0.0 <= result["independence_score"] <= 1.0


# ── End-to-End CLI Tests ────────────────────────────────────────────────────


class TestCLIMultiSystem:
    """End-to-end CLI tests with --systems argument."""

    def test_vedic_western_json_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "system_assessments" in parsed
        assert "cross_system_convergence" in parsed
        assert "VEDIC" in parsed["system_assessments"]
        assert "WESTERN" in parsed["system_assessments"]
        assert parsed["systems"] == ["vedic", "western"]

    def test_vedic_western_text_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "INDIVIDUAL SYSTEM ASSESSMENTS" in output
        assert "CROSS-SYSTEM CONVERGENCE" in output
        assert "VEDIC" in output
        assert "WESTERN" in output

    def test_cross_system_convergence_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "wealth",
            "--systems", "vedic,western",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        convergence = parsed["cross_system_convergence"]
        assert convergence["adjusted_convergence"] <= convergence["raw_convergence"]
        assert 0.0 <= convergence["independence_score"] <= 1.0

    def test_source_attributions_in_json(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "marriage",
            "--systems", "vedic,western",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        vedic = parsed["system_assessments"]["VEDIC"]
        western = parsed["system_assessments"]["WESTERN"]
        assert vedic["provenance"]["source_tradition"] == "BPHS"
        assert western["provenance"]["source_tradition"] == "LILLY"

    def test_single_system_backward_compatible(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Default --systems vedic should produce the same output structure."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "JRS ASSESSMENT" in output
        assert "Career" in output

    def test_single_system_json_backward_compatible(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Default --systems vedic JSON should use 'assessment' key."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "assessment" in parsed
        assert "system_assessments" not in parsed

    def test_multiple_queries_with_multi_system(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify multi-system works for different query domains."""
        for query in ("career", "wealth", "marriage", "education"):
            rc = main([
                "--birth-date", "15-01-1990",
                "--birth-time", "10:30",
                "--place", "Delhi, India",
                "--query", query,
                "--systems", "vedic,western",
                "--json",
            ])
            assert rc == 0
            output = capsys.readouterr().out
            parsed = json.loads(output)
            assert "system_assessments" in parsed
            assert "cross_system_convergence" in parsed

    def test_deterministic_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Multi-system output should be deterministic."""
        args = [
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western",
            "--json",
        ]
        main(args)
        output1 = capsys.readouterr().out
        main(args)
        output2 = capsys.readouterr().out
        parsed1 = json.loads(output1)
        parsed2 = json.loads(output2)
        # The deterministic_id and scores should be identical
        assert (
            parsed1["cross_system_convergence"]["adjusted_convergence"]
            == parsed2["cross_system_convergence"]["adjusted_convergence"]
        )
        assert (
            parsed1["cross_system_convergence"]["independence_score"]
            == parsed2["cross_system_convergence"]["independence_score"]
        )
