"""Validation system configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidValidationConfigError
from .models import ValidationConfig

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "match_threshold",
    "trigger_weights",
    "source_reliability",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "validation.toml"
)


def load_validation_config(path: Path | None = None) -> ValidationConfig:
    """Load and validate validation configuration from a TOML file.

    Args:
        path: Path to the TOML config file. Defaults to ``config/validation.toml``.

    Returns:
        A validated ``ValidationConfig`` instance.

    Raises:
        InvalidValidationConfigError: If the config file is missing, malformed,
            or contains undeclared fields.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidValidationConfigError(
            f"Validation config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidValidationConfigError(f"Invalid TOML: {exc}") from exc

    val_section = raw.get("validation")
    if not isinstance(val_section, dict):
        raise InvalidValidationConfigError(
            "Missing top-level [validation] section",
        )

    # Validate declared fields
    unknown = set(val_section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidValidationConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = val_section.get("version", "1.0")
    if not isinstance(version, str):
        raise InvalidValidationConfigError("version must be a string")

    match_threshold = val_section.get("match_threshold", 0.5)
    if not isinstance(match_threshold, (int, float)):
        raise InvalidValidationConfigError("match_threshold must be a number")

    # Parse trigger weights
    tw_raw = val_section.get("trigger_weights", {})
    if not isinstance(tw_raw, dict):
        raise InvalidValidationConfigError("trigger_weights must be a dict")
    trigger_weights: dict[str, float] = {}
    for key, val in tw_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidValidationConfigError(
                f"trigger_weights.{key} must be a number",
            )
        trigger_weights[key] = float(val)

    # Parse source reliability
    sr_raw = val_section.get("source_reliability", {})
    if not isinstance(sr_raw, dict):
        raise InvalidValidationConfigError("source_reliability must be a dict")
    source_reliability: dict[str, float] = {}
    for key, val in sr_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidValidationConfigError(
                f"source_reliability.{key} must be a number",
            )
        source_reliability[key] = float(val)

    return ValidationConfig(
        version=version,
        match_threshold=float(match_threshold),
        trigger_weights=trigger_weights,
        source_reliability=source_reliability,
    )
