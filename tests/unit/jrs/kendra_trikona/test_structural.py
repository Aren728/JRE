"""JRS-072 Kendra-Trikona Structural Reasoning unit tests."""

from __future__ import annotations

import pytest
from jrs.kendra_trikona.models import KendraTrikonaType, StructuralYoga
from jrs.kendra_trikona.service import KendraTrikonaService


class TestKendraTrikonaService:
    def test_kendra_lord_in_trikona(self) -> None:
        """Test A: 1st lord (Mars) in 5th house (Leo) -> KENDRA_LORD_IN_TRIKONA."""
        service = KendraTrikonaService()
        facts = {
            "lagna": "MESHA",  # Aries (1)
            "planets": {
                "MARS": {"rashi": "SIMHA", "longitude": 120.0},  # Leo (5)
            }
        }
        yogas = service.evaluate(facts)
        
        kt_yogas = [y for y in yogas if y.yoga_type == KendraTrikonaType.KENDRA_LORD_IN_TRIKONA]
        assert len(kt_yogas) == 1
        
        yoga = kt_yogas[0]
        assert yoga.planet_a == "MARS"
        assert yoga.house_a == 1  # Mars rules 1st (Aries)
        assert yoga.house_b == 5  # Mars is in 5th (Leo)

    def test_trikona_lord_in_kendra(self) -> None:
        """Test B: 5th lord (Sun) in 10th house (Capricorn) -> TRIKONA_LORD_IN_KENDRA."""
        service = KendraTrikonaService()
        facts = {
            "lagna": "MESHA",  # Aries (1)
            "planets": {
                "SUN": {"rashi": "MAKARA", "longitude": 270.0},  # Capricorn (10)
            }
        }
        yogas = service.evaluate(facts)
        
        kt_yogas = [y for y in yogas if y.yoga_type == KendraTrikonaType.TRIKONA_LORD_IN_KENDRA]
        assert len(kt_yogas) == 1
        
        yoga = kt_yogas[0]
        assert yoga.planet_a == "SUN"
        assert yoga.house_a == 5  # Sun rules 5th (Leo)
        assert yoga.house_b == 10  # Sun is in 10th (Capricorn)
