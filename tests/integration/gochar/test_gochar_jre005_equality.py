"""JRE-005 cross-layer equality tests (TEST-PLAN row 7-8, SPEC §16, DC §9).

Hard gates:
- the NATAL transit-house analysis equals the JRE-005
  ``derive_transit_analysis`` output for the same inputs (byte-identical
  serialized values);
- the transit-to-natal aspect echo covers the full transit-body ×
  natal-planet pair set in canonical order (SPEC §11.4).
"""

from __future__ import annotations

import json

import bhava
from gochar import GocharNatalRequest, result_to_json
from jyotish import BodyId


def test_natal_house_analysis_equals_jre005(gochar_service, jyotish_service, birth) -> None:
    """TEST-PLAN row 7 — GocharService NATAL house facts == JRE-005 output."""
    from gochar import GocharConfig

    req = GocharNatalRequest(
        birth=birth,
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS),
        config=GocharConfig(house_system="WHOLE_SIGN", aspect_echo=True),
    )
    result = gochar_service.analyze_natal(req)

    # Independent JRE-005 composition of the same JRE-003 inputs.
    import datetime as dt

    from jyotish import TransitReferencePoint

    transit = jyotish_service.transit_through_houses(
        birth,
        dt.date(2026, 6, 15),
        dt.time(12, 0, 0),
        "UTC",
        TransitReferencePoint.LAGNA,
    )
    natal_chart = jyotish_service.chart(birth)
    expected = bhava.derive_transit_analysis(transit, natal_chart)

    actual = json.loads(result_to_json(result))["transit_house_analysis"]
    expected_payload = json.loads(bhava.result_to_json(expected))
    assert actual == expected_payload


def test_transit_to_natal_full_pair_set(gochar_service, birth) -> None:
    """TEST-PLAN row 8 — transit body × natal planet pairs, canonical order."""
    req = GocharNatalRequest(
        birth=birth,
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
    )
    result = gochar_service.analyze_natal(req)
    assert result.transit_to_natal_aspects is not None
    pairs = [
        (g.first.value, g.second.value) for g in result.transit_to_natal_aspects
    ]
    assert pairs[0] == ("SUN", "SUN")
    assert pairs[1] == ("SUN", "MOON")
    assert pairs[8] == ("SUN", "KETU")
    assert pairs[9] == ("MOON", "SUN")
    assert pairs[-1] == ("MOON", "KETU")
    assert len(pairs) == 18
