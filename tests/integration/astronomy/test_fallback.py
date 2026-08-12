"""Fallback behavior (Test plan §4).

- Explicit MOSEPH requests succeed with ``ephemeris_files == ()``.
- When SWIEPH data fails verification (checksum corruption in a directory
  that contains the required files) and ``allow_fallback=True``: the run
  succeeds in MOSEPH and records it (never silent).
- With ``allow_fallback=False``: ``EphemerisDataError``.
"""

from __future__ import annotations

import shutil

import pytest
from tests.integration.astronomy.conftest import DATA_DIR, make_request

from astronomy.errors import EphemerisDataError
from astronomy.models import CalculationConfig, EphemerisMode


@pytest.fixture
def corrupted_data_dir(tmp_path):
    """A directory with the required .se1 files, one byte corrupted."""
    for name in ("sepl_18.se1", "semo_18.se1"):
        shutil.copy2(DATA_DIR / name, tmp_path / name)
    path = tmp_path / "sepl_18.se1"
    data = bytearray(path.read_bytes())
    data[100] ^= 0xFF  # flip a byte
    path.write_bytes(bytes(data))
    return tmp_path


def test_moseph_requested_explicitly(service):
    config = CalculationConfig(ephemeris_mode=EphemerisMode.MOSEPH)
    result = service.compute(make_request(config=config))
    assert result.provider_run.ephemeris_mode is EphemerisMode.MOSEPH
    assert result.provider_run.ephemeris_files == ()


def test_fallback_to_moseph_when_data_corrupted(service, corrupted_data_dir):
    config = CalculationConfig(
        ephemeris_mode=EphemerisMode.SWIEPH,
        ephemeris_path=str(corrupted_data_dir),
        allow_fallback=True,
    )
    result = service.compute(make_request(config=config))
    assert result.provider_run.ephemeris_mode is EphemerisMode.MOSEPH
    assert result.provider_run.ephemeris_files == ()
    assert len(result.positions) == 9


def test_no_fallback_raises_data_error(service, corrupted_data_dir):
    config = CalculationConfig(
        ephemeris_mode=EphemerisMode.SWIEPH,
        ephemeris_path=str(corrupted_data_dir),
        allow_fallback=False,
    )
    with pytest.raises(EphemerisDataError):
        service.compute(make_request(config=config))


def test_fallback_results_are_deterministic(service, corrupted_data_dir):
    config = CalculationConfig(
        ephemeris_path=str(corrupted_data_dir), allow_fallback=True
    )
    first = service.compute(make_request(config=config))
    second = service.compute(make_request(config=config))
    assert first.positions == second.positions
    assert first.provider_run.ephemeris_mode is EphemerisMode.MOSEPH
