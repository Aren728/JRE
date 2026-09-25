"""Phase 10: Ablation analysis unit tests.

Covers the statistical and report logic of scripts/ablation_matrix.py
without executing corpus runs: exact binomial McNemar against
hand-computed values, pairwise delta/verdict classification, seal
anchor agreement with the module constants, and report integrity.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import pytest

from jrs.validation.benchmark import BASELINE_MICRO_F1, F1_TOLERANCE

_SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "ablation_matrix.py"
_spec = importlib.util.spec_from_file_location("ablation_matrix", _SCRIPT)
ablation = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(ablation)

REPORT_JSON = Path(__file__).resolve().parents[4] / "reports" / "ablation_matrix.json"


# ── Exact binomial McNemar ──────────────────────────────────────────────────
class TestMcNemarExact:
    @pytest.mark.parametrize(
        "b,c,expected_p",
        [
            (0, 0, 1.0),
            (1, 3, 0.625),         # 2 * (C(4,0)+C(4,1)) / 2^4 = 10/16
            (0, 8, 0.0078125),     # 2 / 2^8
            (0, 10, 0.001953125),  # 2 / 2^10
            (5, 5, 1.0),
            (2, 9, 0.0654296875),  # 2 * (C(11,0)+C(11,1)+C(11,2)) / 2^11 = 134/2048
        ],
    )
    def test_against_hand_computed_values(
        self, b: int, c: int, expected_p: float
    ) -> None:
        result = ablation.mcnemar_exact(b, c)
        assert result["p_value"] == pytest.approx(expected_p)
        assert result["n_discordant"] == b + c
        assert result["statistic"] == min(b, c)

    def test_significance_threshold(self) -> None:
        assert ablation.mcnemar_exact(0, 8)["significant_at_alpha"] is True
        assert ablation.mcnemar_exact(2, 9)["significant_at_alpha"] is False
        assert ablation.mcnemar_exact(0, 0)["significant_at_alpha"] is False

    def test_matches_binomial_cdf_reference(self) -> None:
        """Cross-check the iterative tail against math.comb enumeration."""
        for b, c in [(0, 5), (1, 7), (3, 12), (2, 20)]:
            n = b + c
            k = min(b, c)
            expected = (
                2.0
                * sum(math.comb(n, i) for i in range(k + 1))
                / 2.0**n
            )
            result = ablation.mcnemar_exact(b, c)
            assert result["p_value"] == pytest.approx(min(1.0, expected))


# ── Pairwise analysis ───────────────────────────────────────────────────────
def _fake_run(
    scenario: str,
    decisions: dict[str, str],
    micro_f1: float,
    counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "flags": {},
        "observed": counts,
        "micro_f1": micro_f1,
        "macro_f1": micro_f1,
        "precision": 0.7,
        "recall": 0.8,
        "n_charts": 40,
        "event_decisions": decisions,
    }


class TestPairwise:
    def test_delta_and_discordant_directions(self) -> None:
        full = _fake_run(
            "FULL",
            {"e1": "tp", "e2": "tp", "e3": "fn", "e4": "fp"},
            0.7565,
            {"tp": 2, "fp": 1, "fn": 1},
        )
        ablated = _fake_run(
            "A3",
            {"e1": "fn", "e2": "tp", "e3": "fn", "e4": "fp"},
            0.7435,
            {"tp": 1, "fp": 1, "fn": 2},
        )
        row = ablation._pairwise(full, ablated)
        assert row["f1_delta"] == pytest.approx(0.0130)
        assert row["mcnemar"]["b_regressed"] == 1  # e1: tp -> fn
        assert row["mcnemar"]["c_improved"] == 0
        assert row["verdict"] == "INSIGNIFICANT_POSITIVE"  # p=1.0, delta>0
        assert row["counts_delta"] == {"tp": -1, "fp": 0, "fn": +1}

    def test_significant_contributor_classification(self) -> None:
        full = _fake_run(
            "FULL",
            {f"e{i}": "tp" for i in range(12)},
            0.80,
            {"tp": 12, "fp": 0, "fn": 0},
        )
        ablated = _fake_run(
            "A3",
            {**{f"e{i}": "fn" for i in range(10)}, "e10": "tp", "e11": "tp"},
            0.70,
            {"tp": 2, "fp": 0, "fn": 10},
        )
        row = ablation._pairwise(full, ablated)
        assert row["mcnemar"]["significant_at_alpha"] is True
        assert row["verdict"] == "SIGNIFICANT_CONTRIBUTOR"

    def test_degrader_classification(self) -> None:
        # Removing the mechanism IMPROVES the system significantly:
        # 8 events gain TP when the mechanism is removed (c=8, b=0,
        # exact p = 2/2^8 = 0.0078), while F1 drops.
        full = _fake_run(
            "FULL",
            {**{f"e{i}": "tp" for i in range(4)}, **{f"e{i}": "fp" for i in range(4, 14)}},
            0.4444,
            {"tp": 4, "fp": 10, "fn": 0},
        )
        ablated = _fake_run(
            "A4",
            {**{f"e{i}": "tp" for i in range(12)}, **{f"e{i}": "fp" for i in range(12, 14)}},
            0.9231,
            {"tp": 12, "fp": 2, "fn": 0},
        )
        row = ablation._pairwise(full, ablated)
        assert row["f1_delta"] < 0
        assert row["mcnemar"]["c_improved"] == 8
        assert row["mcnemar"]["significant_at_alpha"] is True
        assert row["verdict"] == "SIGNIFICANT_DEGRADER"

    def test_neutral_when_no_discordant_events(self) -> None:
        full = _fake_run("FULL", {"e1": "tp"}, 0.7565, {"tp": 1, "fp": 0, "fn": 0})
        ablated = _fake_run("A1", {"e1": "tp"}, 0.7565, {"tp": 1, "fp": 0, "fn": 0})
        row = ablation._pairwise(full, ablated)
        assert row["verdict"] == "NEUTRAL"
        assert row["mcnemar"]["p_value"] == 1.0

    def test_gate_breach_flagged(self) -> None:
        full = _fake_run("FULL", {}, 0.7565, {"tp": 3, "fp": 0, "fn": 0})
        # Ablated far below baseline tolerance.
        ablated = _fake_run("A3", {}, 0.60, {"tp": 0, "fp": 0, "fn": 3})
        row = ablation._pairwise(full, ablated)
        assert row["gate_breach"] is True
        assert row["within_tolerance_of_baseline"] is False


# ── Experiment registry & seal agreement ────────────────────────────────────
class TestRegistryAndSeal:
    def test_experiments_match_sealed_companion(self) -> None:
        # Each ablation is the FULL system minus exactly one flag.
        full_flags = {env: True for env in ablation.FLAG_ENV_VARS.values()}
        for exp in ablation.EXPERIMENTS:
            off = [env for env, on in exp["flags"].items() if not on]
            assert len(off) == 1, exp["id"]
            expected = dict(full_flags)
            expected[off[0]] = False
            assert exp["flags"] == expected

    def test_env_var_spellings_are_canonical(self) -> None:
        # Guards against the JRS_GOCHARA_SCORING misspelling class.
        assert ablation.FLAG_ENV_VARS["GOCHARA"] == "JRS_GOCHARA_SCORING"
        assert ablation.FLAG_ENV_VARS["ASHTAKAVARGA"] == "JRS_ASHTA_SCORING"
        assert ablation.FLAG_ENV_VARS["MULTI_VARGA"] == "JRS_VARGA_SCORING"
        assert ablation.FLAG_ENV_VARS["DASHA_TRANSIT"] == "JRS_DASHA_TRANSIT_SCORING"

    def test_sealed_anchors_agree_with_module_constants(self) -> None:
        assert ablation.SEALED_BASELINE["micro_f1"] == BASELINE_MICRO_F1
        assert ablation.SEALED_BASELINE == {"micro_f1": 0.7435, "tp": 71, "fp": 31, "fn": 18}
        assert ablation.SEALED_COMPANION == {"micro_f1": 0.7565, "tp": 73, "fp": 32, "fn": 15}
        assert ablation.F1_TOLERANCE is F1_TOLERANCE


# ── Written report integrity (produced by the real run) ─────────────────────
@pytest.mark.skipif(
    not REPORT_JSON.exists(), reason="ablation matrix not yet executed"
)
class TestWrittenReport:
    def test_report_shape_and_anchors(self) -> None:
        report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        assert report["analysis_id"] == "JRE-ABLATION-001"
        assert report["baseline_match"] is True
        assert report["companion_match"] is True
        assert len(report["experiments"]) == 4
        ids = {row["experiment_id"] for row in report["experiments"]}
        assert ids == {"A1", "A2", "A3", "A4"}
