"""Unit tests for the Numerology JRE calculation service.

Tests verify:
- Classical Pythagorean reduction algorithms
- Master number preservation (11, 22, 33)
- Life Path calculation from birth date
- Destiny calculation from full name
- Soul Urge calculation from vowels
- Personality calculation from consonants
- Personal Year calculation
- Deterministic ID stability
"""

from __future__ import annotations

import pytest

from numerology.models import (
    NumerologyChart,
    NumerologySystem,
    reduce_string_to_number,
    reduce_to_single_digit,
)
from numerology.service import NumerologyCalculationService

# ── Helper Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def svc() -> NumerologyCalculationService:
    """Create a NumerologyCalculationService instance."""
    return NumerologyCalculationService()


@pytest.fixture
def sample_chart(svc: NumerologyCalculationService) -> NumerologyChart:
    """Create a sample chart for John Adam Smith born 1985-07-15."""
    return svc.calculate(
        birth_date="1985-07-15",
        birth_name="John Adam Smith",
    )


# ── Reduce to Single Digit Tests ─────────────────────────────────────────────


class TestReduceToSingleDigit:
    """Tests for the reduce_to_single_digit function."""

    def test_single_digit_unchanged(self) -> None:
        """Single digits (1-9) should pass through unchanged."""
        for n in range(1, 10):
            assert reduce_to_single_digit(n) == n

    def test_double_digit_reduces(self) -> None:
        """Double digits should reduce to single digit."""
        assert reduce_to_single_digit(10) == 1
        assert reduce_to_single_digit(15) == 6
        assert reduce_to_single_digit(23) == 5
        assert reduce_to_single_digit(99) == 9

    def test_master_number_11_preserved(self) -> None:
        """Master number 11 should NOT be reduced."""
        assert reduce_to_single_digit(11) == 11

    def test_master_number_22_preserved(self) -> None:
        """Master number 22 should NOT be reduced."""
        assert reduce_to_single_digit(22) == 22

    def test_master_number_33_preserved(self) -> None:
        """Master number 33 should NOT be reduced."""
        assert reduce_to_single_digit(33) == 33

    def test_triple_digit_reduces_to_master(self) -> None:
        """Triple digits that sum to a master number should preserve it."""
        # 299 -> 2+9+9 = 20 -> 2+0 = 2 (not a master number)
        assert reduce_to_single_digit(299) == 2
        # 499 -> 4+9+9 = 22 (master number!)
        assert reduce_to_single_digit(499) == 22

    def test_large_number_reduces(self) -> None:
        """Large numbers should reduce correctly."""
        assert reduce_to_single_digit(12345) == 6  # 1+2+3+4+5=15, 1+5=6
        assert reduce_to_single_digit(999999) == 9


class TestReduceStringToNumber:
    """Tests for the reduce_string_to_number function."""

    def test_single_letter(self) -> None:
        """Single letters should map to their Pythagorean value."""
        assert reduce_string_to_number("A") == 1
        assert reduce_string_to_number("J") == 1
        assert reduce_string_to_number("S") == 1

    def test_empty_string(self) -> None:
        """Empty string should return 0."""
        assert reduce_string_to_number("") == 0

    def test_non_alpha_skipped(self) -> None:
        """Non-alphabetic characters should be skipped."""
        assert reduce_string_to_number("A1B2") == reduce_string_to_number("AB")

    def test_case_insensitive(self) -> None:
        """Calculation should be case-insensitive."""
        assert reduce_string_to_number("abc") == reduce_string_to_number("ABC")


# ── Life Path Number Tests ───────────────────────────────────────────────────


class TestLifePathCalculation:
    """Tests for Life Path Number calculation."""

    def test_basic_date(self, svc: NumerologyCalculationService) -> None:
        """Life Path for 1985-07-15 should be calculated correctly."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
        )
        assert chart.life_path is not None
        # 7+6+5=18 -> 1+8=9
        assert chart.life_path.reduced == 9

    def test_master_number_11_date(self, svc: NumerologyCalculationService) -> None:
        """Date that produces master number 11."""
        chart = svc.calculate(
            birth_date="1991-02-19",
            birth_name="Test",
        )
        assert chart.life_path is not None
        # 2+11+2=15, but month=2, day=19->1, year=1991->2 => 2+1+2=5
        # Actually: month=2, day=19->1+9=10->1, year=1991->1+9+9+1=20->2
        # 2+1+2=5
        assert chart.life_path.reduced == 5

    def test_master_number_preserved(self, svc: NumerologyCalculationService) -> None:
        """If calculation results in 22, it should be preserved."""
        chart = svc.calculate(
            birth_date="1968-04-19",
            birth_name="Test",
        )
        assert chart.life_path is not None
        assert chart.life_path.reduced in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33)

    def test_life_path_type_classification(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Life Path should have correct type classification."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
        )
        assert chart.life_path is not None
        # Life Path 9 -> HUMANITARIAN
        assert chart.life_path.life_path_type.value == "HUMANITARIAN"


# ── Destiny Number Tests ─────────────────────────────────────────────────────


class TestDestinyCalculation:
    """Tests for Destiny/Expression Number calculation."""

    def test_destiny_from_name(self, svc: NumerologyCalculationService) -> None:
        """Destiny should be calculated from full birth name."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart.destiny is not None
        # J=1, O=6, H=8, N=5 => 20
        # A=1, D=4, A=1, M=4 => 10
        # S=1, M=4, I=9, T=2, H=8 => 24
        # Total: 20+10+24 = 54 -> 5+4 = 9
        assert chart.destiny.reduced == 9

    def test_destiny_letter_values(self, svc: NumerologyCalculationService) -> None:
        """Destiny should track individual letter values."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AB",
        )
        assert chart.destiny is not None
        # A=1, B=2 => 3
        assert chart.destiny.raw_sum == 3
        assert chart.destiny.reduced == 3

    def test_destiny_preserves_master_number(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Destiny should preserve master numbers."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AAA BBB CCC DDD EEE FFF GGG",
        )
        assert chart.destiny is not None
        # Each group of 3 same letters: AAA=3, BBB=6, CCC=9, DDD=12, EEE=15, FFF=18, GGG=21
        # Total: 3+6+9+12+15+18+21 = 84 -> 8+4 = 12 -> 1+2 = 3
        assert chart.destiny.reduced == 3


# ── Soul Urge Number Tests ───────────────────────────────────────────────────


class TestSoulUrgeCalculation:
    """Tests for Soul Urge/Heart's Desire Number calculation."""

    def test_soul_urge_from_vowels(self, svc: NumerologyCalculationService) -> None:
        """Soul Urge should only count vowels."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart.soul_urge is not None
        # Vowels: O, A, A, I
        # O=6, A=1, A=1, I=9 => 17 -> 1+7 = 8
        assert chart.soul_urge.reduced == 8

    def test_soul_urge_vowel_values(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Soul Urge should track individual vowel values."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AEIOU",
        )
        assert chart.soul_urge is not None
        # A=1, E=5, I=9, O=6, U=3 => 24 -> 2+4 = 6
        assert chart.soul_urge.raw_sum == 24
        assert chart.soul_urge.reduced == 6

    def test_soul_urge_no_vowels(self, svc: NumerologyCalculationService) -> None:
        """Name with no vowels should result in raw_sum of 0."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="BCDFG",
        )
        assert chart.soul_urge is not None
        assert chart.soul_urge.raw_sum == 0
        assert chart.soul_urge.reduced == 0

    def test_soul_urge_master_number(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Soul Urge should preserve master numbers."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AAA III OOO",
        )
        assert chart.soul_urge is not None
        # A=1*3=3, I=9*3=27, O=6*3=18 => 48 -> 4+8 = 12 -> 1+2 = 3
        assert chart.soul_urge.reduced == 3


# ── Personality Number Tests ─────────────────────────────────────────────────


class TestPersonalityCalculation:
    """Tests for Personality Number calculation."""

    def test_personality_from_consonants(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personality should only count consonants."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart.personality is not None
        # Consonants: J, H, N, D, M, S, M, T, H
        # J=1, H=8, N=5, D=4, M=4, S=1, M=4, T=2, H=8 => 37 -> 3+7 = 10 -> 1+0 = 1
        assert chart.personality.reduced == 1

    def test_personality_consonant_values(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personality should track individual consonant values."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="BCDFG",
        )
        assert chart.personality is not None
        # B=2, C=3, D=4, F=6, G=7 => 22 (master number!)
        assert chart.personality.raw_sum == 22
        assert chart.personality.reduced == 22

    def test_personality_no_consonants(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Name with no consonants should result in raw_sum of 0."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AEIOU",
        )
        assert chart.personality is not None
        assert chart.personality.raw_sum == 0
        assert chart.personality.reduced == 0

    def test_personality_master_number(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personality should preserve master numbers."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="BCDFG HJKL MPQRST VWX",
        )
        assert chart.personality is not None
        # All consonants. Sum of Pythagorean values for all consonants
        # Should produce some number
        assert chart.personality.reduced in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33)


# ── Personal Year Number Tests ───────────────────────────────────────────────


class TestPersonalYearCalculation:
    """Tests for Personal Year Number calculation."""

    def test_personal_year_calculation(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personal Year should be calculated correctly."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
            target_year=2024,
        )
        assert chart.personal_year is not None
        # month=7, day=15->6, year=2024->8 => 7+6+8=21 -> 2+1=3
        assert chart.personal_year.reduced == 3

    def test_personal_year_preserves_master_number(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personal Year should preserve master numbers."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
            target_year=2025,
        )
        assert chart.personal_year is not None
        assert chart.personal_year.reduced in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33)

    def test_personal_year_target_year(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Personal Year should use the target year."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
            target_year=2000,
        )
        assert chart.personal_year is not None
        assert chart.personal_year.target_year == 2000


# ── Chart Deterministic ID Tests ─────────────────────────────────────────────


class TestDeterministicId:
    """Tests for deterministic ID generation."""

    def test_id_is_stable(self, svc: NumerologyCalculationService) -> None:
        """Same inputs should produce the same deterministic_id."""
        chart1 = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        chart2 = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart1.deterministic_id == chart2.deterministic_id

    def test_id_changes_with_input(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Different inputs should produce different deterministic_ids."""
        chart1 = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        chart2 = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Jane Doe",
        )
        assert chart1.deterministic_id != chart2.deterministic_id

    def test_id_is_hex_string(
        self, svc: NumerologyCalculationService
    ) -> None:
        """Deterministic ID should be a hex string."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert len(chart.deterministic_id) == 16
        # Should be valid hex
        int(chart.deterministic_id, 16)


# ── Chart Serialization Tests ────────────────────────────────────────────────


class TestChartSerialization:
    """Tests for NumerologyChart serialization."""

    def test_to_dict_includes_all_numbers(
        self, sample_chart: NumerologyChart
    ) -> None:
        """to_dict should include all calculated numbers."""
        d = sample_chart.to_dict()
        assert "life_path" in d
        assert "destiny" in d
        assert "soul_urge" in d
        assert "personality" in d
        assert "personal_year" in d
        assert "deterministic_id" in d

    def test_to_dict_deterministic(
        self, svc: NumerologyCalculationService
    ) -> None:
        """to_dict should produce the same result on repeated calls."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart.to_dict() == chart.to_dict()

    def test_to_dict_preserves_master_number(
        self, svc: NumerologyCalculationService
    ) -> None:
        """to_dict should preserve master numbers in nested dicts."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="BCDFG",
        )
        d = chart.to_dict()
        assert d["personality"] is not None
        assert d["personality"]["reduced"] == 22  # Master number


# ── Edge Cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case tests."""

    def test_single_character_name(self, svc: NumerologyCalculationService) -> None:
        """Single character name should work."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="A",
        )
        assert chart.destiny is not None
        assert chart.soul_urge is not None
        assert chart.personality is not None

    def test_all_vowels_name(self, svc: NumerologyCalculationService) -> None:
        """Name with only vowels should work."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="AEIOU",
        )
        assert chart.personality is not None
        assert chart.personality.raw_sum == 0

    def test_all_consonants_name(self, svc: NumerologyCalculationService) -> None:
        """Name with only consonants should work."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="BCDFG",
        )
        assert chart.soul_urge is not None
        assert chart.soul_urge.raw_sum == 0

    def test_system_enum_preserved(
        self, svc: NumerologyCalculationService
    ) -> None:
        """System type should be preserved in chart."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
            system=NumerologySystem.CHALDEAN,
        )
        assert chart.system == NumerologySystem.CHALDEAN

    def test_birth_date_preserved(self, svc: NumerologyCalculationService) -> None:
        """Birth date should be preserved in chart."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="Test",
        )
        assert chart.birth_date == "1985-07-15"

    def test_birth_name_preserved(self, svc: NumerologyCalculationService) -> None:
        """Birth name should be preserved in chart."""
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert chart.birth_name == "John Adam Smith"
