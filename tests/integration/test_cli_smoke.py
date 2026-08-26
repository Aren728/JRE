"""JRS-086 Multi-System CLI Smoke Test."""

from __future__ import annotations

import json

import pytest

from jrs.cli import main

CLI_BASE_ARGS: list[str] = [
    "--birth-date", "28-09-1979",
    "--birth-time", "18:24",
    "--place", "Mumbai, India",
    "--query", "career",
    "--latitude", "28.6139",
    "--longitude", "77.2090",
    "--birth-name", "Raj Kumar Singh",
]


class TestCLIMultiSystemSmoke:
    """Smoke tests for the CLI multi-system pipeline."""

    def test_cli_multi_system_smoke(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Run CLI with --systems vedic,western,numerology --query career.

        Assert exit code is 0 and output text contains
        'Vedic', 'Western', 'Numerology', and 'Yoga'.
        """
        # ── Text mode: verify Vedic, Western, Numerology ──
        rc = main([
            *CLI_BASE_ARGS,
            "--systems", "vedic,western,numerology",
        ])
        assert rc == 0

        text_output = capsys.readouterr().out
        assert "Vedic" in text_output
        assert "Western" in text_output
        assert "Numerology" in text_output

        # ── JSON mode: verify all systems + convergence ──
        rc2 = main([
            *CLI_BASE_ARGS,
            "--systems", "vedic,western,numerology",
            "--json",
        ])
        assert rc2 == 0

        json_output = capsys.readouterr().out
        parsed = json.loads(json_output)

        assert "VEDIC" in parsed["system_assessments"]
        assert "WESTERN" in parsed["system_assessments"]
        assert "NUMEROLOGY" in parsed["system_assessments"]
        assert "cross_system_convergence" in parsed

        # ── Yoga domain: verify via single-system JSON output ──
        rc3 = main([
            *CLI_BASE_ARGS,
            "--systems", "vedic",
            "--json",
        ])
        assert rc3 == 0

        yoga_json = capsys.readouterr().out
        assert "Yoga" in yoga_json
