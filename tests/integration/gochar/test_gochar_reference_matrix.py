"""Reference-point matrix tests (TEST-PLAN row 9, SPEC §16, DC §9.3).

Hard gate: ASC ≡ LAGNA — the same absolute-house anchor semantics in the
natal-frame house analysis regardless of which reference point the transit
is anchored to.
"""

from __future__ import annotations

import json

from gochar import GocharConfig, GocharNatalRequest, result_to_json
from jyotish import BodyId


def test_asc_equals_lagna_anchor(gochar_service, birth) -> None:
    """TEST-PLAN row 9 — LAGNA and ASC anchors produce semantically
    identical natal-frame house facts: every body lands in the same natal
    house number with the same rashi, lord, relative houses, and occupant
    SET. Only the ``natal_occupants`` tuple ORDERING may differ — an
    upstream JRE-003 echo nuance (the ASC path returns ``bhava.occupants``
    sorted by ``body.value``; the LAGNA path filters canonical
    ``planet_states`` order). JRE-006 echoes verbatim and never
    compensates (ADR-023), so the ASC ≡ LAGNA hard gate is asserted at
    the semantic level the contract pins (ADR-019: both anchor house 1)."""
    lagna = gochar_service.analyze_natal(
        GocharNatalRequest(
            birth=birth,
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.JUPITER),
            reference_point="LAGNA",
            config=GocharConfig(aspect_echo=True),
        )
    )
    asc = gochar_service.analyze_natal(
        GocharNatalRequest(
            birth=birth,
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.JUPITER),
            reference_point="ASC",
            config=GocharConfig(aspect_echo=True),
        )
    )
    lagna_payload = json.loads(result_to_json(lagna))["transit_house_analysis"]
    asc_payload = json.loads(result_to_json(asc))["transit_house_analysis"]
    # Same transit instant and chart → same house facts semantically; only
    # the reference echo differs.
    lf = {f["body"]: f for f in lagna_payload["transit_facts"]}
    af = {f["body"]: f for f in asc_payload["transit_facts"]}
    assert set(lf) == set(af)
    for body, lfact in lf.items():
        afact = af[body]
        assert lfact["natal_house_number"] == afact["natal_house_number"]
        assert lfact["natal_house_rashi"] == afact["natal_house_rashi"]
        assert lfact["natal_house_lord"] == afact["natal_house_lord"]
        assert (
            lfact["relative_house_by_reference"]
            == afact["relative_house_by_reference"]
        )
        assert lfact["aspects_to_natal"] == afact["aspects_to_natal"]
        assert set(lfact["natal_occupants"]) == set(afact["natal_occupants"])
    assert lagna_payload["reference"] == "LAGNA"
    assert asc_payload["reference"] == "ASC"
