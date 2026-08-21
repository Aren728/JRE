"""Shared builders for JRE-022 Synthesis unit tests."""

from __future__ import annotations

import pytest

from synthesis.models import (
    AshtakavargaIndicator,
    AvasthaIndicator,
    BalaIndicator,
    DashaIndicator,
    HouseIndicator,
    SynthesisCategory,
    SynthesisInput,
    SynthesisRule,
    YogaIndicator,
    ConditionType,
)


def make_yoga_indicator(
    yoga_id: str = "GAJAKESARI_YOGA",
    present: bool = True,
) -> YogaIndicator:
    """Build a ``YogaIndicator``."""
    return YogaIndicator(yoga_id=yoga_id, present=present)


def make_bala_indicator(
    planet: str = "JUPITER",
    bala_type: str = "SHADBALA",
    value: float = 6.0,
) -> BalaIndicator:
    """Build a ``BalaIndicator``."""
    return BalaIndicator(planet=planet, bala_type=bala_type, value=value)


def make_dasha_indicator(
    lord: str = "JUPITER",
    period_start: str = "2020-01-01T00:00:00Z",
    period_end: str = "2030-01-01T00:00:00Z",
) -> DashaIndicator:
    """Build a ``DashaIndicator``."""
    return DashaIndicator(lord=lord, period_start=period_start, period_end=period_end)


def make_house_indicator(
    planet: str = "JUPITER",
    house: int = 10,
) -> HouseIndicator:
    """Build a ``HouseIndicator``."""
    return HouseIndicator(planet=planet, house=house)


def make_ashtakavarga_indicator(
    house: int = 2,
    score: int = 30,
) -> AshtakavargaIndicator:
    """Build an ``AshtakavargaIndicator``."""
    return AshtakavargaIndicator(house=house, score=score)


def make_avastha_indicator(
    planet: str = "SUN",
    state: str = "DEEPTADI",
) -> AvasthaIndicator:
    """Build an ``AvasthaIndicator``."""
    return AvasthaIndicator(planet=planet, state=state)


@pytest.fixture
def empty_input() -> SynthesisInput:
    """Empty synthesis input with no indicators."""
    return SynthesisInput()


@pytest.fixture
def career_favorable_input() -> SynthesisInput:
    """Input favorable for CAREER category."""
    return SynthesisInput(
        yogas=(YogaIndicator(yoga_id="RAJA_YOGA", present=True),),
        balas=(BalaIndicator(planet="SUN", bala_type="SHADBALA", value=6.0),),
        house_occupancies=(HouseIndicator(planet="SUN", house=10),),
        dasha=DashaIndicator(lord="SUN", period_start="2020-01-01T00:00:00Z", period_end="2026-01-01T00:00:00Z"),
    )


@pytest.fixture
def wealth_favorable_input() -> SynthesisInput:
    """Input favorable for WEALTH category."""
    return SynthesisInput(
        yogas=(YogaIndicator(yoga_id="GAJAKESARI_YOGA", present=True),),
        balas=(BalaIndicator(planet="JUPITER", bala_type="SHADBALA", value=7.0),),
        house_occupancies=(HouseIndicator(planet="JUPITER", house=2),),
        ashtakavarga=(AshtakavargaIndicator(house=2, score=32),),
    )


@pytest.fixture
def marriage_favorable_input() -> SynthesisInput:
    """Input favorable for MARRIAGE category."""
    return SynthesisInput(
        house_occupancies=(HouseIndicator(planet="VENUS", house=7),),
        balas=(BalaIndicator(planet="VENUS", bala_type="SHADBALA", value=6.5),),
    )


@pytest.fixture
def sample_rules() -> dict[str, tuple[SynthesisRule, ...]]:
    """A small set of rules for testing."""
    return {
        "CAREER": (
            SynthesisRule(
                category=SynthesisCategory.CAREER,
                condition_type=ConditionType.YOGA_PRESENT,
                condition_params={"yoga_id": "RAJA_YOGA"},
                weight=3.0,
            ),
            SynthesisRule(
                category=SynthesisCategory.CAREER,
                condition_type=ConditionType.BALA_ABOVE,
                condition_params={"planet": "SUN", "bala_type": "SHADBALA", "threshold": 5.0},
                weight=1.5,
            ),
        ),
        "WEALTH": (
            SynthesisRule(
                category=SynthesisCategory.WEALTH,
                condition_type=ConditionType.YOGA_PRESENT,
                condition_params={"yoga_id": "GAJAKESARI_YOGA"},
                weight=2.5,
            ),
        ),
    }
