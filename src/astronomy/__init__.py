"""JRE-002 Astronomical Core — deterministic, provider-independent astronomy.

Public API (nothing astrological — no houses, rashis, nakshatras, yogas,
dashas, gochar, benefic/malefic, or predictions):

- ``AstronomicalService`` — the deterministic facade.
- ``EphemerisRequest`` / ``EphemerisResult`` and the supporting models.
- ``EphemerisProvider`` / ``ProviderRegistry`` / ``get_provider`` for
  provider selection and future providers.
- Typed errors and JSON serialization helpers.

Consumers (the future Generic Gochar and Individual Kundali engines) must
obtain raw positions only through this surface and derive any Jyotish
quantities themselves.
"""

from .errors import (
    EphemerisDataError,
    EphemerisError,
    InvalidCoordinatesError,
    InvalidTimestampError,
    UnsupportedProviderError,
)
from .models import (
    Ayanamsa,
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    EphemerisRequest,
    EphemerisResult,
    NodeType,
    PositionType,
    ProviderMetadata,
    ProviderRun,
    RetrogradeState,
)
from .provider import EphemerisProvider, ProviderRegistry, default_registry, get_provider
from .serialize import config_from_dict, request_from_dict, result_to_dict, result_to_json
from .service import AstronomicalService

__version__ = "0.3.0"

__all__ = [
    "AstronomicalService",
    "EphemerisRequest",
    "EphemerisResult",
    "CalculationConfig",
    "BodyId",
    "BodyPosition",
    "ProviderMetadata",
    "ProviderRun",
    "RetrogradeState",
    "Ayanamsa",
    "EphemerisMode",
    "PositionType",
    "NodeType",
    "EphemerisProvider",
    "ProviderRegistry",
    "default_registry",
    "get_provider",
    "EphemerisError",
    "InvalidTimestampError",
    "InvalidCoordinatesError",
    "UnsupportedProviderError",
    "EphemerisDataError",
    "result_to_json",
    "result_to_dict",
    "request_from_dict",
    "config_from_dict",
]
