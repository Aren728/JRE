"""Property domain configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .errors import InvalidPropertyConfigError
from .models import PropertyConfig, PropertyOutcomeTaxonomy, PropertyRule

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_id",
    "default_strength",
    "rules",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "domains" / "property.toml"
)


def load_property_config(path: Path | None = None) -> PropertyConfig:
    """Load and validate property domain configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``PropertyConfig`` instance.

    Raises:
        InvalidPropertyConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidPropertyConfigError(
            f"Property config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidPropertyConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("property")
    if not isinstance(section, dict):
        raise InvalidPropertyConfigError(
            "Missing top-level [property] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidPropertyConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    source_id = section.get("source_id", "BPHS")
    default_strength = section.get("default_strength", "MODERATE")

    return PropertyConfig(
        version=str(version),
        source_id=str(source_id),
        default_strength=str(default_strength),
    )


def load_property_rules(path: Path | None = None) -> tuple[PropertyRule, ...]:
    """Load property rules from the TOML config.

    Args:
        path: Path to the TOML config file.

    Returns:
        A tuple of PropertyRule objects.

    Raises:
        InvalidPropertyConfigError: If the config or rules are invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidPropertyConfigError(
            f"Property config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidPropertyConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("property")
    if not isinstance(section, dict):
        raise InvalidPropertyConfigError(
            "Missing top-level [property] section",
        )

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise InvalidPropertyConfigError("rules must be a list")

    rules: list[PropertyRule] = []
    for rule_data in rules_raw:
        rules.append(_parse_rule(rule_data))

    return tuple(rules)


def _parse_rule(data: dict[str, Any]) -> PropertyRule:
    """Parse a single rule from TOML data."""
    rule_id = data.get("rule_id", "")
    if not rule_id:
        raise InvalidPropertyConfigError("rule_id must not be empty")

    description = data.get("description", "")
    conditions = data.get("condition_facts", [])
    if not isinstance(conditions, list):
        raise InvalidPropertyConfigError(
            f"rule {rule_id}: condition_facts must be a list",
        )

    outcome_str = data.get("outcome", "")
    try:
        outcome = PropertyOutcomeTaxonomy(outcome_str)
    except ValueError as exc:
        raise InvalidPropertyConfigError(
            f"rule {rule_id}: unknown outcome '{outcome_str}'",
        ) from exc

    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidPropertyConfigError(
            f"rule {rule_id}: unknown direction '{direction_str}'",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidPropertyConfigError(
            f"rule {rule_id}: unknown strength '{strength_str}'",
        ) from exc

    return PropertyRule(
        rule_id=rule_id,
        description=description,
        condition_facts=tuple(conditions),
        outcome=outcome,
        direction=direction,
        strength=strength,
        source_id=data.get("source_id", "BPHS"),
        location=data.get("location", ""),
        timing_relevance=data.get("timing_relevance", ""),
    )
