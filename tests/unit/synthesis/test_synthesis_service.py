"""Unit tests for JRE-022 SynthesisService."""

from __future__ import annotations

import pytest

from synthesis.errors import InvalidSynthesisRequestError
from synthesis.models import (
    BalaIndicator,
    HouseIndicator,
    SynthesisCategory,
    SynthesisInput,
    SynthesisReport,
    VerdictStrength,
    YogaIndicator,
)
from synthesis.service import SynthesisService
from tests.unit.synthesis.conftest import (
    make_bala_indicator,
    make_house_indicator,
    make_yoga_indicator,
)


class TestSynthesisServiceBasic:
    def test_generate_career_verdict(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
            balas=(make_bala_indicator("SUN", "SHADBALA", 6.0),),
            house_occupancies=(make_house_indicator("SUN", 10),),
        )
        report = svc.generate_verdict(data)
        assert isinstance(report, SynthesisReport)
        assert len(report.verdicts) > 0

    def test_generate_wealth_verdict(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("GAJAKESARI_YOGA", True),),
            balas=(make_bala_indicator("JUPITER", "SHADBALA", 7.0),),
            house_occupancies=(make_house_indicator("JUPITER", 2),),
        )
        report = svc.generate_verdict(data)
        assert isinstance(report, SynthesisReport)

    def test_empty_input_produces_zero_scores(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput()
        report = svc.generate_verdict(data)
        for verdict in report.verdicts:
            assert verdict.score == 0.0
            assert verdict.strength == VerdictStrength.VERY_WEAK

    def test_selective_categories(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
        )
        report = svc.generate_verdict(
            data, categories=(SynthesisCategory.CAREER,),
        )
        for verdict in report.verdicts:
            assert verdict.category == SynthesisCategory.CAREER

    def test_deterministic(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
        )
        r1 = svc.generate_verdict(data)
        r2 = svc.generate_verdict(data)
        assert r1.to_dict() == r2.to_dict()

    def test_config_property(self) -> None:
        svc = SynthesisService()
        assert svc.config is not None
        assert svc.config.version == "0.1.0"

    def test_all_categories_have_rules(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput()
        report = svc.generate_verdict(data)
        # Should produce verdicts for all configured categories
        assert len(report.verdicts) > 0

    def test_score_accumulates(self) -> None:
        svc = SynthesisService()
        # Multiple favorable indicators for CAREER
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
            balas=(make_bala_indicator("SUN", "SHADBALA", 6.0),),
            house_occupancies=(
                make_house_indicator("SUN", 10),
                make_house_indicator("JUPITER", 10),
            ),
            dasha=__import__("synthesis.models", fromlist=["DashaIndicator"]).DashaIndicator(
                lord="SUN", period_start="2020-01-01T00:00:00Z", period_end="2026-01-01T00:00:00Z",
            ),
        )
        report = svc.generate_verdict(data)
        career_verdict = report.verdict_for(SynthesisCategory.CAREER)
        assert career_verdict is not None
        assert career_verdict.score > 0.0
        assert len(career_verdict.evidence_ids) > 0


class TestSynthesisServiceValidation:
    def test_invalid_input_type_raises(self) -> None:
        svc = SynthesisService()
        with pytest.raises(InvalidSynthesisRequestError):
            svc.generate_verdict("NOT_A_INPUT")  # type: ignore[arg-type]

    def test_valid_input_passes(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput()
        report = svc.generate_verdict(data)
        assert isinstance(report, SynthesisReport)
