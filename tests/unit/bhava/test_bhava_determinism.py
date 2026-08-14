"""In-process determinism + canonical ordering (TEST-PLAN §4/§21)."""

from __future__ import annotations

import json

from tests.unit.bhava.conftest import make_whole_sign_chart

from bhava import BhavaConfig, derive_house_analysis, result_to_json
from jyotish import BodyId


def test_same_chart_same_config_bit_identical() -> None:
    chart = make_whole_sign_chart()
    cfg = BhavaConfig(
        house_systems=(__import__("jyotish").HouseSystem.WHOLE_SIGN,)
    )
    a = result_to_json(derive_house_analysis(chart, cfg))
    b = result_to_json(derive_house_analysis(chart, cfg))
    assert a == b
    assert json.loads(a) == json.loads(b)


def test_canonical_orderings(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    # Houses ascending.
    assert [h.house_number for h in analysis.derived_houses] == list(range(1, 13))
    # Bodies canonical (SUN..KETU).
    assert [f.body for f in analysis.planet_house_facts] == [
        BodyId.SUN,
        BodyId.MOON,
        BodyId.MARS,
        BodyId.MERCURY,
        BodyId.JUPITER,
        BodyId.VENUS,
        BodyId.SATURN,
        BodyId.RAHU,
        BodyId.KETU,
    ]
    # References pinned order.
    assert list(analysis.relative_house_table) == ["LAGNA", "MOON", "SUN", "ASC"]
    # Categories canonical order.
    assert [c.value for c in analysis.derived_houses[0].categories] == ["KENDRA", "TRIKONA"]
    assert [c.value for c in analysis.derived_houses[5].categories] == ["DUSTHANA", "UPACHAYA"]


def test_dict_order_stable_across_runs(whole_sign_chart) -> None:
    first = json.dumps(
        __import__("bhava").result_to_dict(derive_house_analysis(whole_sign_chart))
    )
    second = json.dumps(
        __import__("bhava").result_to_dict(derive_house_analysis(whole_sign_chart))
    )
    assert first == second
