"""Loads ``config/rectification.toml`` into a validated ``RectificationConfig``.

TOML authority: ``config/rectification.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidRectificationConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidRectificationConfigError
from .models import RectificationConfig

DEFAULT_CONFIG_PATH: Path = Path("config/rectification.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "max_offset_seconds",
    "method_weights",
    "method_tolerances",
    "evidence_weights",
)


def _safe_float(raw: object, default: float) -> float:
    """Extract a float from an object, or return default."""
    if isinstance(raw, (int, float)):
        return float(raw)
    return default


def _safe_float_dict(raw: object) -> dict[str, float]:
    """Extract a dict[str, float] from an object, or return empty dict."""
    result: dict[str, float] = {}
    if isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(key, str) and isinstance(val, (int, float)):
                result[key] = float(val)
    return result


def load_config(path: str | Path | None = None) -> RectificationConfig:
    """Load and validate JRE-021 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidRectificationConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/rectification.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("rectification", {})
    if not isinstance(section, dict):
        raise InvalidRectificationConfigError(
            f"[rectification] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidRectificationConfigError(
            "config/rectification.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    version = section.get("version", "0.1.0")
    if not isinstance(version, str) or version == "":
        raise InvalidRectificationConfigError(
            f"version must be a non-empty string, got {version!r}"
        )

    max_offset_raw = section.get("max_offset_seconds", 86400.0)
    max_offset = _safe_float(max_offset_raw, 86400.0)
    if max_offset <= 0:
        raise InvalidRectificationConfigError(
            f"max_offset_seconds must be positive, got {max_offset!r}"
        )

    method_weights = _safe_float_dict(section.get("method_weights"))
    method_tolerances = _safe_float_dict(section.get("method_tolerances"))
    evidence_weights = _safe_float_dict(section.get("evidence_weights"))

    return RectificationConfig(
        version=version,
        max_offset_seconds=max_offset,
        method_weights=method_weights,
        method_tolerances=method_tolerances,
        evidence_weights=evidence_weights,
    )
