"""Convergence engine configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidConvergenceConfigError
from .models import ConvergenceConfig

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_weights",
    "strength_weights",
    "independence_penalty",
    "strongly_supported_min_independent",
    "strongly_supported_min_supporting",
    "supported_min_independent",
    "supported_min_supporting",
    "weakly_supported_min_supporting",
    "strongly_contradicted_min_contradicting",
    "contradicted_min_contradicting",
    "convergent_min_windows",
    "high_confidence_min_weight",
    "low_confidence_max_weight",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "config" / "convergence.toml"
)


def load_convergence_config(path: Path | None = None) -> ConvergenceConfig:
    """Load and validate convergence configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``ConvergenceConfig`` instance.

    Raises:
        InvalidConvergenceConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidConvergenceConfigError(
            f"Convergence config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidConvergenceConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("convergence")
    if not isinstance(section, dict):
        raise InvalidConvergenceConfigError(
            "Missing top-level [convergence] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidConvergenceConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    independence_penalty = float(section.get("independence_penalty", 0.5))
    strongly_supported_min_independent = int(
        section.get("strongly_supported_min_independent", 3),
    )
    strongly_supported_min_supporting = int(
        section.get("strongly_supported_min_supporting", 4),
    )
    supported_min_independent = int(
        section.get("supported_min_independent", 2),
    )
    supported_min_supporting = int(
        section.get("supported_min_supporting", 2),
    )
    weakly_supported_min_supporting = int(
        section.get("weakly_supported_min_supporting", 1),
    )
    strongly_contradicted_min_contradicting = int(
        section.get("strongly_contradicted_min_contradicting", 3),
    )
    contradicted_min_contradicting = int(
        section.get("contradicted_min_contradicting", 2),
    )
    convergent_min_windows = int(section.get("convergent_min_windows", 1))
    high_confidence_min_weight = float(
        section.get("high_confidence_min_weight", 0.8),
    )
    low_confidence_max_weight = float(
        section.get("low_confidence_max_weight", 0.4),
    )

    # Parse source weights
    sw_raw = section.get("source_weights", {})
    if not isinstance(sw_raw, dict):
        raise InvalidConvergenceConfigError("source_weights must be a dict")
    source_weights: dict[str, float] = {}
    for key, val in sw_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidConvergenceConfigError(
                f"source_weights.{key} must be a number",
            )
        source_weights[key] = float(val)

    # Parse strength weights
    stw_raw = section.get("strength_weights", {})
    if not isinstance(stw_raw, dict):
        raise InvalidConvergenceConfigError("strength_weights must be a dict")
    strength_weights: dict[str, float] = {}
    for key, val in stw_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidConvergenceConfigError(
                f"strength_weights.{key} must be a number",
            )
        strength_weights[key] = float(val)

    return ConvergenceConfig(
        version=str(version),
        source_weights=source_weights,
        strength_weights=strength_weights,
        independence_penalty=independence_penalty,
        strongly_supported_min_independent=strongly_supported_min_independent,
        strongly_supported_min_supporting=strongly_supported_min_supporting,
        supported_min_independent=supported_min_independent,
        supported_min_supporting=supported_min_supporting,
        weakly_supported_min_supporting=weakly_supported_min_supporting,
        strongly_contradicted_min_contradicting=strongly_contradicted_min_contradicting,
        contradicted_min_contradicting=contradicted_min_contradicting,
        convergent_min_windows=convergent_min_windows,
        high_confidence_min_weight=high_confidence_min_weight,
        low_confidence_max_weight=low_confidence_max_weight,
    )
