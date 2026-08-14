"""Error taxonomy tests (TEST-PLAN §19, SPEC §29)."""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

from bhava import (
    BhavaService,
    UnplacedBodyError,
    derive_house_analysis,
)
from bhava.errors import (
    BhavaError,
    InconsistentChartError,
    InvalidAnalysisRequestError,
    InvalidBhavaConfigError,
    UnsupportedReferenceError,
)
from bhava.models import BhavaConfig, UnplacedBodyBehavior
from jyotish import BodyId, HouseSystem


def test_error_hierarchy() -> None:
    for cls in (
        InvalidAnalysisRequestError,
        InvalidBhavaConfigError,
        InconsistentChartError,
        UnplacedBodyError,
        UnsupportedReferenceError,
    ):
        assert issubclass(cls, BhavaError)


def test_unsupported_reference() -> None:
    from bhava.service import _effective_references

    with pytest.raises(UnsupportedReferenceError) as exc:
        _effective_references(("LAGNA", "NONE"))
    assert "NONE" in str(exc.value)


def test_empty_references_rejected() -> None:
    from bhava.service import _effective_references

    with pytest.raises(InvalidAnalysisRequestError):
        _effective_references(())


def test_inconsistent_chart_wrong_count(whole_sign_chart) -> None:
    from dataclasses import replace

    chart = replace(whole_sign_chart, bhavas=whole_sign_chart.bhavas[:11])
    with pytest.raises(InconsistentChartError) as exc:
        derive_house_analysis(chart)
    assert "12 bhavas" in str(exc.value)


def test_inconsistent_chart_house_numbers(whole_sign_chart) -> None:
    from dataclasses import replace

    bad = list(whole_sign_chart.bhavas)
    bad[0] = replace(bad[0], house_number=13)
    chart = replace(whole_sign_chart, bhavas=tuple(bad))
    with pytest.raises(InconsistentChartError):
        derive_house_analysis(chart)


def test_inconsistent_chart_duplicate_bodies(whole_sign_chart) -> None:
    from dataclasses import replace

    states = list(whole_sign_chart.planet_states)
    states.append(states[0])
    chart = replace(whole_sign_chart, planet_states=tuple(states))
    with pytest.raises(InconsistentChartError):
        derive_house_analysis(chart)


def test_inconsistent_chart_non_canonical_order(whole_sign_chart) -> None:
    from dataclasses import replace

    states = list(whole_sign_chart.planet_states)
    states[0], states[1] = states[1], states[0]
    chart = replace(whole_sign_chart, planet_states=tuple(states))
    with pytest.raises(InconsistentChartError):
        derive_house_analysis(chart)


def test_inconsistent_chart_empty_states() -> None:
    from dataclasses import replace

    bhavas = tuple(make_bhava(h, (h - 1) * 30.0, h * 30.0) for h in range(1, 13))
    chart = make_chart((), bhavas)
    chart = replace(chart, planet_states=())
    with pytest.raises(InconsistentChartError):
        derive_house_analysis(chart)


def test_chart_system_must_be_in_config(whole_sign_chart) -> None:
    from dataclasses import replace

    chart = replace(whole_sign_chart, config=whole_sign_chart.config)  # WHOLE_SIGN
    cfg = BhavaConfig(house_systems=(HouseSystem.PLACIDUS,))
    with pytest.raises(InvalidBhavaConfigError):
        derive_house_analysis(chart, cfg)


def test_unplaced_body_raises_by_default() -> None:
    """A body in planet_states but inside no bhava span → UnplacedBodyError
    under the default RAISE policy (ADR-018)."""
    states = (make_planet_state(BodyId.SUN, 5.0),)
    bhavas = tuple(make_bhava(h, (h - 1) * 30.0, h * 30.0) for h in range(1, 13))
    # SUN at 5° is in house 1 — remove it from occupants to force unplaced.
    from dataclasses import replace

    bhavas = (replace(bhavas[0], occupants=(), occupant_states=()),) + bhavas[1:]
    chart = make_chart(states, bhavas)
    with pytest.raises(UnplacedBodyError) as exc:
        derive_house_analysis(chart)
    assert "SUN" in str(exc.value)
    assert "WHOLE_SIGN" in str(exc.value)


def test_unplaced_body_whole_sign_fallback_labels_rule() -> None:
    states = (make_planet_state(BodyId.SUN, 5.0),)
    bhavas = tuple(make_bhava(h, (h - 1) * 30.0, h * 30.0) for h in range(1, 13))
    from dataclasses import replace

    bhavas = (replace(bhavas[0], occupants=(), occupant_states=()),) + bhavas[1:]
    chart = make_chart(states, bhavas)
    cfg = BhavaConfig(unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK)
    analysis = derive_house_analysis(chart, cfg)
    fact = analysis.planet_house_facts[0]
    assert fact.house_rule == "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"
    assert "PLANET_HOUSE_WHOLE_SIGN_FALLBACK" in fact.derivation.id
    assert "chart.lagna" in fact.derivation.inputs


def test_jyotish_errors_propagate_unchanged() -> None:
    """Malformed birth data → JRE-003 InvalidBirthDataError propagates."""
    from jyotish.errors import InvalidBirthDataError

    service = BhavaService()
    from bhava import BhavaService as _BS  # noqa: F401  (reuse)

    with pytest.raises(InvalidBirthDataError):
        service.analyze(
            __import__("jyotish").BirthData(
                date="not-a-date", time="10:00", timezone="UTC", latitude=0.0, longitude=0.0
            )
        )
