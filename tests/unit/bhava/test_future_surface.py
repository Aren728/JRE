"""Future-compatibility invariants (TEST-PLAN §24, SPEC §11.4, ADR-019)."""

from __future__ import annotations

import pytest

from bhava import (
    SIGN_GRID_FRAME_SUPPORTED,
    BhavaConfig,
    ChartEcho,
    RelativeHouseFrame,
    derive_house_analysis,
)
from bhava.errors import InvalidBhavaConfigError


def test_sign_grid_frame_deferred_machine_testable() -> None:
    assert SIGN_GRID_FRAME_SUPPORTED is False
    assert list(RelativeHouseFrame) == [RelativeHouseFrame.HOUSE_OCCUPANCY]
    assert len(RelativeHouseFrame) == 1


def test_chart_echo_sign_grid_flag(whole_sign_chart) -> None:
    echo: ChartEcho = derive_house_analysis(whole_sign_chart).chart_echo
    assert echo.sign_grid_frame_supported is False
    assert echo.anchor_frame is RelativeHouseFrame.HOUSE_OCCUPANCY


def test_unknown_anchor_frame_rejected() -> None:
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"anchor_frame": "SIGN_GRID"})


def test_house_categories_membership_sets() -> None:
    from bhava import house_categories

    assert [c.value for c in house_categories(1)] == ["KENDRA", "TRIKONA"]
    assert [c.value for c in house_categories(5)] == ["TRIKONA"]
    assert [c.value for c in house_categories(6)] == ["DUSTHANA", "UPACHAYA"]
    assert [c.value for c in house_categories(10)] == ["KENDRA", "UPACHAYA"]
    assert [c.value for c in house_categories(12)] == ["DUSTHANA"]
    assert house_categories(2) == ()
