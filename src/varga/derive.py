"""JRE-008 pure Varga derivation (normative specification §8-§11, §21-§22).

All calculation is a pure function of a JRE-003 ``PlanetState`` fact and a
``VargaDefinition``. No position recalculation, no ayanamsa, no ephemeris,
no epsilon/tolerance math: division boundaries are exact rationals of the
decimal degree value, and segment membership uses the frozen
``HALF_OPEN_LOW`` convention ([lower, upper)).

Three subdivision strategies are supported (UNIFORM / UNEQUAL_TABLE /
SPECIALIZED) and the full set of source-pinned mapping strategies. D30 is
the explicit five-band table; D60 is the BPHS remainder algorithm
preserved for auditability.
"""

from __future__ import annotations

from fractions import Fraction

from jyotish import BodyId, PlanetState, RashiId

from .errors import InvalidVargaRequestError
from .models import (
    BoundaryConvention,
    ExplicitTableParams,
    FixedStartParams,
    IntervalEntry,
    MappingStrategy,
    ModalityStartParams,
    OddEvenStartParams,
    RelativeModalityParams,
    SubdivisionStrategy,
    VargaCalculationMethod,
    VargaChart,
    VargaDefinition,
    VargaPosition,
    VargaProvenance,
    compute_position_identity,
    source_state_identity,
    varga_chart_identity,
    varga_definition_identity,
)

#: Canonical zodiacal order (RashiId declaration order == zodiacal order).
_RASHI_ORDER: tuple[RashiId, ...] = tuple(RashiId)


def rashi_index(rashi: RashiId) -> int:
    """The zodiacal index (Aries=0 .. Pisces=11) of a RashiId."""
    return _RASHI_ORDER.index(rashi)


def sign_at(index: int) -> RashiId:
    """The RashiId at a zodiacal index (mod 12)."""
    return _RASHI_ORDER[index % 12]


def _is_odd(rashi: RashiId) -> bool:
    return rashi_index(rashi) % 2 == 0


def _is_movable(rashi: RashiId) -> bool:
    return rashi_index(rashi) % 3 == 0


def _is_fixed(rashi: RashiId) -> bool:
    return rashi_index(rashi) % 3 == 1


def _is_dual(rashi: RashiId) -> bool:
    return rashi_index(rashi) % 3 == 2


def _rashi_from_str(raw: str | None, what: str) -> RashiId:
    if raw is None:
        raise InvalidVargaRequestError(f"{what} start sign is required, got None")
    try:
        return RashiId(raw)
    except ValueError as exc:
        raise InvalidVargaRequestError(f"invalid {what} start sign {raw!r}") from exc


# --------------------------------------------------------------------------- #
# Subdivision (exact rational; §11)
# --------------------------------------------------------------------------- #


def _uniform_segment(
    degree: Fraction, division_count: int
) -> tuple[int, float, float]:
    """Division index (1-based) and segment bounds for a uniform division.

    Exact rational boundary mechanism: segment size = Fraction(30, n) and
    the index is floor(degree / segment) + 1 — computed in exact rational
    arithmetic so an exact boundary belongs to the *lower* (new) division
    under HALF_OPEN_LOW. No epsilon, no tolerance, no snapping.
    """
    if division_count <= 0:
        raise InvalidVargaRequestError(
            f"division_count must be positive, got {division_count!r}"
        )
    segment = Fraction(30, division_count)
    index = int(degree // segment) + 1
    index = min(index, division_count)  # degree < 30 guaranteed; defensive
    lower = float(segment * (index - 1))
    upper = float(segment * index)
    return index, lower, upper


def _table_segment(
    degree: Fraction,
    bands: tuple[IntervalEntry, ...],
) -> tuple[int, float, float]:
    """Division index and bounds for an explicit unequal table (D30)."""
    for position, band in enumerate(bands):
        lower = Fraction(band.lower_deg)
        upper = Fraction(band.upper_deg)
        if lower <= degree < upper:
            return position + 1, float(lower), float(upper)
    raise InvalidVargaRequestError(
        f"degree {float(degree)!r} does not fall in any table band"
    )


def _d60_segment(degree: Fraction) -> tuple[int, float, float]:
    """D60 (BPHS §22): 60 segments of exactly 30' — the same uniform
    subdivision as UNIFORM with n=60, expressed explicitly."""
    return _uniform_segment(degree, 60)


# --------------------------------------------------------------------------- #
# Sign mapping (§9)
# --------------------------------------------------------------------------- #


def _modality_offset(rashi: RashiId, params: ModalityStartParams) -> int:
    """Absolute modality start (D16/D20/D45): offset from the source sign
    to the fixed start sign (Aries/Leo/Sagittarius family)."""
    if _is_movable(rashi):
        start = params.movable_start
    elif _is_fixed(rashi):
        start = params.fixed_start
    else:
        start = params.dual_start
    start_index = rashi_index(_rashi_from_str(start.value, "modality"))
    return (start_index - rashi_index(rashi)) % 12


def _relative_modality_offset(rashi: RashiId, params: RelativeModalityParams) -> int:
    """Relative modality start (D9, BPHS ch. 6 v.12): zodiacal offset from
    the source sign — movable +0, fixed +8 (9th), dual +4 (5th)."""
    if _is_movable(rashi):
        return params.movable_offset
    if _is_fixed(rashi):
        return params.fixed_offset
    return params.dual_offset


def _odd_even_offset(
    rashi: RashiId, params: OddEvenStartParams, source_index: int
) -> int:
    """Per-parity start: relative offsets from the source sign (D7/D10) or
    absolute start signs (D24: Leo/Cancer; D40: Aries/Libra)."""
    if params.odd_start is not None or params.even_start is not None:
        start = params.odd_start if _is_odd(rashi) else params.even_start
        assert start is not None
        return (rashi_index(_rashi_from_str(start.value, "odd/even")) - source_index) % 12
    assert params.odd_offset is not None and params.even_offset is not None
    return params.odd_offset if _is_odd(rashi) else params.even_offset


def _fixed_offset(rashi: RashiId, params: FixedStartParams, source_index: int) -> int:
    if params.remainder:
        raise InvalidVargaRequestError("remainder mapping requires the D60 specialized path")
    if params.self_start:
        return 0
    start = params.odd_start if _is_odd(rashi) else params.even_start
    if start is None:
        raise InvalidVargaRequestError(
            f"fixed start sign is undefined for {rashi.value!r}"
        )
    start_index = rashi_index(_rashi_from_str(start.value, "fixed"))
    return (start_index - source_index) % 12


def _map_sign(
    rashi: RashiId,
    division_index: int,
    method: VargaCalculationMethod,
    degree: Fraction,
) -> RashiId:
    """Map (source sign, division index) to the resulting varga sign."""
    strategy = method.mapping_strategy
    params = method.mapping_parameters
    source_index = rashi_index(rashi)
    if strategy is MappingStrategy.MODALITY_START:
        if isinstance(params, ModalityStartParams):
            offset = _modality_offset(rashi, params)
        elif isinstance(params, RelativeModalityParams):
            offset = _relative_modality_offset(rashi, params)
        else:
            raise InvalidVargaRequestError(
                "MODALITY_START requires ModalityStartParams or RelativeModalityParams"
            )
    elif strategy is MappingStrategy.ODD_EVEN_START:
        assert isinstance(params, OddEvenStartParams)
        offset = _odd_even_offset(rashi, params, source_index)
    elif strategy is MappingStrategy.TRINAL_SEQUENCE:
        # Drekkana (BPHS ch. 6 v.7-8 + Speculum): 1st -> same sign,
        # 2nd -> 4th from it (+4), 3rd -> 8th from it (+8), for ALL
        # signs. Absolute offsets from the source sign (the speculum
        # lists 1/5/9 etc. counting the source as 1).
        offset = {1: 0, 2: 4, 3: 8}[division_index]
        return sign_at(source_index + offset)
    elif strategy is MappingStrategy.KENDRA_SEQUENCE:
        # Chaturthamsa (BPHS ch. 6 v.9 + Speculum): 1st -> same sign,
        # 2nd -> 4th from it (+3), 3rd -> 7th from it (+6), 4th -> 10th
        # from it (+9), for ALL signs. Absolute offsets from the source.
        offset = {1: 0, 2: 3, 3: 6, 4: 9}[division_index]
        return sign_at(source_index + offset)
    elif strategy is MappingStrategy.SELF_SEQUENCE:
        # Dwadashamsa (BPHS ch. 6 v.15 + Speculum): the 12 divisions
        # fall successively in the 12 signs from the sign in question
        # for ALL signs (Santhanam BPHS; the "even signs from the 9th"
        # reading is not source-pinned and is not implemented).
        offset = 0
    elif strategy is MappingStrategy.FIXED_START:
        assert isinstance(params, FixedStartParams)
        offset = _fixed_offset(rashi, params, source_index)
    elif strategy is MappingStrategy.EXPLICIT_TABLE:
        assert isinstance(params, ExplicitTableParams)
        bands = params.odd_bands if _is_odd(rashi) else params.even_bands
        for band in bands:
            if Fraction(band.lower_deg) <= degree < Fraction(band.upper_deg):
                return band.destination
        raise InvalidVargaRequestError(
            f"degree {float(degree)!r} does not fall in any {rashi.value!r} D30 band"
        )
    elif strategy is MappingStrategy.SPECIALIZED:
        assert isinstance(params, FixedStartParams)
        if params.remainder:
            # D60 remainder algorithm (BPHS ch. 6 v.33-41; §22): multiply
            # the degree by 2, take (remainder mod 12) + 1, and count
            # forward from the source sign for BOTH odd and even signs.
            # The BPHS worked example is decisive: Venus at Capricorn
            # 13°25' (an even sign) -> 26°50' -> remainder 2 -> +1 = 3
            # -> count 3 from Capricorn -> Pisces. The odd/even reversal
            # in BPHS applies only to the shashtiamsa NAMES (a lordship
            # table, out of JRE-008 scope), not to sign positions. Modern
            # "from the 9th"/"from the 7th" even-sign readings are not
            # source-pinned and are NOT implemented.
            doubled = degree * 2
            remainder = doubled % 12
            count = int(remainder) + 1
            return sign_at(source_index + count - 1)
        if params.hora:
            # D2 hora (BPHS ch. 6 v.5-6 + Speculum of Horas): the result
            # is always one of the fixed pair — the first half of an odd
            # sign is Leo, the second half Cancer; the reverse for an even
            # sign. No zodiacal advancement.
            assert params.odd_start is not None and params.even_start is not None
            if _is_odd(rashi) == (division_index == 1):
                return params.odd_start
            return params.even_start
        raise InvalidVargaRequestError(
            "SPECIALIZED mapping requires remainder=True or hora=True"
        )
    else:  # ELEMENT_START — no V1 varga uses it (D27 deferred).
        raise InvalidVargaRequestError(
            f"mapping strategy {strategy.value!r} has no V1 implementation"
        )
    return sign_at(source_index + offset + (division_index - 1))


# --------------------------------------------------------------------------- #
# Position / chart assembly
# --------------------------------------------------------------------------- #


def compute_varga_position(
    state: PlanetState,
    definition: VargaDefinition,
    method: VargaCalculationMethod | None = None,
) -> VargaPosition:
    """Compute one deterministic ``VargaPosition`` from a JRE-003 state."""
    selected = method if method is not None else definition.calculation_method
    if selected.applicable_varga != definition.varga_id:
        raise InvalidVargaRequestError(
            f"method {selected.method_id!r} applies to varga "
            f"{selected.applicable_varga!r}, not {definition.varga_id!r}"
        )
    if definition.boundary_convention is not BoundaryConvention.HALF_OPEN_LOW:
        raise InvalidVargaRequestError(
            f"boundary_convention must be {BoundaryConvention.HALF_OPEN_LOW.value}, "
            f"got {definition.boundary_convention.value!r}"
        )
    degree_f = state.degree_in_rashi
    if not (0.0 <= degree_f < 30.0):
        raise InvalidVargaRequestError(
            "degree_in_rashi must be in [0, 30) (JRE-003 normalization), "
            f"got {degree_f!r}"
        )
    # Exact decimal rational of the JRE-003 value (the shortest decimal
    # that round-trips to the float). NO approximation: a nearest-rational
    # snap (e.g. ``limit_denominator``) could move a just-below-boundary
    # value onto the boundary, violating HALF_OPEN_LOW (§10).
    degree = Fraction(str(degree_f))

    subdivision = selected.subdivision_strategy
    if subdivision is SubdivisionStrategy.UNIFORM:
        index, lower, upper = _uniform_segment(degree, definition.division_number)
    elif subdivision is SubdivisionStrategy.UNEQUAL_TABLE:
        params = selected.mapping_parameters
        assert isinstance(params, ExplicitTableParams)
        bands = params.odd_bands if _is_odd(state.rashi) else params.even_bands
        index, lower, upper = _table_segment(degree, bands)
    elif subdivision is SubdivisionStrategy.SPECIALIZED:
        params = selected.mapping_parameters
        if isinstance(params, FixedStartParams) and params.remainder:
            index, lower, upper = _d60_segment(degree)
        else:
            # D2: uniform 2-band subdivision.
            index, lower, upper = _uniform_segment(degree, definition.division_number)
    else:  # pragma: no cover - enum is exhaustive
        raise InvalidVargaRequestError(
            f"subdivision strategy {subdivision.value!r} has no V1 implementation"
        )

    varga_sign = _map_sign(state.rashi, index, selected, degree)
    source_id = source_state_identity(state)
    provenance = VargaProvenance(
        source_state_id=source_id,
        provider_id=state.provider_id,
        ephemeris_version=state.ephemeris_version,
        varga_method_id=selected.method_id,
        varga_method_version=selected.version,
        varga_definition_version=definition.version,
        source_citations=selected.source_references,
        tradition_profile=definition.tradition_profile,
        boundary_convention=definition.boundary_convention,
        input_rashi=state.rashi,
        input_degree_in_rashi=state.degree_in_rashi,
    )
    position_id = compute_position_identity(
        body=state.body,
        source_state_id=source_id,
        source_degree_in_rashi=state.degree_in_rashi,
        source_rashi=state.rashi,
        longitude_used=state.longitude_used,
        division_index=index,
        segment_lower_deg=lower,
        segment_upper_deg=upper,
        varga_sign=varga_sign,
        varga_id=definition.varga_id,
        method_id=selected.method_id,
        definition_version=definition.version,
        provenance=provenance,
    )
    return VargaPosition(
        body=state.body,
        source_state_id=source_id,
        source_degree_in_rashi=state.degree_in_rashi,
        source_rashi=state.rashi,
        longitude_used=state.longitude_used,
        division_index=index,
        segment_lower_deg=lower,
        segment_upper_deg=upper,
        varga_sign=varga_sign,
        varga_id=definition.varga_id,
        method_id=selected.method_id,
        definition_version=definition.version,
        provenance=provenance,
        position_id=position_id,
    )


def canonical_body_order(states: tuple[PlanetState, ...]) -> tuple[PlanetState, ...]:
    """Return states in JRE-003 canonical ``BodyId`` order, deduplicated
    (deterministic ordering)."""
    by_body: dict[BodyId, PlanetState] = {}
    for state in states:
        by_body[state.body] = state
    return tuple(by_body[body] for body in tuple(BodyId) if body in by_body)


def assemble_varga_chart(
    states: tuple[PlanetState, ...],
    definition: VargaDefinition,
    method: VargaCalculationMethod | None = None,
    context_chart_identity: str | None = None,
) -> VargaChart:
    """Assemble the standalone ``VargaChart`` for one definition."""
    if not states:
        raise InvalidVargaRequestError("varga chart requires at least one planet state")
    selected = method if method is not None else definition.calculation_method
    positions = tuple(
        compute_varga_position(state, definition, selected)
        for state in canonical_body_order(states)
    )
    definition_id = varga_definition_identity(definition)
    chart = VargaChart(
        varga_id=definition.varga_id,
        method_id=selected.method_id,
        definition_version=definition.version,
        positions=positions,
        varga_definition_identity=definition_id,
        varga_chart_identity="",
        context_chart_identity=context_chart_identity,
        provenance=positions[0].provenance,
    )
    chart_id = varga_chart_identity(chart)
    return VargaChart(
        varga_id=chart.varga_id,
        method_id=chart.method_id,
        definition_version=chart.definition_version,
        positions=chart.positions,
        varga_definition_identity=chart.varga_definition_identity,
        varga_chart_identity=chart_id,
        context_chart_identity=chart.context_chart_identity,
        provenance=chart.provenance,
    )
