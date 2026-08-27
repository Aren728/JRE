"""Integration tests for JRS-084 Yoga CLI Exposure."""

from __future__ import annotations

import json

import pytest

from jrs.cli import main


class TestYogaCLI:
    """Tests for the --include-yogas CLI flag."""

    def test_without_include_yogas_no_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test A: CLI without --include-yogas -> 'Active Yogas' section is absent."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "Active Yogas" not in output

    def test_without_include_yogas_json_no_key(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test A (JSON): CLI without --include-yogas -> active_yogas key absent."""
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
        assert "active_yogas" not in parsed

    def test_with_include_yogas_text_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test B: CLI with --include-yogas and Sun/Mercury conjunct -> Budhaditya Yoga present."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--include-yogas",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        assert "Active Yogas" in output
        assert "Budhaditya Yoga" in output

    def test_with_include_yogas_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test B (JSON): CLI with --include-yogas -> active_yogas array with Budhaditya."""
        rc = main([
            "--birth-date", "28-09-1979",
            "--birth-time", "18:24",
            "--place", "Mumbai, India",
            "--query", "career",
            "--include-yogas",
            "--json",
        ])
        assert rc == 0
        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "active_yogas" in parsed
        yogas = parsed["active_yogas"]
        names = [y["yoga_name"] for y in yogas]
        assert "Budhaditya Yoga" in names
