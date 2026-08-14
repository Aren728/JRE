"""Loads ``config/knowledge.toml`` into a validated ``KnowledgeConfig``.

Implements SPEC §13: every default is explicit, pins enforce exact-match
(mismatch is a ``CatalogIntegrityError`` at load time), and the
credibility/weight coefficients are validated configuration (SPEC §10,
supersession #7) — they never affect rule *selection*. No environment
overrides (determinism).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidConfigError
from .models import ConflictPolicy, KnowledgeConfig

DEFAULT_CONFIG_PATH: Path = Path("config/knowledge.toml")

#: Keys the provenance-completeness table must carry (SPEC §10.2).
COMPLETENESS_LEVELS = ("full", "verse", "chapter", "source")


def _completeness_table(section: dict[str, object]) -> dict[str, float]:
    """Read the nested ``[knowledge.provenance_completeness]`` table."""
    defaults = dict(zip(COMPLETENESS_LEVELS, (1.0, 0.85, 0.7, 0.5), strict=True))
    raw = section.get("provenance_completeness")
    if raw is None:
        return dict(defaults)
    if not isinstance(raw, dict):
        raise InvalidConfigError(f"provenance_completeness must be a table, got {raw!r}")
    return {level: float(raw.get(level, default)) for level, default in defaults.items()}


def validate(config: KnowledgeConfig) -> KnowledgeConfig:
    """Validate a ``KnowledgeConfig``; raises ``InvalidConfigError``."""
    if config.max_rules_per_synthesis <= 0:
        raise InvalidConfigError(
            f"max_rules_per_synthesis must be positive, got {config.max_rules_per_synthesis}"
        )
    credibility_weights = [
        config.credibility_authority_weight,
        config.credibility_provenance_weight,
        config.credibility_specificity_weight,
    ]
    if any(weight < 0.0 or weight > 1.0 for weight in credibility_weights):
        raise InvalidConfigError(
            f"credibility weights must be in [0, 1], got {credibility_weights}"
        )
    if abs(sum(credibility_weights) - 1.0) > 1e-9:
        raise InvalidConfigError(
            f"credibility weights must sum to 1.0, got {sum(credibility_weights)}"
        )
    for key in COMPLETENESS_LEVELS:
        if key not in config.provenance_completeness:
            raise InvalidConfigError(
                f"provenance_completeness must cover {list(COMPLETENESS_LEVELS)}, missing {key!r}"
            )
    for key, level in config.provenance_completeness.items():
        if not 0.0 <= level <= 1.0:
            raise InvalidConfigError(
                f"provenance_completeness[{key!r}] must be in [0, 1], got {level}"
            )
    for field in (
        "weight_authority_coeff",
        "weight_specificity_coeff",
        "weight_source_rank_coeff",
    ):
        if getattr(config, field) <= 0.0:
            raise InvalidConfigError(f"{field} must be positive, got {getattr(config, field)}")
    return config


def load_config(path: str | Path | None = None) -> KnowledgeConfig:
    """Load and validate JRE-004 defaults from a TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return validate(KnowledgeConfig())

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("knowledge", {})

    def _opt_str(key: str) -> str | None:
        value = section.get(key)
        if value is None or value == "":
            return None
        return str(value)

    rule_pins = section.get("rule_catalog_versions") or {}
    if not isinstance(rule_pins, dict):
        raise InvalidConfigError(f"rule_catalog_versions must be a table, got {rule_pins!r}")

    config = KnowledgeConfig(
        default_profile_id=str(section.get("default_profile_id", "bphs-classical")),
        default_conflict_policy=ConflictPolicy(
            section.get("default_conflict_policy", ConflictPolicy.FIRST_WINS.value)
        ),
        source_catalog_version=_opt_str("source_catalog_version"),
        rule_catalog_versions={str(k): str(v) for k, v in rule_pins.items()},
        profile_catalog_version=_opt_str("profile_catalog_version"),
        facts_catalog_version=_opt_str("facts_catalog_version"),
        enforce_provenance=bool(section.get("enforce_provenance", True)),
        verify_checksums=bool(section.get("verify_checksums", True)),
        max_rules_per_synthesis=int(section.get("max_rules_per_synthesis", 200)),
        weight_authority_coeff=float(section.get("weight_authority_coeff", 1.0)),
        weight_specificity_coeff=float(section.get("weight_specificity_coeff", 0.5)),
        weight_source_rank_coeff=float(section.get("weight_source_rank_coeff", 0.05)),
        credibility_authority_weight=float(section.get("credibility_authority_weight", 0.55)),
        credibility_provenance_weight=float(section.get("credibility_provenance_weight", 0.30)),
        credibility_specificity_weight=float(section.get("credibility_specificity_weight", 0.15)),
        provenance_completeness=_completeness_table(section),
    )
    return validate(config)
