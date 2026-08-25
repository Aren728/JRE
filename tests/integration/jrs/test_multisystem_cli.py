"""Integration tests for JRS-070: Multi-System CLI Integration.

Tests the --systems flag, multi-system convergence calculation,
independence penalty display, and provenance attribution.
"""

from __future__ import annotations

import json

import pytest

from jrs.cli import (
    _build_cross_system_result,
    build_parser,
    main,
)
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
)
from jrs.multisystem.service import IndependenceAnalyzer

# ── Parser Tests ─────────────────────────────────────────────────────────────


class TestParserMultiSystemFlag:
    """Tests for the --systems CLI flag."""

    def test_default_system_is_vedic(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
        ])
        assert args.systems == "vedic"

    def test_systems_flag_accepted(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western",
        ])
        assert args.systems == "vedic,western"

    def test_three_systems_accepted(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic,western,numerology",
        ])
        assert args.systems == "vedic,western,numerology"

    def test_format_json_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--format", "json",
        ])
        assert args.format == "json"

    def test_format_text_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--format", "text",
        ])
        assert args.format == "text"

    def test_json_flag_still_works(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--json",
        ])
        assert args.json_output is True

    def test_invalid_system_rejected(self) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "invalid_system",
        ])
        assert rc == 1


# ── Single-System Backward Compatibility ─────────────────────────────────────


class TestSingleSystemBackwardCompat:
    """Verify single-system usage (default: vedic) continues to work unchanged."""

    def test_default_vedic_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
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

    def test_default_vedic_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
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
        assert "birth_data" in parsed
        assert parsed["systems"] == ["vedic"]
        assert "cross_system_convergence" not in parsed

    def test_explicit_single_system_vedic(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "vedic",
            "--json",
        ])
        assert rc == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["systems"] == ["vedic"]
        assert "cross_system_convergence" not in parsed

    def test_single_western_system(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "western",
            "--json",
        ])
        assert rc == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["systems"] == ["western"]
        assert "cross_system_convergence" not in parsed

    def test_single_numerology_system(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--systems", "numerology",
            "--json",
        ])
        assert rc == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["systems"] == ["numerology"]
        assert "cross_system_convergence" not in parsed


# ── Multi-System Convergence ────────────────────────────────────────────────


class TestMultiSystemConvergence:
    """Verify multi-system usage produces correct convergence calculations."""

    def test_vedic_western_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ])
        assert rc == 0
        parsed = json.loads(capsys.readouterr().out)
        assert "system_assessments" in parsed
        assert "cross_system_convergence" in parsed
        assert "VEDIC" in parsed["system_assessments"]
        assert "WESTERN" in parsed["system_assessments"]
        conv = parsed["cross_system_convergence"]
        assert 0.0 <= conv["raw_convergence"] <= 1.0
        assert 0.0 <= conv["independence_score"] <= 1.0
        assert 0.0 <= conv["adjusted_convergence"] <= 1.0

    def test_three_system_json(self, capsys: pytest.CaptureFixture[str]) -> None:
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
        parsed = json.loads(capsys.readouterr().out)
        assert len(parsed["system_assessments"]) == 3
        conv = parsed["cross_system_convergence"]
        assert len(conv["systems"]) == 3

    def test_vedic_western_text(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "INDIVIDUAL SYSTEM ASSESSMENTS" in output
        assert "CROSS-SYSTEM CONVERGENCE" in output
        assert "VEDIC" in output
        assert "WESTERN" in output

    def test_adjusted_convergence_leq_raw(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Adjusted convergence must never exceed raw convergence."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ])
        assert rc == 0
        conv = json.loads(capsys.readouterr().out)["cross_system_convergence"]
        assert conv["adjusted_convergence"] <= conv["raw_convergence"]


# ── Independence Penalty Display ────────────────────────────────────────────


class TestIndependencePenalty:
    """Verify the independence penalty is correctly calculated and displayed."""

    def test_vedic_western_independence_less_than_one(self) -> None:
        """Vedic and Western share derivative roots, so independence < 1.0."""
        analyzer = IndependenceAnalyzer()
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC, source_tradition="BPHS",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN, source_tradition="LILLY",
        )
        independence = analyzer.calculate_collective_independence(
            [prov_vedic, prov_western],
        )
        assert independence < 1.0
        assert independence > 0.0

    def test_numerology_independence_with_astrology(self) -> None:
        """Numerology shares no roots with astrology, so independence = 1.0."""
        analyzer = IndependenceAnalyzer()
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY, source_tradition="PYTHAGOREAN",
        )
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC, source_tradition="BPHS",
        )
        independence = analyzer.calculate_collective_independence(
            [prov_num, prov_vedic],
        )
        assert independence == 1.0

    def test_independence_penalty_in_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """JSON output must include independence score showing the penalty."""
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ])
        conv = json.loads(capsys.readouterr().out)["cross_system_convergence"]
        assert conv["independence_score"] < 1.0
        assert conv["adjusted_convergence"] < conv["raw_convergence"]

    def test_independence_penalty_in_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Text output must show the independence score."""
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
        ])
        output = capsys.readouterr().out
        assert "Independence score:" in output
        assert "Adjusted convergence:" in output


# ── Provenance Attribution ──────────────────────────────────────────────────


class TestProvenanceAttribution:
    """Verify provenance is correctly attributed for each piece of evidence."""

    def test_vedic_provenance_source(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ])
        parsed = json.loads(capsys.readouterr().out)
        vedic = parsed["system_assessments"]["VEDIC"]
        assert vedic["provenance"]["system_type"] == "VEDIC"
        assert vedic["provenance"]["source_tradition"] == "BPHS"

    def test_western_provenance_source(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ])
        parsed = json.loads(capsys.readouterr().out)
        western = parsed["system_assessments"]["WESTERN"]
        assert western["provenance"]["system_type"] == "WESTERN"
        assert western["provenance"]["source_tradition"] in ("LILLY", "PTOLEMY")

    def test_numerology_provenance_source(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--birth-name", "Raj Kumar Singh",
            "--systems", "vedic,numerology",
            "--json",
        ])
        parsed = json.loads(capsys.readouterr().out)
        num = parsed["system_assessments"]["NUMEROLOGY"]
        assert num["provenance"]["system_type"] == "NUMEROLOGY"
        assert num["provenance"]["source_tradition"] == "PYTHAGOREAN"

    def test_provenance_shown_in_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
        ])
        output = capsys.readouterr().out
        assert "Source: BPHS" in output
        assert "Source: LILLY" in output or "Source: PTOLEMY" in output

    def test_each_system_has_provenance(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([
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
        parsed = json.loads(capsys.readouterr().out)
        for sys_name, assessment in parsed["system_assessments"].items():
            assert assessment["provenance"] is not None, (
                f"{sys_name} missing provenance"
            )
            assert assessment["provenance"]["source_tradition"]


# ── Format Flag Tests ───────────────────────────────────────────────────────


class TestFormatFlag:
    """Verify --format flag works for text and JSON output."""

    def test_format_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--format", "json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "assessment" in parsed

    def test_format_text(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--format", "text",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "JRS ASSESSMENT" in output

    def test_format_json_overrides_json_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--format takes precedence over --json."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--json",
            "--format", "text",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "JRS ASSESSMENT" in output


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestDeterminism:
    """Verify deterministic output across runs."""

    def test_multi_system_deterministic(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = [
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--latitude", "28.6139",
            "--longitude", "77.2090",
            "--systems", "vedic,western",
            "--json",
        ]
        main(args)
        output1 = json.loads(capsys.readouterr().out)
        main(args)
        output2 = json.loads(capsys.readouterr().out)
        assert (
            output1["cross_system_convergence"]["adjusted_convergence"]
            == output2["cross_system_convergence"]["adjusted_convergence"]
        )
        assert (
            output1["cross_system_convergence"]["independence_score"]
            == output2["cross_system_convergence"]["independence_score"]
        )

    def test_three_system_deterministic(self, capsys: pytest.CaptureFixture[str]) -> None:
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
        output1 = json.loads(capsys.readouterr().out)
        main(args)
        output2 = json.loads(capsys.readouterr().out)
        assert (
            output1["cross_system_convergence"]
            == output2["cross_system_convergence"]
        )


# ── Cross-System Result Builder ─────────────────────────────────────────────


class TestCrossSystemResultBuilder:
    """Unit tests for _build_cross_system_result."""

    def test_two_systems_produces_result(self) -> None:
        assessments = (
            SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_ASCENT",
                assessment_status="SUPPORTED",
                timing_status="INACTIVE",
                provenance=EvidenceProvenance(
                    system_type=SystemType.VEDIC,
                    source_tradition="BPHS",
                ),
            ),
            SystemAssessment(
                system_type=SystemType.WESTERN,
                outcome_taxonomy="CAREER_PROMINENCE",
                assessment_status="SUPPORTED",
                timing_status="INACTIVE",
                provenance=EvidenceProvenance(
                    system_type=SystemType.WESTERN,
                    source_tradition="LILLY",
                ),
            ),
        )
        result = _build_cross_system_result(assessments)
        assert "raw_convergence" in result
        assert "independence_score" in result
        assert "adjusted_convergence" in result
        assert result["adjusted_convergence"] <= result["raw_convergence"]

    def test_single_system_returns_empty(self) -> None:
        assessments = (
            SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_ASCENT",
                assessment_status="SUPPORTED",
                timing_status="INACTIVE",
            ),
        )
        result = _build_cross_system_result(assessments)
        assert result == {}

    def test_independence_affects_convergence(self) -> None:
        """Vedic+Western (shared roots) should have lower independence
        than independent systems, resulting in more dampening."""
        vedic_western = (
            SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_ASCENT",
                assessment_status="SUPPORTED",
                timing_status="INACTIVE",
                provenance=EvidenceProvenance(
                    system_type=SystemType.VEDIC, source_tradition="BPHS",
                ),
            ),
            SystemAssessment(
                system_type=SystemType.WESTERN,
                outcome_taxonomy="CAREER_PROMINENCE",
                assessment_status="SUPPORTED",
                timing_status="INACTIVE",
                provenance=EvidenceProvenance(
                    system_type=SystemType.WESTERN, source_tradition="LILLY",
                ),
            ),
        )
        result_vw = _build_cross_system_result(vedic_western)
        assert result_vw["independence_score"] < 1.0
        assert result_vw["adjusted_convergence"] < result_vw["raw_convergence"]
