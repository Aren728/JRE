"""JRE-012 DrikService facade.

``DrikService.calculate_aspects`` is the canonical entry point: it
validates the request and computes the classical Jyotish aspect graph
from natal planet positions.

Classical Jyotish aspects:
- All planets: 7th house (180 degrees)
- Mars: 4th (90 deg) and 8th (210 deg)
- Jupiter: 5th (120 deg) and 9th (240 deg)
- Saturn: 3rd (60 deg) and 10th (270 deg)

Detection uses angular distance with configurable orb, not just
sign-to-sign counting, for precision near sign boundaries.

It performs NO prediction, interpretation, or judgment.
"""

from __future__ import annotations

from jyotish import BodyId, PlanetState

from .config import load_config
from .errors import InvalidDrikRequestError
from .models import (
    HOUSE_OFFSET_DEGREES,
    AspectApplication,
    AspectDirection,
    AspectRule,
    AspectType,
    DrikConfig,
    DrikResult,
)

# House number -> ideal angle in degrees
_HOUSE_TO_ANGLE: dict[int, float] = {h: d for h, d in HOUSE_OFFSET_DEGREES.items()}


class DrikService:
    """Deterministic Drik (aspect) computation facade."""

    def __init__(self, config: DrikConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> DrikConfig:
        return self._config

    def calculate_aspects(
        self,
        planet_states: tuple[PlanetState, ...],
    ) -> DrikResult:
        """Compute the classical Jyotish aspect graph.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.

        Returns
        -------
        DrikResult
            Complete aspect graph with all applicable aspects.
        """
        self._validate_request(planet_states)

        aspects: list[AspectApplication] = []

        for source in planet_states:
            for target in planet_states:
                if source.body == target.body:
                    continue
                app = self._compute_aspect(source, target)
                if app is not None:
                    aspects.append(app)

        return DrikResult(aspects=tuple(aspects))

    def get_aspect_rules(self) -> tuple[AspectRule, ...]:
        """Return all configured aspect rules."""
        rules: list[AspectRule] = []
        for planet_str, houses in self._config.aspect_houses.items():
            planet = BodyId(planet_str)
            for house in houses:
                aspect_type = self._house_to_aspect_type(planet, house)
                rules.append(AspectRule(
                    source_planet=planet,
                    target_house_offset=house,
                    aspect_type=aspect_type,
                ))
        return tuple(rules)

    # ------------------------------------------------------------------ #
    # Internal computation
    # ------------------------------------------------------------------ #

    def _compute_aspect(
        self,
        source: PlanetState,
        target: PlanetState,
    ) -> AspectApplication | None:
        """Compute one aspect from source to target, or None.

        For each of the source planet's configured house offsets, we
        check if the actual angular distance from source to target is
        within the orb of the ideal angle for that house.  The closest
        matching aspect wins.
        """
        source_houses = self._config.aspect_houses.get(
            source.body.value, (7,)
        )

        actual_distance = self._forward_distance(
            source.longitude_used, target.longitude_used
        )

        best: AspectApplication | None = None
        best_orb = float("inf")

        for house in source_houses:
            ideal_angle = _HOUSE_TO_ANGLE.get(house)
            if ideal_angle is None:
                continue

            orb = self._circular_distance(actual_distance, ideal_angle)

            if orb <= self._config.default_orb_deg and orb < best_orb:
                direction = self._aspect_direction(source, target, ideal_angle)
                aspect_type = self._house_to_aspect_type(source.body, house)
                best = AspectApplication(
                    source_planet=source.body,
                    target_planet=target.body,
                    aspect_type=aspect_type,
                    ideal_angle_deg=ideal_angle,
                    angular_distance_deg=actual_distance,
                    orb_deg=orb,
                    direction=direction,
                    house_offset=house,
                )
                best_orb = orb

        return best

    def _forward_distance(self, lon_from: float, lon_to: float) -> float:
        """Forward zodiacal distance from lon_from to lon_to in [0, 360)."""
        return (lon_to - lon_from) % 360.0

    def _circular_distance(self, a: float, b: float) -> float:
        """Minimum angular distance between two angles in [0, 180]."""
        diff = abs(a - b) % 360.0
        return min(diff, 360.0 - diff)

    def _aspect_direction(
        self,
        source: PlanetState,
        target: PlanetState,
        ideal_angle: float,
    ) -> AspectDirection:
        """Determine if the aspect is applying, separating, or exact."""
        actual = self._forward_distance(source.longitude_used, target.longitude_used)
        diff_from_exact = actual - ideal_angle

        # Normalize diff to [-180, 180]
        if diff_from_exact > 180.0:
            diff_from_exact -= 360.0
        elif diff_from_exact < -180.0:
            diff_from_exact += 360.0

        if abs(diff_from_exact) < 0.01:
            return AspectDirection.EXACT

        source_speed = source.speed_longitude
        target_speed = target.speed_longitude
        relative_speed = target_speed - source_speed

        if diff_from_exact > 0:
            if relative_speed < 0:
                return AspectDirection.APPLYING
            return AspectDirection.SEPARATING
        if relative_speed > 0:
            return AspectDirection.APPLYING
        return AspectDirection.SEPARATING

    def _house_to_aspect_type(self, planet: BodyId, house: int) -> AspectType:
        """Map a planet + house offset to the appropriate AspectType."""
        if house == 7:
            return AspectType.STANDARD
        if planet == BodyId.MARS:
            return AspectType.MARS_SPECIAL
        if planet == BodyId.JUPITER:
            return AspectType.JUPITER_SPECIAL
        if planet == BodyId.SATURN:
            return AspectType.SATURN_SPECIAL
        return AspectType.STANDARD

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Drik computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidDrikRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidDrikRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )
