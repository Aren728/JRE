"""Loads ``config/muhurta.toml`` into a validated ``MuhurtaConfig``.

TOML authority: ``config/muhurta.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidMuhurtaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from jyotish import NakshatraId

from .errors import InvalidMuhurtaConfigError
from .models import (
    CategoryRule,
    Karana,
    MuhurtaConfig,
    Tithi,
    Var,
    Yoga,
)

DEFAULT_CONFIG_PATH: Path = Path("config/muhurta.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "inauspicious_tithis",
    "inauspicious_karanas",
    "inauspicious_yogas",
    "categories",
)


def _parse_tithi_list(raw: list[str], context: str) -> tuple[Tithi, ...]:
    """Parse a list of strings into Tithi enum values."""
    result: list[Tithi] = []
    for item in raw:
        try:
            result.append(Tithi(item))
        except ValueError as exc:
            raise InvalidMuhurtaConfigError(
                f"{context}: invalid tithi {item!r}"
            ) from exc
    return tuple(result)


def _parse_karana_list(raw: list[str], context: str) -> tuple[Karana, ...]:
    """Parse a list of strings into Karana enum values."""
    result: list[Karana] = []
    for item in raw:
        try:
            result.append(Karana(item))
        except ValueError as exc:
            raise InvalidMuhurtaConfigError(
                f"{context}: invalid karana {item!r}"
            ) from exc
    return tuple(result)


def _parse_yoga_list(raw: list[str], context: str) -> tuple[Yoga, ...]:
    """Parse a list of strings into Yoga enum values."""
    result: list[Yoga] = []
    for item in raw:
        try:
            result.append(Yoga(item))
        except ValueError as exc:
            raise InvalidMuhurtaConfigError(
                f"{context}: invalid yoga {item!r}"
            ) from exc
    return tuple(result)


def _parse_nakshatra_list(raw: list[str], context: str) -> tuple[NakshatraId, ...]:
    """Parse a list of strings into NakshatraId enum values."""
    result: list[NakshatraId] = []
    for item in raw:
        try:
            result.append(NakshatraId(item))
        except ValueError as exc:
            raise InvalidMuhurtaConfigError(
                f"{context}: invalid nakshatra {item!r}"
            ) from exc
    return tuple(result)


def _parse_var_list(raw: list[str], context: str) -> tuple[Var, ...]:
    """Parse a list of strings into Var enum values."""
    result: list[Var] = []
    for item in raw:
        try:
            result.append(Var(item))
        except ValueError as exc:
            raise InvalidMuhurtaConfigError(
                f"{context}: invalid vara {item!r}"
            ) from exc
    return tuple(result)


def _parse_category_rule(
    cat_name: str, raw: dict[str, object],
) -> CategoryRule:
    """Parse a single category rule from TOML data."""
    ctx = f"categories.{cat_name}"

    raw_nak = raw.get("required_nakshatras", [])
    required_nak = (
        _parse_nakshatra_list(list(raw_nak), ctx)
        if isinstance(raw_nak, list)
        else ()
    )

    raw_tithis = raw.get("avoided_tithis", [])
    avoided_tithis = (
        _parse_tithi_list(list(raw_tithis), ctx)
        if isinstance(raw_tithis, list)
        else ()
    )

    raw_karanas = raw.get("avoided_karanas", [])
    avoided_karanas = (
        _parse_karana_list(list(raw_karanas), ctx)
        if isinstance(raw_karanas, list)
        else ()
    )

    raw_yogas = raw.get("avoided_yogas", [])
    avoided_yogas = (
        _parse_yoga_list(list(raw_yogas), ctx)
        if isinstance(raw_yogas, list)
        else ()
    )

    raw_vars = raw.get("avoided_vars", [])
    avoided_vars = (
        _parse_var_list(list(raw_vars), ctx)
        if isinstance(raw_vars, list)
        else ()
    )

    raw_pref = raw.get("preferred_vars", [])
    preferred_vars = (
        _parse_var_list(list(raw_pref), ctx)
        if isinstance(raw_pref, list)
        else ()
    )

    weight_req_raw = raw.get("weight_required", 0.3)
    weight_avoid_raw = raw.get("weight_avoided", 0.5)
    weight_pref_raw = raw.get("weight_preferred", 0.2)
    weight_req = float(weight_req_raw) if isinstance(weight_req_raw, (int, float)) else 0.3
    weight_avoid = float(weight_avoid_raw) if isinstance(weight_avoid_raw, (int, float)) else 0.5
    weight_pref = float(weight_pref_raw) if isinstance(weight_pref_raw, (int, float)) else 0.2

    return CategoryRule(
        required_nakshatras=required_nak,
        avoided_tithis=avoided_tithis,
        avoided_karanas=avoided_karanas,
        avoided_yogas=avoided_yogas,
        avoided_vars=avoided_vars,
        preferred_vars=preferred_vars,
        weight_required=weight_req,
        weight_avoided=weight_avoid,
        weight_preferred=weight_pref,
    )


def load_config(path: str | Path | None = None) -> MuhurtaConfig:
    """Load and validate JRE-020 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidMuhurtaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/muhurta.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("muhurta", {})
    if not isinstance(section, dict):
        raise InvalidMuhurtaConfigError(
            f"[muhurta] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidMuhurtaConfigError(
            "config/muhurta.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    version = section.get("version", "0.1.0")
    if not isinstance(version, str) or version == "":
        raise InvalidMuhurtaConfigError(
            f"version must be a non-empty string, got {version!r}"
        )

    raw_tithis = section.get("inauspicious_tithis", [])
    inauspicious_tithis = (
        _parse_tithi_list(list(raw_tithis), "inauspicious_tithis")
        if isinstance(raw_tithis, list)
        else ()
    )

    raw_karanas = section.get("inauspicious_karanas", [])
    inauspicious_karanas = (
        _parse_karana_list(list(raw_karanas), "inauspicious_karanas")
        if isinstance(raw_karanas, list)
        else ()
    )

    raw_yogas = section.get("inauspicious_yogas", [])
    inauspicious_yogas = (
        _parse_yoga_list(list(raw_yogas), "inauspicious_yogas")
        if isinstance(raw_yogas, list)
        else ()
    )

    raw_categories = section.get("categories", {})
    category_rules: dict[str, CategoryRule] = {}
    if isinstance(raw_categories, dict):
        for cat_name, cat_raw in raw_categories.items():
            if isinstance(cat_raw, dict):
                category_rules[str(cat_name)] = _parse_category_rule(
                    str(cat_name), cat_raw,
                )

    return MuhurtaConfig(
        version=version,
        inauspicious_tithis=inauspicious_tithis,
        inauspicious_karanas=inauspicious_karanas,
        inauspicious_yogas=inauspicious_yogas,
        category_rules=category_rules,
    )
