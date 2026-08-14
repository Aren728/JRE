"""Swiss Ephemeris adapter surface for the Jyotish layer (internal).

Consumers should use ``jyotish.get_house_provider`` /
``jyotish.get_eclipse_provider`` — never import ``swisseph`` directly. This
package is the ONLY place the ``swisseph`` binding may be imported by
JRE-003 (enforced by a static test).
"""

from .eclipse import SwissEphemerisEclipseProvider
from .houses import SwissEphemerisHouseCuspProvider

__all__ = ["SwissEphemerisHouseCuspProvider", "SwissEphemerisEclipseProvider"]
