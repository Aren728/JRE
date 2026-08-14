"""Configuration: explicit defaults, validation, no hidden settings (req. J)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from astronomy.models import Ayanamsa, NodeType, PositionType
from jyotish.config import DEFAULT_CONFIG_PATH, load_config, validate
from jyotish.errors import InvalidConfigError, InvalidOrbError
from jyotish.models import (
    DEFAULT_ASPECT_ORBS,
    AspectKind,
    HouseSystem,
    JyotishConfig,
    ZodiacMode,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_repo_config_file_exists_and_parses():
    path = REPO_ROOT / DEFAULT_CONFIG_PATH
    assert path.is_file(), f"expected {path}"
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    assert "jyotish" in data
    assert "aspect_orbs" in data["jyotish"]


def test_load_config_reads_repo_defaults():
    config = load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)
    assert config.zodiac_mode is ZodiacMode.SIDEREAL
    assert config.house_system is HouseSystem.WHOLE_SIGN
    assert config.conjunction_orb_deg == 8.0
    assert config.coordinate_precision == 1
    assert config.aspect_orbs_deg == DEFAULT_ASPECT_ORBS


def test_load_config_missing_file_uses_defaults(tmp_path):
    config = load_config(tmp_path / "nope.toml")
    assert config == load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)


def test_load_config_overrides(tmp_path):
    path = tmp_path / "custom.toml"
    path.write_text(
        "[jyotish]\nzodiac_mode = 'TROPICAL'\nhouse_system = 'PLACIDUS'\n"
        "conjunction_orb_deg = 10.0\ncoordinate_precision = 2\n"
        "[jyotish.aspect_orbs]\nCONJUNCTION = 10.0\nOPPOSITION = 8.0\nTRINE = 7.0\n"
        "SQUARE = 7.0\nSEXTILE = 5.0\nQUINCUNX = 4.0\nSEMISEXTILE = 2.0\n"
    )
    config = load_config(path)
    assert config.zodiac_mode is ZodiacMode.TROPICAL
    assert config.house_system is HouseSystem.PLACIDUS
    assert config.conjunction_orb_deg == 10.0
    assert config.coordinate_precision == 2


def test_conjunction_override_without_aspect_table_rejected(tmp_path):
    """Changing conjunction_orb_deg alone is inconsistent -> rejected."""
    path = tmp_path / "inconsistent.toml"
    path.write_text(
        "[jyotish]\nconjunction_orb_deg = 10.0\n"
    )
    with pytest.raises(InvalidOrbError, match="must equal"):
        load_config(path)


def test_default_config_is_valid():
    assert validate(JyotishConfig()) == JyotishConfig()


@pytest.mark.parametrize("precision", [-1, 4, 10])
def test_coordinate_precision_range_enforced(precision):
    with pytest.raises(InvalidConfigError, match="coordinate_precision"):
        validate(JyotishConfig(coordinate_precision=precision))


def test_conjunction_orb_must_be_positive():
    with pytest.raises(InvalidOrbError, match="conjunction_orb_deg"):
        validate(JyotishConfig(conjunction_orb_deg=0.0))


def test_aspect_orbs_must_cover_all_kinds():
    orbs = dict(DEFAULT_ASPECT_ORBS)
    del orbs[AspectKind.TRINE]
    with pytest.raises(InvalidOrbError, match="missing"):
        validate(JyotishConfig(aspect_orbs_deg=orbs))


def test_aspect_orbs_unknown_kind_rejected():
    from jyotish.models import ApplyingSeparating as _unused  # noqa: F401

    orbs = dict(DEFAULT_ASPECT_ORBS)
    orbs["FRIENDSHIP"] = 1.0  # type: ignore[dict-item]
    with pytest.raises(InvalidOrbError, match="extra"):
        validate(JyotishConfig(aspect_orbs_deg=orbs))  # type: ignore[arg-type]


def test_conjunction_consistency_enforced():
    orbs = dict(DEFAULT_ASPECT_ORBS)
    orbs[AspectKind.CONJUNCTION] = 5.0
    with pytest.raises(InvalidOrbError, match="must equal"):
        validate(JyotishConfig(conjunction_orb_deg=8.0, aspect_orbs_deg=orbs))


def test_each_orb_positive():
    orbs = dict(DEFAULT_ASPECT_ORBS)
    orbs[AspectKind.SQUARE] = -1.0
    with pytest.raises(InvalidOrbError, match="positive"):
        validate(JyotishConfig(aspect_orbs_deg=orbs))


def test_transit_parameters_positive():
    with pytest.raises(InvalidConfigError, match="transit_sample_step_hours"):
        validate(JyotishConfig(transit_sample_step_hours=0.0))
    with pytest.raises(InvalidConfigError, match="transit_tolerance_jd"):
        validate(JyotishConfig(transit_tolerance_jd=-1.0))


def test_config_to_dict_round_trip():
    config = JyotishConfig(zodiac_mode=ZodiacMode.TROPICAL, coordinate_precision=2)
    restored = JyotishConfig.from_dict(config.to_dict())
    assert restored == config


# --------------------------------------------------------------------------- #
# SPEC §19/§20 error taxonomy: unknown enum values -> InvalidConfigError
# --------------------------------------------------------------------------- #


def test_validate_unknown_enum_values_raise_typed_error():
    """Raw strings / unknown values where an enum is expected must raise
    ``InvalidConfigError`` (SPEC §19/§20) — never a crash in the registry."""
    with pytest.raises(InvalidConfigError, match="house_system"):
        validate(JyotishConfig(house_system="BOGUS"))  # type: ignore[arg-type]
    with pytest.raises(InvalidConfigError, match="zodiac_mode"):
        validate(JyotishConfig(zodiac_mode="BOGUS"))  # type: ignore[arg-type]
    with pytest.raises(InvalidConfigError, match="node_model"):
        validate(JyotishConfig(node_model="BOGUS"))  # type: ignore[arg-type]
    with pytest.raises(InvalidConfigError, match="position_type"):
        validate(JyotishConfig(position_type="BOGUS"))  # type: ignore[arg-type]
    with pytest.raises(InvalidConfigError, match="ayanamsa"):
        validate(JyotishConfig(ayanamsa="BOGUS"))  # type: ignore[arg-type]


def test_config_from_dict_unknown_enum_raises_typed_error():
    """The JSON input parser must surface the documented ``InvalidConfigError``
    (SPEC §21: input parsers validate on construction, typed errors) instead of
    a raw ``ValueError``."""
    from jyotish.serialize import config_from_dict

    # The ValueError from enum construction is wrapped into the typed error
    # and names the enum (e.g. ``'BOGUS' is not a valid HouseSystem``).
    with pytest.raises(InvalidConfigError, match="HouseSystem"):
        config_from_dict({"house_system": "BOGUS"})
    with pytest.raises(InvalidConfigError, match="ZodiacMode"):
        config_from_dict({"zodiac_mode": "BOGUS"})


def test_load_config_unknown_enum_raises_typed_error(tmp_path):
    """Invalid TOML enum values raise ``InvalidConfigError`` (SPEC §19),
    not a raw ``ValueError``."""
    path = tmp_path / "bad.toml"
    path.write_text("[jyotish]\nzodiac_mode = 'BOGUS'\n")
    with pytest.raises(InvalidConfigError, match="zodiac_mode"):
        load_config(path)
    path2 = tmp_path / "bad2.toml"
    path2.write_text("[jyotish]\nhouse_system = 'BOGUS'\n")
    with pytest.raises(InvalidConfigError, match="house_system"):
        load_config(path2)


# --------------------------------------------------------------------------- #
# DATA-CONTRACT §10/§12: empty ``"config": {}`` shape + round-trip
# --------------------------------------------------------------------------- #


def test_config_from_dict_empty_dict_equals_defaults():
    """DATA-CONTRACT §10 documents ``"config": {}`` as a valid input shape;
    it must deserialize to the full default config (ayanamsa LAHIRI, not None)
    so the service boundary accepts it (§12 round-trip semantics)."""
    from jyotish.serialize import config_from_dict

    assert config_from_dict({}) == JyotishConfig()
    assert config_from_dict({}).ayanamsa is Ayanamsa.LAHIRI


def test_config_from_dict_explicit_null_ayanamsa_preserved():
    """An explicit ``"ayanamsa": null`` must stay None (Ayanamsa | None),
    distinct from a missing key which uses the LAHIRI default."""
    from jyotish.serialize import config_from_dict

    config = config_from_dict({"ayanamsa": None})
    assert config.ayanamsa is None
    assert config == JyotishConfig(ayanamsa=None)


def test_config_from_dict_full_round_trip_all_fields():
    """DATA-CONTRACT §12: ``config_from_dict`` round-trips every field."""
    from jyotish.serialize import config_from_dict

    for config in (
        JyotishConfig(),
        JyotishConfig(zodiac_mode=ZodiacMode.TROPICAL, ayanamsa=None),
        JyotishConfig(
            house_system=HouseSystem.PLACIDUS,
            node_model=NodeType.TRUE,
            position_type=PositionType.TRUE,
            timezone="Asia/Kolkata",
            coordinate_precision=2,
        ),
    ):
        assert config_from_dict(config.to_dict()) == config


# --------------------------------------------------------------------------- #
# SPEC §19: config/jyotish.toml is authoritative for every declared default
# --------------------------------------------------------------------------- #


def test_load_config_honors_all_declared_keys(tmp_path):
    """Every default declared in ``config/jyotish.toml`` must actually be read
    by ``load_config`` (SPEC §19 "no hidden defaults") — ayanamsa, node_model,
    position_type and timezone are not silently ignored."""
    path = tmp_path / "custom.toml"
    path.write_text(
        "[jyotish]\n"
        "zodiac_mode = 'TROPICAL'\n"
        "ayanamsa = 'RAMAN'\n"
        "house_system = 'PLACIDUS'\n"
        "node_model = 'TRUE'\n"
        "position_type = 'TRUE'\n"
        "timezone = 'Asia/Kolkata'\n"
        "coordinate_precision = 2\n"
    )
    config = load_config(path)
    assert config.zodiac_mode is ZodiacMode.TROPICAL
    assert config.ayanamsa is Ayanamsa.RAMAN
    assert config.house_system is HouseSystem.PLACIDUS
    assert config.node_model is NodeType.TRUE
    assert config.position_type is PositionType.TRUE
    assert config.timezone == "Asia/Kolkata"
    assert config.coordinate_precision == 2


def test_repo_toml_declared_values_are_authoritative():
    """The committed config/jyotish.toml declares values equal to the
    documented defaults; loading it must not silently drop any of them."""
    config = load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)
    assert config.ayanamsa is Ayanamsa.LAHIRI
    assert config.node_model is NodeType.MEAN
    assert config.position_type is PositionType.APPARENT
    assert config.timezone == "UTC"
