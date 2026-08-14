"""Model/enum/config tests (TEST-PLAN §3)."""

from __future__ import annotations

import json

import pytest

from bhava import (
    BhavaConfig,
    BoundaryKind,
    DerivationId,
    FactFrame,
    HouseCategory,
    OccupancyStatus,
    RelativeHouseFrame,
    UnplacedBodyBehavior,
    result_to_dict,
    result_to_json,
)
from bhava.errors import InvalidBhavaConfigError
from jyotish import BodyId, HouseSystem


def test_bhava_config_defaults() -> None:
    cfg = BhavaConfig()
    assert cfg.cusp_proximity_orb_deg == 3.0
    assert cfg.house_systems == (HouseSystem.WHOLE_SIGN,)
    assert cfg.include_empty_houses is True
    assert cfg.unplaced_body_behavior is UnplacedBodyBehavior.RAISE
    assert cfg.tradition_profile is None
    assert cfg.anchor_frame is RelativeHouseFrame.HOUSE_OCCUPANCY
    assert cfg.derivation_version == "0.2.0"


def test_config_round_trip() -> None:
    cfg = BhavaConfig(
        cusp_proximity_orb_deg=2.5,
        house_systems=(HouseSystem.WHOLE_SIGN, HouseSystem.PLACIDUS),
        include_empty_houses=False,
        unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK,
        tradition_profile="parashari",
        anchor_frame=RelativeHouseFrame.HOUSE_OCCUPANCY,
        derivation_version="0.2.0",
    )
    assert BhavaConfig.from_dict(cfg.to_dict()) == cfg
    assert json.loads(result_to_json(cfg)) == cfg.to_dict()


def test_config_missing_key_uses_default() -> None:
    cfg = BhavaConfig.from_dict({})
    assert cfg == BhavaConfig()


def test_config_explicit_null_profile() -> None:
    cfg = BhavaConfig.from_dict({"tradition_profile": None})
    assert cfg.tradition_profile is None


def test_config_enum_serialization() -> None:
    assert OccupancyStatus.OCCUPIED.value == "OCCUPIED"
    assert BoundaryKind.SIGN_BOUNDARY.value == "SIGN_BOUNDARY"
    assert HouseCategory.KENDRA.value == "KENDRA"
    assert RelativeHouseFrame.HOUSE_OCCUPANCY.value == "HOUSE_OCCUPANCY"
    assert FactFrame.NATAL.value == "NATAL"
    assert FactFrame.TRANSIT.value == "TRANSIT"
    assert DerivationId.RELATIVE_HOUSE.value == "RELATIVE_HOUSE"


def test_unknown_enum_value_rejected() -> None:
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"unplaced_body_behavior": "AUTO_FALLBACK"})
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"anchor_frame": "SIGN_GRID"})
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"house_systems": ["PLACIDUS", "NONSENSE"]})


def test_float_round_trip_and_negative_zero() -> None:
    cfg = BhavaConfig(cusp_proximity_orb_deg=3.0)
    payload = result_to_dict(cfg)
    payload["cusp_proximity_orb_deg"] = -0.0
    assert json.loads(json.dumps(payload))["cusp_proximity_orb_deg"] == 0.0
    assert result_to_dict(cfg)["cusp_proximity_orb_deg"] == 3.0


def test_body_ids_reused_from_jyotish() -> None:
    assert BodyId.SUN.value == "SUN"
    assert BodyId.RAHU.value == "RAHU"
