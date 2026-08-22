"""Nakshatra Relationship & Activation models — deterministic fact layer.

JRE-026 computes NakshatraActivation objects from existing planet positions.
It outputs ONLY facts, NEVER predictions or interpretations.

Core Models:
- NakshatraRelationshipType: classification of nakshatra-based relationships
- NakshatraActivation: a single activation fact linking a planet to a nakshatra
- NakshatraActivationReport: complete report for all computed activations
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, NakshatraId, PlanetState

#: Pinned package version.
NAKSHATRA_ACTIVATION_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NakshatraRelationshipType(StrEnum):
    """Classification of nakshatra-based relationships.

    These are FACT classifications, not interpretive labels.
    Each type describes a distinct astronomical/positional relationship.
    """

    #: Planet occupies a nakshatra in the natal chart
    NAKSHATRA_OCCUPANCY = "NAKSHATRA_OCCUPANCY"

    #: Nakshatra lord is activated by another planet's position or transit
    NAKSHATRA_LORD_ACTIVATION = "NAKSHATRA_LORD_ACTIVATION"

    #: Transit planet ingresses into a natal nakshatra
    TRANSIT_NAKSHATRA_INGRESS = "TRANSIT_NAKSHATRA_INGRESS"

    #: Natal planet's nakshatra is activated by a transit or dasha
    NATAL_NAKSHATRA_ACTIVATION = "NATAL_NAKSHATRA_ACTIVATION"

    #: Two planets exchange nakshatra lords (mutual activation)
    MUTUAL_NAKSHATRA_EXCHANGE = "MUTUAL_NAKSHATRA_EXCHANGE"

    #: One planet's nakshatra depends on another's (e.g., through conjunction)
    NAKSHATRA_DEPENDENCY = "NAKSHATRA_DEPENDENCY"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NakshatraActivation:
    """A single nakshatra activation fact.

    This is a DETERMINISTIC FACT — it describes an astronomical relationship
    that exists in the chart, not an interpretation of what it means.
    """

    #: The planet that triggers or occupies the nakshatra
    source_planet: BodyId

    #: The natal position of the source planet
    source_position: PlanetState

    #: The nakshatra involved
    nakshatra: NakshatraId

    #: The lord of the nakshatra
    nakshatra_lord: BodyId

    #: The natal state of the nakshatra lord (if present in chart)
    natal_lord_state: PlanetState | None

    #: The transit state of the nakshatra lord (if transiting)
    transit_lord_state: PlanetState | None

    #: The type of relationship
    relationship_type: NakshatraRelationshipType

    #: When the activation begins (ISO-UTC or empty for natal-only)
    activation_start: str = ""

    #: When the activation ends (ISO-UTC or empty for natal-only)
    activation_end: str = ""

    #: Which varga charts are affected by this activation
    affected_vargas: tuple[str, ...] = ()

    #: Aspect relationships involving the nakshatra lord
    aspect_relationships: tuple[str, ...] = ()

    #: Dasha relationship (which dasha period activates this)
    dasha_relationship: str = ""

    #: Provenance of this activation fact
    provenance: str = ""

    #: Deterministic content-addressed identity
    deterministic_id: str = field(default="")

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", self._compute_deterministic_id()
            )

    def _compute_deterministic_id(self) -> str:
        """Compute a deterministic SHA-256 hash for this activation."""
        data = {
            "source_planet": self.source_planet.value,
            "nakshatra": self.nakshatra.value,
            "nakshatra_lord": self.nakshatra_lord.value,
            "relationship_type": self.relationship_type.value,
            "activation_start": self.activation_start,
            "activation_end": self.activation_end,
        }
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        hasher = hashlib.sha256()
        hasher.update(b"nakshatra_activation:")
        hasher.update(serialized.encode("utf-8"))
        return hasher.hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class NakshatraActivationReport:
    """Complete report of all nakshatra activations for a chart."""

    #: All computed activations
    activations: tuple[NakshatraActivation, ...]

    #: Version
    version: str = NAKSHATRA_ACTIVATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "activations": [a.to_dict() for a in self.activations],
            "activation_count": len(self.activations),
            "version": self.version,
        }

    def result_for(self, planet: BodyId) -> tuple[NakshatraActivation, ...]:
        """Return activations involving a specific planet."""
        return tuple(a for a in self.activations if a.source_planet is planet)

    def result_for_nakshatra(
        self, nakshatra: NakshatraId
    ) -> tuple[NakshatraActivation, ...]:
        """Return activations involving a specific nakshatra."""
        return tuple(a for a in self.activations if a.nakshatra is nakshatra)


# ---------------------------------------------------------------------------
# Generic serialization helpers
# ---------------------------------------------------------------------------


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> .value; tuples -> lists; -0.0 -> 0.0)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {_model_to_dict(key): _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    if isinstance(model, PlanetState):
        return {
            "body": model.body.value,
            "longitude_used": model.longitude_used,
            "rashi": model.rashi.value,
            "nakshatra": model.nakshatra.value,
            "pada": int(model.pada),
        }
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)
