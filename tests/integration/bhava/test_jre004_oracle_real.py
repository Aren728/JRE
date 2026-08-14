"""JRE-004 relative-house oracle equality on real charts (TEST-PLAN §10).

JRE-004 is a READ-ONLY oracle: ``normalize_snapshot`` is imported and
never modified. Equality is pinned for the four references
{LAGNA, MOON, SUN, ASC} (SPEC §11.3).
"""

from __future__ import annotations

import dataclasses

import pytest

from bhava import BhavaConfig
from jyotish import HouseSystem, JyotishConfig

REFS = ("LAGNA", "MOON", "SUN", "ASC")

knowledge = pytest.importorskip("knowledge")


def _oracle_four_refs(chart) -> dict[str, dict[str, int]]:
    from knowledge.synthesis import normalize_snapshot

    relative = normalize_snapshot(chart)["relative_houses"]
    return {ref: relative[ref] for ref in REFS}


@pytest.mark.parametrize("system", ["WHOLE_SIGN", "PLACIDUS", "KOCH", "EQUAL"])
def test_oracle_equality_real_chart(bhava_service, jyotish_service, birth, system) -> None:
    chart = jyotish_service.chart(
        birth, dataclasses.replace(JyotishConfig(), house_system=HouseSystem(system))
    )
    analysis = bhava_service.analyze_chart(
        chart, config=BhavaConfig(house_systems=(HouseSystem(system),))
    )
    assert analysis.relative_house_table == _oracle_four_refs(chart)
