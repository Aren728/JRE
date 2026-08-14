"""``SwissEphemerisHouseCuspProvider`` — the initial house-cusp adapter.

Behavior contract (Specialist §4.1, §12, §13):

- WHOLE_SIGN: never requests the binding's ``'W'`` system; the pure
  ascendant-anchored derivation from ``houses.whole_sign_cusps`` is used
  (empirically equal to the binding's ``'W'`` cusps).
- Cusp systems (EQUAL, PLACIDUS, KOCH, REGIOMONTANUS, CAMPANUS) use
  ``swe.houses_ex`` with the hsys byte from ``constants.HSYS_BY_SYSTEM``.
- Sidereal mode (``zodiac_mode == SIDEREAL``): ``FLG_SIDEREAL`` is passed so
  the returned cusps/ascendant are already in the sidereal frame (the frame
  rotation does not commute with the spherical house computation —
  ``tropical − ayanamsa`` differs by ≈ 13″ and is NOT used).
- Every ``swe.set_*`` is executed from the immutable config under a lock
  (process-global binding state), mirroring the astronomy adapter.
"""

from __future__ import annotations

import threading

import swisseph as swe

from ..houses import HouseCuspProvider, whole_sign_cusps
from ..models import (
    HouseCuspResult,
    HouseProviderMetadata,
    HouseSystem,
    JyotishConfig,
)
from .constants import EPHEMERIS_VERSION, FLAG_SWIEPH, HSYS_BY_SYSTEM

#: Binding/library identity for HouseProviderMetadata.
LIBRARY_NAME = "pysweph"


class SwissEphemerisHouseCuspProvider(HouseCuspProvider):
    """Deterministic Swiss Ephemeris house-cusp adapter."""

    provider_id = "swisseph.pysweph.houses"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metadata = HouseProviderMetadata(
            provider_id=self.provider_id,
            library_name=LIBRARY_NAME,
            library_version=str(getattr(swe, "version", "unknown")),
            ephemeris_version=EPHEMERIS_VERSION,
        )

    @property
    def metadata(self) -> HouseProviderMetadata:
        return self._metadata

    def compute_cusps(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        house_system: HouseSystem,
        config: JyotishConfig,
    ) -> HouseCuspResult:
        sidereal = config.zodiac_mode.value == "SIDEREAL"
        flags = FLAG_SWIEPH
        if sidereal:
            _set_sid_mode(config)
            flags = int(flags) | int(swe.FLG_SIDEREAL)

        with self._lock:
            if house_system is HouseSystem.WHOLE_SIGN:
                # Ascendant/MC still come from the binding (system-independent);
                # the cusps are the pure ascendant-anchored whole-sign set.
                _, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b"E", flags)
                ascendant = ascmc[0] % 360.0
                mc = ascmc[1] % 360.0
                cusps = whole_sign_cusps(ascendant)
            else:
                hsys = HSYS_BY_SYSTEM[house_system.value]
                cusp_raw, ascmc = swe.houses_ex(jd_ut, latitude, longitude, hsys, flags)
                cusps = tuple(c % 360.0 for c in cusp_raw[1:13])
                ascendant = ascmc[0] % 360.0
                mc = ascmc[1] % 360.0

        ayanamsa_value: float | None = None
        if sidereal:
            ayanamsa_value = float(swe.get_ayanamsa_ut(jd_ut))

        return HouseCuspResult(
            cusps=cusps,
            ascendant_deg=ascendant,
            mc_deg=mc,
            ayanamsa_value=ayanamsa_value,
            provider=self._metadata,
        )


def _set_sid_mode(config: JyotishConfig) -> None:
    """Apply the config ayanamsa to the binding's sidereal mode."""
    from astronomy.models import Ayanamsa

    if config.ayanamsa is None:
        raise ValueError("ayanamsa must be set for SIDEREAL house computation")
    sidm = {
        Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
        Ayanamsa.RAMAN: swe.SIDM_RAMAN,
        Ayanamsa.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
    }[config.ayanamsa]
    swe.set_sid_mode(sidm, 0.0, 0.0)
