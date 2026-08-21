"""JRE-022 SynthesisService facade.

``SynthesisService.generate_verdict`` is the canonical entry point:
it consumes structural outputs from upstream engines and generates
deterministic, rule-based classical interpretations (verdicts).

It produces NO qualitative output beyond the rule matrix.
"""

from __future__ import annotations

from .config import load_config
from .errors import InvalidSynthesisRequestError
from .models import (
    SynthesisCategory,
    SynthesisConfig,
    SynthesisInput,
    SynthesisReport,
    SynthesisRule,
    generate_verdicts,
)


class SynthesisService:
    """Deterministic Synthesis (Verdict) computation facade."""

    def __init__(self, config: SynthesisConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> SynthesisConfig:
        return self._config

    def generate_verdict(
        self,
        data: SynthesisInput,
        categories: tuple[SynthesisCategory, ...] | None = None,
    ) -> SynthesisReport:
        """Generate a synthesis report from upstream engine outputs.

        Parameters
        ----------
        data : SynthesisInput
            Aggregated input data from upstream engines.
        categories : tuple of SynthesisCategory, optional
            Specific categories to evaluate.  If None, all configured
            categories are evaluated.

        Returns
        -------
        SynthesisReport
            Verdicts for each evaluated category.
        """
        self._validate_request(data)

        # Filter rules to requested categories if specified
        if categories is not None:
            filtered_rules: dict[str, tuple[SynthesisRule, ...]] = {}
            for cat in categories:
                cat_rules = self._config.rules.get(cat.value)
                if cat_rules:
                    filtered_rules[cat.value] = cat_rules
            rules_to_use = filtered_rules
        else:
            rules_to_use = self._config.rules

        verdicts = generate_verdicts(
            rules=rules_to_use,
            data=data,
            thresholds=self._config.strength_thresholds,
        )

        return SynthesisReport(verdicts=verdicts)

    def _validate_request(self, data: SynthesisInput) -> None:
        """Validate the synthesis request."""
        if not isinstance(data, SynthesisInput):
            raise InvalidSynthesisRequestError(
                f"data must be a SynthesisInput, got {type(data).__name__}"
            )
