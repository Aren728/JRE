"""Shared fixtures for JRE Advanced Charts unit tests.

Provides synthetic natal data and aspect data for testing the divisional chart,
shadbala, and ashtakavarga engines.
"""

from __future__ import annotations

import pytest


# ── Synthetic natal longitudes ──────────────────────────────

# Aries (MESHA) = 0°, Taurus (VRISHABHA) = 30°, etc.
SAMPLE_NATAL_LONGITUDES: dict[str, float] = {
    "SUN": 15.0,      # 15° Aries (MESHA)
    "MOON": 45.5,     # 15.5° Taurus (VRISHABHA)
    "MARS": 90.0,     # 0° Cancer (KARKA)
    "MERCURY": 195.0, # 15° Virgo (KANYA)
    "JUPITER": 250.0, # 10° Sagittarius (DHANUSHA)
    "VENUS": 330.0,   # 0° Pisces (MEENA)
    "SATURN": 300.0,  # 0° Aquarius (KUMBHA)
}

SAMPLE_LAGNA_LONGITUDE: float = 100.0  # 10° Cancer (KARKA)


@pytest.fixture
def natal_longitudes() -> dict[str, float]:
    """Standard sample natal longitudes for testing."""
    return dict(SAMPLE_NATAL_LONGITUDES)


@pytest.fixture
def lagna_longitude() -> float:
    """Standard sample lagna longitude for testing."""
    return SAMPLE_LAGNA_LONGITUDE


@pytest.fixture
def all_zero_longitudes() -> dict[str, float]:
    """All planets at 0° Aries for edge-case testing."""
    return {planet: 0.0 for planet in [
        "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"
    ]}


@pytest.fixture
def natal_data_for_shadbala() -> dict:
    """Natal data dict in the format expected by compute_shadbala."""
    return {
        "planets": {
            "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                     "retrograde": False, "speed": 1.0},
            "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                      "retrograde": False, "speed": 13.0},
            "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                      "retrograde": False, "speed": 0.5},
            "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.5},
            "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                         "retrograde": False, "speed": 0.2},
            "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                       "retrograde": False, "speed": 1.2},
            "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                        "retrograde": True, "speed": -0.1},
        }
    }


@pytest.fixture
def natal_data_for_ashtakavarga() -> dict:
    """Natal data dict in the format expected by compute_ashtakavarga."""
    return {
        "planets": {
            "SUN": {"house": 1, "rashi": "MESHA"},
            "MOON": {"house": 2, "rashi": "VRISHABHA"},
            "MARS": {"house": 4, "rashi": "KARKA"},
            "MERCURY": {"house": 6, "rashi": "KANYA"},
            "JUPITER": {"house": 8, "rashi": "DHANUSHA"},
            "VENUS": {"house": 10, "rashi": "MEENA"},
            "SATURN": {"house": 11, "rashi": "KUMBHA"},
            "RAHU": {"house": 5, "rashi": "SIMHA"},
            "KETU": {"house": 11, "rashi": "KUMBHA"},
        }
    }
