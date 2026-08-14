"""Planet-to-planet geometry (requirement B, ADR-004).

Conjunction and aspects are defined from EXACT angular separation, never
"same house". A 25°-apart pair in one rashi is NOT conjunct; a 2°-apart pair
in different rashis IS. Same-rashi and same-bhava are separate boolean facts.
"""

from __future__ import annotations

import pytest
from tests.unit.jyotish.conftest import make_planet_state

from astronomy.models import BodyId
from jyotish.geometry import (
    angular_separation_deg,
    applying_separating,
    circular_distance_deg,
    normalized_separation_deg,
    pair_geometry,
)
from jyotish.models import ApplyingSeparating, AspectKind, JyotishConfig


def _config(**overrides):
    return JyotishConfig(**overrides)


def test_angular_separation_identity():
    assert angular_separation_deg(100.0, 0.0, 100.0, 0.0) == pytest.approx(0.0)
    assert angular_separation_deg(0.0, 0.0, 180.0, 0.0) == pytest.approx(180.0)
    assert angular_separation_deg(0.0, 0.0, 90.0, 0.0) == pytest.approx(90.0)
    assert angular_separation_deg(350.0, 0.0, 10.0, 0.0) == pytest.approx(20.0)


def test_angular_separation_uses_latitude():
    # Two points on the ecliptic with different latitudes.
    sep = angular_separation_deg(0.0, 0.0, 0.0, 30.0)
    assert sep == pytest.approx(30.0)


def test_normalized_separation_range():
    for a, b in [(0, 0), (0, 360), (350, 10), (120, 300), (200, 100)]:
        value = normalized_separation_deg(a, b)
        assert 0.0 <= value < 360.0
    assert normalized_separation_deg(0.0, 0.0) == 0.0
    assert normalized_separation_deg(0.0, 90.0) == pytest.approx(90.0)
    assert normalized_separation_deg(90.0, 0.0) == pytest.approx(270.0)


def test_circular_distance():
    assert circular_distance_deg(10.0, 0.0) == pytest.approx(10.0)
    assert circular_distance_deg(170.0, 180.0) == pytest.approx(10.0)
    assert circular_distance_deg(355.0, 0.0) == pytest.approx(5.0)
    assert circular_distance_deg(5.0, 180.0) == pytest.approx(175.0)


def test_conjunction_within_orb():
    a = make_planet_state(BodyId.SUN, longitude_used=100.0, speed=1.0)
    b = make_planet_state(BodyId.MOON, longitude_used=102.5, speed=13.0)
    geo = pair_geometry(a, b, _config(conjunction_orb_deg=8.0))
    assert geo.conjunction is True
    assert geo.conjunction_distance_deg == pytest.approx(2.5)
    assert geo.separation_deg == pytest.approx(2.5)


def test_wide_separation_not_conjunction():
    a = make_planet_state(BodyId.SUN, longitude_used=100.0)
    b = make_planet_state(BodyId.MOON, longitude_used=125.0)
    geo = pair_geometry(a, b, _config(conjunction_orb_deg=8.0))
    assert geo.conjunction is False
    assert geo.separation_deg == pytest.approx(25.0)


def test_same_rashi_but_wide_separation():
    """12° Aries and 28° Aries share a rashi; separation is 16° — not conjunct."""
    a = make_planet_state(BodyId.SUN, longitude_used=12.0)
    b = make_planet_state(BodyId.MOON, longitude_used=28.0)
    geo = pair_geometry(a, b, _config(conjunction_orb_deg=8.0))
    assert geo.same_rashi is True
    assert geo.separation_deg == pytest.approx(16.0)
    assert geo.conjunction is False


def test_different_rashi_close_pair_is_conjunct():
    a = make_planet_state(BodyId.SUN, longitude_used=29.0)
    b = make_planet_state(BodyId.MOON, longitude_used=31.0)
    geo = pair_geometry(a, b, _config(conjunction_orb_deg=8.0))
    assert geo.same_rashi is False
    assert geo.conjunction is True
    assert geo.separation_deg == pytest.approx(2.0)


def test_same_bhava_is_separate_fact():
    a = make_planet_state(BodyId.SUN, longitude_used=12.0)
    b = make_planet_state(BodyId.MOON, longitude_used=28.0)
    geo = pair_geometry(a, b, _config(), same_bhava=True)
    assert geo.same_bhava is True
    assert geo.same_rashi is True
    assert geo.conjunction is False
    # In generic mode (no chart) same_bhava stays None.
    generic = pair_geometry(a, b, _config())
    assert generic.same_bhava is None


def test_exact_opposition_detected():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=180.0)
    geo = pair_geometry(a, b, _config())
    opposition = next(aspect for aspect in geo.aspects if aspect.kind is AspectKind.OPPOSITION)
    assert opposition.distance_from_exact_deg == pytest.approx(0.0)
    assert opposition.within_orb is True


def test_aspect_kinds_cover_all_seven():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=180.0)
    geo = pair_geometry(a, b, _config())
    assert {aspect.kind for aspect in geo.aspects} == set(AspectKind)


def test_aspect_distance_and_orb():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=175.0)  # 5° from opposition
    geo = pair_geometry(a, b, _config())
    opposition = next(aspect for aspect in geo.aspects if aspect.kind is AspectKind.OPPOSITION)
    assert opposition.distance_from_exact_deg == pytest.approx(5.0)
    assert opposition.within_orb is True  # orb 8
    assert opposition.orb_deg == 8.0


def test_aspect_outside_orb():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=160.0)  # 20° from opposition
    geo = pair_geometry(a, b, _config())
    opposition = next(aspect for aspect in geo.aspects if aspect.kind is AspectKind.OPPOSITION)
    assert opposition.distance_from_exact_deg == pytest.approx(20.0)
    assert opposition.within_orb is False


def test_custom_orb_table_respected():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=62.0)  # 2° from sextile
    geo = pair_geometry(a, b, _config(aspect_orbs_deg={k: 1.0 for k in AspectKind}))
    sextile = next(aspect for aspect in geo.aspects if aspect.kind is AspectKind.SEXTILE)
    assert sextile.within_orb is False
    assert sextile.orb_deg == 1.0


def test_applying_separating_closed_form():
    cfg = _config()
    # Second body is 2° ahead of exact (separation 2°, ideal 0) and moving
    # faster: the gap widens -> SEPARATING.
    state = applying_separating(100.0, 1.0, 102.0, 13.0, 0.0, cfg.station_speed_epsilon)
    assert state is ApplyingSeparating.SEPARATING
    # Second body is 2° behind exact (separation 358°, ideal 0) and moving
    # faster: the gap narrows toward 0° -> APPLYING.
    state = applying_separating(100.0, 1.0, 98.0, 13.0, 0.0, cfg.station_speed_epsilon)
    assert state is ApplyingSeparating.APPLYING
    # Exactly at aspect -> NONE.
    state = applying_separating(100.0, 1.0, 100.0, 13.0, 0.0, cfg.station_speed_epsilon)
    assert state is ApplyingSeparating.NONE
    # Relative speed at zero (stationary reference) -> NONE.
    state = applying_separating(100.0, 1.0, 98.0, 1.0, 0.0, cfg.station_speed_epsilon)
    assert state is ApplyingSeparating.NONE


def test_pair_geometry_preserves_argument_order():
    sun = make_planet_state(BodyId.SUN, longitude_used=10.0)
    mars = make_planet_state(BodyId.MARS, longitude_used=50.0)
    geo = pair_geometry(mars, sun, _config())
    assert geo.first is BodyId.MARS
    assert geo.second is BodyId.SUN


def test_all_pairs_canonical_ordering_and_count():
    from jyotish.geometry import all_pairs

    states = (
        make_planet_state(BodyId.SUN, longitude_used=10.0),
        make_planet_state(BodyId.MOON, longitude_used=40.0),
        make_planet_state(BodyId.MARS, longitude_used=70.0),
        make_planet_state(BodyId.VENUS, longitude_used=100.0),
        make_planet_state(BodyId.JUPITER, longitude_used=130.0),
        make_planet_state(BodyId.MERCURY, longitude_used=160.0),
        make_planet_state(BodyId.SATURN, longitude_used=190.0),
        make_planet_state(BodyId.RAHU, longitude_used=220.0),
        make_planet_state(BodyId.KETU, longitude_used=40.0),
    )
    pairs = all_pairs(states, _config())
    assert len(pairs) == 36  # C(9, 2)
    assert pairs[0].first is BodyId.SUN and pairs[0].second is BodyId.MOON
    # Canonical (first, second) ordering is non-decreasing in BodyId order.
    order = [
        BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.MERCURY, BodyId.JUPITER,
        BodyId.VENUS, BodyId.SATURN, BodyId.RAHU, BodyId.KETU,
    ]
    for pair in pairs:
        assert order.index(pair.first) < order.index(pair.second)


def test_orb_config_echoed():
    a = make_planet_state(BodyId.SUN, longitude_used=0.0)
    b = make_planet_state(BodyId.MOON, longitude_used=90.0)
    geo = pair_geometry(a, b, _config(conjunction_orb_deg=10.0))
    assert geo.orb_config["conjunction"] == 10.0
    assert geo.orb_config["aspects"][AspectKind.TRINE.value] == 7.0
