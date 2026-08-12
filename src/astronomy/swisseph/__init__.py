"""Swiss Ephemeris adapter surface (internal).

Consumers should use ``astronomy.get_provider()`` or the default registry —
never import ``swisseph`` directly. This package is the ONLY place the
``swisseph`` binding may be imported for position computations.
"""

from .provider import SwissEphemerisProvider

__all__ = ["SwissEphemerisProvider"]
