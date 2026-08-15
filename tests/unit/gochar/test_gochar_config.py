"""Config tests (TEST-PLAN §2 row 3, SPEC §5/§22, DC §2).

TOML authority: ``config/gochar.toml`` declares every default; a config
missing any declared field is a load error; a missing file yields the
validated dataclass defaults. ``GocharConfig`` is immutable and validated
at construction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gochar
from gochar import GocharConfig, InvalidGocharConfigError, load_config

TOML_PATH = Path("config/gochar.toml")


def test_toml_declares_every_default() -> None:
    """SPEC §5/§22 — no hidden defaults: the TOML declares all six fields."""
    assert TOML_PATH.is_file(), f"missing {TOML_PATH}"
    text = TOML_PATH.read_text(encoding="utf-8")
    # Compare against the declared key set only (comments may name fields).
    keys = {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    }
    for field in (
        "reference_point",
        "house_system",
        "sample_step_hours",
        "aspect_echo",
        "natal_house_series",
        "version",
    ):
        assert field in keys, f"TOML missing declared field {field!r}"
    # tradition_profile is intentionally omitted (TOML has no null).
    assert "tradition_profile" not in keys


def test_load_config_echoes_toml() -> None:
    cfg = load_config()
    assert cfg.reference_point == "LAGNA"
    assert cfg.house_system == "WHOLE_SIGN"
    assert cfg.sample_step_hours == 24.0
    assert cfg.aspect_echo is True
    assert cfg.natal_house_series is False
    assert cfg.tradition_profile is None
    assert cfg.version == "0.2.0"


def test_load_config_missing_field_is_load_error(tmp_path) -> None:
    """SPEC §5 — a config missing any declared field is a load error."""
    from gochar.config import load_config as load_from

    path = tmp_path / "gochar.toml"
    path.write_text(
        "[gochar]\n"
        'reference_point = "LAGNA"\n'
        'house_system = "WHOLE_SIGN"\n'
        "sample_step_hours = 24.0\n"
        "aspect_echo = true\n"
        # natal_house_series deliberately omitted
        'version = "0.2.0"\n',
        encoding="utf-8",
    )
    with pytest.raises(InvalidGocharConfigError, match="natal_house_series"):
        load_from(path)


def test_missing_file_yields_dataclass_defaults(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg == GocharConfig()
    assert gochar.validate(cfg) is cfg


def test_config_immutable() -> None:
    cfg = GocharConfig()
    with pytest.raises(AttributeError):
        cfg.reference_point = "MOON"  # type: ignore[misc]


def test_config_validation_rejects_unknown_reference() -> None:
    with pytest.raises(InvalidGocharConfigError, match="reference_point"):
        GocharConfig(reference_point="MIDHEAVEN")


def test_config_validation_rejects_unknown_house_system() -> None:
    with pytest.raises(InvalidGocharConfigError, match="house_system"):
        GocharConfig(house_system="BOGUS")


def test_config_validation_sample_step_bounds() -> None:
    for bad in (0.0, -1.0, 720.0001, 100000.0):
        with pytest.raises(InvalidGocharConfigError, match="sample_step_hours"):
            GocharConfig(sample_step_hours=bad)


def test_config_validation_rejects_bad_flags() -> None:
    with pytest.raises(InvalidGocharConfigError, match="aspect_echo"):
        GocharConfig(aspect_echo="yes")  # type: ignore[arg-type]
    with pytest.raises(InvalidGocharConfigError, match="natal_house_series"):
        GocharConfig(natal_house_series=1)  # type: ignore[arg-type]


def test_config_validation_rejects_empty_tradition_profile() -> None:
    with pytest.raises(InvalidGocharConfigError, match="tradition_profile"):
        GocharConfig(tradition_profile="")


def test_config_from_dict_partial_overrides() -> None:
    """DC §2/§7 — missing keys keep defaults; overrides win."""
    cfg = gochar.config_from_dict({"reference_point": "MOON"})
    assert cfg.reference_point == "MOON"
    assert cfg.house_system == "WHOLE_SIGN"
    assert cfg.aspect_echo is True
    assert gochar.config_from_dict({}) == GocharConfig()


def test_config_from_dict_unknown_enum() -> None:
    with pytest.raises(InvalidGocharConfigError):
        gochar.config_from_dict({"house_system": "NOPE"})
    with pytest.raises(InvalidGocharConfigError):
        gochar.config_from_dict({"reference_point": "NOPE"})


def test_config_to_dict_round_trip() -> None:
    cfg = GocharConfig(reference_point="SUN", sample_step_hours=12.0)
    assert gochar.config_from_dict(cfg.to_dict()) == cfg
