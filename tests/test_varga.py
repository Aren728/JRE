"""
Unit tests for D3/D10 varga helpers and ayanamsha offset selection.
"""

import pytest
from src.jrs.engine.calculator import calculate_d3_sign, calculate_d10_sign, get_ayanamsha_offset


def test_calculate_d3_sign_first_drekkana():
    # Aries 5° -> first Drekkana = Aries
    assert calculate_d3_sign(5.0) == "Mesha"


def test_calculate_d3_sign_second_drekkana():
    # Aries 15° -> second Drekkana = Leo
    assert calculate_d3_sign(15.0) == "Simha"


def test_calculate_d3_sign_third_drekkana():
    # Aries 25° -> third Drekkana = Sagittarius
    assert calculate_d3_sign(25.0) == "Dhanu"


def test_calculate_d10_sign_odd_sign_start():
    # Aries 2° -> Dashamsha starts in Aries -> Aries
    assert calculate_d10_sign(2.0) == "Mesha"


def test_calculate_d10_sign_even_sign_start():
    # Taurus 2° -> Dashamsha starts in Capricorn -> Capricorn
    assert calculate_d10_sign(32.0) == "Makara"


def test_get_ayanamsha_offset_known_modes():
    assert get_ayanamsha_offset("lahiri") == 0.0
    assert get_ayanamsha_offset("raman") == 1.4167
    assert get_ayanamsha_offset("kp") == 0.1000


def test_get_ayanamsha_offset_unknown_and_none():
    assert get_ayanamsha_offset(None) == 0.0
    assert get_ayanamsha_offset("") == 0.0
    assert get_ayanamsha_offset("invalid") == 0.0
