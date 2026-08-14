"""House cusp provider abstraction and pure whole-sign derivation (ADR-002).

- ``HouseCuspProvider`` protocol + ``HouseCuspRegistry`` (frozen after first
  use, mirroring astronomy's registry).
- ``whole_sign_cusps`` — the pure, ascendant-anchored whole-sign derivation.
  Empirically equal to the binding's ``'W'`` cusps (Specialist supersession
  notice #2); the initial adapter never requests ``'W'`` from the binding.

House systems are explicit and never mixed (ADR-002): one chart uses one
system; results from different systems are never combined.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from . import nakshatra as _nakshatra
from . import rashi as _rashi
from .errors import UnsupportedHouseSystemError
from .geometry import cusp_aspects_to_occupants
from .models import (
    Bhava,
    HouseCuspResult,
    HouseProviderMetadata,
    HouseSystem,
    JyotishConfig,
    PlanetState,
)

#: Stable identifier of the initial (Swiss Ephemeris) house provider.
SWISSEPH_HOUSE_PROVIDER_ID = "swisseph.pysweph.houses"


@runtime_checkable
class HouseCuspProvider(Protocol):
    """Contract every house-cusp provider must satisfy (Specialist §3.1)."""

    provider_id: str

    @property
    def metadata(self) -> HouseProviderMetadata: ...

    def compute_cusps(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        house_system: HouseSystem,
        config: JyotishConfig,
    ) -> HouseCuspResult: ...


class HouseCuspRegistry:
    """Process-scoped house provider registry; frozen after first use."""

    def __init__(self) -> None:
        self._providers: dict[str, HouseCuspProvider] = {}
        self._by_system: dict[HouseSystem, str] = {}
        self._frozen = False

    def register(self, provider: HouseCuspProvider, systems: tuple[HouseSystem, ...]) -> None:
        if self._frozen:
            raise RuntimeError("house registry is frozen after the first use")
        self._providers[provider.provider_id] = provider
        for system in systems:
            self._by_system[system] = provider.provider_id

    def get(self, provider_id: str) -> HouseCuspProvider:
        try:
            return self._providers[provider_id]
        except KeyError:
            raise UnsupportedHouseSystemError(
                f"house provider {provider_id!r} is not registered"
            ) from None

    def get_for(self, house_system: HouseSystem) -> HouseCuspProvider:
        """Provider for a house system; raises ``UnsupportedHouseSystemError``
        for any value with no registered provider (SPEC §20 / TEST-PLAN §5)."""
        try:
            provider_id = self._by_system[house_system]
        except KeyError:
            # Robust to raw-string values: never crash formatting the message.
            label = getattr(house_system, "value", house_system)
            raise UnsupportedHouseSystemError(
                f"no provider registered for house system {label!r}"
            ) from None
        return self._providers[provider_id]

    def freeze(self) -> None:
        self._frozen = True

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    @property
    def supported_systems(self) -> tuple[HouseSystem, ...]:
        return tuple(sorted(self._by_system, key=lambda h: h.value))


def whole_sign_cusps(ascendant_deg: float) -> tuple[float, ...]:
    """Pure ascendant-anchored whole-sign cusps (12 values in [0, 360)).

    House 1 is the sign containing the ascendant; house *n* is the *n*-th
    subsequent sign. Cusp of house *h* = ``((asc_sign_index + h − 1) mod 12) *
    30``. Matches the binding's ``'W'`` cusps (verified).
    """
    asc_index = int(ascendant_deg // 30.0) % 12
    return tuple(((asc_index + h - 1) % 12) * 30.0 for h in range(1, 13))


def compute_bhavas(
    cusp_result: HouseCuspResult,
    planet_states: tuple[PlanetState, ...],
    config: JyotishConfig,
) -> tuple[Bhava, ...]:
    """Build the 12 ``Bhava`` objects from cusps and planet states (§13.1).

    Occupants are bodies whose ``longitude_used`` falls in the house span
    (wrap-aware for house 12). Each house's aspects are cusp-point-to-occupant
    aspect relationships (empty when no occupants).
    """
    cusps = list(cusp_result.cusps)
    bhavas: list[Bhava] = []
    for h in range(1, 13):
        start = cusps[h - 1]
        end = cusps[h % 12] if h < 12 else cusps[0]
        if end <= start:
            end += 360.0
        occupants: list[PlanetState] = []
        for state in planet_states:
            lon = state.longitude_used
            in_span = (start <= lon < end) or (start <= lon + 360.0 < end)
            if in_span:
                occupants.append(state)
        occupants.sort(key=lambda s: s.body.value)
        rashi = _rashi.rashi_of(start % 360.0)
        aspects = tuple(
            aspect
            for occupant in occupants
            for aspect in cusp_aspects_to_occupants(start % 360.0, occupant, config)
        )
        bhavas.append(
            Bhava(
                house_number=h,
                start_deg=start % 360.0,
                end_deg=end % 360.0,
                rashi=rashi,
                house_lord=_rashi.lord_of(rashi),
                occupants=tuple(o.body for o in occupants),
                occupant_states=tuple(occupants),
                aspects=aspects,
                nakshatra=_nakshatra.nakshatra_of(start % 360.0),
            )
        )
    return tuple(bhavas)


def bhava_containing_longitude(
    bhavas: tuple[Bhava, ...], longitude_deg: float
) -> Bhava | None:
    """The bhava whose span contains a longitude (None if outside all spans)."""
    lon = longitude_deg % 360.0
    for bhava in bhavas:
        start, end = bhava.start_deg, bhava.end_deg
        if start <= end:
            if start <= lon < end:
                return bhava
        elif lon >= start or lon < end:
            return bhava
    return None
