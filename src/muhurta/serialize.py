"""Deterministic serialization for JRE-020 Muhurta.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from jyotish import NakshatraId

from .models import (
    CategoryRule,
    Karana,
    MuhurtaConfig,
    Tithi,
    Var,
    Yoga,
    to_dict_value,
)


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-020 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-020 result to JSON (exact float round-trip)."""
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


def muhurta_config_from_dict(data: dict[str, Any]) -> MuhurtaConfig:
    """Deserialize a ``MuhurtaConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")

    inauspicious_tithis = tuple(
        Tithi(t) for t in _safe_str_list(data.get("inauspicious_tithis"))
    )

    inauspicious_karanas = tuple(
        Karana(k) for k in _safe_str_list(data.get("inauspicious_karanas"))
    )

    inauspicious_yogas = tuple(
        Yoga(y) for y in _safe_str_list(data.get("inauspicious_yogas"))
    )

    raw_cats: Any = data.get("category_rules", {})
    category_rules: dict[str, CategoryRule] = {}
    if isinstance(raw_cats, dict):
        for cat_name, cat_data in raw_cats.items():
            if isinstance(cat_data, dict):
                cat_dict: dict[str, Any] = cat_data
                category_rules[str(cat_name)] = CategoryRule(
                    required_nakshatras=tuple(
                        NakshatraId(n) for n in _safe_str_list(
                            cat_dict.get("required_nakshatras")
                        )
                    ),
                    avoided_tithis=tuple(
                        Tithi(t) for t in _safe_str_list(
                            cat_dict.get("avoided_tithis")
                        )
                    ),
                    avoided_karanas=tuple(
                        Karana(k) for k in _safe_str_list(
                            cat_dict.get("avoided_karanas")
                        )
                    ),
                    avoided_yogas=tuple(
                        Yoga(y) for y in _safe_str_list(
                            cat_dict.get("avoided_yogas")
                        )
                    ),
                    avoided_vars=tuple(
                        Var(v) for v in _safe_str_list(
                            cat_dict.get("avoided_vars")
                        )
                    ),
                    preferred_vars=tuple(
                        Var(v) for v in _safe_str_list(
                            cat_dict.get("preferred_vars")
                        )
                    ),
                    weight_required=_safe_float(
                        cat_dict.get("weight_required"), 0.3
                    ),
                    weight_avoided=_safe_float(
                        cat_dict.get("weight_avoided"), 0.5
                    ),
                    weight_preferred=_safe_float(
                        cat_dict.get("weight_preferred"), 0.2
                    ),
                )

    return MuhurtaConfig(
        version=str(version),
        inauspicious_tithis=inauspicious_tithis,
        inauspicious_karanas=inauspicious_karanas,
        inauspicious_yogas=inauspicious_yogas,
        category_rules=category_rules,
    )
