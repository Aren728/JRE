"""Aspect state echo tests (TEST-PLAN §2 rows 17-18, SPEC §15, ADR-029).

JRE-006 echoes JRE-003 ``PairGeometry`` results — including
``AspectKind`` and ``ApplyingSeparating`` state at the instant. Aspect
**events** (perfection timestamps) are NOT in v0.1; the limitation is
machine-testable: ``GocharIntervalResult`` contains no aspect-event kind,
and instant results carry aspect state only.
"""

from __future__ import annotations

from gochar import (
    GocharConfig,
    GocharInstantRequest,
    GocharIntervalRequest,
    GocharNatalRequest,
    GocharService,
    result_to_dict,
)
from jyotish import (
    ApplyingSeparating,
    AspectKind,
    BirthData,
    BodyId,
)

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)


def test_instant_aspect_state_echoed(fake_service) -> None:
    svc = GocharService(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
    )
    result = svc.analyze_instant(req)
    geometry = result.pair_geometry[0]
    # All 7 AspectKind entries echoed (JRE-003 pin).
    kinds = [aspect.kind for aspect in geometry.aspects]
    assert set(kinds) == set(AspectKind)
    # ApplyingSeparating is instant state, present on every aspect.
    for aspect in geometry.aspects:
        assert aspect.applying_separating in (
            ApplyingSeparating.APPLYING,
            ApplyingSeparating.SEPARATING,
            ApplyingSeparating.NONE,
        )


def test_natal_transit_to_natal_aspects_full_pair_set(fake_service) -> None:
    """SPEC §11.4 / TEST-PLAN row 8 — full transit×natal pair set in
    canonical order (transit body outer, natal body inner)."""
    svc = GocharService(fake_service)
    req = GocharNatalRequest(
        birth=BIRTH,
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
    )
    result = svc.analyze_natal(req)
    assert result.transit_to_natal_aspects is not None
    # 9 natal planets × 2 requested transit bodies = 18 pairs.
    assert len(result.transit_to_natal_aspects) == 18
    pairs = [
        (g.first.value, g.second.value) for g in result.transit_to_natal_aspects
    ]
    assert pairs[0] == ("SUN", "SUN")
    assert pairs[1] == ("SUN", "MOON")
    assert pairs[9] == ("MOON", "SUN")


def test_natal_aspect_echo_disabled(fake_service) -> None:
    svc = GocharService(fake_service)
    req = GocharNatalRequest(
        birth=BIRTH,
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(aspect_echo=False),
    )
    result = svc.analyze_natal(req)
    assert result.transit_to_natal_aspects is None
    assert "pair-geometry" not in result.provenance.algorithm


def test_no_aspect_event_kind_in_interval(fake_service) -> None:
    """SPEC §25.3 / ADR-029 — interval events contain only the JRE-003
    ``TransitEventKind`` set; aspect perfection events are deferred."""
    svc = GocharService(fake_service)
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-15T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
    )
    result = svc.analyze_interval(req)
    from jyotish import TransitEventKind

    for event in result.events:
        assert isinstance(event.kind, TransitEventKind)
    # No aspect-related kind exists in the JRE-003 enum.
    assert not hasattr(TransitEventKind, "ASPECT_EXACT")


def test_aspect_echo_never_interpreted(fake_service) -> None:
    """Aspect facts are geometric only — no auspiciousness/meaning fields."""
    svc = GocharService(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
    )
    payload = result_to_dict(svc.analyze_instant(req))
    first_aspect = payload["pair_geometry"][0]["aspects"][0]
    assert set(first_aspect) == {
        "kind",
        "exact_angle_deg",
        "separation_deg",
        "distance_from_exact_deg",
        "within_orb",
        "orb_deg",
        "applying_separating",
    }
