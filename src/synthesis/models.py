"""JRE-022 Synthesis (Verdict) models — core data structures.

JRE-022 consumes the structural outputs of JRE-010 through JRE-021
and generates structured, rule-based classical interpretations (verdicts),
strictly as deterministic data points without probabilistic AI.

Core Models:
- ``SynthesisCategory``: enum of life domains
- ``SynthesisRule``: category, condition_type, condition_params, weight
- ``Verdict``: category, score, strength, evidence_ids
- ``SynthesisReport``: verdicts, version
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

#: Pinned package version.
SYNTHESIS_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class SynthesisCategory(StrEnum):
    """Standard synthesis categories (life domains)."""

    CAREER = "CAREER"
    WEALTH = "WEALTH"
    MARRIAGE = "MARRIAGE"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    PROPERTY = "PROPERTY"
    CHILDREN = "CHILDREN"
    LITIGATION = "LITIGATION"
    TRAVEL = "TRAVEL"
    GENERAL = "GENERAL"


class ConditionType(StrEnum):
    """Types of structural conditions in the rule matrix."""

    YOGA_PRESENT = "YOGA_PRESENT"
    YOGA_ABSENT = "YOGA_ABSENT"
    BALA_ABOVE = "BALA_ABOVE"
    BALA_BELOW = "BALA_BELOW"
    DASHA_LORD_IS = "DASHA_LORD_IS"
    PLANET_IN_HOUSE = "PLANET_IN_HOUSE"
    PLANET_ASPECTS_HOUSE = "PLANET_ASPECTS_HOUSE"
    HOUSE_LORD_IN_HOUSE = "HOUSE_LORD_IN_HOUSE"
    ASHTAKAVARGA_ABOVE = "ASHTAKAVARGA_ABOVE"
    AVASTHA_STATE = "AVASTHA_STATE"
    KARAKA_PRESENT = "KARAKA_PRESENT"
    COMBINED_AND = "COMBINED_AND"
    COMBINED_OR = "COMBINED_OR"


class VerdictStrength(StrEnum):
    """Strength classification for a verdict score."""

    VERY_STRONG = "VERY_STRONG"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    VERY_WEAK = "VERY_WEAK"


# --------------------------------------------------------------------------- #
# Default strength thresholds
# --------------------------------------------------------------------------- #

DEFAULT_STRENGTH_THRESHOLDS: dict[str, float] = {
    "VERY_STRONG": 8.0,
    "STRONG": 6.0,
    "MODERATE": 4.0,
    "WEAK": 2.0,
    "VERY_WEAK": 0.0,
}

DEFAULT_SCORE_RANGE: tuple[float, float] = (0.0, 10.0)


# --------------------------------------------------------------------------- #
# Input data models (represent outputs from upstream engines)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class YogaIndicator:
    """A yoga presence indicator from the Yoga engine."""

    yoga_id: str
    present: bool

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class BalaIndicator:
    """A planetary strength (Bala) value from the Bala engine."""

    planet: str
    bala_type: str  # e.g. "SHADBALA", "BHAVA_BALA"
    value: float

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class DashaIndicator:
    """Current Dasha lord from the Dasha engine."""

    lord: str
    period_start: str  # ISO-UTC
    period_end: str  # ISO-UTC

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class HouseIndicator:
    """Planet-to-house occupancy from the chart engine."""

    planet: str
    house: int  # 1-12

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class AshtakavargaIndicator:
    """Ashtakavarga score for a house."""

    house: int  # 1-12
    score: int  # typically 0-56

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class AvasthaIndicator:
    """Planetary Avastha (state) from the Avastha engine."""

    planet: str
    state: str  # e.g. "DEEPTADI", "SUPTA", "SWAPNA"

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class SynthesisInput:
    """Aggregated input data from all upstream engines.

    Each field is a tuple of indicators from the respective engine.
    Empty tuples indicate the engine's output was not provided.
    """

    yogas: tuple[YogaIndicator, ...] = ()
    balas: tuple[BalaIndicator, ...] = ()
    dasha: DashaIndicator | None = None
    house_occupancies: tuple[HouseIndicator, ...] = ()
    ashtakavarga: tuple[AshtakavargaIndicator, ...] = ()
    avasthas: tuple[AvasthaIndicator, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Core synthesis models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SynthesisRule:
    """A single rule in the classical rule matrix."""

    category: SynthesisCategory
    condition_type: ConditionType
    condition_params: dict[str, Any]
    weight: float

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class Verdict:
    """A deterministic verdict for one life domain."""

    category: SynthesisCategory
    score: float
    strength: VerdictStrength
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class SynthesisReport:
    """Complete synthesis report with verdicts for all categories."""

    verdicts: tuple[Verdict, ...]
    version: str = SYNTHESIS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def verdict_for(self, category: SynthesisCategory) -> Verdict | None:
        """Return the verdict for a specific category, or None."""
        for v in self.verdicts:
            if v.category == category:
                return v
        return None


@dataclass(frozen=True)
class SynthesisConfig:
    """Immutable JRE-022 configuration."""

    version: str = SYNTHESIS_VERSION
    strength_thresholds: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_STRENGTH_THRESHOLDS)
    )
    score_range: tuple[float, float] = DEFAULT_SCORE_RANGE
    rules: dict[str, tuple[SynthesisRule, ...]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #


def evaluate_condition(
    condition_type: ConditionType,
    params: dict[str, Any],
    data: SynthesisInput,
) -> bool:
    """Evaluate a single rule condition against the input data.

    Parameters
    ----------
    condition_type : ConditionType
        The type of condition to evaluate.
    params : dict
        Parameters for the condition.
    data : SynthesisInput
        The aggregated input data from upstream engines.

    Returns
    -------
    bool
        True if the condition is met.
    """
    if condition_type == ConditionType.YOGA_PRESENT:
        yoga_id = str(params.get("yoga_id", ""))
        return any(
            y.yoga_id == yoga_id and y.present for y in data.yogas
        )

    if condition_type == ConditionType.YOGA_ABSENT:
        yoga_id = str(params.get("yoga_id", ""))
        return not any(
            y.yoga_id == yoga_id and y.present for y in data.yogas
        )

    if condition_type == ConditionType.BALA_ABOVE:
        target_planet = str(params.get("planet", ""))
        target_bala_type = str(params.get("bala_type", ""))
        threshold = float(params.get("threshold", 0.0))
        for bal in data.balas:
            if bal.planet == target_planet and bal.bala_type == target_bala_type:
                return bal.value > threshold
        return False

    if condition_type == ConditionType.BALA_BELOW:
        target_planet = str(params.get("planet", ""))
        target_bala_type = str(params.get("bala_type", ""))
        threshold = float(params.get("threshold", 0.0))
        for bal in data.balas:
            if bal.planet == target_planet and bal.bala_type == target_bala_type:
                return bal.value < threshold
        return False

    if condition_type == ConditionType.DASHA_LORD_IS:
        planet = str(params.get("planet", ""))
        if data.dasha is None:
            return False
        return data.dasha.lord == planet

    if condition_type == ConditionType.PLANET_IN_HOUSE:
        planet = str(params.get("planet", ""))
        house = int(params.get("house", 0))
        return any(
            h.planet == planet and h.house == house
            for h in data.house_occupancies
        )

    if condition_type == ConditionType.PLANET_ASPECTS_HOUSE:
        # Simplified: check if planet is in a house that aspects the target
        planet = str(params.get("planet", ""))
        house = int(params.get("house", 0))
        for h in data.house_occupancies:
            if h.planet == planet:
                # Classic aspects: 1-7, 2-12, 3-11, 4-10, 5-9, 6-8
                aspect_pairs = {(1, 7), (2, 12), (3, 11), (4, 10), (5, 9), (6, 8)}
                for a, b in aspect_pairs:
                    if (h.house == a and house == b) or (h.house == b and house == a):
                        return True
        return False

    if condition_type == ConditionType.HOUSE_LORD_IN_HOUSE:
        from_house = int(params.get("from_house", 0))
        to_house = int(params.get("to_house", 0))
        # Find the lord of from_house (simplified: use standard lords)
        standard_lords = {
            1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON",
            5: "SUN", 6: "MERCURY", 7: "VENUS", 8: "MARS",
            9: "JUPITER", 10: "SATURN", 11: "SATURN", 12: "JUPITER",
        }
        lord = standard_lords.get(from_house, "")
        return any(
            h.planet == lord and h.house == to_house
            for h in data.house_occupancies
        )

    if condition_type == ConditionType.ASHTAKAVARGA_ABOVE:
        target_house = int(params.get("house", 0))
        threshold = int(params.get("threshold", 0))
        for av in data.ashtakavarga:
            if av.house == target_house:
                return av.score > threshold
        return False

    if condition_type == ConditionType.AVASTHA_STATE:
        planet = str(params.get("planet", ""))
        state = str(params.get("state", ""))
        return any(
            a.planet == planet and a.state == state
            for a in data.avasthas
        )

    if condition_type == ConditionType.KARAKA_PRESENT:
        # Simplified: check if a karaka planet is in the expected house
        karaka = str(params.get("karaka", ""))
        house = int(params.get("house", 0))
        return any(
            h.planet == karaka and h.house == house
            for h in data.house_occupancies
        )

    # COMBINED_AND / COMBINED_OR handled at rule level
    return False


def compute_category_score(
    rules: tuple[SynthesisRule, ...],
    data: SynthesisInput,
) -> tuple[float, list[str]]:
    """Compute the aggregate score for a category by evaluating all rules.

    Parameters
    ----------
    rules : tuple of SynthesisRule
        Rules for this category.
    data : SynthesisInput
        The aggregated input data.

    Returns
    -------
    tuple of (float, list[str])
        The aggregate score and list of evidence IDs.
    """
    score = 0.0
    evidence: list[str] = []

    for rule in rules:
        if evaluate_condition(rule.condition_type, rule.condition_params, data):
            score += rule.weight
            evidence.append(
                f"{rule.condition_type.value}:{rule.condition_params}"
            )

    return score, evidence


def classify_strength(
    score: float,
    thresholds: dict[str, float],
) -> VerdictStrength:
    """Map an aggregate score to a VerdictStrength enum.

    Parameters
    ----------
    score : float
        The aggregate score.
    thresholds : dict
        Mapping of strength label to lower bound score.

    Returns
    -------
    VerdictStrength
        The classified strength.
    """
    # Sort thresholds descending by score
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)
    for label, lower_bound in sorted_thresholds:
        if score >= lower_bound:
            try:
                return VerdictStrength(label)
            except ValueError:
                continue
    return VerdictStrength.VERY_WEAK


def generate_verdicts(
    rules: dict[str, tuple[SynthesisRule, ...]],
    data: SynthesisInput,
    thresholds: dict[str, float],
) -> tuple[Verdict, ...]:
    """Generate verdicts for all categories.

    Parameters
    ----------
    rules : dict
        Mapping of category name to rules.
    data : SynthesisInput
        The aggregated input data.
    thresholds : dict
        Strength classification thresholds.

    Returns
    -------
    tuple of Verdict
        One verdict per category with rules.
    """
    verdicts: list[Verdict] = []
    for cat_name, cat_rules in rules.items():
        try:
            category = SynthesisCategory(cat_name)
        except ValueError:
            continue
        score, evidence = compute_category_score(cat_rules, data)
        strength = classify_strength(score, thresholds)
        verdicts.append(Verdict(
            category=category,
            score=score,
            strength=strength,
            evidence_ids=tuple(evidence),
        ))
    return tuple(verdicts)


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> .value; tuples -> lists; -0.0 -> 0.0)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {_model_to_dict(key): _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)
