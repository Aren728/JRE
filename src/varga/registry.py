"""JRE-008 V1 Varga registry (normative specification §12, §19-§22).

The frozen catalog of the 14 V1 Varga definitions. Every entry carries its
own varga-specific, versioned ``VargaCalculationMethod`` (never a generic
``parashara-v1`` identifier). D27 is deliberately absent (deferred — its
source/method divergence is unresolved). D20 carries two distinct methods
(``d20-bphs-v1`` canonical, ``d20-saravali-variant-v1`` variant) that
never merge. D30 is the explicit unequal five-band table; D60 is the
explicit BPHS remainder algorithm.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from jyotish import RashiId, ZodiacMode

from .errors import InvalidVargaRequestError
from .models import (
    VARGA_CATALOG_VERSION,
    VARGA_VERSION,
    BoundaryConvention,
    ExplicitTableParams,
    FixedStartParams,
    IntervalEntry,
    MappingStrategy,
    ModalityStartParams,
    OddEvenStartParams,
    RelativeModalityParams,
    SourceCitation,
    SubdivisionStrategy,
    VargaCalculationMethod,
    VargaDefinition,
)

# --------------------------------------------------------------------------- #
# Source citations (BPHS ch. 6 — R. Santhanam, Ranjan Publications, 1984;
# Saravali ch. 3 — same edition. Verified in the source-pinning research.)
# --------------------------------------------------------------------------- #

BPHS = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="5-6",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D3 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="7-8",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D4 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="9",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D7 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="10-11",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D9 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="12",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D10 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="13-14",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D12 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="15",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D16 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="16",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D20 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="17-21",
    edition=(
        "Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984; "
        "Sanskrit: cara-rashau meshadi, sthirah dhanuradi, dvisvabhavah simhadi"
    ),
)
SARAVALI_D20 = SourceCitation(
    text="SARAVALI",
    chapter="3",
    verse_range="note",
    edition=(
        "Saravali of Kalyana Varma, R. Santhanam translation (Vimsamsa note: "
        "movable from Aries, dual from Sagittarius, common from Leo)"
    ),
)
BPHS_D24 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="22-23",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D30 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="27-28",
    edition=(
        "Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984; "
        "Speculum of Trimsamsas"
    ),
)
BPHS_D40 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="29-30",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D45 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="31-32",
    edition="Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984",
)
BPHS_D60 = SourceCitation(
    text="BPHS",
    chapter="6",
    verse_range="33-41",
    edition=(
        "Brihat Parashara Hora Shastra, R. Santhanam, Ranjan Publications, 1984; "
        "worked example: Capricorn 13d25m -> Pisces (lord Jupiter); "
        "odd/even reversal applies to the shashtiamsa NAMES only, not sign "
        "positions; Phaladeepika differs only in the names list; modern "
        "even-sign 'from the 9th'/'from the 7th' readings are not "
        "source-pinned and are not implemented"
    ),
)

# --------------------------------------------------------------------------- #
# D30 explicit unequal five-band table (§21 — source-backed, never inferred)
# --------------------------------------------------------------------------- #

_D30_ODD_BANDS = (
    IntervalEntry(lower_deg=0.0, upper_deg=5.0, destination=RashiId.MESHA),
    IntervalEntry(lower_deg=5.0, upper_deg=10.0, destination=RashiId.KUMBHA),
    IntervalEntry(lower_deg=10.0, upper_deg=18.0, destination=RashiId.DHANUSHA),
    IntervalEntry(lower_deg=18.0, upper_deg=25.0, destination=RashiId.MITHUNA),
    IntervalEntry(lower_deg=25.0, upper_deg=30.0, destination=RashiId.TULA),
)
_D30_EVEN_BANDS = (
    IntervalEntry(lower_deg=0.0, upper_deg=5.0, destination=RashiId.VRISHABHA),
    IntervalEntry(lower_deg=5.0, upper_deg=12.0, destination=RashiId.KANYA),
    IntervalEntry(lower_deg=12.0, upper_deg=20.0, destination=RashiId.MEENA),
    IntervalEntry(lower_deg=20.0, upper_deg=25.0, destination=RashiId.MAKARA),
    IntervalEntry(lower_deg=25.0, upper_deg=30.0, destination=RashiId.VRISHCHIKA),
)


# --------------------------------------------------------------------------- #
# Method constructors
# --------------------------------------------------------------------------- #


def _method(
    method_id: str,
    varga_id: str,
    subdivision: SubdivisionStrategy,
    mapping: MappingStrategy,
    params: object,
    sources: tuple[SourceCitation, ...],
) -> VargaCalculationMethod:
    return VargaCalculationMethod(
        method_id=method_id,
        version="1",
        subdivision_strategy=subdivision,
        mapping_strategy=mapping,
        mapping_parameters=params,  # type: ignore[arg-type]  # narrowed by each caller
        boundary_convention=BoundaryConvention.HALF_OPEN_LOW,
        source_references=sources,
        applicable_varga=varga_id,
    )


def _definition(
    varga_id: str,
    name: str,
    division_number: int,
    method: VargaCalculationMethod,
    zodiac_mode: str,
    ayanamsa: str | None,
) -> VargaDefinition:
    return VargaDefinition(
        varga_id=varga_id,
        canonical_name=name,
        division_number=division_number,
        calculation_method=method,
        zodiac_mode=zodiac_mode,
        ayanamsa=ayanamsa,
        boundary_convention=BoundaryConvention.HALF_OPEN_LOW,
        tradition_profile=None,
        version=VARGA_VERSION,
        source_citations=method.source_references,
        catalog_version=VARGA_CATALOG_VERSION,
    )


#: Default zodiac/ayanamsa echoes (from the JRE-003 defaults: SIDEREAL/LAHIRI).
_ZODIAC = ZodiacMode.SIDEREAL.value
_AYANAMSA = "LAHIRI"

_V1_DEFINITIONS: dict[str, VargaDefinition] = {
    "D2": _definition(
        "D2",
        "HORA",
        2,
        _method(
            "d2-bphs-v1",
            "D2",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.SPECIALIZED,
            FixedStartParams(
                odd_start=RashiId.SIMHA, even_start=RashiId.KARKA, hora=True
            ),
            (BPHS,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D3": _definition(
        "D3",
        "DREKKANA",
        3,
        _method(
            "d3-bphs-v1",
            "D3",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.TRINAL_SEQUENCE,
            FixedStartParams(self_start=True),
            (BPHS_D3,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D4": _definition(
        "D4",
        "CHATURTHAMSA",
        4,
        _method(
            "d4-bphs-v1",
            "D4",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.KENDRA_SEQUENCE,
            FixedStartParams(self_start=True),
            (BPHS_D4,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D7": _definition(
        "D7",
        "SAPTAMSA",
        7,
        _method(
            "d7-bphs-v1",
            "D7",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.ODD_EVEN_START,
            OddEvenStartParams(odd_offset=0, even_offset=6),
            (BPHS_D7,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D9": _definition(
        "D9",
        "NAVAMSA",
        9,
        _method(
            "d9-bphs-v1",
            "D9",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.MODALITY_START,
            RelativeModalityParams(movable_offset=0, fixed_offset=8, dual_offset=4),
            (BPHS_D9,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D10": _definition(
        "D10",
        "DASAMSA",
        10,
        _method(
            "d10-bphs-v1",
            "D10",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.ODD_EVEN_START,
            OddEvenStartParams(odd_offset=0, even_offset=8),
            (BPHS_D10,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D12": _definition(
        "D12",
        "DWADASHAMSA",
        12,
        _method(
            "d12-bphs-v1",
            "D12",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.SELF_SEQUENCE,
            FixedStartParams(self_start=True),
            (BPHS_D12,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D16": _definition(
        "D16",
        "SHODASAMSA",
        16,
        _method(
            "d16-bphs-v1",
            "D16",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.MODALITY_START,
            ModalityStartParams(
                movable_start=RashiId.MESHA,
                fixed_start=RashiId.SIMHA,
                dual_start=RashiId.DHANUSHA,
            ),
            (BPHS_D16,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D20": _definition(
        "D20",
        "VIMSAMSA",
        20,
        _method(
            "d20-bphs-v1",
            "D20",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.MODALITY_START,
            ModalityStartParams(
                movable_start=RashiId.MESHA,
                fixed_start=RashiId.DHANUSHA,
                dual_start=RashiId.SIMHA,
            ),
            (BPHS_D20,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D24": _definition(
        "D24",
        "CHATURVIMSAMSA",
        24,
        _method(
            "d24-bphs-v1",
            "D24",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.ODD_EVEN_START,
            OddEvenStartParams(odd_start=RashiId.SIMHA, even_start=RashiId.KARKA),
            (BPHS_D24,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D30": _definition(
        "D30",
        "TRIMSAMSA",
        30,
        _method(
            "d30-bphs-v1",
            "D30",
            SubdivisionStrategy.UNEQUAL_TABLE,
            MappingStrategy.EXPLICIT_TABLE,
            ExplicitTableParams(odd_bands=_D30_ODD_BANDS, even_bands=_D30_EVEN_BANDS),
            (BPHS_D30,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D40": _definition(
        "D40",
        "KHAVEDAMSA",
        40,
        _method(
            "d40-bphs-v1",
            "D40",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.ODD_EVEN_START,
            OddEvenStartParams(odd_start=RashiId.MESHA, even_start=RashiId.TULA),
            (BPHS_D40,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D45": _definition(
        "D45",
        "AKSHAVEDAMSA",
        45,
        _method(
            "d45-bphs-v1",
            "D45",
            SubdivisionStrategy.UNIFORM,
            MappingStrategy.MODALITY_START,
            ModalityStartParams(
                movable_start=RashiId.MESHA,
                fixed_start=RashiId.SIMHA,
                dual_start=RashiId.DHANUSHA,
            ),
            (BPHS_D45,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
    "D60": _definition(
        "D60",
        "SHASTHIAMSA",
        60,
        _method(
            "d60-bphs-v1",
            "D60",
            SubdivisionStrategy.SPECIALIZED,
            MappingStrategy.SPECIALIZED,
            FixedStartParams(remainder=True),
            (BPHS_D60,),
        ),
        _ZODIAC,
        _AYANAMSA,
    ),
}

#: The D20 Saravali-variant method (distinct identity; never merged with
#: ``d20-bphs-v1``; non-canonical).
_D20_SARAVALI_METHOD = _method(
    "d20-saravali-variant-v1",
    "D20",
    SubdivisionStrategy.UNIFORM,
    MappingStrategy.MODALITY_START,
    ModalityStartParams(
        movable_start=RashiId.MESHA,
        fixed_start=RashiId.SIMHA,
        dual_start=RashiId.DHANUSHA,
    ),
    (BPHS_D20, SARAVALI_D20),
)

#: Immutable registry of the 14 V1 definitions (deterministic, frozen).
VARGA_REGISTRY: Mapping[str, VargaDefinition] = MappingProxyType(dict(_V1_DEFINITIONS))

#: Method variants by varga id (only D20 in V1).
_VARIANTS: dict[str, tuple[VargaCalculationMethod, ...]] = {
    "D20": (_D20_SARAVALI_METHOD,),
}


def get_varga_definition(
    varga_id: str, method_id: str | None = None
) -> VargaDefinition:
    """Return the frozen definition for ``varga_id``, optionally selecting
    a specific method. Unknown ids/methods raise ``InvalidVargaRequestError``.

    The returned definition always carries the *selected* method — for a
    variant request, a new definition object is assembled with the variant
    method (same identity fields otherwise), so the variant's identity
    differs from the canonical one.
    """
    if varga_id not in VARGA_REGISTRY:
        raise InvalidVargaRequestError(
            f"unknown varga {varga_id!r}; frozen V1 varga ids: {list(VARGA_REGISTRY)}"
        )
    definition = VARGA_REGISTRY[varga_id]
    if method_id is None or method_id == definition.calculation_method.method_id:
        return definition
    for variant in _VARIANTS.get(varga_id, ()):
        if variant.method_id == method_id:
            return VargaDefinition(
                varga_id=definition.varga_id,
                canonical_name=definition.canonical_name,
                division_number=definition.division_number,
                calculation_method=variant,
                zodiac_mode=definition.zodiac_mode,
                ayanamsa=definition.ayanamsa,
                boundary_convention=definition.boundary_convention,
                tradition_profile=definition.tradition_profile,
                version=definition.version,
                source_citations=variant.source_references,
                catalog_version=definition.catalog_version,
            )
    available = [definition.calculation_method.method_id] + [
        v.method_id for v in _VARIANTS.get(varga_id, ())
    ]
    raise InvalidVargaRequestError(
        f"unknown method {method_id!r} for varga {varga_id!r}; available: {available}"
    )


def canonical_method_id(varga_id: str) -> str:
    """The canonical (default) method id for a V1 varga."""
    if varga_id not in VARGA_REGISTRY:
        raise InvalidVargaRequestError(f"unknown varga {varga_id!r}")
    return VARGA_REGISTRY[varga_id].calculation_method.method_id


def available_method_ids(varga_id: str) -> tuple[str, ...]:
    """All method ids (canonical + variants) available for a V1 varga."""
    if varga_id not in VARGA_REGISTRY:
        raise InvalidVargaRequestError(f"unknown varga {varga_id!r}")
    definition = VARGA_REGISTRY[varga_id]
    variants = tuple(v.method_id for v in _VARIANTS.get(varga_id, ()))
    return (definition.calculation_method.method_id,) + variants
