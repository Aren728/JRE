"""JRE-008 VargaService facade (normative specification §19).

``VargaService.compute_varga_chart`` is the canonical entry point: it
validates the varga id and optional method id, then assembles the
standalone deterministic ``VargaChart`` from the provided JRE-003
``PlanetState`` facts. It computes nothing beyond the pure derivation —
no positions, no ayanamsa, no ephemeris, no events.
"""

from __future__ import annotations

from jyotish import PlanetState

from .derive import assemble_varga_chart
from .errors import InvalidVargaRequestError
from .models import VargaChart, VargaConfig
from .registry import get_varga_definition


class VargaService:
    """Deterministic Varga computation facade."""

    def __init__(self, config: VargaConfig | None = None) -> None:
        self._config = config if config is not None else VargaConfig()

    @property
    def config(self) -> VargaConfig:
        return self._config

    def compute_varga_chart(
        self,
        states: tuple[PlanetState, ...],
        varga_id: str,
        *,
        method_id: str | None = None,
        context_chart_identity: str | None = None,
    ) -> VargaChart:
        """Compute the standalone Varga chart for ``varga_id`` from the
        provided JRE-003 planet states.

        ``method_id`` optionally selects a non-canonical method variant
        (e.g. ``d20-saravali-variant-v1``); the result carries that
        method's identity and is never merged with the canonical one.
        ``context_chart_identity`` is an opaque opt-in JRE-007 join
        reference.
        """
        if not isinstance(states, tuple) or not states:
            raise InvalidVargaRequestError(
                "states must be a non-empty tuple of PlanetState values"
            )
        for state in states:
            if not isinstance(state, PlanetState):
                raise InvalidVargaRequestError(
                    f"states must contain PlanetState values, got {type(state).__name__}"
                )
        definition = get_varga_definition(varga_id, method_id)
        selected = definition.calculation_method
        if context_chart_identity is not None and (
            not isinstance(context_chart_identity, str) or context_chart_identity == ""
        ):
            raise InvalidVargaRequestError(
                "context_chart_identity must be None or a non-empty string, "
                f"got {context_chart_identity!r}"
            )
        return assemble_varga_chart(
            states,
            definition,
            method=selected,
            context_chart_identity=context_chart_identity,
        )
