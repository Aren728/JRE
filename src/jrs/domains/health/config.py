"""Health domain configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .errors import InvalidHealthConfigError
from .models import HealthConfig, HealthOutcomeTaxonomy, HealthRule, _validate_no_medical_terms

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "source_id",
    "default_strength",
    "rules",
})

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config" / "domains" / "health.toml"
)


def load_health_config(path: Path | None = None) -> HealthConfig:
    """Load and validate health domain configuration from a TOML file.

    Args:
        path: Path to the TOML config file.

    Returns:
        A validated ``HealthConfig`` instance.

    Raises:
        InvalidHealthConfigError: If the config is invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidHealthConfigError(
            f"Health config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidHealthConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("business")
    if not isinstance(section, dict):
        raise InvalidHealthConfigError(
            "Missing top-level [business] section",
        )

    unknown = set(section.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidHealthConfigError(
            f"Unknown config fields: {sorted(unknown)}",
        )

    version = section.get("version", "1.0")
    source_id = section.get("source_id", "BPHS")
    default_strength = section.get("default_strength", "MODERATE")

    return HealthConfig(
        version=str(version),
        source_id=str(source_id),
        default_strength=str(default_strength),
    )


def load_health_rules(path: Path | None = None) -> tuple[HealthRule, ...]:
    """Load health rules from the TOML config.

    Args:
        path: Path to the TOML config file.

    Returns:
        A tuple of HealthRule objects.

    Raises:
        InvalidHealthConfigError: If the config or rules are invalid.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidHealthConfigError(
            f"Health config not found: {config_path}",
        )

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidHealthConfigError(f"Invalid TOML: {exc}") from exc

    section = raw.get("business")
    if not isinstance(section, dict):
        raise InvalidHealthConfigError(
            "Missing top-level [business] section",
        )

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise InvalidHealthConfigError("rules must be a list")

    rules: list[HealthRule] = []
    for rule_data in rules_raw:
        rules.append(_parse_rule(rule_data))

    return tuple(rules)


def _parse_rule(data: dict[str, Any]) -> HealthRule:
    """Parse a single rule from TOML data."""
    rule_id = data.get("rule_id", "")
    if not rule_id:
        raise InvalidHealthConfigError("rule_id must not be empty")

    description = data.get("description", "")

    # SAFETY: Validate no medical terms in description
    try:
        _validate_no_medical_terms(description)
    except ValueError as exc:
        raise InvalidHealthConfigError(str(exc)) from exc

    conditions = data.get("condition_facts", [])
    if not isinstance(conditions, list):
        raise InvalidHealthConfigError(
            f"rule {rule_id}: condition_facts must be a list",
        )

    # SAFETY: Validate no medical terms in condition facts
    for cond in conditions:
        try:
            _validate_no_medical_terms(str(cond))
        except ValueError as exc:
            raise InvalidHealthConfigError(str(exc)) from exc

    outcome_str = data.get("outcome", "")
    try:
        outcome = HealthOutcomeTaxonomy(outcome_str)
    except ValueError as exc:
        raise InvalidHealthConfigError(
            f"rule {rule_id}: unknown outcome '{outcome_str}'",
        ) from exc

    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidHealthConfigError(
            f"rule {rule_id}: unknown direction '{direction_str}'",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidHealthConfigError(
            f"rule {rule_id}: unknown strength '{strength_str}'",
        ) from exc

    return HealthRule(
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
