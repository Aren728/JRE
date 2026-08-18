"""Model + config tests (normative specification §6-§7, §12, §18).

Frozen definitions carry validated fields with no hidden defaults; the
authoritative ``config/varga.toml`` must exist and declare every field;
programmatic ``VargaConfig`` construction is validated; mapping
parameters are typed and mutually exclusive.
"""

from __future__ import annotations

import pytest

import varga
from varga import (
    BoundaryConvention,
    OddEvenStartParams,
    RelativeModalityParams,
    VargaConfig,
    VargaDefinition,
    compute_deterministic_id,
    load_config,
    validate,
)
from varga.config import DEFAULT_CONFIG_PATH
from varga.errors import InvalidVargaConfigError
from varga.models import VARGA_CATALOG_VERSION, VARGA_VERSION


def test_config_defaults() -> None:
    cfg = VargaConfig()
    assert cfg.catalog_version == "0.1.0"
    assert cfg.version == VARGA_VERSION
    assert cfg.default_boundary_convention == "HALF_OPEN_LOW"
    assert cfg.default_zodiac_mode == "SIDEREAL"
    assert cfg.default_ayanamsa == "LAHIRI"


def test_config_dict_round_trip() -> None:
    cfg = VargaConfig(default_zodiac_mode="TROPICAL")
    assert varga.varga_config_from_dict(cfg.to_dict()) == cfg


def test_config_invalid_values() -> None:
    with pytest.raises(InvalidVargaConfigError):
        VargaConfig(default_boundary_convention="OPEN_LOW")
    with pytest.raises(InvalidVargaConfigError):
        VargaConfig(default_zodiac_mode="BOGUS")
    with pytest.raises(InvalidVargaConfigError):
        VargaConfig(default_ayanamsa="")
    with pytest.raises(InvalidVargaConfigError):
        VargaConfig(catalog_version="")
    with pytest.raises(InvalidVargaConfigError):
        VargaConfig(version="")


def test_toml_defaults_match_dataclass() -> None:
    assert load_config() == VargaConfig()
    assert validate(load_config()) is not None


def test_toml_missing_field_is_error(tmp_path) -> None:
    assert DEFAULT_CONFIG_PATH.is_file(), "config/varga.toml must exist"
    raw = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
    stripped = raw.replace('default_boundary_convention = "HALF_OPEN_LOW"\n', "")
    path = tmp_path / "varga.toml"
    path.write_text(stripped, encoding="utf-8")
    with pytest.raises(InvalidVargaConfigError, match="default_boundary_convention"):
        load_config(path)


def test_missing_toml_is_error(tmp_path) -> None:
    with pytest.raises(InvalidVargaConfigError, match="missing authoritative"):
        load_config(tmp_path / "does-not-exist.toml")


def test_toml_invalid_value_is_error(tmp_path) -> None:
    raw = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
    bad = raw.replace('default_zodiac_mode = "SIDEREAL"', 'default_zodiac_mode = "NOPE"')
    path = tmp_path / "varga.toml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(InvalidVargaConfigError, match="zodiac_mode"):
        load_config(path)


def test_mapping_params_typed_and_validated() -> None:
    with pytest.raises(InvalidVargaConfigError):
        RelativeModalityParams(movable_offset=-1, fixed_offset=8, dual_offset=4)
    with pytest.raises(InvalidVargaConfigError):
        RelativeModalityParams(movable_offset=12, fixed_offset=8, dual_offset=4)
    with pytest.raises(InvalidVargaConfigError):
        OddEvenStartParams(odd_offset=0)  # even_offset missing
    with pytest.raises(InvalidVargaConfigError):
        OddEvenStartParams(even_offset=8)  # odd_offset missing
    with pytest.raises(InvalidVargaConfigError):
        # Absolute and relative forms are mutually exclusive.
        OddEvenStartParams(
            odd_offset=0,
            even_offset=8,
            odd_start=__import__("jyotish").RashiId.SIMHA,
            even_start=__import__("jyotish").RashiId.KARKA,
        )


def test_odd_even_absolute_requires_both_starts() -> None:
    with pytest.raises(InvalidVargaConfigError):
        OddEvenStartParams(odd_start=__import__("jyotish").RashiId.SIMHA)


def test_interval_entry_validation() -> None:
    from jyotish import RashiId
    from varga import IntervalEntry

    with pytest.raises(InvalidVargaConfigError):
        IntervalEntry(lower_deg=-1.0, upper_deg=5.0, destination=RashiId.MESHA)
    with pytest.raises(InvalidVargaConfigError):
        IntervalEntry(lower_deg=5.0, upper_deg=5.0, destination=RashiId.MESHA)
    with pytest.raises(InvalidVargaConfigError):
        IntervalEntry(lower_deg=0.0, upper_deg=31.0, destination=RashiId.MESHA)


def test_definition_validation() -> None:
    method = varga.get_varga_definition("D2").calculation_method

    def build(**overrides: object) -> VargaDefinition:
        fields = dict(
            varga_id="D2",
            canonical_name="HORA",
            division_number=2,
            calculation_method=method,
            zodiac_mode="SIDEREAL",
            ayanamsa=None,
            boundary_convention=BoundaryConvention.HALF_OPEN_LOW,
            tradition_profile=None,
            version="1",
            source_citations=(),
        )
        fields.update(overrides)
        return VargaDefinition(**fields)  # type: ignore[arg-type]

    with pytest.raises(InvalidVargaConfigError):
        build(varga_id="")
    with pytest.raises(InvalidVargaConfigError):
        build(division_number=0)
    with pytest.raises(InvalidVargaConfigError):
        build(zodiac_mode="")
    with pytest.raises(InvalidVargaConfigError):
        build(ayanamsa="")
    with pytest.raises(InvalidVargaConfigError):
        build(boundary_convention="OPEN_LOW")  # type: ignore[arg-type]
    with pytest.raises(InvalidVargaConfigError):
        build(version="")
    with pytest.raises(InvalidVargaConfigError):
        build(source_citations=())


def test_ayanamsa_is_opaque_string_echo() -> None:
    definition = varga.get_varga_definition("D9")
    assert definition.ayanamsa == "LAHIRI"
    assert isinstance(definition.ayanamsa, str)
    # The definition identity is a plain sha256 hex digest.
    assert len(varga.varga_definition_identity(definition)) == 64


def test_compute_deterministic_id_domain_separated() -> None:
    data = {"bodies": ["SUN", "MOON"], "lon": 5.0}
    a = compute_deterministic_id("jre008:position", data)
    assert compute_deterministic_id("jre008:position", data) == a
    assert compute_deterministic_id("jre008:chart", data) != a
    assert compute_deterministic_id("jre008:position", {"bodies": ["SUN"]}) != a
    assert len(a) == 64


def test_version_pinned() -> None:
    assert varga.__version__ == VARGA_VERSION == "0.1.0"
    assert VARGA_CATALOG_VERSION == "0.1.0"


def test_public_all_importable() -> None:
    for name in varga.__all__:
        assert hasattr(varga, name)
