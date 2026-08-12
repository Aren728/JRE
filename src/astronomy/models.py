"""Pure data model for the JRE astronomical core (JRE-002).

This module contains ONLY data definitions: enums, immutable dataclasses and
their (de)serialization helpers. It imports nothing beyond the standard
library and never references the Swiss Ephemeris binding, so consumers and the
service layer can rely on it without coupling to any provider.

The field-level contract is defined in
``docs/architecture/JRE-002-DATA-CONTRACT.md`` (v0.3.0).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any, cast

# --------------------------------------------------------------------------- #
# Enums (string values are the JSON values)
# --------------------------------------------------------------------------- #


class BodyId(StrEnum):
    """The nine celestial bodies computed by the core."""

    SUN = "SUN"
    MOON = "MOON"
    MARS = "MARS"
    MERCURY = "MERCURY"
    JUPITER = "JUPITER"
    VENUS = "VENUS"
    SATURN = "SATURN"
    RAHU = "RAHU"
    KETU = "KETU"


class RetrogradeState(StrEnum):
    """Longitude-motion state of a body at the computed instant."""

    DIRECT = "DIRECT"
    RETROGRADE = "RETROGRADE"
    STATIONARY = "STATIONARY"


class Ayanamsa(StrEnum):
    """Sidereal zodiac zero-point definitions (maps to swe.SIDM_* in the adapter)."""

    LAHIRI = "LAHIRI"
    RAMAN = "RAMAN"
    FAGAN_BRADLEY = "FAGAN_BRADLEY"


class EphemerisMode(StrEnum):
    """Requested/actual ephemeris computation mode."""

    SWIEPH = "SWIEPH"  # high precision, bundled .se1 data files
    MOSEPH = "MOSEPH"  # Moshier analytical approximation (fallback)


class PositionType(StrEnum):
    """Apparent (light-time/aberration/nutation corrected) vs true geometric."""

    APPARENT = "APPARENT"
    TRUE = "TRUE"


class NodeType(StrEnum):
    """Lunar node model used for Rahu/Ketu."""

    MEAN = "MEAN"
    TRUE = "TRUE"


# --------------------------------------------------------------------------- #
# Shared constants and pure helpers
# --------------------------------------------------------------------------- #

#: Canonical output ordering for bodies (declaration order).
CANONICAL_BODIES: tuple[BodyId, ...] = (
    BodyId.SUN,
    BodyId.MOON,
    BodyId.MARS,
    BodyId.MERCURY,
    BodyId.JUPITER,
    BodyId.VENUS,
    BodyId.SATURN,
    BodyId.RAHU,
    BodyId.KETU,
)

#: Starting value for the stationary classification threshold (deg/day).
#: Pending calibration by the VALIDATOR stage against real station dates;
#: any change is a versioned decision (Specialist spec §16, §36.1).
STATIONARY_SPEED_EPSILON: float = 1e-9


def classify_retrograde(
    speed_longitude: float, epsilon: float = STATIONARY_SPEED_EPSILON
) -> RetrogradeState:
    """Classify direct/retrograde/stationary from the longitude speed (deg/day)."""
    if speed_longitude < -epsilon:
        return RetrogradeState.RETROGRADE
    if speed_longitude > epsilon:
        return RetrogradeState.DIRECT
    return RetrogradeState.STATIONARY


def _model_to_dict(model: Any) -> Any:
    """Serialize a frozen dataclass: enums -> values, tuples -> lists, None stays."""
    if isinstance(model, Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(item) for item in model]
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, (_dt.date, _dt.time)):
        return model.isoformat()
    return model


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CalculationConfig:
    """Immutable snapshot of every setting that can change the output.

    Any future setting that influences the astronomical result MUST be added
    here (and to ``to_dict``/``from_dict``) — never implicitly.
    """

    ayanamsa: Ayanamsa | None = Ayanamsa.LAHIRI
    ayanamsa_override: tuple[float, float] | None = None
    ephemeris_mode: EphemerisMode = EphemerisMode.SWIEPH
    position_type: PositionType = PositionType.APPARENT
    node_type: NodeType = NodeType.MEAN
    ephemeris_path: str | None = None
    allow_fallback: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ayanamsa": None if self.ayanamsa is None else self.ayanamsa.value,
            "ayanamsa_override": (
                None if self.ayanamsa_override is None else list(self.ayanamsa_override)
            ),
            "ephemeris_mode": self.ephemeris_mode.value,
            "position_type": self.position_type.value,
            "node_type": self.node_type.value,
            "ephemeris_path": self.ephemeris_path,
            "allow_fallback": self.allow_fallback,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalculationConfig:
        ayanamsa_raw = data.get("ayanamsa")
        override_raw = data.get("ayanamsa_override")
        return cls(
            ayanamsa=None if ayanamsa_raw is None else Ayanamsa(ayanamsa_raw),
            ayanamsa_override=(
                None if override_raw is None else (float(override_raw[0]), float(override_raw[1]))
            ),
            ephemeris_mode=EphemerisMode(data["ephemeris_mode"]),
            position_type=PositionType(data["position_type"]),
            node_type=NodeType(data["node_type"]),
            ephemeris_path=data.get("ephemeris_path"),
            allow_fallback=bool(data.get("allow_fallback", True)),
        )


# --------------------------------------------------------------------------- #
# Request
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EphemerisRequest:
    """Validated input to the astronomical core (local civil time inputs)."""

    date: _dt.date
    time: _dt.time
    timezone: str
    latitude: float
    longitude: float
    bodies: tuple[BodyId, ...] | None = None  # None => all nine, canonical order
    config: CalculationConfig = field(default_factory=CalculationConfig)
    provider_id: str | None = None  # None => registry default provider

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "time": self.time.isoformat(),
            "timezone": self.timezone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "bodies": None if self.bodies is None else [b.value for b in self.bodies],
            "config": self.config.to_dict(),
            "provider_id": self.provider_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EphemerisRequest:
        bodies_raw = data.get("bodies")
        return cls(
            date=_dt.date.fromisoformat(data["date"]),
            time=_dt.time.fromisoformat(data["time"]),
            timezone=data["timezone"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            bodies=(
                None if bodies_raw is None else tuple(BodyId(b) for b in bodies_raw)
            ),
            config=CalculationConfig.from_dict(data["config"]),
            provider_id=data.get("provider_id"),
        )


# --------------------------------------------------------------------------- #
# Per-body output
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BodyPosition:
    """Raw astronomical state of one body at the computed instant."""

    body: BodyId
    longitude_tropical: float  # deg [0, 360), ecliptic-of-date, geocentric
    longitude_sidereal: float | None  # deg [0, 360); None iff no ayanamsa
    latitude: float  # deg [-90, 90], ecliptic latitude
    distance_au: float
    speed_longitude: float  # deg/day
    speed_latitude: float  # deg/day
    speed_distance: float  # AU/day
    retrograde: RetrogradeState
    position_type: PositionType
    ayanamsa_value: float | None  # deg ayanamsa applied; None iff no ayanamsa

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Provider metadata
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProviderMetadata:
    """Provider-stable metadata (does not vary per call)."""

    provider_id: str
    library_name: str
    library_version: str
    ephemeris_version: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class ProviderRun:
    """Per-call outcome of a provider (records the mode/files actually used)."""

    positions: tuple[BodyPosition, ...]
    ephemeris_mode: EphemerisMode
    ephemeris_files: tuple[str, ...]  # files used; () for MOSEPH

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Result envelope
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EphemerisResult:
    """The full service result: raw astronomy + audit metadata, nothing more."""

    request_snapshot: EphemerisRequest
    timestamp_utc_iso: str
    timestamp_local_iso: str
    julian_day_ut: float
    positions: tuple[BodyPosition, ...]
    provider: ProviderMetadata
    provider_run: ProviderRun
    config: CalculationConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_snapshot": self.request_snapshot.to_dict(),
            "timestamp_utc_iso": self.timestamp_utc_iso,
            "timestamp_local_iso": self.timestamp_local_iso,
            "julian_day_ut": self.julian_day_ut,
            "positions": [p.to_dict() for p in self.positions],
            "provider": self.provider.to_dict(),
            "provider_run": self.provider_run.to_dict(),
            "config": self.config.to_dict(),
        }
