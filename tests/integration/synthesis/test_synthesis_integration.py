"""Integration tests for JRE-022 Synthesis.

Verifies the full SynthesisReport against known reference scenarios,
ensuring end-to-end correctness from inputs through to
the final verdict scores and strength classifications.
"""

from __future__ import annotations

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
    make_ashtakavarga_indicator,
    make_bala_indicator,
    make_dasha_indicator,
    make_house_indicator,
    make_yoga_indicator,
)


# --------------------------------------------------------------------------- #
# Reference scenario: Strong career chart
# --------------------------------------------------------------------------- #


class TestReferenceStrongCareer:
    """Reference: Career-favorable chart with multiple strong indicators."""

    def test_career_score_above_moderate(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
            balas=(make_bala_indicator("SUN", "SHADBALA", 6.0),),
            house_occupancies=(make_house_indicator("SUN", 10),),
            dasha=make_dasha_indicator("SUN"),
        )
        report = svc.generate_verdict(data)
        career = report.verdict_for(SynthesisCategory.CAREER)
        assert career is not None
        # RAJA_YOGA (3.0) + BALA_ABOVE (1.5) + SUN_IN_10 (2.0) + DASHA_LORD_SUN (1.0) = 7.5
        assert career.score >= 4.0
        assert career.strength in (VerdictStrength.MODERATE, VerdictStrength.STRONG, VerdictStrength.VERY_STRONG)

    def test_evidence_ids_populated(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
            balas=(make_bala_indicator("SUN", "SHADBALA", 6.0),),
            house_occupancies=(make_house_indicator("SUN", 10),),
        )
        report = svc.generate_verdict(data)
        career = report.verdict_for(SynthesisCategory.CAREER)
        assert career is not None
        assert len(career.evidence_ids) >= 2


# --------------------------------------------------------------------------- #
# Reference scenario: Strong wealth chart
# --------------------------------------------------------------------------- #


class TestReferenceStrongWealth:
    """Reference: Wealth-favorable chart."""

    def test_wealth_score_high(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("GAJAKESARI_YOGA", True),),
            balas=(make_bala_indicator("JUPITER", "SHADBALA", 7.0),),
            house_occupancies=(make_house_indicator("JUPITER", 2),),
            ashtakavarga=(make_ashtakavarga_indicator(2, 32),),
        )
        report = svc.generate_verdict(data)
        wealth = report.verdict_for(SynthesisCategory.WEALTH)
        assert wealth is not None
        # GAJAKESARI (2.5) + BALA (2.0) + JUPITER_IN_2 (1.5) + ASHTAKAVARGA (1.0) = 7.0
        assert wealth.score >= 4.0


# --------------------------------------------------------------------------- #
# Reference scenario: Marriage indicators
# --------------------------------------------------------------------------- #


class TestReferenceMarriage:
    """Reference: Marriage-favorable chart."""

    def test_marriage_score_from_venus(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            house_occupancies=(make_house_indicator("VENUS", 7),),
            balas=(make_bala_indicator("VENUS", "SHADBALA", 6.5),),
        )
        report = svc.generate_verdict(data)
        marriage = report.verdict_for(SynthesisCategory.MARRIAGE)
        assert marriage is not None
        # VENUS_IN_7 (2.5) + BALA (1.5) = 4.0
        assert marriage.score >= 3.0


# --------------------------------------------------------------------------- #
# Reference scenario: Empty input
# --------------------------------------------------------------------------- #


class TestReferenceEmptyInput:
    """Reference: No indicators — all verdicts should be VERY_WEAK."""

    def test_all_very_weak(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput()
        report = svc.generate_verdict(data)
        for verdict in report.verdicts:
            assert verdict.score == 0.0
            assert verdict.strength == VerdictStrength.VERY_WEAK


# --------------------------------------------------------------------------- #
# Reference scenario: Deterministic output
# --------------------------------------------------------------------------- #


class TestReferenceDeterminism:
    """Reference: Same inputs produce identical output."""

    def test_deterministic_output(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
            balas=(make_bala_indicator("SUN", "SHADBALA", 6.0),),
        )
        r1 = svc.generate_verdict(data)
        r2 = svc.generate_verdict(data)
        assert r1.to_dict() == r2.to_dict()


# --------------------------------------------------------------------------- #
# Reference scenario: Selective categories
# --------------------------------------------------------------------------- #


class TestReferenceSelectiveCategories:
    """Reference: Only evaluate specific categories."""

    def test_only_career(self) -> None:
        svc = SynthesisService()
        data = SynthesisInput(
            yogas=(make_yoga_indicator("RAJA_YOGA", True),),
        )
        report = svc.generate_verdict(
            data, categories=(SynthesisCategory.CAREER,),
        )
        assert all(v.category == SynthesisCategory.CAREER for v in report.verdicts)
