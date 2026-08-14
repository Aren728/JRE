"""Pure data model for the Jyotish coordinate and state layer (JRE-003).

This module contains ONLY data definitions: enums, immutable dataclasses and
generic (de)serialization helpers. It imports nothing beyond the standard
library and ``astronomy.models`` (pure data, per DATA-CONTRACT §0/§1: enums
like ``BodyId`` are reused from astronomy, never redefined). It never imports
the Swiss Ephemeris binding, providers, or any interpretation layer, so
consumers can rely on it without coupling.

The field-level contract is defined in
``docs/architecture/JRE-003-DATA-CONTRACT.md`` (v0.3.0).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum
from typing import Any, cast

from astronomy.models import (
    Ayanamsa,
    BodyId,
    NodeType,
    PositionType,
    ProviderMetadata,
    RetrogradeState,
)

# --------------------------------------------------------------------------- #
# Jyotish-owned enums (string values are the JSON values)
# --------------------------------------------------------------------------- #


class ZodiacMode(StrEnum):
    """Classification frame: sidereal (default) or tropical (ADR-003)."""

    SIDEREAL = "SIDEREAL"
    TROPICAL = "TROPICAL"


class HouseSystem(StrEnum):
    """Explicit house systems; never mixed in one chart (ADR-002)."""

    WHOLE_SIGN = "WHOLE_SIGN"
    EQUAL = "EQUAL"
    PLACIDUS = "PLACIDUS"
    KOCH = "KOCH"
    REGIOMONTANUS = "REGIOMONTANUS"
    CAMPANUS = "CAMPANUS"


class RashiId(StrEnum):
    """The 12 sidereal/tropical signs, in zodiacal order (Mesha first)."""

    MESHA = "MESHA"
    VRISHABHA = "VRISHABHA"
    MITHUNA = "MITHUNA"
    KARKA = "KARKA"
    SIMHA = "SIMHA"
    KANYA = "KANYA"
    TULA = "TULA"
    VRISHCHIKA = "VRISHCHIKA"
    DHANUSHA = "DHANUSHA"
    MAKARA = "MAKARA"
    KUMBHA = "KUMBHA"
    MEENA = "MEENA"


class NakshatraId(StrEnum):
    """All 27 nakshatras, in zodiacal order from 0° sidereal."""

    ASHWINI = "ASHWINI"
    BHARANI = "BHARANI"
    KRITTIKA = "KRITTIKA"
    ROHINI = "ROHINI"
    MRIGASHIRA = "MRIGASHIRA"
    ARDRA = "ARDRA"
    PUNARVASU = "PUNARVASU"
    PUSHYA = "PUSHYA"
    ASHLESHA = "ASHLESHA"
    MAGHA = "MAGHA"
    PURVA_PHALGUNI = "PURVA_PHALGUNI"
    UTTARA_PHALGUNI = "UTTARA_PHALGUNI"
    HASTA = "HASTA"
    CHITRA = "CHITRA"
    SWATI = "SWATI"
    VISHAKHA = "VISHAKHA"
    ANURADHA = "ANURADHA"
    JYESHTHA = "JYESHTHA"
    MULA = "MULA"
    PURVA_ASHADHA = "PURVA_ASHADHA"
    UTTARA_ASHADHA = "UTTARA_ASHADHA"
    SHRAVANA = "SHRAVANA"
    DHANISHTHA = "DHANISHTHA"
    SHATABHISHA = "SHATABHISHA"
    PURVA_BHADRAPADA = "PURVA_BHADRAPADA"
    UTTARA_BHADRAPADA = "UTTARA_BHADRAPADA"
    REVATI = "REVATI"


class AspectKind(StrEnum):
    """Exact-degree aspect kinds (ADR-004); ideal angles in geometry.py."""

    CONJUNCTION = "CONJUNCTION"
    SEMISEXTILE = "SEMISEXTILE"
    SEXTILE = "SEXTILE"
    SQUARE = "SQUARE"
    TRINE = "TRINE"
    QUINCUNX = "QUINCUNX"
    OPPOSITION = "OPPOSITION"


class ApplyingSeparating(StrEnum):
    """Whether an aspect is closing toward or opening from exactness."""

    APPLYING = "APPLYING"
    SEPARATING = "SEPARATING"
    NONE = "NONE"


class TransitEventKind(StrEnum):
    """Continuous-transit event kinds (requirement E)."""

    RASHI_INGRESS = "RASHI_INGRESS"
    RASHI_EGRESS = "RASHI_EGRESS"
    NAKSHATRA_INGRESS = "NAKSHATRA_INGRESS"
    NAKSHATRA_EGRESS = "NAKSHATRA_EGRESS"
    PADA_INGRESS = "PADA_INGRESS"
    PADA_EGRESS = "PADA_EGRESS"
    STATION_RETROGRADE = "STATION_RETROGRADE"
    STATION_DIRECT = "STATION_DIRECT"


class TransitReferencePoint(StrEnum):
    """Reference point for transit-through-houses numbering (requirement F)."""

    LAGNA = "LAGNA"
    MOON = "MOON"
    SUN = "SUN"
    ASC = "ASC"


class EclipseKind(StrEnum):
    """Eclipse family (requirement H)."""

    SOLAR = "SOLAR"
    LUNAR = "LUNAR"


class EclipseClassification(StrEnum):
    """Astronomical eclipse classification (data only, ADR-006)."""

    TOTAL = "TOTAL"
    PARTIAL = "PARTIAL"
    ANNULAR = "ANNULAR"
    HYBRID = "HYBRID"
    PENUMBRAL = "PENUMBRAL"


class Pada(IntEnum):
    """Nakshatra quarter 1–4 (serialized as number)."""

    PADA_1 = 1
    PADA_2 = 2
    PADA_3 = 3
    PADA_4 = 4


# --------------------------------------------------------------------------- #
# Generic (de)serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Serialize a frozen dataclass: enums -> values, tuples -> lists, None stays."""
    if isinstance(model, Enum):
        return model.value
    if isinstance(model, dict):
        return {
            _model_to_dict(key): _model_to_dict(value) for key, value in model.items()
        }
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(item) for item in model]
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, (_dt.date, _dt.time)):
        return model.isoformat()
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_ASPECT_ORBS: dict[AspectKind, float] = {
    AspectKind.CONJUNCTION: 8.0,
    AspectKind.OPPOSITION: 8.0,
    AspectKind.TRINE: 7.0,
    AspectKind.SQUARE: 7.0,
    AspectKind.SEXTILE: 5.0,
    AspectKind.QUINCUNX: 4.0,
    AspectKind.SEMISEXTILE: 2.0,
}


@dataclass(frozen=True)
class JyotishConfig:
    """Immutable snapshot of every setting that can change JRE-003 output.

    ``timezone`` and ``coordinate_precision`` are presentation-only (they do
    not change facts). Everything else is part of the calculation identity
    (Specialist spec §18). Defaults mirror ``config/jyotish.toml``.
    """

    zodiac_mode: ZodiacMode = ZodiacMode.SIDEREAL
    ayanamsa: Ayanamsa | None = Ayanamsa.LAHIRI
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    node_model: NodeType = NodeType.MEAN
    position_type: PositionType = PositionType.APPARENT
    provider_id: str | None = None
    ephemeris_version: str | None = None
    timezone: str = "UTC"
    coordinate_precision: int = 1
    conjunction_orb_deg: float = 8.0
    aspect_orbs_deg: dict[AspectKind, float] = field(
        default_factory=lambda: dict(DEFAULT_ASPECT_ORBS)
    )
    station_speed_epsilon: float = 1e-9
    transit_sample_step_hours: float = 6.0
    transit_tolerance_jd: float = 1e-4

    def to_dict(self) -> dict[str, Any]:
        return {
            "zodiac_mode": self.zodiac_mode.value,
            "ayanamsa": None if self.ayanamsa is None else self.ayanamsa.value,
            "house_system": self.house_system.value,
            "node_model": self.node_model.value,
            "position_type": self.position_type.value,
            "provider_id": self.provider_id,
            "ephemeris_version": self.ephemeris_version,
            "timezone": self.timezone,
            "coordinate_precision": self.coordinate_precision,
            "conjunction_orb_deg": self.conjunction_orb_deg,
            "aspect_orbs_deg": {k.value: v for k, v in self.aspect_orbs_deg.items()},
            "station_speed_epsilon": self.station_speed_epsilon,
            "transit_sample_step_hours": self.transit_sample_step_hours,
            "transit_tolerance_jd": self.transit_tolerance_jd,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JyotishConfig:
        # A missing key means "use the field default" (LAHIRI); an explicit
        # null means "no ayanamsa" (Ayanamsa | None). DATA-CONTRACT §2/§10:
        # the documented empty ``"config": {}`` input shape must equal the
        # defaults so it is accepted by the service boundary.
        if "ayanamsa" not in data:
            ayanamsa_value: Ayanamsa | None = Ayanamsa.LAHIRI
        else:
            ayanamsa_raw = data["ayanamsa"]
            ayanamsa_value = None if ayanamsa_raw is None else Ayanamsa(ayanamsa_raw)
        orbs_raw = data.get("aspect_orbs_deg")
        return cls(
            zodiac_mode=ZodiacMode(data.get("zodiac_mode", ZodiacMode.SIDEREAL.value)),
            ayanamsa=ayanamsa_value,
            house_system=HouseSystem(data.get("house_system", HouseSystem.WHOLE_SIGN.value)),
            node_model=NodeType(data.get("node_model", NodeType.MEAN.value)),
            position_type=PositionType(data.get("position_type", PositionType.APPARENT.value)),
            provider_id=data.get("provider_id"),
            ephemeris_version=data.get("ephemeris_version"),
            timezone=data.get("timezone", "UTC"),
            coordinate_precision=int(data.get("coordinate_precision", 1)),
            conjunction_orb_deg=float(data.get("conjunction_orb_deg", 8.0)),
            aspect_orbs_deg=(
                {AspectKind(k): float(v) for k, v in orbs_raw.items()}
                if orbs_raw is not None
                else dict(DEFAULT_ASPECT_ORBS)
            ),
            station_speed_epsilon=float(data.get("station_speed_epsilon", 1e-9)),
            transit_sample_step_hours=float(data.get("transit_sample_step_hours", 6.0)),
            transit_tolerance_jd=float(data.get("transit_tolerance_jd", 1e-4)),
        )


# --------------------------------------------------------------------------- #
# Per-body classification state
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DmsValue:
    """Degrees/minutes/seconds representation (presentational only)."""

    degrees: int
    minutes: int
    seconds: float
    sign: int

    def format(self, precision: int) -> str:
        """Format as e.g. ``"143°15'32.4\""`` at precision 1 (round-half-even)."""
        sign_str = "-" if self.sign < 0 else ""
        return f"{sign_str}{self.degrees}°{self.minutes:02d}'{self.seconds:.{precision}f}\""


@dataclass(frozen=True)
class PlanetState:
    """Continuous per-body Jyotish fact (requirements A and E)."""

    body: BodyId
    longitude_tropical: float
    longitude_sidereal: float | None
    longitude_used: float
    dms: DmsValue
    rashi: RashiId
    degree_in_rashi: float
    nakshatra: NakshatraId
    nakshatra_lord: BodyId
    pada: Pada
    degree_in_nakshatra: float
    latitude: float
    speed_longitude: float
    retrograde: RetrogradeState
    timestamp_utc_iso: str
    julian_day_ut: float
    provider_id: str
    ephemeris_version: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Planet-to-planet geometry
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AspectRelationship:
    """One exact-degree aspect kind between a pair (ADR-004)."""

    kind: AspectKind
    exact_angle_deg: float
    separation_deg: float
    distance_from_exact_deg: float
    within_orb: bool
    orb_deg: float
    applying_separating: ApplyingSeparating

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class PairGeometry:
    """Planet-to-planet geometric fact (requirement B)."""

    first: BodyId
    second: BodyId
    separation_deg: float
    normalized_separation_deg: float
    same_rashi: bool
    same_bhava: bool | None
    conjunction: bool
    conjunction_distance_deg: float
    aspects: tuple[AspectRelationship, ...]
    orb_config: dict[str, Any]
    config_snapshot: JyotishConfig

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Houses / lagna / natal chart
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class HouseProviderMetadata:
    """Provider-stable metadata for the house-cusp provider."""

    provider_id: str
    library_name: str
    library_version: str
    ephemeris_version: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class HouseCuspResult:
    """House cusps + ascendant/MC in the ``longitude_used`` frame."""

    cusps: tuple[float, ...]  # 12 values, [0, 360)
    ascendant_deg: float
    mc_deg: float
    ayanamsa_value: float | None
    provider: HouseProviderMetadata

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class Bhava:
    """One house (requirement C)."""

    house_number: int
    start_deg: float
    end_deg: float
    rashi: RashiId
    house_lord: BodyId
    occupants: tuple[BodyId, ...]
    occupant_states: tuple[PlanetState, ...]
    aspects: tuple[AspectRelationship, ...]
    nakshatra: NakshatraId | None

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class LagnaState:
    """Ascendant classification (requirement D)."""

    ascendant_longitude_deg: float
    dms: DmsValue
    rashi: RashiId
    degree_in_rashi: float
    nakshatra: NakshatraId
    nakshatra_lord: BodyId
    pada: Pada
    degree_in_nakshatra: float
    bhava_relationship: Bhava | None
    house_system: HouseSystem

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class BirthData:
    """Request input only — echoed as a snapshot, never engine state (req. L)."""

    date: str  # ISO date (civil local)
    time: str  # ISO time (civil local)
    timezone: str  # IANA zone
    latitude: float
    longitude: float

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class NatalChart:
    """Individual-mode core result (requirement D/C)."""

    birth_snapshot: BirthData
    lagna: LagnaState
    bhavas: tuple[Bhava, ...]
    planet_states: tuple[PlanetState, ...]
    config: JyotishConfig
    provider_metadata: tuple[ProviderMetadata, ...]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Transit outputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SearchMetadata:
    """Determinism echo of the event search (ADR-005)."""

    algorithm: str
    sample_step_hours: float
    tolerance_jd: float
    iterations: int
    position_calls: int

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class TransitEvent:
    """One continuous-transit event (requirement E)."""

    body: BodyId
    kind: TransitEventKind
    event_julian_day_ut: float
    event_utc_iso: str
    boundary_deg: float | None
    reached: RashiId | NakshatraId | Pada | None
    direction: RetrogradeState
    search_metadata: SearchMetadata

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class HouseTransitEntry:
    """Transit of one planet through a natal house (requirement F)."""

    body: BodyId
    natal_house_number: int
    natal_house_lord: BodyId
    natal_occupants: tuple[BodyId, ...]
    aspects_to_natal: tuple[AspectRelationship, ...]
    natal_house_rashi: RashiId

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class TransitThroughHouses:
    """Transit instant against a natal chart (requirement F)."""

    reference: TransitReferencePoint
    transit_instant_utc_iso: str
    planet_states: tuple[PlanetState, ...]
    entries: tuple[HouseTransitEntry, ...]
    birth_snapshot: BirthData
    config: JyotishConfig

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Eclipse facts (data only, ADR-006)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EclipseContact:
    """One eclipse contact instant."""

    phase: str  # "P1","P2","MAX","P3","P4"/"U1".."U4"/"PENUMBRAL_BEGIN"/...
    julian_day_ut: float
    utc_iso: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class GeographicVisibility:
    """Geographic path/center where available (requirement H)."""

    latitude_deg: float
    longitude_deg: float
    description: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class EclipseEvent:
    """Astronomical eclipse facts only — no causation, no significance."""

    kind: EclipseKind
    classification: EclipseClassification
    maximum_jd_ut: float
    maximum_utc_iso: str
    contacts: tuple[EclipseContact, ...]
    magnitude: float
    node_positions: tuple[PlanetState, ...]
    solar_lunar_positions: tuple[PlanetState, ...]
    geographic_visibility: GeographicVisibility | None
    pre_event_interval_days: float
    post_event_interval_days: float
    provider_id: str
    ephemeris_version: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))
