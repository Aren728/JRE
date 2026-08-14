"""JRE-004 relative-house equality oracle (TEST-PLAN §10, ADR-014).

JRE-004 is a READ-ONLY compatibility oracle: this test imports
``knowledge.synthesis.normalize_snapshot`` and never modifies it. The
equality contract (SPEC §11.3) pins the four references
{LAGNA, MOON, SUN, ASC} — JRE-004's ``relative_houses`` additionally
carries every body as a reference, which JRE-005 does not emit.
"""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

from bhava import BhavaConfig, derive_house_analysis
from bhava.models import UnplacedBodyBehavior
from jyotish import BodyId, HouseSystem

knowledge = pytest.importorskip("knowledge")

REFS = ("LAGNA", "MOON", "SUN", "ASC")


def _oracle_four_refs(chart) -> dict[str, dict[str, int]]:
    from knowledge.synthesis import normalize_snapshot

    relative = normalize_snapshot(chart)["relative_houses"]
    return {ref: relative[ref] for ref in REFS}


def test_oracle_equality_whole_sign(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    assert analysis.relative_house_table == _oracle_four_refs(whole_sign_chart)


def test_oracle_equality_cusp_spans() -> None:
    """Cusp-anchored spans (10° offset) — occupancy-based, never silently
    whole-sign; JRE-004 consumes the same chart bhavas."""
    states = tuple(
        make_planet_state(body, 15.0 + index * 30.0)
        for index, body in enumerate(BodyId)
    )
    bhavas = tuple(
        make_bhava(
            h, 10.0 + (h - 1) * 30.0, 10.0 + h * 30.0, (states[h - 1],) if h <= len(states) else ()
        )
        for h in range(1, 13)
    )
    chart = make_chart(states, bhavas, HouseSystem.PLACIDUS)
    analysis = derive_house_analysis(
        chart, BhavaConfig(house_systems=(HouseSystem.PLACIDUS,))
    )
    assert analysis.relative_house_table == _oracle_four_refs(chart)


def test_oracle_equality_multi_occupant_house() -> None:
    """Two occupants in house 1 — setdefault-first-occupancy semantics
    shared with JRE-004."""
    states = (
        make_planet_state(BodyId.SUN, 5.0),
        make_planet_state(BodyId.MOON, 15.0),
        make_planet_state(BodyId.MARS, 35.0),
        make_planet_state(BodyId.MERCURY, 65.0),
        make_planet_state(BodyId.JUPITER, 95.0),
        make_planet_state(BodyId.VENUS, 125.0),
        make_planet_state(BodyId.SATURN, 155.0),
        make_planet_state(BodyId.RAHU, 185.0),
        make_planet_state(BodyId.KETU, 215.0),
    )
    bhavas = [
        make_bhava(1, 0.0, 30.0, (states[0], states[1])),
        make_bhava(2, 30.0, 60.0, (states[2],)),
        make_bhava(3, 60.0, 90.0, (states[3],)),
        make_bhava(4, 90.0, 120.0, (states[4],)),
        make_bhava(5, 120.0, 150.0, (states[5],)),
        make_bhava(6, 150.0, 180.0, (states[6],)),
        make_bhava(7, 180.0, 210.0, (states[7],)),
        make_bhava(8, 210.0, 240.0, (states[8],)),
        make_bhava(9, 240.0, 270.0),
        make_bhava(10, 270.0, 300.0),
        make_bhava(11, 300.0, 330.0),
        make_bhava(12, 330.0, 360.0),
    ]
    chart = make_chart(states, tuple(bhavas))
    analysis = derive_house_analysis(chart)
    assert analysis.relative_house_table == _oracle_four_refs(chart)


def test_oracle_equality_with_whole_sign_fallback() -> None:
    """Synthetic unplaced body: JRE-005 WHOLE_SIGN_FALLBACK mirrors
    JRE-004's robustness fallback (same arithmetic), so equality holds."""
    from dataclasses import replace

    from tests.unit.bhava.conftest import make_whole_sign_chart

    chart = make_whole_sign_chart()
    bhavas = list(chart.bhavas)
    bhavas[0] = replace(bhavas[0], occupants=(), occupant_states=())
    chart = replace(chart, bhavas=tuple(bhavas))
    cfg = BhavaConfig(unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK)
    analysis = derive_house_analysis(chart, cfg)
    assert analysis.relative_house_table == _oracle_four_refs(chart)
