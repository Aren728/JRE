"""Deterministic fake provider used by unit tests (no Swiss Ephemeris needed).

It also serves as the reference implementation of the ``EphemerisProvider``
contract for future providers.
"""

from __future__ import annotations

from astronomy.models import (
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    ProviderMetadata,
    ProviderRun,
    classify_retrograde,
)


class FakeProvider:
    """A fully deterministic stub provider for pipeline/registry tests."""

    provider_id = "fake"

    def __init__(self, provider_id: str = "fake") -> None:
        self.provider_id = provider_id
        self.metadata = ProviderMetadata(
            provider_id=self.provider_id,
            library_name="fake",
            library_version="0.0.1",
            ephemeris_version="fake",
        )
        self.calls: list[tuple[float, tuple[BodyId, ...], CalculationConfig]] = []

    def compute(
        self, jd_ut: float, bodies: tuple[BodyId, ...], config: CalculationConfig
    ) -> ProviderRun:
        self.calls.append((jd_ut, bodies, config))
        positions = tuple(
            BodyPosition(
                body=body,
                longitude_tropical=float(
                    (jd_ut + float(body.value.__hash__() if body.value else 0)) % 360
                ),
                longitude_sidereal=None if config.ayanamsa is None else float(
                    (jd_ut + float(body.value.__hash__() if body.value else 0)) % 360 - 24.0
                ),
                latitude=0.0,
                distance_au=1.0,
                speed_longitude=1.0,
                speed_latitude=0.0,
                speed_distance=0.0,
                retrograde=classify_retrograde(1.0),
                position_type=config.position_type,
                ayanamsa_value=24.0 if config.ayanamsa is not None else None,
            )
            for body in bodies
        )
        return ProviderRun(
            positions=positions,
            ephemeris_mode=config.ephemeris_mode,
            ephemeris_files=(
                ("sepl_18.se1", "semo_18.se1")
                if config.ephemeris_mode is EphemerisMode.SWIEPH
                else ()
            ),
        )
