"""Evidence framework configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidEvidenceConfigError
from .models import EvidenceConfig

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_weights",
    "strength_multipliers",
    "max_chain_depth",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "config" / "evidence.toml"
)


def load_evidence_config(path: Path | None = None) -> EvidenceConfig:
    """Load and validate evidence configuration from a TOML file.

    Args:
        path: Path to the TOML config file. Defaults to ``config/evidence.toml``.

    Returns:
        A validated ``EvidenceConfig`` instance.

    Raises:
        InvalidEvidenceConfigError: If the config file is missing, malformed,
            or contains undeclared fields.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidEvidenceConfigError(
            f"Evidence config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidEvidenceConfigError(f"Invalid TOML: {exc}") from exc

    ev_section = raw.get("evidence")
    if not isinstance(ev_section, dict):
        raise InvalidEvidenceConfigError(
            "Missing top-level [evidence] section",
        )

    # Validate declared fields
    unknown = set(ev_section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidEvidenceConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = ev_section.get("version", "1.0")
    if not isinstance(version, str):
        raise InvalidEvidenceConfigError("version must be a string")

    max_depth = ev_section.get("max_chain_depth", 10)
    if not isinstance(max_depth, int):
        raise InvalidEvidenceConfigError("max_chain_depth must be an int")

    # Parse source weights
    sw_raw = ev_section.get("source_weights", {})
    if not isinstance(sw_raw, dict):
        raise InvalidEvidenceConfigError("source_weights must be a dict")
    source_weights: dict[str, float] = {}
    for key, val in sw_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidEvidenceConfigError(
                f"source_weights.{key} must be a number",
            )
        source_weights[key] = float(val)

    # Parse strength multipliers
    sm_raw = ev_section.get("strength_multipliers", {})
    if not isinstance(sm_raw, dict):
        raise InvalidEvidenceConfigError("strength_multipliers must be a dict")
    strength_multipliers: dict[str, float] = {}
    for key, val in sm_raw.items():
        if not isinstance(val, (int, float)):
            raise InvalidEvidenceConfigError(
                f"strength_multipliers.{key} must be a number",
            )
        strength_multipliers[key] = float(val)

    return EvidenceConfig(
        version=version,
        source_weights=source_weights,
        strength_multipliers=strength_multipliers,
        max_chain_depth=max_depth,
    )
