"""JRE-008 Varga models (normative specification §5-§7, §12, §16-§17).

JRE-008 is a deterministic factual engine: it computes divisional-chart
state from established JRE-003 ``PlanetState`` facts and never recalculates
longitude, ayanamsa, or positions. It defines only varga-owned enums
(``BoundaryConvention``, ``SubdivisionStrategy``, ``MappingStrategy``);
every astronomical enum is imported from the ``jyotish`` public root.

The core calculation contract is fully typed: no ``dict[str, Any]`` for
``VargaCalculationMethod``. ``VargaDefinition.ayanamsa`` is an opaque
validated string echo of the value supplied through the JRE-003
``JyotishConfig`` (never ``astronomy.Ayanamsa`` — that module is
forbidden here), matching the ``ContextConfig.house_system: str`` /
``BhavaConfig.tradition_profile: str | None`` echo precedents.

Deterministic identity follows the JRE-007 discipline: domain-separated
SHA-256 over the canonical dict of the fact (``compute_deterministic_id``).
Different methods (e.g. ``d20-bphs-v1`` vs ``d20-saravali-variant-v1``)
never merge — identity changes whenever any calculation-defining field
changes.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from jyotish import (
    BodyId,
    PlanetState,
    RashiId,
    ZodiacMode,
)

from .errors import InvalidVargaConfigError, InvalidVargaRequestError

#: Pinned package version (same policy as JRE-002/003/004/005/006/007).
VARGA_VERSION = "0.1.0"

#: Pinned Varga catalog version (same policy as RASHI_/NAKSHATRA_CATALOG_VERSION).
VARGA_CATALOG_VERSION = "0.1.0"

#: Frozen V1 Varga ids (D27 deferred — its method divergence is unresolved).
VARGA_IDS: tuple[str, ...] = (
    "D2",
    "D3",
    "D4",
    "D7",
    "D9",
    "D10",
    "D12",
    "D16",
    "D20",
    "D24",
    "D30",
    "D40",
    "D45",
    "D60",
)


class SubdivisionStrategy(StrEnum):
    """How a sign is subdivided into divisions (§7)."""

    UNIFORM = "UNIFORM"
    UNEQUAL_TABLE = "UNEQUAL_TABLE"
    SPECIALIZED = "SPECIALIZED"


class MappingStrategy(StrEnum):
    """How division indices map to resulting signs (§8/§9).

    A strategy exists only where it corresponds to a source-pinned
    calculation rule. ``SPECIALIZED`` is used by D60 (BPHS remainder
    algorithm) and by D2 (fixed Leo/Cancer hora output).
    """

    MODALITY_START = "MODALITY_START"
    ODD_EVEN_START = "ODD_EVEN_START"
    FIXED_START = "FIXED_START"
    KENDRA_SEQUENCE = "KENDRA_SEQUENCE"
    TRINAL_SEQUENCE = "TRINAL_SEQUENCE"
    SELF_SEQUENCE = "SELF_SEQUENCE"
    ELEMENT_START = "ELEMENT_START"
    EXPLICIT_TABLE = "EXPLICIT_TABLE"
    SPECIALIZED = "SPECIALIZED"


class BoundaryConvention(StrEnum):
    """Frozen V1 boundary convention (§10)."""

    HALF_OPEN_LOW = "HALF_OPEN_LOW"


# --------------------------------------------------------------------------- #
# Source references (provenance-grounded citations; §6/§16)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SourceCitation:
    """A source-pinned citation for a Varga calculation method (§6)."""

    text: str
    chapter: str
    verse_range: str
    edition: str
    notes: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("text", "chapter", "verse_range", "edition"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or value == "":
                raise InvalidVargaConfigError(
                    f"SourceCitation.{field_name} must be a non-empty string, got {value!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Mapping parameters (typed; never dict[str, Any]; §7/§9)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ModalityStartParams:
    """MODALITY_START (absolute): fixed starting sign per source-sign
    modality (D16/D20/D45). The mapped sign is ``start + (division_index
    - 1)`` (mod 12)."""

    movable_start: RashiId
    fixed_start: RashiId
    dual_start: RashiId

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class RelativeModalityParams:
    """MODALITY_START (relative): zodiacal offsets from the source sign
    per source-sign modality — D9 (movable +0, fixed +8, dual +4, BPHS
    ch. 6 v.12). The mapped sign is ``source + offset +
    (division_index - 1)`` (mod 12)."""

    movable_offset: int
    fixed_offset: int
    dual_offset: int

    def __post_init__(self) -> None:
        for name, value in (
            ("movable_offset", self.movable_offset),
            ("fixed_offset", self.fixed_offset),
            ("dual_offset", self.dual_offset),
        ):
            if not isinstance(value, int) or not 0 <= value < 12:
                raise InvalidVargaConfigError(
                    f"{name} must be an integer in [0, 12), got {value!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class OddEvenStartParams:
    """ODD_EVEN_START: per-parity starting rule.

    Relative form (D7/D10): ``odd_offset``/``even_offset`` are zodiacal
    offsets from the source sign; the mapped sign is ``source + offset +
    (division_index - 1)`` (mod 12). Absolute form (D24/D40):
    ``odd_start``/``even_start`` are fixed starting signs applied to any
    odd/even source sign; the mapped sign is ``start + (division_index -
    1)`` (mod 12). Exactly one form must be supplied.
    """

    odd_offset: int | None = None
    even_offset: int | None = None
    odd_start: RashiId | None = None
    even_start: RashiId | None = None

    def __post_init__(self) -> None:
        if self.odd_start is not None or self.even_start is not None:
            if self.odd_start is None or self.even_start is None:
                raise InvalidVargaConfigError(
                    "absolute odd/even starts require both odd_start and even_start"
                )
            if self.odd_offset is not None or self.even_offset is not None:
                raise InvalidVargaConfigError(
                    "absolute odd/even starts cannot be combined with offsets"
                )
            return
        if self.odd_offset is None or self.even_offset is None:
            raise InvalidVargaConfigError(
                "odd/even offsets require both odd_offset and even_offset"
            )
        for name, value in (
            ("odd_offset", self.odd_offset),
            ("even_offset", self.even_offset),
        ):
            if not isinstance(value, int) or not 0 <= value < 12:
                raise InvalidVargaConfigError(
                    f"{name} must be an integer in [0, 12), got {value!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class IntervalEntry:
    """One band of an explicit unequal table (D30 §21)."""

    lower_deg: float
    upper_deg: float
    destination: RashiId

    def __post_init__(self) -> None:
        if not isinstance(self.lower_deg, (int, float)) or not isinstance(
            self.upper_deg, (int, float)
        ):
            raise InvalidVargaConfigError(
                f"interval bounds must be numbers, got {self.lower_deg!r}/{self.upper_deg!r}"
            )
        if self.lower_deg < 0.0 or self.upper_deg > 30.0 or self.lower_deg >= self.upper_deg:
            raise InvalidVargaConfigError(
                f"invalid interval [{self.lower_deg}, {self.upper_deg}) — must satisfy "
                "0 <= lower < upper <= 30"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class ExplicitTableParams:
    """EXPLICIT_TABLE: ordered non-overlapping bands (D30)."""

    odd_bands: tuple[IntervalEntry, ...]
    even_bands: tuple[IntervalEntry, ...]

    def __post_init__(self) -> None:
        for label, bands in (("odd_bands", self.odd_bands), ("even_bands", self.even_bands)):
            if not bands:
                raise InvalidVargaConfigError(f"{label} must not be empty")
            if any(not isinstance(band, IntervalEntry) for band in bands):
                raise InvalidVargaConfigError(f"{label} must contain only IntervalEntry values")
            cursor = 0.0
            for band in bands:
                if band.lower_deg != cursor:
                    raise InvalidVargaConfigError(
                        f"{label} must be contiguous and ordered; expected lower={cursor}, "
                        f"got {band.lower_deg!r}"
                    )
                cursor = band.upper_deg
            if cursor != 30.0:
                raise InvalidVargaConfigError(
                    f"{label} must cover exactly [0, 30), ends at {cursor}"
                )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class FixedStartParams:
    """FIXED_START / SPECIALIZED mapping parameters.

    For D2 (hora): ``hora=True`` selects the fixed Leo/Cancer pair — the
    first/second half of an odd sign is Leo/Cancer and the reverse for an
    even sign (BPHS ch. 6 v.5-6; no zodiacal advancement). For D12
    (self): ``self_start=True`` counts from the source sign. For D60
    (specialized remainder): ``remainder=True`` selects the BPHS
    remainder algorithm (§22).
    """

    odd_start: RashiId | None = None
    even_start: RashiId | None = None
    self_start: bool = False
    remainder: bool = False
    hora: bool = False

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


#: The typed union of all mapping-parameter blocks (§7).
MappingParams = (
    ModalityStartParams
    | RelativeModalityParams
    | OddEvenStartParams
    | ExplicitTableParams
    | FixedStartParams
)


# --------------------------------------------------------------------------- #
# VargaCalculationMethod (§7)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaCalculationMethod:
    """The complete, versioned algorithm for one Varga (§7)."""

    method_id: str
    version: str
    subdivision_strategy: SubdivisionStrategy
    mapping_strategy: MappingStrategy
    mapping_parameters: MappingParams
    boundary_convention: BoundaryConvention
    source_references: tuple[SourceCitation, ...]
    applicable_varga: str
    applicable_tradition_profile: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.method_id, str) or self.method_id == "":
            raise InvalidVargaConfigError(
                f"method_id must be a non-empty string, got {self.method_id!r}"
            )
        if not isinstance(self.version, str) or self.version == "":
            raise InvalidVargaConfigError(
                f"version must be a non-empty string, got {self.version!r}"
            )
        if not isinstance(self.subdivision_strategy, SubdivisionStrategy):
            raise InvalidVargaConfigError(
                "subdivision_strategy must be a SubdivisionStrategy, "
                f"got {self.subdivision_strategy!r}"
            )
        if not isinstance(self.mapping_strategy, MappingStrategy):
            raise InvalidVargaConfigError(
                f"mapping_strategy must be a MappingStrategy, got {self.mapping_strategy!r}"
            )
        if not self.source_references:
            raise InvalidVargaConfigError("source_references must not be empty")
        if not isinstance(self.applicable_varga, str) or self.applicable_varga == "":
            raise InvalidVargaConfigError(
                f"applicable_varga must be a non-empty string, got {self.applicable_varga!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# VargaDefinition (§6)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaDefinition:
    """Frozen definition of one Varga (§6).

    ``ayanamsa`` is an opaque validated echo of the ayanamsa value
    supplied through the JRE-003 ``JyotishConfig`` — a ``str | None``,
    never an ``astronomy.Ayanamsa`` reference and never recalculated.
    """

    varga_id: str
    canonical_name: str
    division_number: int
    calculation_method: VargaCalculationMethod
    zodiac_mode: str
    ayanamsa: str | None
    boundary_convention: BoundaryConvention
    tradition_profile: str | None
    version: str
    source_citations: tuple[SourceCitation, ...]
    catalog_version: str = VARGA_CATALOG_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.varga_id, str) or self.varga_id == "":
            raise InvalidVargaConfigError(
                f"varga_id must be a non-empty string, got {self.varga_id!r}"
            )
        if not isinstance(self.canonical_name, str) or self.canonical_name == "":
            raise InvalidVargaConfigError(
                f"canonical_name must be a non-empty string, got {self.canonical_name!r}"
            )
        if not isinstance(self.division_number, int) or self.division_number <= 0:
            raise InvalidVargaConfigError(
                f"division_number must be a positive integer, got {self.division_number!r}"
            )
        if not isinstance(self.zodiac_mode, str) or self.zodiac_mode == "":
            raise InvalidVargaConfigError(
                f"zodiac_mode must be a non-empty string echo, got {self.zodiac_mode!r}"
            )
        if self.ayanamsa is not None and (
            not isinstance(self.ayanamsa, str) or self.ayanamsa == ""
        ):
            raise InvalidVargaConfigError(
                "ayanamsa must be None or a non-empty string echo, "
                f"got {self.ayanamsa!r}"
            )
        if not isinstance(self.boundary_convention, BoundaryConvention):
            raise InvalidVargaConfigError(
                "boundary_convention must be a BoundaryConvention, "
                f"got {self.boundary_convention!r}"
            )
        if self.tradition_profile is not None and (
            not isinstance(self.tradition_profile, str) or self.tradition_profile == ""
        ):
            raise InvalidVargaConfigError(
                "tradition_profile must be None or a non-empty string, "
                f"got {self.tradition_profile!r}"
            )
        if not isinstance(self.version, str) or self.version == "":
            raise InvalidVargaConfigError(
                f"version must be a non-empty string, got {self.version!r}"
            )
        if not isinstance(self.catalog_version, str) or self.catalog_version == "":
            raise InvalidVargaConfigError(
                f"catalog_version must be a non-empty string, got {self.catalog_version!r}"
            )
        if not isinstance(self.source_citations, tuple) or not self.source_citations:
            raise InvalidVargaConfigError("source_citations must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Provenance (§16)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaProvenance:
    """Complete answer to *where did this Varga fact come from?* (§16)."""

    source_state_id: str
    provider_id: str
    ephemeris_version: str
    varga_method_id: str
    varga_method_version: str
    varga_definition_version: str
    source_citations: tuple[SourceCitation, ...]
    tradition_profile: str | None
    boundary_convention: BoundaryConvention
    input_rashi: RashiId
    input_degree_in_rashi: float

    def __post_init__(self) -> None:
        for field_name in (
            "source_state_id",
            "provider_id",
            "ephemeris_version",
            "varga_method_id",
            "varga_method_version",
            "varga_definition_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or value == "":
                raise InvalidVargaRequestError(
                    f"VargaProvenance.{field_name} must be a non-empty string, got {value!r}"
                )
        if self.tradition_profile is not None and (
            not isinstance(self.tradition_profile, str) or self.tradition_profile == ""
        ):
            raise InvalidVargaRequestError(
                "tradition_profile must be None or a non-empty string, "
                f"got {self.tradition_profile!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# VargaPosition (§14)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaPosition:
    """One deterministic factual varga position (§14)."""

    body: BodyId
    source_state_id: str
    source_degree_in_rashi: float
    source_rashi: RashiId
    longitude_used: float
    division_index: int
    segment_lower_deg: float
    segment_upper_deg: float
    varga_sign: RashiId
    varga_id: str
    method_id: str
    definition_version: str
    provenance: VargaProvenance
    position_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_state_id",
            "varga_id",
            "method_id",
            "definition_version",
            "position_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or value == "":
                raise InvalidVargaRequestError(
                    f"VargaPosition.{field_name} must be a non-empty string, got {value!r}"
                )
        if not isinstance(self.division_index, int) or self.division_index <= 0:
            raise InvalidVargaRequestError(
                f"division_index must be a positive integer, got {self.division_index!r}"
            )
        if not (0.0 <= self.source_degree_in_rashi < 30.0):
            raise InvalidVargaRequestError(
                "degree_in_rashi must be in [0, 30) (JRE-003 normalization), "
                f"got {self.source_degree_in_rashi!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# VargaChart (§17/§23 — standalone result, optional JRE-007 join)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaChart:
    """The standalone deterministic Varga result for one definition.

    ``context_chart_identity`` is an *opaque* opt-in join reference to a
    JRE-007 ``chart_identity`` string; JRE-008 never imports JRE-007
    internals and never modifies JRE-007.
    """

    varga_id: str
    method_id: str
    definition_version: str
    positions: tuple[VargaPosition, ...]
    varga_definition_identity: str
    varga_chart_identity: str
    context_chart_identity: str | None
    provenance: VargaProvenance

    def __post_init__(self) -> None:
        if not self.positions:
            raise InvalidVargaRequestError("varga chart requires at least one position")
        for field_name in ("varga_id", "method_id", "definition_version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or value == "":
                raise InvalidVargaRequestError(
                    f"VargaChart.{field_name} must be a non-empty string, got {value!r}"
                )
        if self.context_chart_identity is not None and (
            not isinstance(self.context_chart_identity, str)
            or self.context_chart_identity == ""
        ):
            raise InvalidVargaRequestError(
                "context_chart_identity must be None or a non-empty string, "
                f"got {self.context_chart_identity!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# VargaConfig (§18)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VargaConfig:
    """Immutable JRE-008 configuration (§18). TOML is authoritative; every
    default is declared in ``config/varga.toml`` (no hidden defaults).
    Programmatic construction is explicitly validated at construction.
    """

    catalog_version: str = VARGA_CATALOG_VERSION
    version: str = VARGA_VERSION
    default_boundary_convention: str = "HALF_OPEN_LOW"
    default_zodiac_mode: str = "SIDEREAL"
    default_ayanamsa: str | None = "LAHIRI"

    def __post_init__(self) -> None:
        validate(self)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VargaConfig:
        config = cls(
            catalog_version=_as_string(
                data.get("catalog_version"), "catalog_version", VARGA_CATALOG_VERSION
            ),
            version=_as_string(data.get("version"), "version", VARGA_VERSION),
            default_boundary_convention=_as_string(
                data.get("default_boundary_convention"),
                "default_boundary_convention",
                "HALF_OPEN_LOW",
            ),
            default_zodiac_mode=_as_string(
                data.get("default_zodiac_mode"), "default_zodiac_mode", "SIDEREAL"
            ),
            default_ayanamsa=_as_optional_string(
                data.get("default_ayanamsa"), "default_ayanamsa"
            ),
        )
        return validate(config)


def validate(config: VargaConfig) -> VargaConfig:
    """Validate a ``VargaConfig``; raises ``InvalidVargaConfigError``."""
    for field_name in (
        "catalog_version",
        "version",
        "default_boundary_convention",
        "default_zodiac_mode",
    ):
        value = getattr(config, field_name)
        if not isinstance(value, str) or value == "":
            raise InvalidVargaConfigError(
                f"{field_name} must be a non-empty string, got {value!r}"
            )
    if config.default_boundary_convention != BoundaryConvention.HALF_OPEN_LOW.value:
        raise InvalidVargaConfigError(
            f"default_boundary_convention must be {BoundaryConvention.HALF_OPEN_LOW.value}, "
            f"got {config.default_boundary_convention!r}"
        )
    try:
        ZodiacMode(config.default_zodiac_mode)
    except ValueError as exc:
        raise InvalidVargaConfigError(
            "default_zodiac_mode must be a jyotish.ZodiacMode value, "
            f"got {config.default_zodiac_mode!r}"
        ) from exc
    if config.default_ayanamsa is not None and (
        not isinstance(config.default_ayanamsa, str) or config.default_ayanamsa == ""
    ):
        raise InvalidVargaConfigError(
            "default_ayanamsa must be None or a non-empty string echo, "
            f"got {config.default_ayanamsa!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Deterministic identity (JRE-007 discipline, §17)
# --------------------------------------------------------------------------- #


def compute_deterministic_id(domain: str, data: Any) -> str:
    """Compute a deterministic SHA-256 hash for a domain and data payload.

    Identical to the JRE-007 primitive (domain-separated, sorted keys,
    compact separators) so cross-layer identity joins are consistent.
    """
    serialized = json.dumps(
        _model_to_dict(data),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    hasher = hashlib.sha256()
    hasher.update(f"{domain}:".encode())
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


def source_state_identity(state: PlanetState) -> str:
    """Deterministic identity of one JRE-003 input state (echo only)."""
    return compute_deterministic_id("jre008:source-state", state.to_dict())


def varga_definition_identity(definition: VargaDefinition) -> str:
    """Deterministic identity of a Varga definition — changes whenever any
    calculation-defining field changes (§16/§17)."""
    return compute_deterministic_id("jre008:varga-definition", definition)


def compute_position_identity(
    *,
    body: BodyId,
    source_state_id: str,
    source_degree_in_rashi: float,
    source_rashi: RashiId,
    longitude_used: float,
    division_index: int,
    segment_lower_deg: float,
    segment_upper_deg: float,
    varga_sign: RashiId,
    varga_id: str,
    method_id: str,
    definition_version: str,
    provenance: VargaProvenance,
) -> str:
    """Deterministic identity of one Varga fact (§16/§17). Computed from
    the fact's canonical content — never from ``position_id`` itself."""
    payload = {
        "body": body,
        "source_state_id": source_state_id,
        "source_degree_in_rashi": source_degree_in_rashi,
        "source_rashi": source_rashi,
        "longitude_used": longitude_used,
        "division_index": division_index,
        "segment_lower_deg": segment_lower_deg,
        "segment_upper_deg": segment_upper_deg,
        "varga_sign": varga_sign,
        "varga_id": varga_id,
        "method_id": method_id,
        "definition_version": definition_version,
        "provenance": provenance,
    }
    return compute_deterministic_id("jre008:varga-position", payload)


def varga_position_identity(position: VargaPosition) -> str:
    """Deterministic identity of one Varga fact (§16/§17)."""
    return compute_position_identity(
        body=position.body,
        source_state_id=position.source_state_id,
        source_degree_in_rashi=position.source_degree_in_rashi,
        source_rashi=position.source_rashi,
        longitude_used=position.longitude_used,
        division_index=position.division_index,
        segment_lower_deg=position.segment_lower_deg,
        segment_upper_deg=position.segment_upper_deg,
        varga_sign=position.varga_sign,
        varga_id=position.varga_id,
        method_id=position.method_id,
        definition_version=position.definition_version,
        provenance=position.provenance,
    )


def varga_chart_identity(chart: VargaChart) -> str:
    """Deterministic identity of a Varga chart (§16/§17).

    Computed from the chart's canonical content (excluding
    ``varga_chart_identity`` itself, which is the identity being computed).
    """
    payload = {
        "varga_id": chart.varga_id,
        "method_id": chart.method_id,
        "definition_version": chart.definition_version,
        "positions": chart.positions,
        "varga_definition_identity": chart.varga_definition_identity,
        "context_chart_identity": chart.context_chart_identity,
        "provenance": chart.provenance,
    }
    return compute_deterministic_id("jre008:varga-chart", payload)


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> ``.value``; tuples -> lists; ``-0.0`` -> ``0.0``)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {key: _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        if model != model or model in (float("inf"), float("-inf")):
            raise ValueError("NaN and Infinity are not allowed in deterministic serialization")
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)


def _as_string(raw: Any, field: str, default: str) -> str:
    if raw is None:
        return default
    if not isinstance(raw, str) or raw == "":
        raise InvalidVargaConfigError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def _as_optional_string(raw: Any, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or raw == "":
        raise InvalidVargaConfigError(f"{field} must be None or a non-empty string, got {raw!r}")
    return raw
