"""Pure derivation functions for the JRE-005 Bhava / House engine.

Implements the normative formulas of Specialist Spec §9–§22 over the
JRE-003 public API only (ADR-013). JRE-003 values appear exclusively as
echoes (``echoed_from``); JRE-005 never recomputes positions, cusps,
spans, lagna, or geometry. All outputs are deterministic: ordering is
pinned in SPEC §27.
"""

from __future__ import annotations

import jyotish
from jyotish import (
    Bhava,
    BodyId,
    HouseSystem,
    NatalChart,
    PairGeometry,
    PlanetState,
    RashiId,
    TransitReferencePoint,
    TransitThroughHouses,
)

from .errors import InconsistentChartError, UnplacedBodyError
from .models import (
    CATEGORY_MEMBERS,
    GOLDEN_VERSION,
    AspectToHouseFact,
    BhavaConfig,
    BoundaryKind,
    ChartEcho,
    DerivationBlock,
    DerivationId,
    DerivedHouseFact,
    FactFrame,
    HouseAnalysis,
    HouseCategory,
    HouseOwnershipFact,
    OccupancyStatus,
    PlanetHouseFact,
    RelativeHouseFact,
    TransitHouseAnalysis,
    TransitHouseFact,
    UnplacedBodyBehavior,
    validate,
)

#: The four supported references in pinned declaration order (SPEC §27).
REFERENCE_ORDER: tuple[TransitReferencePoint, ...] = tuple(TransitReferencePoint)

#: Canonical body order (JRE-003 canonical: SUN..KETU) via public enum.
BODY_ORDER: tuple[BodyId, ...] = tuple(BodyId)
_BODY_RANK: dict[BodyId, int] = {body: i for i, body in enumerate(BODY_ORDER)}


# --------------------------------------------------------------------------- #
# Pure primitives (public, unit-testable — SPEC §4/S8)
# --------------------------------------------------------------------------- #


def shortest_arc_deg(a: float, b: float) -> float:
    """Wrap-aware shortest angular arc ``min(|a-b|, 360-|a-b|)`` (ADR-017)."""
    delta = abs(a - b) % 360.0
    return min(delta, 360.0 - delta)


def near_cusp(longitude_used_deg: float, start_deg: float, end_deg: float, orb_deg: float) -> bool:
    """Inclusive cusp-proximity test (SPEC §19): within ``orb_deg`` of either
    boundary of the house span."""
    return shortest_arc_deg(longitude_used_deg, start_deg) <= orb_deg or shortest_arc_deg(
        longitude_used_deg, end_deg
    ) <= orb_deg


def house_categories(house_number: int) -> tuple[HouseCategory, ...]:
    """Membership set in canonical enum order (SPEC §17); overlaps preserved."""
    return tuple(
        category
        for category in HouseCategory
        if house_number in CATEGORY_MEMBERS[category]
    )


def relative_house(house_of_b: int, house_of_r: int) -> int:
    """Pinned formula (ADR-014, SPEC §11.2): ``((B - R) mod 12) + 1``."""
    return ((house_of_b - house_of_r) % 12) + 1


def whole_sign_house(rashi: RashiId, lagna_rashi: RashiId) -> int:
    """Whole-sign house of a rashi from the lagna rashi (SPEC §10)."""
    return (
        (jyotish.RASHI_ORDER.index(rashi) - jyotish.RASHI_ORDER.index(lagna_rashi)) % 12
    ) + 1


# --------------------------------------------------------------------------- #
# Input validation (SPEC §8)
# --------------------------------------------------------------------------- #


def _validate_chart(chart: NatalChart, config: BhavaConfig) -> None:
    if len(chart.bhavas) != 12:
        raise InconsistentChartError(
            f"chart must have exactly 12 bhavas, got {len(chart.bhavas)}"
        )
    numbers = [bhava.house_number for bhava in chart.bhavas]
    if sorted(numbers) != list(range(1, 13)):
        raise InconsistentChartError(f"house numbers must be exactly 1..12, got {numbers}")
    if chart.lagna.rashi not in jyotish.RASHI_ORDER:
        raise InconsistentChartError(f"lagna rashi invalid: {chart.lagna.rashi!r}")
    if not chart.planet_states:
        raise InconsistentChartError("planet_states must be non-empty")
    bodies = [state.body for state in chart.planet_states]
    if len(set(bodies)) != len(bodies):
        raise InconsistentChartError(f"planet_states must have unique bodies, got {bodies}")
    if bodies != sorted(bodies, key=lambda b: _BODY_RANK[b]):
        raise InconsistentChartError(
            f"planet_states must be in canonical BodyId order, got {bodies}"
        )
    if chart.config.house_system not in config.house_systems:
        from .errors import InvalidBhavaConfigError

        raise InvalidBhavaConfigError(
            f"chart.config.house_system {chart.config.house_system.value} must be one of "
            f"BhavaConfig.house_systems {[s.value for s in config.house_systems]}"
        )


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _derivation(
    derivation_id: str,
    inputs: tuple[str, ...],
    config: BhavaConfig,
    house_system: HouseSystem,
) -> DerivationBlock:
    return DerivationBlock(
        id=derivation_id,
        derivation_version=config.derivation_version,
        inputs=inputs,
        source_catalog_versions={
            "rashi": jyotish.RASHI_CATALOG_VERSION,
            "nakshatra": jyotish.NAKSHATRA_CATALOG_VERSION,
        },
        house_system=house_system,
    )


def _state_for(chart: NatalChart, body: BodyId) -> PlanetState:
    for state in chart.planet_states:
        if state.body == body:
            return state
    raise InconsistentChartError(f"body {body.value} absent from chart.planet_states")


def _house_of(chart: NatalChart) -> dict[BodyId, int]:
    """Occupancy map: first bhava (ascending) listing the body (SPEC §13)."""
    house_of: dict[BodyId, int] = {}
    for bhava in chart.bhavas:
        for body in bhava.occupants:
            house_of.setdefault(body, bhava.house_number)
    return house_of


def _resolve_house_number(
    body: BodyId,
    house_of: dict[BodyId, int],
    chart: NatalChart,
    config: BhavaConfig,
    house_system: HouseSystem,
) -> tuple[int, DerivationId]:
    """House of a body with the pinned unplaced-body policy (ADR-018)."""
    if body in house_of:
        return house_of[body], DerivationId.PLANET_HOUSE_OCCUPANCY
    if config.unplaced_body_behavior is UnplacedBodyBehavior.RAISE:
        state = _state_for(chart, body)
        raise UnplacedBodyError(
            f"body {body.value} unplaced in {house_system.value}: "
            f"longitude_used {state.longitude_used}"
        )
    state = _state_for(chart, body)
    return (
        whole_sign_house(state.rashi, chart.lagna.rashi),
        DerivationId.PLANET_HOUSE_WHOLE_SIGN_FALLBACK,
    )


def _lord_of_house(house_number: int, chart: NatalChart) -> BodyId:
    """Echo of the occupied house's ``Bhava.house_lord`` (SPEC §13/§14)."""
    return chart.bhavas[house_number - 1].house_lord


def _boundary_kind(bhava: Bhava) -> BoundaryKind:
    """SIGN_BOUNDARY when the span starts exactly on the rashi boundary
    (SPEC §9/§10: exact float equality on ``30 * index`` values)."""
    index = jyotish.RASHI_ORDER.index(bhava.rashi)
    if bhava.start_deg == index * 30.0:
        return BoundaryKind.SIGN_BOUNDARY
    return BoundaryKind.COMPUTED_CUSP


def _reference_anchors(
    chart: NatalChart,
    house_of: dict[BodyId, int],
    config: BhavaConfig,
    house_system: HouseSystem,
    references: tuple[TransitReferencePoint, ...],
) -> dict[TransitReferencePoint, int]:
    """Absolute house of each reference anchor in the occupancy frame
    (SPEC §11.1): LAGNA/ASC -> 1; MOON/SUN -> the resolved house of that
    body (same fallback gating)."""
    anchors: dict[TransitReferencePoint, int] = {}
    for reference in references:
        if reference in (TransitReferencePoint.LAGNA, TransitReferencePoint.ASC):
            anchors[reference] = 1
            continue
        body = BodyId[reference.value]
        if any(state.body == body for state in chart.planet_states):
            house_number, _ = _resolve_house_number(body, house_of, chart, config, house_system)
            anchors[reference] = house_number
    return anchors


def _relative_house_by_reference(
    house_number: int,
    anchors: dict[TransitReferencePoint, int],
) -> dict[str, int]:
    """``{ref: relative_house(B, R)}`` in pinned reference order (SPEC §11)."""
    return {
        reference.value: relative_house(house_number, anchor)
        for reference, anchor in anchors.items()
    }


def _chart_echo(chart: NatalChart, config: BhavaConfig, house_system: HouseSystem) -> ChartEcho:
    return ChartEcho(
        house_system=house_system,
        jyotish_config=chart.config.to_dict(),
        provider_metadata=[metadata.to_dict() for metadata in chart.provider_metadata],
        rashi_catalog_version=jyotish.RASHI_CATALOG_VERSION,
        nakshatra_catalog_version=jyotish.NAKSHATRA_CATALOG_VERSION,
        anchor_frame=config.anchor_frame,
        sign_grid_frame_supported=False,
        cusp_proximity_orb_deg=config.cusp_proximity_orb_deg,
        unplaced_body_behavior=config.unplaced_body_behavior.value,
        tradition_profile=config.tradition_profile,
        derivation_version=config.derivation_version,
        golden_version=GOLDEN_VERSION,
    )


def _pair_key(a: BodyId, b: BodyId) -> tuple[BodyId, BodyId]:
    return (a, b) if _BODY_RANK[a] < _BODY_RANK[b] else (b, a)


def _aspect_rows(
    bhava: Bhava,
    pair_map: dict[tuple[BodyId, BodyId], PairGeometry],
    derivation: DerivationBlock,
    house_system: HouseSystem,
) -> tuple[AspectToHouseFact, ...]:
    """Geometric aspect-to-house aggregation (SPEC §20) — echo only.

    Two sources, both echoes:
    - ``Bhava.aspects`` (cusp-to-occupant); rows are emitted grouped by
      occupant (JRE-003 emits 7 kinds per occupant in canonical occupant
      order), attributed deterministically to ``target="CUSP"``.
    - ``PairGeometry.aspects`` (JRE-003 ``all_pairs``) for each occupant
      against every other body: ``target=<occupant>``.
    """
    rows: list[AspectToHouseFact] = []
    occupants = bhava.occupants
    house_number = bhava.house_number

    if occupants and bhava.aspects:
        per = len(bhava.aspects) // len(occupants)
        last = len(occupants) - 1
        for index, aspect in enumerate(bhava.aspects):
            rows.append(
                AspectToHouseFact(
                    house_system=house_system,
                    house_number=house_number,
                    target="CUSP",
                    source_body=occupants[min(index // per, last)],
                    kind=aspect.kind,
                    exact_angle_deg=aspect.exact_angle_deg,
                    distance_from_exact_deg=aspect.distance_from_exact_deg,
                    within_orb=aspect.within_orb,
                    applying_separating=aspect.applying_separating,
                    echoed_from="bhava.aspects",
                    derivation=derivation,
                )
            )

    if occupants:
        for occupant in occupants:
            occupant_value = occupant.value
            for other in BODY_ORDER:
                if other == occupant:
                    continue
                geometry = pair_map.get(_pair_key(occupant, other))
                if geometry is None:
                    continue
                for aspect in geometry.aspects:
                    rows.append(
                        AspectToHouseFact(
                            house_system=house_system,
                            house_number=house_number,
                            target=occupant_value,
                            source_body=other,
                            kind=aspect.kind,
                            exact_angle_deg=aspect.exact_angle_deg,
                            distance_from_exact_deg=aspect.distance_from_exact_deg,
                            within_orb=aspect.within_orb,
                            applying_separating=aspect.applying_separating,
                            echoed_from="pair_geometry",
                            derivation=derivation,
                        )
                    )
    return tuple(rows)


def _cusp_proximate_bodies(
    bhava: Bhava, chart: NatalChart, config: BhavaConfig
) -> tuple[BodyId, ...]:
    """Occupants within ``cusp_proximity_orb_deg`` of either cusp (SPEC §19)."""
    orb = config.cusp_proximity_orb_deg
    result: list[BodyId] = []
    for occupant in bhava.occupants:
        state = _state_for(chart, occupant)
        if near_cusp(state.longitude_used, bhava.start_deg, bhava.end_deg, orb):
            result.append(occupant)
    return tuple(result)


# --------------------------------------------------------------------------- #
# Natal derivation
# --------------------------------------------------------------------------- #


def derive_house_analysis(
    chart: NatalChart,
    config: BhavaConfig | None = None,
    references: tuple[TransitReferencePoint, ...] | None = None,
    pair_geometries: tuple[PairGeometry, ...] | None = None,
) -> HouseAnalysis:
    """Derive the per-system house analysis from one JRE-003 chart
    (SPEC §9–§21). ``references=None`` means all four in pinned order."""
    config = validate(config or BhavaConfig())
    refs = references or REFERENCE_ORDER
    _validate_chart(chart, config)
    house_system = chart.config.house_system

    house_of = _house_of(chart)
    anchors = _reference_anchors(chart, house_of, config, house_system, refs)
    body_order = tuple(state.body for state in chart.planet_states)

    # Planet-house facts (SPEC §13).
    planet_facts: list[PlanetHouseFact] = []
    for body in body_order:
        state = _state_for(chart, body)
        house_number, rule = _resolve_house_number(body, house_of, chart, config, house_system)
        sign_lord = jyotish.sign_lord_of(state.rashi)
        house_lord = _lord_of_house(house_number, chart)
        planet_facts.append(
            PlanetHouseFact(
                house_system=house_system,
                body=body,
                house_number=house_number,
                house_rule=rule.value,
                rashi=state.rashi,
                degree_in_rashi=state.degree_in_rashi,
                retrograde=state.retrograde,
                is_node=body in (BodyId.RAHU, BodyId.KETU),
                sign_lord=sign_lord,
                house_lord=house_lord,
                own_sign=sign_lord == body,
                own_house=house_lord == body,
                relative_house_by_reference=_relative_house_by_reference(house_number, anchors),
                echoed_from="planet_state",
                derivation=_derivation(
                    rule,
                    ("chart.bhavas", "chart.lagna", "chart.planet_states"),
                    config,
                    house_system,
                ),
            )
        )
    planet_by_body = {fact.body: fact for fact in planet_facts}

    # Pair geometry is computed once per analysis and shared across houses
    # (SPEC §30: no redundant recomputation). The caller may supply it
    # (SPEC §20: "supplied by the caller or computed by the service via
    # JRE-003 ``pair_geometry``") — the delegated JRE-003 computation is
    # excluded from the JRE-005 performance budget (SPEC §30).
    if pair_geometries is None:
        pair_geometries = jyotish.all_pairs(
            chart.planet_states, chart.config, bhavas=chart.bhavas
        )
    pair_map: dict[tuple[BodyId, BodyId], PairGeometry] = {
        _pair_key(geometry.first, geometry.second): geometry
        for geometry in pair_geometries
    }

    # Shared derivation blocks (fields identical across rows — SPEC §23).
    aspect_derivation = _derivation(
        DerivationId.ASPECT_TO_HOUSE_AGGREGATION,
        ("bhava.aspects", "bhava.occupants", "pair_geometry"),
        config,
        house_system,
    )
    house_derivation = _derivation(
        DerivationId.HOUSE_OCCUPANCY_STATUS, ("chart.bhavas", "chart.lagna"), config, house_system
    )
    ownership_derivation = _derivation(
        DerivationId.OWNERSHIP, ("chart.bhavas", "rashi_catalog"), config, house_system
    )
    relative_derivation = _derivation(
        DerivationId.RELATIVE_HOUSE, ("chart.bhavas", "chart.lagna"), config, house_system
    )

    # Derived house rows (SPEC §9–§12, §14, §17, §19, §20).
    derived_houses: list[DerivedHouseFact] = []
    for bhava in chart.bhavas:
        house_number = bhava.house_number
        occupied = bool(bhava.occupants)
        lord_placement = planet_by_body.get(bhava.house_lord)
        derived_houses.append(
            DerivedHouseFact(
                house_system=house_system,
                house_number=house_number,
                rashi=bhava.rashi,
                lord=bhava.house_lord,
                occupancy_status=OccupancyStatus.OCCUPIED if occupied else OccupancyStatus.EMPTY,
                occupants=bhava.occupants,
                categories=house_categories(house_number),
                start_deg=bhava.start_deg,
                end_deg=bhava.end_deg,
                boundary_kind=_boundary_kind(bhava),
                cusp_nakshatra=bhava.nakshatra,
                cusp_proximate_bodies=_cusp_proximate_bodies(bhava, chart, config),
                aspects_received=_aspect_rows(bhava, pair_map, aspect_derivation, house_system),
                lord_placement=lord_placement,
                echoed_from="bhava.house_lord",
                derivation=house_derivation,
            )
        )

    # Ownership facts (SPEC §15/§16).
    sign_lords: dict[RashiId, BodyId] = {
        rashi: jyotish.sign_lord_of(rashi) for rashi in jyotish.RASHI_ORDER
    }
    lorded_houses_by_body: dict[BodyId, list[int]] = {body: [] for body in BODY_ORDER}
    for bhava in chart.bhavas:
        lorded_houses_by_body[bhava.house_lord].append(bhava.house_number)
    ownership_facts = [
        HouseOwnershipFact(
            house_system=house_system,
            body=body,
            lorded_signs=tuple(rashi for rashi in jyotish.RASHI_ORDER if sign_lords[rashi] == body),
            lorded_houses=tuple(lorded_houses_by_body[body]),
            derivation=ownership_derivation,
        )
        for body in body_order
    ]

    # Relative-house table + rows (SPEC §11). References whose anchor body
    # is absent from the chart are omitted (mirrors JRE-004 semantics:
    # "a reference body absent from the chart yields no map").
    relative_house_table: dict[str, dict[str, int]] = {}
    relative_house_facts: list[RelativeHouseFact] = []
    for reference, anchor in anchors.items():
        table: dict[str, int] = {}
        for body in body_order:
            house_number, _ = _resolve_house_number(
                body, house_of, chart, config, house_system
            )
            value = relative_house(house_number, anchor)
            table[body.value] = value
            relative_house_facts.append(
                RelativeHouseFact(
                    house_system=house_system,
                    body=body,
                    reference=reference,
                    reference_absolute_house=anchor,
                    relative_house_number=value,
                    derivation=relative_derivation,
                )
            )
        relative_house_table[reference.value] = table

    # Empty/occupied summaries (SPEC §12; gated by ``include_empty_houses``).
    if config.include_empty_houses:
        empty_numbers = tuple(
            fact.house_number
            for fact in derived_houses
            if fact.occupancy_status is OccupancyStatus.EMPTY
        )
        occupied_numbers = tuple(
            fact.house_number
            for fact in derived_houses
            if fact.occupancy_status is OccupancyStatus.OCCUPIED
        )
        empty_count = len(empty_numbers)
    else:
        empty_numbers, occupied_numbers, empty_count = (), (), 0

    return HouseAnalysis(
        house_system=house_system,
        chart_echo=_chart_echo(chart, config, house_system),
        derived_houses=tuple(derived_houses),
        planet_house_facts=tuple(planet_facts),
        ownership_facts=tuple(ownership_facts),
        relative_house_table=relative_house_table,
        relative_house_facts=tuple(relative_house_facts),
        aspects_to_houses=tuple(
            aspect for fact in derived_houses for aspect in fact.aspects_received
        ),
        empty_house_numbers=empty_numbers,
        occupied_house_numbers=occupied_numbers,
        empty_house_count=empty_count,
        derivation=_derivation(
            DerivationId.HOUSE_OCCUPANCY_STATUS,
            ("chart.bhavas", "chart.lagna", "chart.planet_states"),
            config,
            house_system,
        ),
    )


# --------------------------------------------------------------------------- #
# Transit derivation (gochar scope v0.2.0 — ADR-021)
# --------------------------------------------------------------------------- #


def derive_transit_analysis(
    transit: TransitThroughHouses,
    natal_chart: NatalChart,
    config: BhavaConfig | None = None,
    references: tuple[TransitReferencePoint, ...] | None = None,
) -> TransitHouseAnalysis:
    """Derive gochar-frame facts from a JRE-003 transit and its natal chart
    (SPEC §22). The natal chart is a required input (the transit result does
    not embed the natal bhavas)."""
    config = validate(config or BhavaConfig())
    refs = references or REFERENCE_ORDER
    _validate_chart(natal_chart, config)
    house_system = natal_chart.config.house_system

    house_of = _house_of(natal_chart)
    anchors = _reference_anchors(natal_chart, house_of, config, house_system, refs)
    transit_states = {state.body: state for state in transit.planet_states}

    facts: list[TransitHouseFact] = []
    for entry in transit.entries:
        transit_state = transit_states.get(entry.body)
        if transit_state is None:
            raise InconsistentChartError(
                f"transit entry {entry.body.value} missing from transit.planet_states"
            )
        containing = jyotish.bhava_containing_longitude(
            natal_chart.bhavas, transit_state.longitude_used
        )
        if containing is not None:
            house_number = containing.house_number
            rule = DerivationId.PLANET_HOUSE_OCCUPANCY
        elif config.unplaced_body_behavior is UnplacedBodyBehavior.RAISE:
            raise UnplacedBodyError(
                f"body {entry.body.value} unplaced in natal frame of {house_system.value}: "
                f"longitude_used {transit_state.longitude_used}"
            )
        else:
            house_number = whole_sign_house(transit_state.rashi, natal_chart.lagna.rashi)
            rule = DerivationId.PLANET_HOUSE_WHOLE_SIGN_FALLBACK
        facts.append(
            TransitHouseFact(
                frame=FactFrame.TRANSIT,
                body=entry.body,
                natal_house_number=entry.natal_house_number,
                natal_house_rashi=entry.natal_house_rashi,
                natal_house_lord=entry.natal_house_lord,
                natal_occupants=entry.natal_occupants,
                aspects_to_natal=tuple(aspect.to_dict() for aspect in entry.aspects_to_natal),
                relative_house_by_reference=_relative_house_by_reference(house_number, anchors),
                echoed_from="transit_through_houses.entries",
                derivation=_derivation(
                    rule,
                    ("transit_through_houses.entries", "natal_chart.bhavas"),
                    config,
                    house_system,
                ),
            )
        )

    return TransitHouseAnalysis(
        birth_snapshot=transit.birth_snapshot,
        config=config,
        transit_instant_utc_iso=transit.transit_instant_utc_iso,
        reference=transit.reference,
        transit_facts=tuple(facts),
        chart_echo=_chart_echo(natal_chart, config, house_system),
        golden_version=GOLDEN_VERSION,
    )
