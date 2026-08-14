"""DMS representation: presentational only; rounding policy (Specialist §8)."""

from __future__ import annotations

import pytest

from jyotish.dms import from_degrees


def test_whole_degrees():
    value = from_degrees(143.0, 1)
    assert value.degrees == 143
    assert value.minutes == 0
    assert value.seconds == 0.0
    assert value.sign == 1


def test_known_decomposition():
    # 143.2566 deg = 143°15'23.76" -> rounds to 143°15'23.8" at precision 1.
    value = from_degrees(143.2566, 1)
    assert value.degrees == 143
    assert value.minutes == 15
    assert value.seconds == pytest.approx(23.8)
    assert value.sign == 1


def test_negative_sign_preserved():
    value = from_degrees(-12.5, 1)
    assert value.sign == -1
    assert value.degrees == 12
    assert value.minutes == 30


def test_seconds_rollover_to_minutes():
    # 10°59'59.9999" rounds to 11°00'00" at precision 0.
    value = from_degrees(10 + 59 / 60 + 59.9999 / 3600, 0)
    assert value.degrees == 11
    assert value.minutes == 0
    assert value.seconds == 0.0


def test_minutes_rollover_to_degrees():
    # 29°59'59.6" -> 30°00'00" at precision 0.
    value = from_degrees(29 + 59 / 60 + 59.6 / 3600, 0)
    assert value.degrees == 30
    assert value.minutes == 0


def test_three_sixty_wraps_to_zero():
    value = from_degrees(360.0, 1)
    assert value.degrees == 0
    assert value.sign == 1


def test_round_half_even_at_seconds():
    # round(0.5, 0) -> 0 (banker's rounding); round(1.5, 0) -> 2.
    value = from_degrees(1.0 / 3600.0 * 0.5, 0)
    assert value.seconds == 0.0
    value = from_degrees(1.0 / 3600.0 * 1.5, 0)
    assert value.seconds == 2.0


def test_format_string():
    value = from_degrees(143.2566, 1)
    assert value.format(1) == "143°15'23.8\""
