"""Yoga domain service unit tests."""

from __future__ import annotations

import pytest
from jrs.convergence.models import DomainAssessment
from jrs.domains.yoga.service import YogaDomainService


class TestYogaDomainService:
    def test_manifesting_yoga_returns_evidence_records(self) -> None:
        """Test A: Valid, manifesting yoga -> DomainAssessment with 1+ evidence records."""
        service = YogaDomainService()

        # MESHA lagna with SUN in SIMHA (5th house = Trikona)
        # SUN rules 5th house (SIMHA), placed in 5th -> TRIKONA_LORD_IN_KENDRA? No.
        # Let's set up: MARS in MITHUNA (3rd) won't trigger.
        # We need a kendra lord in a trikona house or vice versa.
        # MESHA lagna: 1st lord=MARS, 4th lord=MOON, 7th lord=VENUS, 10th lord=SATURN
        # 5th lord=SUN, 9th lord=JUPITER
        # Put SATURN (10th lord = kendra lord) in MEENA (12th house) -> trikona? No, 12th is not trikona.
        # Put SATURN in SIMHA (5th house = trikona) -> KENDRA_LORD_IN_TRIKONA
        # SIMHA is rashi number 5, lagna MESHA is 1. House = (5-1)%12+1 = 5. Yes.
        # SATURN is combust? No. Debilitated? No. House 5 is not dusthana. -> FORMED
        # active_dasha_lord = SATURN -> manifests.
        facts = {
            "lagna": "MESHA",
            "planets": {
                "SATURN": {"rashi": "SIMHA", "house": 5, "combust": False, "debilitated": False},
            },
            "active_dasha_lord": "SATURN",
            "transit_planet": "JUPITER",
        }

        result = service.assess(facts)

        assert isinstance(result, DomainAssessment)
        assert result.outcome_taxonomy == "YOGA_FORMATION"
        assert result.dimensions.supporting_count >= 1

    def test_no_yogas_returns_empty_assessment(self) -> None:
        """Test B: No yogas detected -> DomainAssessment with 0 evidence records."""
        service = YogaDomainService()

        # Empty facts -> no structural yogas detected
        facts: dict = {}

        result = service.assess(facts)

        assert isinstance(result, DomainAssessment)
        assert result.dimensions.supporting_count == 0
        assert result.dimensions.independent_channels == 0
