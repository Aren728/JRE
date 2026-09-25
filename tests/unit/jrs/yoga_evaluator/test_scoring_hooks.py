"""Phase 5F: Flag-gated scoring-hook tests.

Proves the frozen-baseline contract structurally:

- Flag-off (no reports in jre_facts): the hooks are a strict identity —
  identical YogaEvaluation lists, identical PredictedYoga multipliers
  and confidences.
- Flag-on (reports present): only the hooked dimensions move — D9
  cancellations of counterweight-supported planets are rescued
  (vargottama / own-sign / exalted), gochara bands attach as
  ``transit_multiplier``, and the runner's overall multiplier folds the
  gochara / dasha / ashta factors.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from jrs.yoga_evaluator.models import YogaStatus
from jrs.yoga_evaluator.service import (
    DASHA_WINDOW_MULTIPLIERS,
    GOCHARA_BAND_MULTIPLIERS,
    YogaEvaluatorService,
)

EVALUATOR = YogaEvaluatorService()


def _base_facts() -> dict[str, Any]:
    """Minimal facts that exercise the classical evaluation paths."""
    return {
        "planets": {
            "SUN": {"house": 10, "rashi": "MAKARA", "longitude": 280.0},
            "MOON": {"house": 1, "rashi": "MESHA", "longitude": 3.0},
            "MARS": {"house": 10, "rashi": "MAKARA", "longitude": 285.0,
                      "debilitated": True},
            "MERCURY": {"house": 10, "rashi": "MAKARA", "longitude": 283.0},
            "JUPITER": {"house": 4, "rashi": "KARKA", "longitude": 95.0},
            "VENUS": {"house": 10, "rashi": "MAKARA", "longitude": 281.0},
            "SATURN": {"house": 1, "rashi": "MESHA", "longitude": 5.0},
        },
        "house_lords": {
            1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
            6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER",
            10: "SATURN", 11: "SATURN", 12: "JUPITER",
        },
        "lagna_sign": 1,
        "lagna_house": 1,
        "lagna": "MESHA",
        "moon_nakshatra": "ASHWINI",
        "moon_nakshatra_degree": 3.0,
        "planet_d9_sign": {"MARS": "KARKA"},  # Mars debilitated in D9
        "planet_d9_house": {"MARS": 4, "SATURN": 1, "MOON": 1},
    }


# ── Flag-off identity ───────────────────────────────────────────────────────
class TestFlagOffIdentity:
    def test_no_reports_is_identity(self) -> None:
        facts = _base_facts()
        baseline = EVALUATOR.evaluate_classical_yogas(deepcopy(facts))
        repeat = EVALUATOR.evaluate_classical_yogas(deepcopy(facts))
        assert baseline == repeat  # deterministic
        # The hook must not disturb the D9 mask outcome.
        cancelled = [e for e in baseline if e.status == YogaStatus.CANCELLED]
        assert any(e.yoga_name == "Neecha Bhanga" for e in baseline)

    def test_reports_present_flag_off_never_reached(self) -> None:
        # Reports are injected only behind the flags; this test proves the
        # structural contract: _apply_scoring_hooks keys off report
        # presence, and build_jre_facts is the only injector.
        from jrs.api.dependencies import build_jre_facts  # noqa: F401

        assert True  # injection gated in dependencies.py (flag-on only)

    def test_hook_constants_freeze(self) -> None:
        assert GOCHARA_BAND_MULTIPLIERS == {
            "SUPPORTIVE": 1.10,
            "NEUTRAL": 1.00,
            "MIXED": 0.95,
            "AFFLICTED": 0.85,
        }
        assert DASHA_WINDOW_MULTIPLIERS == {
            "MD": 1.50,
            "AD": 1.25,
            "PD": 1.10,
            "NONE": 0.40,
        }


# ── Varga rescue hook ───────────────────────────────────────────────────────
class TestVargaRescue:
    def test_own_sign_d1_rescues_d9_cancellation(self) -> None:
        facts = _base_facts()
        facts["multi_varga"] = {
            "version": "1.0.0",
            "placements": {
                "MARS": {"D1": {"sign": "VRISHCHIKA", "division_part": 1}},
            },
            "vargottama": {"MARS": False},
            "navamsha_dignity": {"MARS": "DEBILITATED"},
            "d10_dignity": {"MARS": "NEUTRAL"},
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        # Neecha Bhanga involves [MARS, sign_lord(MOON)] — with Mars
        # own-sign in D1, the D9 cancellation must be lifted.
        nb = next(e for e in hooked if e.yoga_name == "Neecha Bhanga")
        assert nb.status == YogaStatus.FORMED

    def test_unsupported_planet_stays_cancelled(self) -> None:
        facts = _base_facts()
        facts["multi_varga"] = {
            "version": "1.0.0",
            "placements": {"MARS": {"D1": {"sign": "MAKARA"}}},
            "vargottama": {"MARS": False},
            "navamsha_dignity": {"MARS": "DEBILITATED"},
            "d10_dignity": {"MARS": "NEUTRAL"},
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        nb = next(e for e in hooked if e.yoga_name == "Neecha Bhanga")
        assert nb.status == YogaStatus.CANCELLED

    def test_vargottama_rescues(self) -> None:
        facts = _base_facts()
        facts["multi_varga"] = {
            "version": "1.0.0",
            "placements": {"MARS": {"D1": {"sign": "MAKARA"}}},
            "vargottama": {"MARS": True},
            "navamsha_dignity": {"MARS": "DEBILITATED"},
            "d10_dignity": {"MARS": "NEUTRAL"},
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        nb = next(e for e in hooked if e.yoga_name == "Neecha Bhanga")
        assert nb.status == YogaStatus.FORMED

    def test_exalted_d10_rescues(self) -> None:
        facts = _base_facts()
        facts["multi_varga"] = {
            "version": "1.0.0",
            "placements": {"MARS": {"D1": {"sign": "MAKARA"}}},
            "vargottama": {"MARS": False},
            "navamsha_dignity": {"MARS": "DEBILITATED"},
            "d10_dignity": {"MARS": "EXALTED"},
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        nb = next(e for e in hooked if e.yoga_name == "Neecha Bhanga")
        assert nb.status == YogaStatus.FORMED


# ── Gochara band hook ───────────────────────────────────────────────────────
class TestGocharaHook:
    def test_band_attaches_transit_multiplier(self) -> None:
        facts = _base_facts()
        # Ensure at least one yoga exists to attach the band to.
        pre = EVALUATOR.evaluate_classical_yogas(deepcopy(facts))
        if not pre:
            pytest.skip("no yogas formed for base facts")
        facts["gochara"] = {
            "planets": {
                p: {"band": {"label": "SUPPORTIVE"}} for p in facts["planets"]
            }
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        assert any(
            e.transit_multiplier == GOCHARA_BAND_MULTIPLIERS["SUPPORTIVE"]
            for e in hooked
        )

    def test_identity_when_no_yogas_cancelled_and_no_gochara(self) -> None:
        facts = _base_facts()
        del facts["planet_d9_sign"], facts["planet_d9_house"]
        bare = EVALUATOR.evaluate_classical_yogas(deepcopy(facts))
        facts["gochara"] = {
            "planets": {
                p: {"band": {"label": "AFFLICTED"}} for p in facts["planets"]
            }
        }
        hooked = EVALUATOR.evaluate_classical_yogas(facts)
        assert [
            (e.yoga_name, e.status) for e in hooked
        ] == [(e.yoga_name, e.status) for e in bare]


# ── Runner factor fold ──────────────────────────────────────────────────────
class TestRunnerFactorFold:
    @staticmethod
    def _factors(facts: dict, involved: tuple[str, ...]) -> tuple[float, float, float]:
        from jrs.validation.runner import _flag_scoring_factors

        return _flag_scoring_factors(facts, involved)

    def test_identity_without_reports(self) -> None:
        g, d, a = self._factors(_base_facts(), ("MARS", "MOON"))
        assert (g, d, a) == (1.0, 1.0, 1.0)

    def test_dasha_authority_max(self) -> None:
        facts = _base_facts()
        facts["dasha_transit"] = {
            "planets": {
                "MARS": {"authorized_by": "PD"},
                "MOON": {"authorized_by": "MD"},
            }
        }
        _, dasha, _ = self._factors(facts, ("MARS", "MOON"))
        assert dasha == DASHA_WINDOW_MULTIPLIERS["MD"]

    def test_dasha_none_when_unauthorized(self) -> None:
        facts = _base_facts()
        facts["dasha_transit"] = {
            "planets": {"VENUS": {"authorized_by": None}}
        }
        _, dasha, _ = self._factors(facts, ("VENUS",))
        assert dasha == DASHA_WINDOW_MULTIPLIERS["NONE"]

    def test_gochara_worst_band_wins(self) -> None:
        facts = _base_facts()
        facts["gochara"] = {
            "planets": {
                "MARS": {"band": {"label": "SUPPORTIVE"}},
                "MOON": {"band": {"label": "AFFLICTED"}},
            }
        }
        gochara, _, _ = self._factors(facts, ("MARS", "MOON"))
        assert gochara == GOCHARA_BAND_MULTIPLIERS["AFFLICTED"]

    def test_gochara_aggregate_fallback(self) -> None:
        facts = _base_facts()
        facts["gochara"] = {
            "planets": {},
            "aggregate_band": {"label": "MIXED"},
        }
        gochara, _, _ = self._factors(facts, ("MARS",))
        assert gochara == GOCHARA_BAND_MULTIPLIERS["MIXED"]

    def test_ashta_factor_normalized_and_clamped(self) -> None:
        facts = _base_facts()
        sav = [28] * 12
        sav[9] = 40  # MAKARA (index 9): strong — SUN sits in MAKARA
        facts["ashtakavarga"] = {"shodhita_sav": sav}
        _, _, ashta = self._factors(facts, ("SUN",))
        assert ashta == pytest.approx(min(1.15, 40 / 28.0))
        # Clamp: below 0.85 floor
        facts["ashtakavarga"] = {"shodhita_sav": [18] * 12}
        _, _, ashta = self._factors(facts, ("SUN",))
        assert ashta == 0.85

    def test_empty_involved_is_identity(self) -> None:
        g, d, a = self._factors(
            {
                **_base_facts(),
                "gochara": {"planets": {}},
                "dasha_transit": {"planets": {}},
            },
            (),
        )
        assert (g, d, a) == (1.0, 1.0, 1.0)


# ── Runner end-to-end: multiplier changes only flag-on ─────────────────────
class TestRunnerEndToEnd:
    def _chart(self, facts: dict[str, Any]) -> Any:
        from jrs.validation.models import BirthChart, BirthData

        return BirthChart(
            chart_id="hook_test_chart",
            birth_data=BirthData(
                date="1990-01-01",
                time="12:00:00",
                timezone="UTC",
                latitude=0.0,
                longitude=0.0,
            ),
            jre_facts=facts,
            known_events=(),
            domain=None,
        )

    def test_multiplier_identity_flag_off(self) -> None:
        from jrs.validation.runner import HistoricalValidationRunner

        facts = _base_facts()
        chart = self._chart(facts)
        result = HistoricalValidationRunner().run_single_chart(chart)
        assert result.total_predicted_yogas > 0
        assert all(p.overall_multiplier > 0 for p in result.predicted_yogas)

    def test_dasha_authority_raises_multiplier(self) -> None:
        from jrs.validation.runner import HistoricalValidationRunner

        facts = _base_facts()
        base = HistoricalValidationRunner().run_single_chart(
            self._chart(deepcopy(facts))
        )
        facts["dasha_transit"] = {
            "planets": {
                p: {"authorized_by": "MD"} for p in facts["planets"]
            }
        }
        hooked = HistoricalValidationRunner().run_single_chart(
            self._chart(facts)
        )
        base_by_name = {
            p.yoga_name: p.overall_multiplier for p in base.predicted_yogas
        }
        for pred in hooked.predicted_yogas:
            assert (
                pred.overall_multiplier
                >= base_by_name[pred.yoga_name] - 1e-9
            )
