"""Phase 11A: JRE-BENCH-002 pre-registration integrity tests.

Recomputes the locked power-analysis numbers from first principles and
enforces agreement between the pre-registration document, the power
tool, and the sealed-analysis methodology. This is the test layer that
makes the pre-registration binding: if any locked number drifts, the
confirmatory analysis loses its pre-registered status.
"""

from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PREREG_DOC = (
    REPO_ROOT / "docs" / "validation" / "phase_11a_bench002_preregistration.md"
)
_POWER_SCRIPT = REPO_ROOT / "scripts" / "bench002_power.py"
_spec = importlib.util.spec_from_file_location("bench002_power", _POWER_SCRIPT)
bench002 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(bench002)


class TestExactMcNemarReference:
    def test_min_discordant_for_significance_is_6(self) -> None:
        assert bench002.min_discordant_for_significance() == 6
        # Direct verification of the locked claim p = 2 * 0.5^6.
        assert bench002.exact_p_all_one_direction(6) == pytest.approx(0.03125)
        assert bench002.exact_p_all_one_direction(5) > 0.05
        assert bench002.exact_p_all_one_direction(6) <= 0.05

    def test_power_sign_flip_matches_comb_enumeration(self) -> None:
        """Independent recomputation of the sign-flip power integral."""
        for m, pi in [(6, 0.9), (9, 0.95), (12, 0.9), (20, 0.8)]:
            # Independent implementation: enumerate b ~ Bin(m, pi),
            # reject when the doubled tail at min(b, m-b) <= alpha.
            mass = 0.0
            for b in range(m + 1):
                n, k = m, min(b, m - b)
                p_val = min(
                    1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) * 0.5**n
                )
                if p_val <= 0.05:
                    mass += math.comb(m, b) * pi**b * (1.0 - pi) ** (m - b)
            assert bench002.power_sign_flip(m, pi) == pytest.approx(mass, abs=1e-9)

    def test_locked_power_table_values(self) -> None:
        # §3 of the pre-registration locks these exact values.
        assert bench002.power_sign_flip(12, 0.9) == pytest.approx(0.8891, abs=5e-5)
        assert bench002.power_sign_flip(9, 0.95) == pytest.approx(0.9288, abs=5e-5)
        assert bench002.power_sign_flip(20, 0.8) == pytest.approx(0.8042, abs=5e-5)
        assert bench002.power_sign_flip(6, 1.0) == pytest.approx(1.0)

    def test_min_m_for_target_power_at_pi_09_is_12(self) -> None:
        m = 6
        while bench002.power_sign_flip(m, 0.9) < 0.80:
            m += 1
        assert m == 12


class TestRecommendationArithmetic:
    def test_events_needed_rounds_to_corpus_blocks(self) -> None:
        # 12 target discordant pairs at density 2/120 -> 720 events.
        assert bench002.events_needed(12) == 720
        assert bench002.events_needed(12) % 120 == 0

    def test_recommendation_matches_preregistration(self) -> None:
        report = bench002.build_report()
        rec = report["recommendation"]
        assert rec["target_discordant_pairs"] == 12
        assert rec["scored_events_needed"] == 720
        assert rec["charts_needed"] == 240
        assert rec["power_at_target"] == pytest.approx(0.8891, abs=5e-4)


class TestPreregistrationDocument:
    @pytest.fixture(scope="class")
    def doc_text(self) -> str:
        assert PREREG_DOC.exists(), "pre-registration document missing"
        return PREREG_DOC.read_text(encoding="utf-8")

    def test_status_is_pre_registered(self, doc_text: str) -> None:
        assert "`PRE_REGISTERED`" in doc_text
        assert "JRE-BENCH-002" in doc_text

    def test_locked_numbers_appear_in_document(self, doc_text: str) -> None:
        # Every headline number from the power tool must be present.
        for number in (
            "0.03125",  # minimal-significance p at m=6
            "0.8891",  # power at m=12, pi=0.9
            "720 scored events",
            "240 charts",
            "m = 6",
            "m = 12",
        ):
            assert number in doc_text, number

    def test_power_table_rows_match_tool(self, doc_text: str) -> None:
        """The markdown table's m=6 and m=12 rows match the exact tool."""
        for m, pi, expected in [(6, 0.9, 0.5314), (12, 0.9, 0.8891), (20, 0.9, 0.9887)]:
            row = next(
                line
                for line in doc_text.splitlines()
                if re.match(rf"^\|\s*{m}\s*\|", line)
            )
            # pi=0.9 is the 5th numeric column.
            cells = [c.strip() for c in row.split("|")]
            assert float(cells[5]) == pytest.approx(expected, abs=5e-5), (m, pi)

    def test_no_peeking_protocol_locked(self, doc_text: str) -> None:
        assert "Single confirmatory analysis" in doc_text
        assert "No interim analyses" in doc_text
        assert "analysis-only diff" in doc_text

    def test_deviation_log_present_and_empty(self, doc_text: str) -> None:
        section = doc_text.split("## 7. Deviation Log")[1].split("## 8.")[0]
        # Header row + separator only: no deviation entries at lock time.
        rows = [
            line
            for line in section.splitlines()
            if line.strip().startswith("|") and "---" not in line and "Date" not in line
        ]
        assert rows == []

    def test_ablation_methodology_unchanged(self, doc_text: str) -> None:
        assert "scripts/ablation_matrix.py" in doc_text
        assert "two-sided binomial McNemar" in doc_text
        assert "JRE-ABLATION-001" in doc_text
