"""Config echo tests (TEST-PLAN §20)."""

from __future__ import annotations

from bhava import BhavaConfig, UnplacedBodyBehavior
from jyotish import HouseSystem


def test_config_echo_equals_input(bhava_service, birth) -> None:
    cfg = BhavaConfig(
        cusp_proximity_orb_deg=4.0,
        house_systems=(HouseSystem.WHOLE_SIGN,),
        tradition_profile="parashari",
    )
    result = bhava_service.analyze(birth, config=cfg)
    assert result.config == cfg
    for analysis in result.analyses:
        echo = analysis.chart_echo
        assert echo.cusp_proximity_orb_deg == 4.0
        assert echo.tradition_profile == "parashari"
        assert echo.derivation_version == cfg.derivation_version


def test_analyze_chart_config_echo(bhava_service, jyotish_service, birth) -> None:
    chart = jyotish_service.chart(birth)
    analysis = bhava_service.analyze_chart(
        chart,
        config=BhavaConfig(unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK),
    )
    assert analysis.chart_echo.unplaced_body_behavior == "WHOLE_SIGN_FALLBACK"
    assert analysis.chart_echo.rashi_catalog_version


def test_birth_snapshot_echo(bhava_service, birth) -> None:
    result = bhava_service.analyze(birth)
    assert result.birth_snapshot == birth
    assert result.birth_snapshot.timezone == "Asia/Kolkata"
