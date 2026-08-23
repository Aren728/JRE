"""Western JRS configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .errors import InvalidWesternConfigError
from .models import WesternConfig, WesternOutcomeTaxonomy, WesternRule

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_id",
    "default_strength",
    "rules",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "western" / "basic_rules.toml"
)


def load_western_config(path: Path | None = None) -> WesternConfig:
    """Load and validate Western domain configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``WesternConfig`` instance.

    Raises:
        InvalidWesternConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidWesternConfigError(
            f"Western config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidWesternConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("western")
    if not isinstance(section, dict):
        raise InvalidWesternConfigError(
            "Missing top-level [western] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidWesternConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    source_id = section.get("source_id", "PTOLEMY")
    default_strength = section.get("default_strength", "MODERATE")

    return WesternConfig(
        version=str(version),
        source_id=str(source_id),
        default_strength=str(default_strength),
    )


def load_western_rules(path: Path | None = None) -> tuple[WesternRule, ...]:
    """Load Western rules from the TOML config.

    Args:
        path: Path to the TOML config file.

    Returns:
        A tuple of WesternRule objects.

    Raises:
        InvalidWesternConfigError: If the config or rules are invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidWesternConfigError(
            f"Western config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidWesternConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("western")
    if not isinstance(section, dict):
        raise InvalidWesternConfigError(
            "Missing top-level [western] section",
        )

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise InvalidWesternConfigError("rules must be a list")

    rules: list[WesternRule] = []
    for rule_data in rules_raw:
        rules.append(_parse_rule(rule_data))

    return tuple(rules)


def _parse_rule(data: dict[str, Any]) -> WesternRule:
    """Parse a single rule from TOML data."""
    rule_id = data.get("rule_id", "")
    if not rule_id:
        raise InvalidWesternConfigError("rule_id must not be empty")

    description = data.get("description", "")
    conditions = data.get("condition_facts", [])
    if not isinstance(conditions, list):
        raise InvalidWesternConfigError(
            f"rule {rule_id}: condition_facts must be a list",
        )

    outcome_str = data.get("outcome", "")
    try:
        outcome = WesternOutcomeTaxonomy(outcome_str)
    except ValueError as exc:
        raise InvalidWesternConfigError(
            f"rule {rule_id}: unknown outcome '{outcome_str}'",
        ) from exc

    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidWesternConfigError(
            f"rule {rule_id}: unknown direction '{direction_str}'",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidWesternConfigError(
            f"rule {rule_id}: unknown strength '{strength_str}'",
        ) from exc

    return WesternRule(
        rule_id=rule_id,
        description=description,
        condition_facts=tuple(conditions),
        outcome=outcome,
        direction=direction,
        strength=strength,
        source_id=data.get("source_id", "PTOLEMY"),
        location=data.get("location", ""),
    )
