"""Unit tests for JRE-020 MuhurtaService."""

from __future__ import annotations

import pytest

from muhurta.errors import InvalidMuhurtaRequestError
from muhurta.models import (
    MuhurtaCategory,
    MuhurtaEvaluation,
    MuhurtaWindow,
)
from muhurta.service import MuhurtaService
from tests.unit.muhurta.conftest import make_panchanga, make_window


class TestMuhurtaServiceBasic:
    def test_evaluate_auspicious_window(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        from jyotish import NakshatraId
        from muhurta.models import Karana, Tithi, Var, Yoga
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_PRADEMA,
            vara=Var.THURSDAY,
            nakshatra=NakshatraId.HASTA,
            yoga=Yoga.SUBHA,
            karana=Karana.BALAVA,
        )
        eval_result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        assert isinstance(eval_result, MuhurtaEvaluation)
        assert eval_result.window == window
        assert eval_result.category == MuhurtaCategory.MARRIAGE
        assert 0.0 <= eval_result.fitness_score <= 1.0
        assert isinstance(eval_result.structural_flags, tuple)

    def test_evaluate_inauspicious_window(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        from muhurta.models import Karana, Tithi, Var, Yoga
        from jyotish import NakshatraId
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_NAVAMI,
            vara=Var.SATURDAY,
            nakshatra=NakshatraId.ARDRA,
            yoga=Yoga.SHULA,
            karana=Karana.VISHTI,
        )
        eval_result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        assert eval_result.fitness_score < 1.0
        assert len(eval_result.structural_flags) > 0

    def test_deterministic(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga()
        e1 = svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)
        e2 = svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)
        assert e1.to_dict() == e2.to_dict()

    def test_all_categories_produce_valid_evaluation(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga()
        for category in MuhurtaCategory:
            eval_result = svc.evaluate_window(window, category, panchanga)
            assert isinstance(eval_result, MuhurtaEvaluation)
            assert eval_result.category == category
            assert 0.0 <= eval_result.fitness_score <= 1.0

    def test_config_property(self) -> None:
        svc = MuhurtaService()
        assert svc.config is not None
        assert svc.config.version == "0.1.0"


class TestMuhurtaServiceValidation:
    def test_invalid_window_type_raises(self) -> None:
        svc = MuhurtaService()
        panchanga = make_panchanga()
        with pytest.raises(InvalidMuhurtaRequestError):
            svc.evaluate_window("NOT_A_WINDOW", MuhurtaCategory.GENERAL, panchanga)  # type: ignore[arg-type]

    def test_empty_start_utc_raises(self) -> None:
        svc = MuhurtaService()
        panchanga = make_panchanga()
        window = MuhurtaWindow(start_utc="", end_utc="2024-01-15T12:00:00Z")
        with pytest.raises(InvalidMuhurtaRequestError):
            svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)

    def test_empty_end_utc_raises(self) -> None:
        svc = MuhurtaService()
        panchanga = make_panchanga()
        window = MuhurtaWindow(start_utc="2024-01-15T06:00:00Z", end_utc="")
        with pytest.raises(InvalidMuhurtaRequestError):
            svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)

    def test_invalid_category_type_raises(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga()
        with pytest.raises(InvalidMuhurtaRequestError):
            svc.evaluate_window(window, "NOT_A_CATEGORY", panchanga)  # type: ignore[arg-type]

    def test_invalid_panchanga_type_raises(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        with pytest.raises(InvalidMuhurtaRequestError):
            svc.evaluate_window(window, MuhurtaCategory.GENERAL, "NOT_A_PANCHANGA")  # type: ignore[arg-type]
