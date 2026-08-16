"""Shared fixtures for the JRE-007 integration suite.

These tests require ``pysweph`` and the bundled ``.se1`` data files
(mirrors the JRE-002/003/005/006 integration conftests). If unavailable
the suite skips with a clear reason (TEST-PLAN §1).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bhava import BhavaService
from context import ContextService
from jyotish import BirthData, JyotishService

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
def jyotish_service() -> JyotishService:
    return JyotishService()


@pytest.fixture
def context_service(jyotish_service: JyotishService) -> ContextService:
    return ContextService(jyotish_service, BhavaService(jyotish_service))


@pytest.fixture
def birth() -> BirthData:
    return BirthData(
        date="1990-06-15",
        time="10:00:00",
        timezone="Asia/Kolkata",
        latitude=28.6139,
        longitude=77.2090,
    )
