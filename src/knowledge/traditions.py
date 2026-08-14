"""Tradition profiles: definition, registry, and source-priority validation.

Implements ADR-010: profiles are first-class, explicit, versioned data with
an explicit ``source_priority`` order and conflict policy; there is no
unprofiled mode. ``passthrough_config`` is validated against the pinned
allow-list (SPEC §14) and echoed, never interpreted.

Import direction is one-way: ``traditions -> models, errors, sources``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import (
    CatalogIntegrityError,
    InvalidConfigError,
    RuleSchemaError,
    UnknownProfileError,
    UnknownSourceError,
)
from .models import (
    PASSTHROUGH_FIELD_VALUES,
    ConflictPolicy,
    RuleDomain,
    TraditionProfile,
    read_catalog_file,
)
from .sources import SourceRegistry

PROFILE_CATALOG_VERSION = "1.0.0"

DEFAULT_PROFILES_PATH: Path = Path("datasets/knowledge/profiles/profiles.json")

_PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ProfileRegistry:
    """Immutable registry of ``TraditionProfile`` entries."""

    def __init__(self, profiles: tuple[TraditionProfile, ...], catalog_version: str) -> None:
        self._profiles = profiles
        self._catalog_version = catalog_version
        self._by_id = {profile.profile_id: profile for profile in profiles}

    @property
    def catalog_version(self) -> str:
        return self._catalog_version

    def all(self) -> tuple[TraditionProfile, ...]:
        return self._profiles

    def has(self, profile_id: str) -> bool:
        return profile_id in self._by_id

    def get(self, profile_id: str) -> TraditionProfile:
        try:
            return self._by_id[profile_id]
        except KeyError as exc:
            raise UnknownProfileError(f"unknown profile_id: {profile_id!r}") from exc


def validate_passthrough_config(config: object) -> None:
    """Validate passthrough config against the pinned allow-list (SPEC §14)."""
    if not isinstance(config, dict):
        raise InvalidConfigError(f"passthrough_config must be an object, got {config!r}")
    for key, value in config.items():
        allowed = PASSTHROUGH_FIELD_VALUES.get(key)
        if allowed is None:
            raise InvalidConfigError(f"unknown passthrough field {key!r}")
        if not isinstance(value, str) or value not in allowed:
            raise InvalidConfigError(
                f"invalid passthrough value for {key!r}: {value!r} (allowed: {sorted(allowed)})"
            )


def _parse_profile(data: Any, sources: SourceRegistry) -> TraditionProfile:
    if not isinstance(data, dict):
        raise RuleSchemaError("profile entry must be an object")
    try:
        profile_id = str(data["profile_id"])
        name = str(data["name"])
        version = str(data.get("version", PROFILE_CATALOG_VERSION))
        description = str(data.get("description", ""))
        included = tuple(str(item) for item in data.get("included_sources", []))
        priority = tuple(str(item) for item in data.get("source_priority", []))
        policy = ConflictPolicy(str(data["conflict_policy"]))
        domains_raw = data.get("domains")
        domains = (
            None if domains_raw is None else tuple(RuleDomain(str(item)) for item in domains_raw)
        )
        passthrough = data.get("passthrough_config") or {}
    except (KeyError, ValueError, TypeError) as exc:
        raise RuleSchemaError(f"malformed profile entry: {exc!r}") from exc

    if _PROFILE_ID_RE.match(profile_id) is None:
        raise RuleSchemaError(f"invalid profile_id {profile_id!r}")
    if not included:
        raise RuleSchemaError(f"profile {profile_id!r} has no included_sources")
    for source_id in included:
        if not sources.has(source_id):
            raise UnknownSourceError(
                f"profile {profile_id!r} includes unknown source {source_id!r}"
            )
    extra = [item for item in priority if item not in included]
    if extra:
        raise RuleSchemaError(
            f"profile {profile_id!r} source_priority references sources not in "
            f"included_sources: {extra}"
        )
    validate_passthrough_config(passthrough)
    return TraditionProfile(
        profile_id=profile_id,
        name=name,
        version=version,
        description=description,
        included_sources=included,
        source_priority=priority,
        conflict_policy=policy,
        domains=domains,
        passthrough_config=dict(passthrough),
    )


def load_profiles(
    path: str | Path | None = None,
    *,
    sources: SourceRegistry,
    verify_checksums: bool = True,
    pin: str | None = None,
) -> ProfileRegistry:
    """Load and validate the tradition-profiles catalog."""
    catalog_path = Path(path) if path is not None else DEFAULT_PROFILES_PATH
    try:
        document, digest = read_catalog_file(catalog_path)
    except OSError as exc:
        raise CatalogIntegrityError(f"cannot read catalog {catalog_path}: {exc}") from exc
    except ValueError as exc:
        raise CatalogIntegrityError(f"invalid JSON in catalog {catalog_path}: {exc}") from exc
    if verify_checksums:
        expected = document.get("checksum_sha256")
        if expected != digest:
            raise CatalogIntegrityError(
                f"checksum mismatch for {catalog_path}: expected {expected!r}, got {digest!r}"
            )
    if document.get("catalog_id") != "profiles":
        raise CatalogIntegrityError(
            f"catalog_id mismatch in {catalog_path}: expected 'profiles', "
            f"got {document.get('catalog_id')!r}"
        )
    version = str(document.get("catalog_version", PROFILE_CATALOG_VERSION))
    if pin is not None and version != pin:
        raise CatalogIntegrityError(
            f"version-pin mismatch for {catalog_path}: expected {pin!r}, got {version!r}"
        )
    entries = document.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise CatalogIntegrityError(f"catalog {catalog_path} has no profile entries")
    profiles = tuple(_parse_profile(entry, sources) for entry in entries)
    return ProfileRegistry(profiles, catalog_version=version)
