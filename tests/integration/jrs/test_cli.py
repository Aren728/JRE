"""Integration tests for JRS CLI entry point."""

from __future__ import annotations

import json

import pytest

from jrs.cli import (
    _default_facts_for_query,
    _evaluate_domain,
    _format_text_report,
    _run_assessment,
    build_parser,
    main,
)


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
        ])
        assert args.birth_date == "28-09-1979"
        assert args.birth_time == "18:24"
        assert args.place == "Mumbai, India"
        assert args.query == "career"
        assert args.json_output is False

    def test_json_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "wealth",
            "--json",
        ])
        assert args.json_output is True

    def test_invalid_query(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([
                "--birth-date", "28-09-1979",
                "--birth-time", "18:24",
                "--place", "Mumbai, India",
                "--query", "invalid_query",
            ])


class TestDefaultFacts:
    """Tests for default fact generation."""

    def test_career_facts(self) -> None:
        facts = _default_facts_for_query("career")
        assert "10th_lord_in_kendra_or_trikona" in facts
        assert facts["10th_lord_in_kendra_or_trikona"] is True

    def test_wealth_facts(self) -> None:
        facts = _default_facts_for_query("wealth")
        assert "2nd_lord_in_11th" in facts

    def test_unknown_query(self) -> None:
        facts = _default_facts_for_query("unknown")
        assert facts == {}


class TestEvaluateDomain:
    """Tests for domain evaluation routing."""

    def test_wealth_evaluation(self) -> None:
        records = _evaluate_domain("wealth", {"2nd_lord_in_11th": True})
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert "WEALTH_ACCUMULATION" in outcomes

    def test_career_evaluation(self) -> None:
        records = _evaluate_domain(
            "career", {"sun_strong": True, "sun_10th_connection": True},
        )
        assert len(records) > 0

    def test_education_evaluation(self) -> None:
        records = _evaluate_domain("education", {"4th_lord_in_kendra": True})
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert "HIGHER_EDUCATION" in outcomes

    def test_migration_evaluation(self) -> None:
        records = _evaluate_domain("migration", {"rahu_in_12th": True})
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert "FOREIGN_SETTLEMENT" in outcomes

    def test_empty_facts(self) -> None:
        records = _evaluate_domain("wealth", {})
        assert records == ()


class TestRunAssessment:
    """Tests for full pipeline assessment."""

    def test_wealth_assessment(self) -> None:
        result = _run_assessment(
            domain_key="wealth",
            facts={"2nd_lord_in_11th": True},
            outcome_taxonomy="WEALTH_ACCUMULATION",
            event_windows=(),
        )
        assert "assessment_status" in result
        assert "timing_status" in result
        assert "overall_evidence_strength" in result
        assert "dimensions" in result

    def test_education_assessment(self) -> None:
        result = _run_assessment(
            domain_key="education",
            facts={"4th_lord_in_kendra": True},
            outcome_taxonomy="HIGHER_EDUCATION",
            event_windows=(),
        )
        assert result["assessment_status"] in (
            "WEAKLY_SUPPORTED", "SUPPORTED", "STRONGLY_SUPPORTED",
            "NEUTRAL", "CONTRADICTED", "STRONGLY_CONTRADICTED",
        )

    def test_deterministic_output(self) -> None:
        facts = {"2nd_lord_in_11th": True}
        r1 = _run_assessment("wealth", facts, "WEALTH_ACCUMULATION", ())
        r2 = _run_assessment("wealth", facts, "WEALTH_ACCUMULATION", ())
        assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


class TestFormatTextReport:
    """Tests for text report formatting."""

    def test_report_contains_key_sections(self) -> None:
        assessment = {
            "outcome_taxonomy": "WEALTH_ACCUMULATION",
            "assessment_status": "WEAKLY_SUPPORTED",
            "timing_status": "INACTIVE",
            "overall_evidence_strength": "MODERATE",
            "dimensions": {
                "supporting_count": 2,
                "contradicting_count": 0,
                "mitigations": 0,
                "independent_channels": 1,
                "source_confidence": "HIGH",
                "timing_convergence_count": 0,
            },
        }
        report = _format_text_report(
            assessment, "28-09-1979", "18:24", "Mumbai, India", "wealth",
            {"2nd_lord_in_11th": True},
        )
        assert "JRS ASSESSMENT" in report
        assert "Question:" in report
        assert "Wealth" in report
        assert "Assessment:" in report
        assert "WEAKLY_SUPPORTED" in report
        assert "Evidence:" in report
        assert "Supporting channels:" in report
        assert "Key factors:" in report
        assert "Classical sources:" in report
        assert "Timing:" in report
        assert "Limitations:" in report


class TestMainEndToEnd:
    """End-to-end CLI tests."""

    def test_career_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
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

    def test_career_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
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
        assert parsed["query"] == "career"
        assert parsed["birth_data"]["date"] == "28-09-1979"
        assert parsed["birth_data"]["place"] == "Mumbai, India"

    def test_wealth_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "15-01-1990",
            "--birth-time", "10:30",
            "--place", "Delhi, India",
            "--query", "wealth",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "JRS ASSESSMENT" in output
        assert "Wealth" in output

    def test_education_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "15-01-1990",
            "--birth-time", "10:30",
            "--place", "Delhi, India",
            "--query", "education",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["domain"] == "education"
        assert "HIGHER_EDUCATION" in parsed["assessment"]["outcome_taxonomy"]

    def test_migration_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "15-01-1990",
            "--birth-time", "10:30",
            "--place", "Delhi, India",
            "--query", "migration",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["domain"] == "migration"
        assert "FOREIGN_SETTLEMENT" in parsed["assessment"]["outcome_taxonomy"]

    def test_children_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "15-01-1990",
            "--birth-time", "10:30",
            "--place", "Delhi, India",
            "--query", "children",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["domain"] == "progeny"
        assert "EASY_CONCEPTION" in parsed["assessment"]["outcome_taxonomy"]

    def test_transitions_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([
            "--birth-date", "15-01-1990",
            "--birth-time", "10:30",
            "--place", "Delhi, India",
            "--query", "transitions",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["domain"] == "transitions"
        assert "LIFE_PHASE_SHIFT" in parsed["assessment"]["outcome_taxonomy"]

    def test_yoga_in_assessment_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test A: Full orchestrator output includes Yoga domain assessment."""
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
        # Yoga domain should be registered and present in assessment
        assert "Yoga" in parsed["assessment"]
        yoga_data = parsed["assessment"]["Yoga"]
        # Yoga assessment should contain valid evidence dimensions
        assert "dimensions" in yoga_data
        dims = yoga_data["dimensions"]
        assert "supporting_count" in dims
