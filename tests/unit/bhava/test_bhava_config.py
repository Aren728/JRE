"""Config authority tests (TEST-PLAN §20, SPEC §28)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bhava import BhavaConfig, load_config
from bhava.errors import InvalidBhavaConfigError

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_toml_authority_declares_all_defaults() -> None:
    """config/bhava.toml must declare every default (no hidden defaults)."""
    path = REPO_ROOT / "config" / "bhava.toml"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for key in (
        "cusp_proximity_orb_deg",
        "house_systems",
        "include_empty_houses",
        "unplaced_body_behavior",
        "anchor_frame",
        "derivation_version",
    ):
        assert key in text, f"config/bhava.toml must declare {key}"


def test_load_config_matches_defaults() -> None:
    assert load_config() == BhavaConfig()


def test_load_config_missing_file_uses_defaults(tmp_path: Path) -> None:
    assert load_config(tmp_path / "absent.toml") == BhavaConfig()


def test_load_config_custom_toml(tmp_path: Path) -> None:
    toml = tmp_path / "bhava.toml"
    toml.write_text(
        "[bhava]\n"
        "cusp_proximity_orb_deg = 4.5\n"
        'house_systems = ["PLACIDUS"]\n'
        'unplaced_body_behavior = "WHOLE_SIGN_FALLBACK"\n',
        encoding="utf-8",
    )
    cfg = load_config(toml)
    assert cfg.cusp_proximity_orb_deg == 4.5
    assert cfg.house_systems[0].value == "PLACIDUS"
    assert cfg.unplaced_body_behavior.value == "WHOLE_SIGN_FALLBACK"


def test_unknown_enum_in_toml_rejected(tmp_path: Path) -> None:
    toml = tmp_path / "bhava.toml"
    toml.write_text('[bhava]\nanchor_frame = "SIGN_GRID"\n', encoding="utf-8")
    with pytest.raises(InvalidBhavaConfigError):
        load_config(toml)


def test_orb_validation() -> None:
    from bhava import validate

    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=0.0))
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=-1.0))
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=30.0))
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"cusp_proximity_orb_deg": 31.0})
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=30.0))
    assert validate(BhavaConfig(cusp_proximity_orb_deg=29.999)).cusp_proximity_orb_deg == 29.999


def test_house_system_set_validation() -> None:
    from bhava import validate

    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(house_systems=()))
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(house_systems=("WHOLE_SIGN", "WHOLE_SIGN")))
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"house_systems": []})
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"house_systems": ["WHOLE_SIGN", "WHOLE_SIGN"]})


def test_tradition_profile_validation() -> None:
    from bhava import validate

    assert validate(BhavaConfig(tradition_profile=None)).tradition_profile is None
    assert validate(BhavaConfig(tradition_profile="parashari")).tradition_profile == "parashari"
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(tradition_profile=""))
    with pytest.raises(InvalidBhavaConfigError):
        BhavaConfig.from_dict({"tradition_profile": ""})
