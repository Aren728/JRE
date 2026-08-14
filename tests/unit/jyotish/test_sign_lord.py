"""Focused tests for the additive public ``sign_lord_of`` accessor.

JRE-005 blocker resolution (OPTION A): expose the existing JRE-003
rashi-lord catalog through the public API as ``jyotish.sign_lord_of`` so
JRE-005 can consume sign lordship without importing internals, duplicating
the catalog, or depending on JRE-004.

Requirements verified: all 12 rashis resolve; values match the
``RASHI_LORDS`` source of truth; invalid input follows the existing
``lord_of`` error convention (KeyError); the public export is present in
``__all__``; deterministic behavior.
"""

from __future__ import annotations

import pytest

from astronomy.models import BodyId
from jyotish import RASHI_ORDER, sign_lord_of
from jyotish import __all__ as JYOTISH_ALL
from jyotish.models import RashiId
from jyotish.rashi import RASHI_LORDS
from jyotish.rashi import lord_of as rashi_lord_of


def test_all_twelve_rashis_resolve() -> None:
    for rashi in RASHI_ORDER:
        lord = sign_lord_of(rashi)
        assert isinstance(lord, BodyId)


def test_values_match_rashi_lords_source_of_truth() -> None:
    for index, rashi in enumerate(RASHI_ORDER):
        assert sign_lord_of(rashi) == RASHI_LORDS[index]


def test_delegates_to_existing_rashi_lord_of() -> None:
    for rashi in RASHI_ORDER:
        assert sign_lord_of(rashi) == rashi_lord_of(rashi)


def test_valid_string_input_coerces_like_lord_of() -> None:
    # StrEnum: a plain string of a valid name resolves (same behavior as lord_of).
    assert sign_lord_of("MESHA") == BodyId.MARS  # type: ignore[arg-type]


def test_invalid_input_follows_existing_error_convention() -> None:
    # The catalog lookup raises KeyError for unknown values; sign_lord_of
    # preserves that convention (no new error type introduced).
    with pytest.raises(KeyError):
        sign_lord_of("BOGUS")  # type: ignore[arg-type]


def test_public_api_export_present() -> None:
    assert "sign_lord_of" in JYOTISH_ALL


def test_deterministic() -> None:
    for rashi in RASHI_ORDER:
        assert sign_lord_of(rashi) == sign_lord_of(rashi)


def test_known_classical_lords() -> None:
    # Spot-check the classical Parashari assignment via the public accessor.
    assert sign_lord_of(RashiId.MESHA) == BodyId.MARS
    assert sign_lord_of(RashiId.VRISHABHA) == BodyId.VENUS
    assert sign_lord_of(RashiId.SIMHA) == BodyId.SUN
    assert sign_lord_of(RashiId.MAKARA) == BodyId.SATURN
    assert sign_lord_of(RashiId.MEENA) == BodyId.JUPITER
