"""Deterministic serialization for JRE-022 Synthesis.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import (
    ConditionType,
    SynthesisCategory,
    SynthesisConfig,
    SynthesisRule,
    to_dict_value,
)


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-022 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-022 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def _safe_str_list(raw: object) -> list[str]:
    """Extract a list of strings from an object, or return empty list."""
    if isinstance(raw, list):
        return [str(item) for item in raw if isinstance(item, str)]
    return []


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


def synthesis_config_from_dict(data: dict[str, Any]) -> SynthesisConfig:
    """Deserialize a ``SynthesisConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")

    strength_thresholds = _safe_float_dict(data.get("strength_thresholds"))

    raw_range: Any = data.get("score_range", {})
    if isinstance(raw_range, dict):
        score_min = _safe_float(raw_range.get("min_score", 0.0), 0.0)
        score_max = _safe_float(raw_range.get("max_score", 10.0), 10.0)
    else:
        score_min = 0.0
        score_max = 10.0
    score_range = (score_min, score_max)

    raw_rules: Any = data.get("rules", {})
    rules: dict[str, tuple[SynthesisRule, ...]] = {}
    if isinstance(raw_rules, dict):
        for cat_name, rule_list in raw_rules.items():
            if not isinstance(rule_list, list):
                continue
            parsed_rules: list[SynthesisRule] = []
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
                    category = SynthesisCategory(cat_name)
                except ValueError:
                    continue

                parsed_rules.append(SynthesisRule(
                    category=category,
                    condition_type=cond_type,
                    condition_params=params,
                    weight=weight,
                ))
            rules[str(cat_name)] = tuple(parsed_rules)

    return SynthesisConfig(
        version=str(version),
        strength_thresholds=strength_thresholds,
        score_range=score_range,
        rules=rules,
    )
