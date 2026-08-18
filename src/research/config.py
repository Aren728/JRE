"""Loads ``config/research.toml`` into a validated ``ResearchConfig`` (§18).

TOML authority: ``config/research.toml`` is the single source of defaults;
a config missing any declared field is a load error
(``InvalidResearchConfigError``); a missing file is likewise a load error —
there are NO hidden fallback defaults. Programmatic ``ResearchConfig``
values supplied by a caller remain valid. No environment-variable
configuration.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidResearchConfigError
from .models import ResearchConfig

DEFAULT_CONFIG_PATH: Path = Path("config/research.toml")

#: Every field the TOML must declare.
_DECLARED_FIELDS: tuple[str, ...] = (
    "catalog_version",
    "version",
    "default_source_dir",
    "default_output_dir",
    "supported_extensions",
)


def load_config(path: str | Path | None = None) -> ResearchConfig:
    """Load and validate JRE-009 defaults from the authoritative TOML file.

    The authoritative file (``config/research.toml`` by default) MUST exist
    and MUST declare every default field; otherwise
    ``InvalidResearchConfigError`` is raised deterministically (no hidden
    fallback defaults).
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidResearchConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/research.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("research", {})
    if not isinstance(section, dict):
        raise InvalidResearchConfigError(f"[research] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidResearchConfigError(
            "config/research.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    supported_raw = section["supported_extensions"]
    if not isinstance(supported_raw, (list, tuple)):
        raise InvalidResearchConfigError(
            f"supported_extensions must be a list, got {type(supported_raw).__name__}"
        )
    supported_extensions = tuple(str(ext) for ext in supported_raw)
    if not supported_extensions:
        raise InvalidResearchConfigError("supported_extensions must not be empty")

    config = ResearchConfig(
        catalog_version=str(section["catalog_version"]),
        version=str(section["version"]),
        default_source_dir=str(section["default_source_dir"]),
        default_output_dir=str(section["default_output_dir"]),
        supported_extensions=supported_extensions,
    )
    return validate(config)


def validate(config: ResearchConfig) -> ResearchConfig:
    """Validate a ``ResearchConfig``; raises ``InvalidResearchConfigError``."""
    if not isinstance(config.catalog_version, str) or config.catalog_version == "":
        raise InvalidResearchConfigError(
            f"catalog_version must be a non-empty string, got {config.catalog_version!r}"
        )
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidResearchConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.default_source_dir, str) or config.default_source_dir == "":
        raise InvalidResearchConfigError(
            f"default_source_dir must be a non-empty string, got {config.default_source_dir!r}"
        )
    if not isinstance(config.default_output_dir, str) or config.default_output_dir == "":
        raise InvalidResearchConfigError(
            f"default_output_dir must be a non-empty string, got {config.default_output_dir!r}"
        )
    if not isinstance(config.supported_extensions, tuple) or not config.supported_extensions:
        raise InvalidResearchConfigError(
            f"supported_extensions must be a non-empty tuple, got {config.supported_extensions!r}"
        )
    for ext in config.supported_extensions:
        if not isinstance(ext, str) or ext == "":
            raise InvalidResearchConfigError(
                f"supported_extensions must contain non-empty strings, got {ext!r}"
            )
    return config
