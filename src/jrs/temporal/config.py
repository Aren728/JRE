"""Temporal evidence configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidTemporalConfigError
from .models import TemporalConfig

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "convergence_rules",
    "min_triggers_for_high",
    "min_triggers_for_moderate",
    "activation_type_weights",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "config" / "temporal.toml"
)


def load_temporal_config(path: Path | None = None) -> TemporalConfig:
    """Load and validate temporal evidence configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``TemporalConfig`` instance.

    Raises:
        InvalidTemporalConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidTemporalConfigError(
            f"Temporal config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidTemporalConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("temporal")
    if not isinstance(section, dict):
        raise InvalidTemporalConfigError(
            "Missing top-level [temporal] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidTemporalConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    min_high = section.get("min_triggers_for_high", 3)
    min_moderate = section.get("min_triggers_for_moderate", 2)

    # Parse convergence rules
    cr_raw = section.get("convergence_rules", {})
    if not isinstance(cr_raw, dict):
        raise InvalidTemporalConfigError("convergence_rules must be a dict")
    convergence_rules: dict[str, float] = {}
    for key, val in cr_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidTemporalConfigError(
                f"convergence_rules.{key} must be a number",
            )
        convergence_rules[key] = float(val)

    # Parse activation type weights
    atw_raw = section.get("activation_type_weights", {})
    if not isinstance(atw_raw, dict):
        raise InvalidTemporalConfigError("activation_type_weights must be a dict")
    activation_type_weights: dict[str, float] = {}
    for key, val in atw_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidTemporalConfigError(
                f"activation_type_weights.{key} must be a number",
            )
        activation_type_weights[key] = float(val)

    return TemporalConfig(
        version=str(version),
        convergence_rules=convergence_rules,
        min_triggers_for_high=int(min_high),
        min_triggers_for_moderate=int(min_moderate),
        activation_type_weights=activation_type_weights,
    )
