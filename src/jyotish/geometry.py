"""Planet-to-planet geometry (Specialist spec §10, ADR-004).

Conjunction and aspects are defined from exact angular separation, never from
house/rashi equality. ``same_rashi`` and ``same_bhava`` are separate boolean
facts; a 25°-apart pair in one house is NOT conjunct, a 2°-apart pair in
different houses IS.
"""

from __future__ import annotations

import math

from astronomy.models import BodyId

from .models import (
    ApplyingSeparating,
    AspectKind,
    AspectRelationship,
    Bhava,
    JyotishConfig,
    PairGeometry,
    PlanetState,
)

#: Ideal angle (deg) for each aspect kind (ADR-004 §Consequences).
ASPECT_IDEAL_ANGLES: dict[AspectKind, float] = {
    AspectKind.CONJUNCTION: 0.0,
    AspectKind.SEMISEXTILE: 30.0,
    AspectKind.SEXTILE: 60.0,
    AspectKind.SQUARE: 90.0,
    AspectKind.TRINE: 120.0,
    AspectKind.QUINCUNX: 150.0,
    AspectKind.OPPOSITION: 180.0,
}

#: Canonical pair generation order (BodyId declaration order).
_CANONICAL_ORDER: tuple[BodyId, ...] = (
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


def angular_separation_deg(
    lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    """Great-circle separation on the ecliptic sphere (latitudes included).

    ``acos(sin β1·sin β2 + cos β1·cos β2·cos(λ1 − λ2))`` in [0, 180].
    The acos argument is clamped to [−1, 1] for floating-point safety.
    """
    b1, b2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    arg = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(dl)
    arg = max(-1.0, min(1.0, arg))
    return math.degrees(math.acos(arg))


def normalized_separation_deg(lon1: float, lon2: float) -> float:
    """Ecliptic arc ``(λ2 − λ1) mod 360`` in [0, 360)."""
    value = (lon2 - lon1) % 360.0
    return 0.0 if value == 0.0 else value


def _wrap180(x: float) -> float:
    """Wrap to (−180, 180]."""
    return ((x + 180.0) % 360.0) - 180.0


def circular_distance_deg(separation: float, ideal: float) -> float:
    """``min(|sep − ideal|, 360 − |sep − ideal|)`` in [0, 180]."""
    diff = abs(separation - ideal) % 360.0
    return min(diff, 360.0 - diff)


def applying_separating(
    lon1: float, speed1: float, lon2: float, speed2: float,
    ideal: float, station_epsilon: float,
) -> ApplyingSeparating:
    """Closed-form applying/separating rule (Specialist §10.7).

    Uses the ecliptic-arc separation (longitude speeds are the only speed
    data). ``δ = wrap180((λ2 − λ1) mod 360 − θ)``; the distance to exactness
    changes at rate ``sign(δ)·(v2 − v1)``. APPLYING when decreasing,
    SEPARATING when increasing, NONE when the pair is (nearly) at exactness or
    the relative speed is below the station epsilon.
    """
    delta = _wrap180(normalized_separation_deg(lon1, lon2) - ideal)
    relative_speed = speed2 - speed1
    if abs(delta) <= 1e-9 or abs(relative_speed) <= station_epsilon:
        return ApplyingSeparating.NONE
    if math.copysign(1.0, delta) * relative_speed < 0.0:
        return ApplyingSeparating.APPLYING
    return ApplyingSeparating.SEPARATING


def pair_geometry(
    first: PlanetState,
    second: PlanetState,
    config: JyotishConfig,
    same_bhava: bool | None = None,
) -> PairGeometry:
    """Compute the full pair fact for two planetary states (canonical order)."""
    sep = angular_separation_deg(
        first.longitude_used, first.latitude, second.longitude_used, second.latitude
    )
    norm_sep = normalized_separation_deg(first.longitude_used, second.longitude_used)

    conjunction_orb = config.conjunction_orb_deg
    conjunction = sep <= conjunction_orb

    aspects: list[AspectRelationship] = []
    for kind, ideal in ASPECT_IDEAL_ANGLES.items():
        orb = config.aspect_orbs_deg[kind]
        distance = circular_distance_deg(sep, ideal)
        aspects.append(
            AspectRelationship(
                kind=kind,
                exact_angle_deg=ideal,
                separation_deg=sep,
                distance_from_exact_deg=distance,
                within_orb=distance <= orb,
                orb_deg=orb,
                applying_separating=applying_separating(
                    first.longitude_used,
                    first.speed_longitude,
                    second.longitude_used,
                    second.speed_longitude,
                    ideal,
                    config.station_speed_epsilon,
                ),
            )
        )

    orb_config: dict[str, object] = {
        "conjunction": conjunction_orb,
        "aspects": {k.value: v for k, v in config.aspect_orbs_deg.items()},
    }

    return PairGeometry(
        first=first.body,
        second=second.body,
        separation_deg=sep,
        normalized_separation_deg=norm_sep,
        same_rashi=first.rashi == second.rashi,
        same_bhava=same_bhava,
        conjunction=conjunction,
        conjunction_distance_deg=sep,
        aspects=tuple(aspects),
        orb_config=orb_config,
        config_snapshot=config,
    )


def _same_bhava_flag(
    first: PlanetState, second: PlanetState, bhavas: tuple[Bhava, ...] | None
) -> bool | None:
    """Whether two bodies occupy the same bhava; None without a chart."""
    if bhavas is None:
        return None
    return any(
        first.body in bhava.occupants and second.body in bhava.occupants
        for bhava in bhavas
    )


def all_pairs(
    states: tuple[PlanetState, ...],
    config: JyotishConfig,
    bhavas: tuple[Bhava, ...] | None = None,
) -> tuple[PairGeometry, ...]:
    """All unordered pairs in canonical ``BodyId`` order (C(9,2) = 36 max).

    ``bhavas`` (when a chart exists) supplies the per-pair ``same_bhava``
    fact; generic mode passes ``None`` and the flag stays ``None``.
    """
    by_body: dict[BodyId, PlanetState] = {state.body: state for state in states}
    result: list[PairGeometry] = []
    for i, first in enumerate(_CANONICAL_ORDER):
        for second in _CANONICAL_ORDER[i + 1 :]:
            if first in by_body and second in by_body:
                result.append(
                    pair_geometry(
                        by_body[first],
                        by_body[second],
                        config,
                        same_bhava=_same_bhava_flag(by_body[first], by_body[second], bhavas),
                    )
                )
    return tuple(result)


def cusp_aspects_to_occupants(
    cusp_deg: float, occupant: PlanetState, config: JyotishConfig
) -> tuple[AspectRelationship, ...]:
    """Aspect relationships between a house cusp point and one occupant.

    The cusp is a fixed point (speed 0); separation uses the ecliptic arc so
    applying/separating is well defined for the moving occupant.
    """
    result: list[AspectRelationship] = []
    for kind, ideal in ASPECT_IDEAL_ANGLES.items():
        orb = config.aspect_orbs_deg[kind]
        arc = normalized_separation_deg(cusp_deg, occupant.longitude_used)
        distance = circular_distance_deg(arc, ideal)
        result.append(
            AspectRelationship(
                kind=kind,
                exact_angle_deg=ideal,
                separation_deg=normalized_separation_deg(cusp_deg, occupant.longitude_used),
                distance_from_exact_deg=distance,
                within_orb=distance <= orb,
                orb_deg=orb,
                applying_separating=applying_separating(
                    cusp_deg, 0.0, occupant.longitude_used, occupant.speed_longitude, ideal,
                    config.station_speed_epsilon,
                ),
            )
        )
    return tuple(result)
