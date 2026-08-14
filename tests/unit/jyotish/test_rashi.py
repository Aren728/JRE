"""All 12 Rashi boundaries, lords, and degree-within-rashi (requirement A, §N)."""

from __future__ import annotations

import pytest

from astronomy.models import BodyId
from jyotish.models import RashiId
from jyotish.rashi import (
    RASHI_CATALOG_VERSION,
    RASHI_ORDER,
    RASHI_SOURCE,
    degree_in_rashi,
    lord_of,
    rashi_index_of,
    rashi_of,
    rashi_span,
)

ORDER = list(RashiId)
ARCS = [i * 30.0 for i in range(12)]


def test_catalog_is_versioned_and_sourced():
    assert RASHI_CATALOG_VERSION == "1.0.0"
    assert "Parashara" in RASHI_SOURCE


def test_twelve_rashis_in_zodiacal_order():
    assert len(RASHI_ORDER) == 12
    assert RASHI_ORDER[0] is RashiId.MESHA
    assert RASHI_ORDER[11] is RashiId.MEENA
    assert list(RASHI_ORDER) == ORDER


@pytest.mark.parametrize(
    "index, expected",
    [
        (0, RashiId.MESHA),
        (1, RashiId.VRISHABHA),
        (2, RashiId.MITHUNA),
        (3, RashiId.KARKA),
        (4, RashiId.SIMHA),
        (5, RashiId.KANYA),
        (6, RashiId.TULA),
        (7, RashiId.VRISHCHIKA),
        (8, RashiId.DHANUSHA),
        (9, RashiId.MAKARA),
        (10, RashiId.KUMBHA),
        (11, RashiId.MEENA),
    ],
)
def test_rashi_of_midpoint(index, expected):
    assert rashi_of(index * 30.0 + 15.0) is expected


@pytest.mark.parametrize("index", range(12))
def test_exact_boundary_belongs_to_next_rashi(index):
    """Floor semantics: a longitude exactly at 30°k belongs to the (k+1)-th sign."""
    assert rashi_of(ARCS[index]) is RASHI_ORDER[index % 12]


def test_zero_and_three_sixty_boundaries():
    assert rashi_of(0.0) is RashiId.MESHA
    assert rashi_of(360.0) is RashiId.MESHA
    assert rashi_of(-0.0) is RashiId.MESHA


def test_degree_in_rashi_ranges():
    for lon in (0.0, 29.999, 30.0, 89.0, 359.999):
        value = degree_in_rashi(lon)
        assert 0.0 <= value < 30.0
    assert degree_in_rashi(0.0) == 0.0
    assert degree_in_rashi(30.0) == 0.0
    assert degree_in_rashi(59.5) == pytest.approx(29.5)


@pytest.mark.parametrize("index", range(12))
def test_rashi_span_arc(index):
    start, end = rashi_span(RASHI_ORDER[index])
    assert start == pytest.approx(index * 30.0)
    assert end == pytest.approx((index + 1) * 30.0)


def test_rashi_index_floor_semantics():
    assert rashi_index_of(0.0) == 0
    assert rashi_index_of(30.0) == 1
    assert rashi_index_of(359.999) == 11


@pytest.mark.parametrize(
    "rashi, lord",
    [
        (RashiId.MESHA, BodyId.MARS),
        (RashiId.VRISHABHA, BodyId.VENUS),
        (RashiId.MITHUNA, BodyId.MERCURY),
        (RashiId.KARKA, BodyId.MOON),
        (RashiId.SIMHA, BodyId.SUN),
        (RashiId.KANYA, BodyId.MERCURY),
        (RashiId.TULA, BodyId.VENUS),
        (RashiId.VRISHCHIKA, BodyId.MARS),
        (RashiId.DHANUSHA, BodyId.JUPITER),
        (RashiId.MAKARA, BodyId.SATURN),
        (RashiId.KUMBHA, BodyId.SATURN),
        (RashiId.MEENA, BodyId.JUPITER),
    ],
)
def test_classical_rashi_lords(rashi, lord):
    assert lord_of(rashi) is lord


def test_rashi_of_wraps_large_inputs():
    assert rashi_of(720.0) is RashiId.MESHA  # 24 * 30
    assert rashi_of(750.0) is RashiId.VRISHABHA  # 25 * 30
