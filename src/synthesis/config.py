"""Loads ``config/synthesis.toml`` into a validated ``SynthesisConfig``.

TOML authority: ``config/synthesis.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidSynthesisConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidSynthesisConfigError
from .models import (
    ConditionType,
    SynthesisConfig,
    SynthesisRule,
)

DEFAULT_CONFIG_PATH: Path = Path("config/synthesis.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "strength_thresholds",
    "score_range",
    "rules",
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


def _parse_rules(
    raw_rules: dict[str, list[dict[str, object]]],
) -> dict[str, tuple[SynthesisRule, ...]]:
    """Parse TOML rule sections into structured rules."""
    parsed: dict[str, list[SynthesisRule]] = {}
    for cat_name, rule_list in raw_rules.items():
        if not isinstance(rule_list, list):
            continue
        for raw_rule in rule_list:
            if not isinstance(raw_rule, dict):
                continue
            cond_type_str = str(raw_rule.get("condition_type", ""))
            try:
                cond_type = ConditionType(cond_type_str)
            except ValueError:
                continue

            raw_params = raw_rule.get("condition_params", {})
            params: dict[str, Any] = {}
            if isinstance(raw_params, dict):
                for k, v in raw_params.items():
                    if isinstance(k, str):
                        params[k] = v

            weight = _safe_float(raw_rule.get("weight"), 1.0)

            try:
                from .models import SynthesisCategory
                category = SynthesisCategory(cat_name)
            except ValueError:
                continue

            rule = SynthesisRule(
                category=category,
                condition_type=cond_type,
                condition_params=params,
                weight=weight,
            )
            parsed.setdefault(cat_name, []).append(rule)

    return {k: tuple(v) for k, v in parsed.items()}


def load_config(path: str | Path | None = None) -> SynthesisConfig:
    """Load and validate JRE-022 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidSynthesisConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/synthesis.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("synthesis", {})
    if not isinstance(section, dict):
        raise InvalidSynthesisConfigError(
            f"[synthesis] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidSynthesisConfigError(
            "config/synthesis.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    version = section.get("version", "0.1.0")
    if not isinstance(version, str) or version == "":
        raise InvalidSynthesisConfigError(
            f"version must be a non-empty string, got {version!r}"
        )

    raw_thresholds = section.get("strength_thresholds", {})
    strength_thresholds = _safe_float_dict(raw_thresholds)

    raw_range = section.get("score_range", {})
    if isinstance(raw_range, dict):
        score_min = _safe_float(raw_range.get("min_score", 0.0), 0.0)
        score_max = _safe_float(raw_range.get("max_score", 10.0), 10.0)
    else:
        score_min = 0.0
        score_max = 10.0
    score_range = (score_min, score_max)

    raw_rules = section.get("rules", {})
    rules: dict[str, tuple[SynthesisRule, ...]] = {}
    if isinstance(raw_rules, dict):
        rules = _parse_rules(raw_rules)

    return SynthesisConfig(
        version=version,
        strength_thresholds=strength_thresholds,
        score_range=score_range,
        rules=rules,
    )
