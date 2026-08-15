"""JRE-006 Gochar result/request models (SPEC §9, DATA-CONTRACT §4-§5).

JRE-006 defines **zero new enums** (SPEC §6): every enum it exposes is
reused by import from the ``jyotish`` / ``bhava`` public roots. Result
models *contain* echoed JRE-003/JRE-005 values verbatim and never
re-declare them. ``GocharConfig`` is immutable and validated at
construction; ``config/gochar.toml`` is the single source of defaults.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, cast

from bhava import FactFrame, TransitHouseAnalysis  # noqa: F401  (re-exported type reuse)
from jyotish import (
    ApplyingSeparating,  # noqa: F401
    AspectKind,  # noqa: F401
    BirthData,
    BodyId,
    HouseSystem,  # noqa: F401
    PairGeometry,
    PlanetState,
    TransitEvent,
    TransitEventKind,  # noqa: F401
    TransitReferencePoint,  # noqa: F401
)

from .errors import InvalidGocharConfigError

#: Environment pin for golden fixtures (same policy as JRE-002/003/004/005).
GOLDEN_VERSION = "0.1.0"

#: Pinned package version (SPEC §5 ``version`` default; SPEC §4).
GOCHAR_VERSION = "0.2.0"

#: Pinned reference-point strings (SPEC §5).
REFERENCE_POINT_VALUES: tuple[str, ...] = ("LAGNA", "MOON", "SUN", "ASC")

#: sample_step_hours validation bounds (SPEC §5).
MAX_SAMPLE_STEP_HOURS = 720.0


# --------------------------------------------------------------------------- #
# Configuration (SPEC §5 — TOML authority, no hidden defaults)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GocharConfig:
    """Immutable JRE-006 configuration (SPEC §5). TOML is authoritative;
    every default is declared in ``config/gochar.toml``."""

    reference_point: str = "LAGNA"
    house_system: str = "WHOLE_SIGN"
    sample_step_hours: float = 24.0
    aspect_echo: bool = True
    natal_house_series: bool = False
    tradition_profile: str | None = None
    version: str = GOCHAR_VERSION

    def __post_init__(self) -> None:
        validate(self)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GocharConfig:
        """Deserialize from a JSON-shaped dict (missing key → field default;
        explicit ``null`` → ``None`` where the type allows). Unknown enum
        values raise ``InvalidGocharConfigError`` (SPEC §5)."""
        config = cls(
            reference_point=_as_string(
                data.get("reference_point"), "reference_point", "LAGNA"
            ),
            house_system=_as_string(data.get("house_system"), "house_system", "WHOLE_SIGN"),
            sample_step_hours=_as_float(
                data.get("sample_step_hours"), "sample_step_hours", 24.0
            ),
            aspect_echo=_as_bool(data.get("aspect_echo"), "aspect_echo", True),
            natal_house_series=_as_bool(
                data.get("natal_house_series"), "natal_house_series", False
            ),
            tradition_profile=_as_optional_string(
                data.get("tradition_profile"), "tradition_profile"
            ),
            version=_as_string(data.get("version"), "version", GOCHAR_VERSION),
        )
        return validate(config)


# --------------------------------------------------------------------------- #
# Provenance (SPEC §9.1, ADR-028)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GocharProvenance:
    """Provenance for one gochar result — pure function of the query and
    pinned versions; no environment-dependent data (ADR-028)."""

    derivation_id: str
    derivation_version: str
    source_layers: tuple[str, ...]
    jyotish_version: str
    bhava_version: str
    gochar_version: str
    ephemeris_version: str
    catalog_versions: dict[str, str]
    input_echo: dict[str, Any]
    algorithm: str


# --------------------------------------------------------------------------- #
# Result models (SPEC §9.2-§9.4)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GocharInstantResult:
    """GENERIC instant gochar state — no birth data anywhere (SPEC §9.2)."""

    instant_utc_iso: str
    planet_states: tuple[PlanetState, ...]
    pair_geometry: tuple[PairGeometry, ...] | None
    config_echo: dict[str, Any]
    provenance: GocharProvenance


@dataclass(frozen=True)
class GocharNatalResult:
    """INDIVIDUAL transit-to-natal relationship facts (SPEC §9.3). Natal
    state appears only as the ``birth_snapshot`` echo; transit and natal
    fact sets are never merged (SPEC §17)."""

    instant_utc_iso: str
    birth_snapshot: BirthData
    transit_house_analysis: TransitHouseAnalysis
    transit_to_natal_aspects: tuple[PairGeometry, ...] | None
    reference_point: str
    provenance: GocharProvenance


@dataclass(frozen=True)
class GocharIntervalResult:
    """Interval facts: echoed event stream + sampled state series +
    optional natal-frame house series (SPEC §9.4)."""

    start_utc_iso: str
    end_utc_iso: str
    bodies: tuple[str, ...]
    events: tuple[TransitEvent, ...]
    state_samples: tuple[PlanetState, ...]
    natal_house_series: tuple[TransitHouseAnalysis, ...] | None
    natal_anchor: BirthData | None
    provenance: GocharProvenance


# --------------------------------------------------------------------------- #
# Request models (SPEC §9.5)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GocharInstantRequest:
    """GENERIC instant query: ISO-UTC instant + bodies + optional config."""

    instant_utc_iso: str
    bodies: tuple[BodyId, ...]
    config: GocharConfig | None = None


@dataclass(frozen=True)
class GocharNatalRequest:
    """INDIVIDUAL instant query: birth + instant + bodies + reference."""

    birth: BirthData
    instant_utc_iso: str
    bodies: tuple[BodyId, ...]
    reference_point: str | None = None
    config: GocharConfig | None = None


@dataclass(frozen=True)
class GocharIntervalRequest:
    """Interval query: start/end ISO-UTC + bodies + optional natal anchor."""

    start_utc_iso: str
    end_utc_iso: str
    bodies: tuple[BodyId, ...]
    natal_anchor: BirthData | None = None
    config: GocharConfig | None = None


# --------------------------------------------------------------------------- #
# Validation (SPEC §5)
# --------------------------------------------------------------------------- #


def validate(config: GocharConfig) -> GocharConfig:
    """Validate a ``GocharConfig``; raises ``InvalidGocharConfigError`` with
    the offending value (SPEC §5)."""
    if config.reference_point not in REFERENCE_POINT_VALUES:
        raise InvalidGocharConfigError(
            f"reference_point must be one of {REFERENCE_POINT_VALUES}, "
            f"got {config.reference_point!r}"
        )
    try:
        HouseSystem(config.house_system)
    except ValueError as exc:
        raise InvalidGocharConfigError(
            f"house_system must be a jyotish.HouseSystem value, got {config.house_system!r}"
        ) from exc
    step = config.sample_step_hours
    if not (0.0 < step <= MAX_SAMPLE_STEP_HOURS):
        raise InvalidGocharConfigError(
            f"sample_step_hours must be in (0, {MAX_SAMPLE_STEP_HOURS}], got {step}"
        )
    if not isinstance(config.aspect_echo, bool):
        raise InvalidGocharConfigError(f"aspect_echo must be a boolean, got {config.aspect_echo!r}")
    if not isinstance(config.natal_house_series, bool):
        raise InvalidGocharConfigError(
            f"natal_house_series must be a boolean, got {config.natal_house_series!r}"
        )
    if config.tradition_profile is not None and (
        not isinstance(config.tradition_profile, str) or config.tradition_profile == ""
    ):
        raise InvalidGocharConfigError(
            "tradition_profile must be None or a non-empty string, "
            f"got {config.tradition_profile!r}"
        )
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidGocharConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Generic serialization helpers (mirrors the JRE-003/JRE-005 conventions)
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums → ``.value``; tuples → lists; ``-0.0`` → ``0.0``)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {key: _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)


def _as_string(raw: Any, field: str, default: str) -> str:
    if raw is None:
        return default
    if not isinstance(raw, str) or raw == "":
        raise InvalidGocharConfigError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def _as_float(raw: Any, field: str, default: float) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidGocharConfigError(f"{field} must be a number, got {raw!r}") from exc


def _as_bool(raw: Any, field: str, default: bool) -> bool:
    if raw is None:
        return default
    if not isinstance(raw, bool):
        raise InvalidGocharConfigError(f"{field} must be a boolean, got {raw!r}")
    return raw


def _as_optional_string(raw: Any, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or raw == "":
        raise InvalidGocharConfigError(f"{field} must be None or a non-empty string, got {raw!r}")
    return raw
