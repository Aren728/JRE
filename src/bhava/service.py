"""``BhavaService`` facade (SPEC §5) — a thin wrapper over the pure
derivations and the JRE-003 public API. Never recomputes positions,
cusps, spans, lagna, or geometry; never interprets.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from jyotish import (
    BirthData,
    HouseSystem,
    JyotishConfig,
    JyotishService,
    NatalChart,
    TransitReferencePoint,
    TransitThroughHouses,
)

from .derive import REFERENCE_ORDER, derive_house_analysis, derive_transit_analysis
from .errors import InvalidAnalysisRequestError, InvalidBhavaConfigError, UnsupportedReferenceError
from .models import (
    GOLDEN_VERSION,
    BhavaConfig,
    HouseAnalysis,
    HouseAnalysisResult,
    TransitHouseAnalysis,
    validate,
)


def _parse_systems(values: Any) -> tuple[HouseSystem, ...]:
    if isinstance(values, HouseSystem):
        values = (values,)
    if not isinstance(values, (tuple, list)):
        raise InvalidAnalysisRequestError(f"house_systems must be a sequence, got {values!r}")

    systems: list[HouseSystem] = []
    for value in values:
        if isinstance(value, HouseSystem):
            systems.append(value)
            continue
        try:
            systems.append(HouseSystem(value))
        except ValueError as exc:
            raise InvalidBhavaConfigError(f"unknown house_system value {value!r}") from exc
    return tuple(systems)


def _effective_config(
    config: BhavaConfig | None, house_systems: Any
) -> BhavaConfig:
    cfg = validate(config or BhavaConfig())
    if house_systems is not None:
        cfg = dataclasses.replace(cfg, house_systems=_parse_systems(house_systems))
        cfg = validate(cfg)
    return cfg


def _effective_references(
    references: tuple[TransitReferencePoint, ...] | list[TransitReferencePoint] | None,
) -> tuple[TransitReferencePoint, ...]:
    """Validate the requested references and emit them in the pinned
    declaration order (LAGNA, MOON, SUN, ASC); ``None`` means all four."""
    if references is None:
        return REFERENCE_ORDER
    if not references:
        raise InvalidAnalysisRequestError("references must be non-empty")
    requested = set()
    for reference in references:
        if not isinstance(reference, TransitReferencePoint):
            try:
                reference = TransitReferencePoint(reference)
            except ValueError as exc:
                raise UnsupportedReferenceError(
                    f"unsupported reference value {reference!r}"
                ) from exc
        requested.add(reference)
    return tuple(reference for reference in REFERENCE_ORDER if reference in requested)


class BhavaService:
    """Facade for the derived bhava/house layer (SPEC §5).

    ``analyze`` computes one JRE-003 chart per requested house system
    (ADR-015); ``analyze_chart`` derives from an existing chart;
    ``analyze_transit`` derives gochar-frame facts (ADR-021).
    """

    def __init__(self, jyotish_service: JyotishService | None = None) -> None:
        self._jyotish = jyotish_service or JyotishService()

    def analyze(
        self,
        birth: BirthData,
        house_systems: Any = None,
        references: tuple[TransitReferencePoint, ...] | None = None,
        config: BhavaConfig | None = None,
    ) -> HouseAnalysisResult:
        """One JRE-003 chart per ``house_systems`` entry; facts are never
        mixed across systems (ADR-015). JRE-003 errors (e.g.
        ``InvalidBirthDataError``) propagate unchanged."""
        cfg = _effective_config(config, house_systems)
        refs = _effective_references(references)
        analyses = []
        for system in cfg.house_systems:
            jyotish_config = dataclasses.replace(JyotishConfig(), house_system=system)
            chart = self._jyotish.chart(birth, jyotish_config)
            analyses.append(derive_house_analysis(chart, cfg, refs))
        return HouseAnalysisResult(
            birth_snapshot=birth,
            config=cfg,
            analyses=tuple(analyses),
            golden_version=GOLDEN_VERSION,
        )

    def analyze_chart(
        self,
        chart: NatalChart,
        references: tuple[TransitReferencePoint, ...] | None = None,
        config: BhavaConfig | None = None,
    ) -> HouseAnalysis:
        """Derive from an existing chart (no chart call)."""
        cfg = validate(config or BhavaConfig())
        refs = _effective_references(references)
        return derive_house_analysis(chart, cfg, refs)

    def analyze_transit(
        self,
        transit: TransitThroughHouses,
        natal_chart: NatalChart,
        references: tuple[TransitReferencePoint, ...] | None = None,
        config: BhavaConfig | None = None,
    ) -> TransitHouseAnalysis:
        """Gochar-frame facts (SPEC §22). The natal chart is a required
        input; natal (``NATAL``) and transit (``TRANSIT``) fact sets are
        never merged."""
        cfg = validate(config or BhavaConfig())
        refs = _effective_references(references)
        return derive_transit_analysis(transit, natal_chart, cfg, refs)
