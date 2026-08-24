"""JRS Numerology — Configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .errors import InvalidNumerologyConfigError
from .models import (
    NumerologyConfig,
    NumerologyOutcomeTaxonomy,
    NumerologyRule,
)

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_id",
    "default_strength",
    "rules",
})

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "config" / "numerology"
)

_DEFAULT_CONFIG_PATH: Path = _CONFIG_DIR / "rules.toml"


def load_numerology_config(path: Path | None = None) -> NumerologyConfig:
    """Load and validate Numerology domain configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``NumerologyConfig`` instance.

    Raises:
        InvalidNumerologyConfigError: If the config is invalid.
    """
    config_path = path or _DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise InvalidNumerologyConfigError(
            f"Numerology config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidNumerologyConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("numerology")
    if not isinstance(section, dict):
        raise InvalidNumerologyConfigError(
            "Missing top-level [numerology] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidNumerologyConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    source_id = section.get("source_id", "PYTHAGOREAN")
    default_strength = section.get("default_strength", "MODERATE")

    return NumerologyConfig(
        version=str(version),
        source_id=str(source_id),
        default_strength=str(default_strength),
    )


def load_numerology_rules(
    path: Path | None = None,
) -> tuple[NumerologyRule, ...]:
    """Load Numerology rules from the TOML config.

    Args:
        path: Path to the TOML config file.

    Returns:
        A tuple of NumerologyRule objects.

    Raises:
        InvalidNumerologyConfigError: If the config or rules are invalid.
    """
    config_path = path or _DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise InvalidNumerologyConfigError(
            f"Numerology config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidNumerologyConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("numerology")
    if not isinstance(section, dict):
        raise InvalidNumerologyConfigError(
            "Missing top-level [numerology] section",
        )

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise InvalidNumerologyConfigError("rules must be a list")

    rules: list[NumerologyRule] = []
    for rule_data in rules_raw:
        rules.append(_parse_rule(rule_data))

    return tuple(rules)


def _parse_rule(data: dict[str, Any]) -> NumerologyRule:
    """Parse a single rule from TOML data."""
    rule_id = data.get("rule_id", "")
    if not rule_id:
        raise InvalidNumerologyConfigError("rule_id must not be empty")

    description = data.get("description", "")
    conditions = data.get("condition_facts", [])
    if not isinstance(conditions, list):
        raise InvalidNumerologyConfigError(
            f"rule {rule_id}: condition_facts must be a list",
        )

    outcome_str = data.get("outcome", "")
    try:
        outcome = NumerologyOutcomeTaxonomy(outcome_str)
    except ValueError as exc:
        raise InvalidNumerologyConfigError(
            f"rule {rule_id}: unknown outcome '{outcome_str}'",
        ) from exc

    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidNumerologyConfigError(
            f"rule {rule_id}: unknown direction '{direction_str}'",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidNumerologyConfigError(
            f"rule {rule_id}: unknown strength '{strength_str}'",
        ) from exc

    return NumerologyRule(
        rule_id=rule_id,
        description=description,
        condition_facts=tuple(conditions),
        outcome=outcome,
        direction=direction,
        strength=strength,
        source_id=data.get("source_id", "PYTHAGOREAN"),
        location=data.get("location", ""),
    )
