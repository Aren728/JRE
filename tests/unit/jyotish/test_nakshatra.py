"""All 27 Nakshatras, lords, padas — every boundary exercised (req. G, §N)."""

from __future__ import annotations

import pytest

from astronomy.models import BodyId
from jyotish.models import NakshatraId, Pada
from jyotish.nakshatra import (
    NAKSHATRA_ARC,
    NAKSHATRA_CATALOG_VERSION,
    NAKSHATRA_LORD_CYCLE,
    NAKSHATRA_ORDER,
    NAKSHATRA_SOURCE,
    PADA_ARC,
    degree_in_nakshatra,
    lord_of,
    nakshatra_index_of,
    nakshatra_of,
    nakshatra_span,
    pada_of,
    pada_span,
)

ORDER = list(NakshatraId)
ARCS = [i * NAKSHATRA_ARC for i in range(27)]


def test_catalog_is_versioned_and_sourced():
    assert NAKSHATRA_CATALOG_VERSION == "1.0.0"
    assert "Vimshottari" in NAKSHATRA_SOURCE


def test_twenty_seven_nakshatras_in_order():
    assert len(NAKSHATRA_ORDER) == 27
    assert NAKSHATRA_ORDER[0] is NakshatraId.ASHWINI
    assert NAKSHATRA_ORDER[26] is NakshatraId.REVATI
    assert list(NAKSHATRA_ORDER) == ORDER


def test_arc_constants():
    assert pytest.approx(360.0 / 27.0) == NAKSHATRA_ARC
    assert pytest.approx(NAKSHATRA_ARC / 4.0) == PADA_ARC
    assert pytest.approx(3.0 + 1.0 / 3.0) == PADA_ARC


@pytest.mark.parametrize("index", range(27))
def test_nakshatra_of_midpoint(index):
    assert nakshatra_of(index * NAKSHATRA_ARC + NAKSHATRA_ARC / 2.0) is NAKSHATRA_ORDER[index]


@pytest.mark.parametrize("index", range(27))
def test_exact_nakshatra_boundary_belongs_to_next(index):
    assert nakshatra_of(ARCS[index]) is NAKSHATRA_ORDER[index % 27]


def test_zero_and_three_sixty_boundaries():
    assert nakshatra_of(0.0) is NakshatraId.ASHWINI
    assert nakshatra_of(360.0) is NakshatraId.ASHWINI
    assert nakshatra_of(-0.0) is NakshatraId.ASHWINI


def test_degree_in_nakshatra_ranges():
    for lon in (0.0, ARCS[1], 100.0, 359.999):
        assert 0.0 <= degree_in_nakshatra(lon) < NAKSHATRA_ARC


def test_nakshatra_spans_cover_360():
    total = 0.0
    for index, nak in enumerate(NAKSHATRA_ORDER):
        start, end = nakshatra_span(nak)
        assert end - start == pytest.approx(NAKSHATRA_ARC)
        assert start == pytest.approx(ARCS[index])
        total = end
    assert total == pytest.approx(360.0)


@pytest.mark.parametrize("index", range(27))
def test_pada_quadrants_within_nakshatra(index):
    start = ARCS[index]
    for pada in (Pada.PADA_1, Pada.PADA_2, Pada.PADA_3, Pada.PADA_4):
        p_start, p_end = pada_span(NAKSHATRA_ORDER[index], pada)
        assert p_end - p_start == pytest.approx(PADA_ARC)
        assert p_start == pytest.approx(start + (int(pada) - 1) * PADA_ARC)


@pytest.mark.parametrize("index", range(27))
def test_pada_of_all_four_quarters(index):
    start = ARCS[index]
    for pada_num in (1, 2, 3, 4):
        midpoint = start + (pada_num - 0.5) * PADA_ARC
        assert pada_of(midpoint) is Pada(pada_num)


@pytest.mark.parametrize("index", range(108))
def test_all_108_pada_boundaries(index):
    """Every one of the 108 padas is reachable at its own start longitude.

    ``index`` enumerates padas in zodiacal order: nakshatra index // 4, pada
    (index % 4) + 1. A point just inside the pada start classifies into that
    pada (boundaries are float-fragile at exact equality, so we assert the
    open-interval semantics on both sides of the boundary).
    """
    nak_index, pada_num = divmod(index, 4)
    start = nak_index * NAKSHATRA_ARC + pada_num * PADA_ARC
    assert nakshatra_of(start) is NAKSHATRA_ORDER[nak_index % 27]
    # Just inside the pada -> the pada itself.
    assert pada_of(start + 1e-6) is Pada(pada_num + 1)
    # Just before the boundary -> the previous pada (when within a nakshatra).
    if pada_num > 0:
        assert pada_of(start - 1e-6) is Pada(pada_num)


@pytest.mark.parametrize(
    "index, lord",
    [
        (0, BodyId.KETU),  # ASHWINI
        (1, BodyId.VENUS),  # BHARANI
        (2, BodyId.SUN),  # KRITTIKA
        (3, BodyId.MOON),  # ROHINI
        (4, BodyId.MARS),  # MRIGASHIRA
        (5, BodyId.RAHU),  # ARDRA
        (6, BodyId.JUPITER),  # PUNARVASU
        (7, BodyId.SATURN),  # PUSHYA
        (8, BodyId.MERCURY),  # ASHLESHA
        (9, BodyId.KETU),  # MAGHA
        (10, BodyId.VENUS),  # PURVA_PHALGUNI
        (11, BodyId.SUN),  # UTTARA_PHALGUNI
        (12, BodyId.MOON),  # HASTA
        (13, BodyId.MARS),  # CHITRA
        (14, BodyId.RAHU),  # SWATI
        (15, BodyId.JUPITER),  # VISHAKHA
        (16, BodyId.SATURN),  # ANURADHA
        (17, BodyId.MERCURY),  # JYESHTHA
        (18, BodyId.KETU),  # MULA
        (19, BodyId.VENUS),  # PURVA_ASHADHA
        (20, BodyId.SUN),  # UTTARA_ASHADHA
        (21, BodyId.MOON),  # SHRAVANA
        (22, BodyId.MARS),  # DHANISHTHA
        (23, BodyId.RAHU),  # SHATABHISHA
        (24, BodyId.JUPITER),  # PURVA_BHADRAPADA
        (25, BodyId.SATURN),  # UTTARA_BHADRAPADA
        (26, BodyId.MERCURY),  # REVATI
    ],
)
def test_vimshottari_lord_cycle(index, lord):
    assert lord_of(NAKSHATRA_ORDER[index]) is lord
    # The cycle is the 9-planet Vimshottari sequence repeated three times.
    assert NAKSHATRA_LORD_CYCLE[index % 9] is lord


def test_lord_cycle_repeats_every_nine():
    # The 9-planet cycle repeated 3x covers all 27 nakshatra lords.
    assert len(NAKSHATRA_LORD_CYCLE) == 9
    assert [lord_of(nak) for nak in NAKSHATRA_ORDER] == list(NAKSHATRA_LORD_CYCLE) * 3


def test_nakshatra_of_wraps():
    assert nakshatra_of(720.0) is NakshatraId.ASHWINI


def test_nakshatra_index_floor():
    assert nakshatra_index_of(0.0) == 0
    assert nakshatra_index_of(ARCS[1]) == 1
    assert nakshatra_index_of(359.999) == 26
