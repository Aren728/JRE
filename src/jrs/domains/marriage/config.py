"""Marriage domain configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .errors import InvalidMarriageConfigError
from .models import MarriageConfig, MarriageOutcomeTaxonomy, MarriageRule

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_id",
    "default_strength",
    "rules",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "domains" / "marriage.toml"
)


def load_marriage_config(path: Path | None = None) -> MarriageConfig:
    """Load and validate marriage domain configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``MarriageConfig`` instance.

    Raises:
        InvalidMarriageConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidMarriageConfigError(
            f"Marriage config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidMarriageConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("marriage")
    if not isinstance(section, dict):
        raise InvalidMarriageConfigError(
            "Missing top-level [marriage] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidMarriageConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    source_id = section.get("source_id", "BPHS")
    default_strength = section.get("default_strength", "MODERATE")

    return MarriageConfig(
        version=str(version),
        source_id=str(source_id),
        default_strength=str(default_strength),
    )


def load_marriage_rules(path: Path | None = None) -> tuple[MarriageRule, ...]:
    """Load marriage rules from the TOML config.

    Args:
        path: Path to the TOML config file.

    Returns:
        A tuple of MarriageRule objects.

    Raises:
        InvalidMarriageConfigError: If the config or rules are invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidMarriageConfigError(
            f"Marriage config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidMarriageConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("marriage")
    if not isinstance(section, dict):
        raise InvalidMarriageConfigError(
            "Missing top-level [marriage] section",
        )

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise InvalidMarriageConfigError("rules must be a list")

    rules: list[MarriageRule] = []
    for rule_data in rules_raw:
        rules.append(_parse_rule(rule_data))

    return tuple(rules)


def _parse_rule(data: dict[str, Any]) -> MarriageRule:
    """Parse a single rule from TOML data."""
    rule_id = data.get("rule_id", "")
    if not rule_id:
        raise InvalidMarriageConfigError("rule_id must not be empty")

    description = data.get("description", "")
    conditions = data.get("condition_facts", [])
    if not isinstance(conditions, list):
        raise InvalidMarriageConfigError(
            f"rule {rule_id}: condition_facts must be a list",
        )

    outcome_str = data.get("outcome", "")
    try:
        outcome = MarriageOutcomeTaxonomy(outcome_str)
    except ValueError as exc:
        raise InvalidMarriageConfigError(
            f"rule {rule_id}: unknown outcome '{outcome_str}'",
        ) from exc

    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidMarriageConfigError(
            f"rule {rule_id}: unknown direction '{direction_str}'",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidMarriageConfigError(
            f"rule {rule_id}: unknown strength '{strength_str}'",
        ) from exc

    return MarriageRule(
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
