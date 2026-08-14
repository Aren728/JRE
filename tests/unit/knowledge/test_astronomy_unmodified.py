"""Static gate 4a: ``src/astronomy`` (JRE-002) is byte-for-byte untouched.

The file set and public ``__all__`` are pinned; CODING (JRE-004) must not
change them (SPEC §18, ADR-007).
"""

from __future__ import annotations

from pathlib import Path

import astronomy

SRC = Path(astronomy.__file__).resolve().parent

EXPECTED_FILES = {
    "__init__.py",
    "config.py",
    "coordinates.py",
    "errors.py",
    "models.py",
    "provider.py",
    "serialize.py",
    "service.py",
    "swisseph/__init__.py",
    "swisseph/constants.py",
    "swisseph/ephemeris.py",
    "swisseph/provider.py",
    "time.py",
}

EXPECTED_PUBLIC_API = {
    "AstronomicalService",
    "Ayanamsa",
    "BodyId",
    "BodyPosition",
    "CalculationConfig",
    "EphemerisDataError",
    "EphemerisError",
    "EphemerisMode",
    "EphemerisProvider",
    "EphemerisRequest",
    "EphemerisResult",
    "InvalidCoordinatesError",
    "InvalidTimestampError",
    "NodeType",
    "PositionType",
    "ProviderMetadata",
    "ProviderRegistry",
    "ProviderRun",
    "RetrogradeState",
    "UnsupportedProviderError",
    "config_from_dict",
    "default_registry",
    "get_provider",
    "request_from_dict",
    "result_to_dict",
    "result_to_json",
}


def test_astronomy_file_set_unchanged():
    files = {
        str(path.relative_to(SRC)) for path in SRC.rglob("*.py") if "__pycache__" not in str(path)
    }
    assert files == EXPECTED_FILES


def test_astronomy_public_api_unchanged():
    assert set(astronomy.__all__) == EXPECTED_PUBLIC_API
