"""JRS Orchestrator configuration loader."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import InvalidJRSConfigError
from .models import JRSConfig, RoutingRule

_DECLARED_FIELDS: frozenset[str] = frozenset({
    "version",
    "default_research_depth",
    "routing",
    "engine_hints",
})

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "jrs.toml"


def load_jrs_config(path: Path | None = None) -> JRSConfig:
    """Load and validate JRS configuration from a TOML file.

    Args:
        path: Path to the TOML config file. Defaults to ``config/jrs.toml``.

    Returns:
        A validated ``JRSConfig`` instance.

    Raises:
        InvalidJRSConfigError: If the config file is missing, malformed,
            or contains undeclared fields.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.exists():
        raise InvalidJRSConfigError(f"JRS config not found: {config_path}")

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidJRSConfigError(f"Invalid TOML: {exc}") from exc

    jrs = raw.get("jrs")
    if not isinstance(jrs, dict):
        raise InvalidJRSConfigError("Missing top-level [jrs] section")

    # Validate declared fields
    unknown = set(jrs.keys()) - _DECLARED_FIELDS
    if unknown:
        raise InvalidJRSConfigError(f"Unknown config fields: {sorted(unknown)}")

    version = jrs.get("version", "1.0")
    if not isinstance(version, str):
        raise InvalidJRSConfigError("version must be a string")

    research_depth = jrs.get("default_research_depth", "standard")
    if not isinstance(research_depth, str):
        raise InvalidJRSConfigError("default_research_depth must be a string")

    # Parse routing rules
    routing_raw = jrs.get("routing", {})
    if not isinstance(routing_raw, dict):
        raise InvalidJRSConfigError("routing must be a dict")

    routing: dict[str, RoutingRule] = {}
    for category, rule_data in routing_raw.items():
        if not isinstance(rule_data, dict):
            raise InvalidJRSConfigError(f"routing.{category} must be a dict")
        routing[category] = _parse_routing_rule(rule_data)

    # Parse engine hints
    hints_raw = jrs.get("engine_hints", {})
    if not isinstance(hints_raw, dict):
        raise InvalidJRSConfigError("engine_hints must be a dict")
    engine_hints: dict[str, bool] = {}
    for key, val in hints_raw.items():
        if not isinstance(val, bool):
            raise InvalidJRSConfigError(f"engine_hints.{key} must be a bool")
        engine_hints[key] = val

    return JRSConfig(
        version=version,
        default_research_depth=research_depth,
        routing=routing,
        engine_hints=engine_hints,
    )


def _parse_routing_rule(data: dict[str, Any]) -> RoutingRule:
    """Parse a single routing rule from TOML data."""
    engines = data.get("required_engines", [])
    if not isinstance(engines, list) or not all(isinstance(e, str) for e in engines):
        raise InvalidJRSConfigError("required_engines must be a list of strings")

    topics = data.get("research_topics", [])
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise InvalidJRSConfigError("research_topics must be a list of strings")

    houses = data.get("required_houses", [])
    if not isinstance(houses, list) or not all(isinstance(h, int) for h in houses):
        raise InvalidJRSConfigError("required_houses must be a list of ints")

    return RoutingRule(
        required_engines=tuple(engines),
        research_topics=tuple(topics),
        required_houses=tuple(houses),
    )
