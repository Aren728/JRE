"""Occupancy + empty-house tests (TEST-PLAN §6/§13, SPEC §12/§21)."""

from __future__ import annotations

from bhava import BhavaConfig, OccupancyStatus, derive_house_analysis


def test_occupancy_echo_and_status(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    # Houses 1..9 occupied (one body each), 10..12 empty.
    for h in range(1, 10):
        assert by_number[h].occupancy_status is OccupancyStatus.OCCUPIED
        assert len(by_number[h].occupants) == 1
    for h in range(10, 13):
        assert by_number[h].occupancy_status is OccupancyStatus.EMPTY
        assert by_number[h].occupants == ()


def test_summaries(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    assert analysis.empty_house_numbers == (10, 11, 12)
    assert analysis.occupied_house_numbers == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert analysis.empty_house_count == 3


def test_summaries_gated_by_include_empty_houses(whole_sign_chart) -> None:
    cfg = BhavaConfig(include_empty_houses=False)
    analysis = derive_house_analysis(whole_sign_chart, cfg)
    assert analysis.empty_house_numbers == ()
    assert analysis.occupied_house_numbers == ()
    assert analysis.empty_house_count == 0
    # Per-house status is always present.
    assert analysis.derived_houses[9].occupancy_status is OccupancyStatus.EMPTY


def test_occupants_canonical_order(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    for house in analysis.derived_houses:
        assert house.occupants == tuple(sorted(house.occupants, key=lambda b: b.value))
