"""Shared fixtures for the JRE-002 integration suite.

These tests require ``pysweph`` and the bundled ``.se1`` data files. If they
are unavailable the whole suite skips with a clear reason (Test plan §1).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from astronomy.models import EphemerisRequest
from astronomy.provider import ProviderRegistry
from astronomy.service import AstronomicalService
from astronomy.swisseph.provider import SwissEphemerisProvider

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "datasets" / "ephemeris"

pytest.importorskip("swisseph", reason="pysweph is not installed; integration tests skipped")

if not (DATA_DIR / "sepl_18.se1").is_file() or not (DATA_DIR / "semo_18.se1").is_file():
    pytest.skip(
        "bundled Swiss Ephemeris data files (datasets/ephemeris/*.se1) not found; "
        "integration tests skipped",
        allow_module_level=True,
    )


@pytest.fixture
def service() -> AstronomicalService:
    """A fresh service wired to a fresh Swiss Ephemeris provider."""
    registry = ProviderRegistry()
    registry.register(SwissEphemerisProvider())
    return AstronomicalService(provider_id="swisseph.pysweph", registry=registry)


def make_request(
    date: dt.date = dt.date(1990, 6, 15),
    time: dt.time = dt.time(10, 0, 0),
    timezone: str = "Asia/Kolkata",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    **overrides,
) -> EphemerisRequest:
    """Build a request; pass ``config=``, ``bodies=``, ``provider_id=`` etc."""
    return EphemerisRequest(
        date=date,
        time=time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
        **overrides,
    )
