"""JRE-020 MuhurtaService facade.

``MuhurtaService.evaluate_window`` is the canonical entry point:
it evaluates the structural fitness of a specific time window
for a classical Muhurta category.

It produces NO qualitative output.
"""

from __future__ import annotations

from .config import load_config
from .errors import InvalidMuhurtaRequestError
from .models import (
    MuhurtaCategory,
    MuhurtaConfig,
    MuhurtaEvaluation,
    MuhurtaWindow,
    PanchangaState,
    compute_fitness_score,
    evaluate_panchanga,
)


class MuhurtaService:
    """Deterministic Muhurta (Electional) evaluation facade."""

    def __init__(self, config: MuhurtaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> MuhurtaConfig:
        return self._config

    def evaluate_window(
        self,
        window: MuhurtaWindow,
        category: MuhurtaCategory,
        panchanga: PanchangaState,
    ) -> MuhurtaEvaluation:
        """Evaluate a time window for a specific Muhurta category.

        Parameters
        ----------
        window : MuhurtaWindow
            The time window to evaluate.
        category : MuhurtaCategory
            The electional category.
        panchanga : PanchangaState
            The Panchanga state at the window start.

        Returns
        -------
        MuhurtaEvaluation
            Structural flags and fitness score.
        """
        self._validate_request(window, category, panchanga)

        # Evaluate structural flags
        flags = evaluate_panchanga(panchanga, category, self._config)

        # Compute fitness score
        score = compute_fitness_score(flags, category, self._config)

        return MuhurtaEvaluation(
            window=window,
            panchanga=panchanga,
            structural_flags=flags,
            fitness_score=score,
            category=category,
        )

    def _validate_request(
        self,
        window: MuhurtaWindow,
        category: MuhurtaCategory,
        panchanga: PanchangaState,
    ) -> None:
        """Validate the Muhurta evaluation request."""
        if not isinstance(window, MuhurtaWindow):
            raise InvalidMuhurtaRequestError(
                f"window must be a MuhurtaWindow, got {type(window).__name__}"
            )
        if not isinstance(window.start_utc, str) or window.start_utc == "":
            raise InvalidMuhurtaRequestError(
                "window.start_utc must be a non-empty string"
            )
        if not isinstance(window.end_utc, str) or window.end_utc == "":
            raise InvalidMuhurtaRequestError(
                "window.end_utc must be a non-empty string"
            )
        if not isinstance(category, MuhurtaCategory):
            raise InvalidMuhurtaRequestError(
                f"category must be a MuhurtaCategory, got {type(category).__name__}"
            )
        if not isinstance(panchanga, PanchangaState):
            raise InvalidMuhurtaRequestError(
                f"panchanga must be a PanchangaState, got {type(panchanga).__name__}"
            )
