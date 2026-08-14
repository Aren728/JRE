"""JRE-005 Bhava / House engine — pure data models and enums.

Consumes ONLY the ``jyotish`` public API (``src/jyotish/__init__.py``
exports) and the standard library (ADR-013). Reused JRE-003 types are
imported, never redefined. Every fact carries a ``DerivationBlock``
(ADR-016); echoed JRE-003 fields are marked with ``echoed_from``.

Serialization conventions (DATA-CONTRACT §0): snake_case keys; enums as
their string values; tuples as arrays; ``None`` as ``null``; floats via
Python's round-trip repr (``-0.0 -> 0.0``).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, cast

from jyotish import (
    ApplyingSeparating,
    AspectKind,
    BirthData,
    BodyId,
    HouseSystem,
    NakshatraId,
    RashiId,
    RetrogradeState,
    TransitReferencePoint,
)

from .errors import InvalidBhavaConfigError

# --------------------------------------------------------------------------- #
# Enums (string values are the JSON values)
# --------------------------------------------------------------------------- #


class OccupancyStatus(enum.StrEnum):
    """Whether a bhava has occupants (derived from ``Bhava.occupants``)."""

    OCCUPIED = "OCCUPIED"
    EMPTY = "EMPTY"


class BoundaryKind(enum.StrEnum):
    """Echo classification of a house's opening boundary (SPEC §9)."""

    SIGN_BOUNDARY = "SIGN_BOUNDARY"
    COMPUTED_CUSP = "COMPUTED_CUSP"


class HouseCategory(enum.StrEnum):
    """Classical house-category membership (SPEC §17) — set members, never
    a single label. Declaration order is the canonical sort order."""

    KENDRA = "KENDRA"
    TRIKONA = "TRIKONA"
    DUSTHANA = "DUSTHANA"
    UPACHAYA = "UPACHAYA"


class RelativeHouseFrame(enum.StrEnum):
    """Relative-house anchor frame (ADR-019). Sole member in v0.2.0;
    extension is additive and versioned."""

    HOUSE_OCCUPANCY = "HOUSE_OCCUPANCY"


class UnplacedBodyBehavior(enum.StrEnum):
    """Unplaced-body policy (ADR-018): RAISE (default, no silent fallback)
    or explicit WHOLE_SIGN_FALLBACK (provenance-labeled per body)."""

    RAISE = "RAISE"
    WHOLE_SIGN_FALLBACK = "WHOLE_SIGN_FALLBACK"


class FactFrame(enum.StrEnum):
    """Fact-set tag (ADR-021): natal and transit fact sets are never merged."""

    NATAL = "NATAL"
    TRANSIT = "TRANSIT"


class DerivationId(enum.StrEnum):
    """Stable derivation identities for provenance (SPEC §23.1). New
    derivations append; existing ids never change semantics."""

    PLANET_HOUSE_OCCUPANCY = "PLANET_HOUSE_OCCUPANCY"
    PLANET_HOUSE_WHOLE_SIGN_FALLBACK = "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"
    RELATIVE_HOUSE = "RELATIVE_HOUSE"
    HOUSE_CATEGORIES = "HOUSE_CATEGORIES"
    HOUSE_OCCUPANCY_STATUS = "HOUSE_OCCUPANCY_STATUS"
    SIGN_LORD = "SIGN_LORD"
    HOUSE_LORD_ECHO = "HOUSE_LORD_ECHO"
    OWNERSHIP = "OWNERSHIP"
    OWN_SIGN = "OWN_SIGN"
    OWN_HOUSE = "OWN_HOUSE"
    CUSP_BOUNDARY_KIND = "CUSP_BOUNDARY_KIND"
    CUSP_PROXIMITY = "CUSP_PROXIMITY"
    ASPECT_TO_HOUSE_AGGREGATION = "ASPECT_TO_HOUSE_AGGREGATION"
    LORD_PLACEMENT = "LORD_PLACEMENT"
    EMPTY_HOUSE_SUMMARY = "EMPTY_HOUSE_SUMMARY"
    SIGN_LORD_TABLE = "SIGN_LORD_TABLE"
    TRANSIT_HOUSE_ECHO = "TRANSIT_HOUSE_ECHO"
    TRANSIT_RELATIVE_HOUSE = "TRANSIT_RELATIVE_HOUSE"


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

#: House categories as membership sets (SPEC §17; house numbers 1..12).
CATEGORY_MEMBERS: dict[HouseCategory, frozenset[int]] = {
    HouseCategory.KENDRA: frozenset({1, 4, 7, 10}),
    HouseCategory.TRIKONA: frozenset({1, 5, 9}),
    HouseCategory.DUSTHANA: frozenset({6, 8, 12}),
    HouseCategory.UPACHAYA: frozenset({3, 6, 10, 11}),
}

#: Default cusp-proximity orb in degrees (ADR-017; modern convention).
DEFAULT_CUSP_PROXIMITY_ORB_DEG = 3.0

#: Sign-grid anchor frame is a deferred capability (ADR-019, SPEC §11.4) —
#: machine-testable via this constant, the ``RelativeHouseFrame`` enum, and
#: ``ChartEcho.sign_grid_frame_supported``.
SIGN_GRID_FRAME_SUPPORTED = False

#: Environment pin for golden fixtures (same policy as JRE-002/003/004).
GOLDEN_VERSION = "0.1.0"


@dataclass(frozen=True)
class BhavaConfig:
    """Immutable JRE-005 configuration (SPEC §7). TOML is authoritative;
    every default is declared in ``config/bhava.toml`` (no hidden defaults)."""

    cusp_proximity_orb_deg: float = DEFAULT_CUSP_PROXIMITY_ORB_DEG
    house_systems: tuple[HouseSystem, ...] = (HouseSystem.WHOLE_SIGN,)
    include_empty_houses: bool = True
    unplaced_body_behavior: UnplacedBodyBehavior = UnplacedBodyBehavior.RAISE
    tradition_profile: str | None = None
    anchor_frame: RelativeHouseFrame = RelativeHouseFrame.HOUSE_OCCUPANCY
    derivation_version: str = "0.2.0"

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BhavaConfig:
        """Deserialize a config from a JSON-shaped dict (missing key →
        field default; explicit ``null`` → ``None`` where the type allows).
        Unknown enum values raise ``InvalidBhavaConfigError`` (SPEC §7)."""
        config = cls(
            cusp_proximity_orb_deg=_as_float(
                data.get("cusp_proximity_orb_deg"),
                "cusp_proximity_orb_deg",
                DEFAULT_CUSP_PROXIMITY_ORB_DEG,
            ),
            house_systems=_parse_house_systems(data.get("house_systems")),
            include_empty_houses=_as_bool(
                data.get("include_empty_houses"), "include_empty_houses", True
            ),
            unplaced_body_behavior=_parse_enum(
                UnplacedBodyBehavior,
                data.get("unplaced_body_behavior"),
                "unplaced_body_behavior",
                UnplacedBodyBehavior.RAISE,
            ),
            tradition_profile=_parse_optional_string(
                data.get("tradition_profile"), "tradition_profile"
            ),
            anchor_frame=_parse_enum(
                RelativeHouseFrame,
                data.get("anchor_frame"),
                "anchor_frame",
                RelativeHouseFrame.HOUSE_OCCUPANCY,
            ),
            derivation_version=_as_nonempty_string(
                data.get("derivation_version"), "derivation_version", "0.2.0"
            ),
        )
        return validate(config)


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DerivationBlock:
    """Provenance for one derived fact (ADR-016, SPEC §23)."""

    id: str
    derivation_version: str
    inputs: tuple[str, ...]
    source_catalog_versions: dict[str, str]
    house_system: HouseSystem


# --------------------------------------------------------------------------- #
# Chart echo
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ChartEcho:
    """Echo block of the consumed JRE-003 chart (SPEC §24)."""

    house_system: HouseSystem
    jyotish_config: dict[str, Any]
    provider_metadata: list[dict[str, Any]]
    rashi_catalog_version: str
    nakshatra_catalog_version: str
    anchor_frame: RelativeHouseFrame
    sign_grid_frame_supported: bool
    cusp_proximity_orb_deg: float
    unplaced_body_behavior: str
    tradition_profile: str | None
    derivation_version: str
    golden_version: str


# --------------------------------------------------------------------------- #
# Fact models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AspectToHouseFact:
    """One geometric aspect received by a house (SPEC §20) — echo only."""

    house_system: HouseSystem
    house_number: int
    target: str  # "CUSP" or an occupant BodyId value
    source_body: BodyId
    kind: AspectKind
    exact_angle_deg: float
    distance_from_exact_deg: float
    within_orb: bool
    applying_separating: ApplyingSeparating
    echoed_from: str
    derivation: DerivationBlock


@dataclass(frozen=True)
class PlanetHouseFact:
    """Planet-to-house derivation for one body (SPEC §13)."""

    house_system: HouseSystem
    body: BodyId
    house_number: int
    house_rule: str
    rashi: RashiId
    degree_in_rashi: float
    retrograde: RetrogradeState
    is_node: bool
    sign_lord: BodyId
    house_lord: BodyId
    own_sign: bool
    own_house: bool
    relative_house_by_reference: dict[str, int]
    echoed_from: str
    derivation: DerivationBlock


@dataclass(frozen=True)
class DerivedHouseFact:
    """One derived bhava row (SPEC §9–§12, §14, §17, §19, §20)."""

    house_system: HouseSystem
    house_number: int
    rashi: RashiId
    lord: BodyId
    occupancy_status: OccupancyStatus
    occupants: tuple[BodyId, ...]
    categories: tuple[HouseCategory, ...]
    start_deg: float
    end_deg: float
    boundary_kind: BoundaryKind
    cusp_nakshatra: NakshatraId | None
    cusp_proximate_bodies: tuple[BodyId, ...]
    aspects_received: tuple[AspectToHouseFact, ...]
    lord_placement: PlanetHouseFact | None
    echoed_from: str
    derivation: DerivationBlock


@dataclass(frozen=True)
class HouseOwnershipFact:
    """Ownership projection for one body (SPEC §16)."""

    house_system: HouseSystem
    body: BodyId
    lorded_signs: tuple[RashiId, ...]
    lorded_houses: tuple[int, ...]
    derivation: DerivationBlock


@dataclass(frozen=True)
class RelativeHouseFact:
    """One chart-level relative-house row (SPEC §11)."""

    house_system: HouseSystem
    body: BodyId
    reference: TransitReferencePoint
    reference_absolute_house: int
    relative_house_number: int
    derivation: DerivationBlock


@dataclass(frozen=True)
class HouseAnalysis:
    """Per-house-system derived analysis (SPEC §5, DATA-CONTRACT §8)."""

    house_system: HouseSystem
    chart_echo: ChartEcho
    derived_houses: tuple[DerivedHouseFact, ...]
    planet_house_facts: tuple[PlanetHouseFact, ...]
    ownership_facts: tuple[HouseOwnershipFact, ...]
    relative_house_table: dict[str, dict[str, int]]
    relative_house_facts: tuple[RelativeHouseFact, ...]
    aspects_to_houses: tuple[AspectToHouseFact, ...]
    empty_house_numbers: tuple[int, ...]
    occupied_house_numbers: tuple[int, ...]
    empty_house_count: int
    derivation: DerivationBlock


@dataclass(frozen=True)
class HouseAnalysisResult:
    """Top-level natal result (DATA-CONTRACT §10)."""

    birth_snapshot: BirthData
    config: BhavaConfig
    analyses: tuple[HouseAnalysis, ...]
    golden_version: str


@dataclass(frozen=True)
class TransitHouseFact:
    """Gochar-frame derived fact (SPEC §22, ADR-021)."""

    frame: FactFrame
    body: BodyId
    natal_house_number: int
    natal_house_rashi: RashiId
    natal_house_lord: BodyId
    natal_occupants: tuple[BodyId, ...]
    aspects_to_natal: tuple[dict[str, Any], ...]
    relative_house_by_reference: dict[str, int]
    echoed_from: str
    derivation: DerivationBlock


@dataclass(frozen=True)
class TransitHouseAnalysis:
    """Top-level transit analysis (DATA-CONTRACT §7a)."""

    birth_snapshot: BirthData
    config: BhavaConfig
    transit_instant_utc_iso: str
    reference: TransitReferencePoint
    transit_facts: tuple[TransitHouseFact, ...]
    chart_echo: ChartEcho
    golden_version: str


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

_VALID_ORB_RANGE = (0.0, 30.0)


def validate(config: BhavaConfig) -> BhavaConfig:
    """Validate a ``BhavaConfig``; raises ``InvalidBhavaConfigError`` with
    the offending value (SPEC §29)."""
    orb = config.cusp_proximity_orb_deg
    if not (_VALID_ORB_RANGE[0] < orb < _VALID_ORB_RANGE[1]):
        raise InvalidBhavaConfigError(
            f"cusp_proximity_orb_deg must be in (0, 30.0), got {orb}"
        )
    if not config.house_systems:
        raise InvalidBhavaConfigError("house_systems must be non-empty")
    if len(set(config.house_systems)) != len(config.house_systems):
        raise InvalidBhavaConfigError(
            "house_systems must not contain duplicates: "
            f"{[getattr(s, 'value', s) for s in config.house_systems]}"
        )
    for system in config.house_systems:
        if not isinstance(system, HouseSystem):
            raise InvalidBhavaConfigError(f"unknown house_system value {system!r}")
    if not isinstance(config.unplaced_body_behavior, UnplacedBodyBehavior):
        raise InvalidBhavaConfigError(
            f"unknown unplaced_body_behavior value {config.unplaced_body_behavior!r}"
        )
    if not isinstance(config.anchor_frame, RelativeHouseFrame):
        raise InvalidBhavaConfigError(f"unknown anchor_frame value {config.anchor_frame!r}")
    if config.tradition_profile is not None and (
        not isinstance(config.tradition_profile, str) or config.tradition_profile == ""
    ):
        raise InvalidBhavaConfigError(
            "tradition_profile must be None or a non-empty string, "
            f"got {config.tradition_profile!r}"
        )
    if not isinstance(config.derivation_version, str) or config.derivation_version == "":
        raise InvalidBhavaConfigError(
            f"derivation_version must be a non-empty string, got {config.derivation_version!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (mirrors JRE-003 conventions)."""
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


def _parse_enum[EnumT: enum.Enum](
    enum_cls: type[EnumT], raw: Any, field: str, default: EnumT
) -> EnumT:
    if raw is None:
        return default
    if isinstance(raw, enum_cls):
        return raw
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise InvalidBhavaConfigError(f"unknown {field} value {raw!r}") from exc


def _parse_house_systems(raw: Any) -> tuple[HouseSystem, ...]:
    if raw is None:
        return (HouseSystem.WHOLE_SIGN,)
    if not isinstance(raw, (list, tuple)):
        raise InvalidBhavaConfigError(f"house_systems must be an array, got {raw!r}")
    return tuple(
        _parse_enum(HouseSystem, item, "house_system", HouseSystem.WHOLE_SIGN) for item in raw
    )


def _as_float(raw: Any, field: str, default: float) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidBhavaConfigError(f"{field} must be a number, got {raw!r}") from exc


def _as_bool(raw: Any, field: str, default: bool) -> bool:
    if raw is None:
        return default
    if not isinstance(raw, bool):
        raise InvalidBhavaConfigError(f"{field} must be a boolean, got {raw!r}")
    return raw


def _parse_optional_string(raw: Any, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or raw == "":
        raise InvalidBhavaConfigError(f"{field} must be None or a non-empty string, got {raw!r}")
    return raw


def _as_nonempty_string(raw: Any, field: str, default: str) -> str:
    if raw is None:
        return default
    if not isinstance(raw, str) or raw == "":
        raise InvalidBhavaConfigError(f"{field} must be a non-empty string, got {raw!r}")
    return raw
