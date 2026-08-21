"""JRE-020 Muhurta (Electional) models — core data structures.

JRE-020 computes the Panchanga state and evaluates the structural
fitness of specific time windows for classical categories, strictly
as structural data points without predictive interpretation.

Core Models:
- ``PanchangaState``: tithi, vara, nakshatra, yoga, karana
- ``MuhurtaWindow``: start_utc, end_utc
- ``MuhurtaEvaluation``: window, panchanga, structural_flags, fitness_score
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, NakshatraId, PlanetState, RashiId

#: Pinned package version.
MUHURTA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class Tithi(StrEnum):
    """The 30 lunar days (tithis) of the Panchanga."""

    SHUKLA_PRADEMA = "SHUKLA_PRADEMA"
    SHUKLA_DVITIYA = "SHUKLA_DVITIYA"
    SHUKLA_TRITIYA = "SHUKLA_TRITIYA"
    SHUKLA_CHATURTHI = "SHUKLA_CHATURTHI"
    SHUKLA_PANCHAMI = "SHUKLA_PANCHAMI"
    SHUKLA_SHASHTHI = "SHUKLA_SHASHTHI"
    SHUKLA_SAPTAMI = "SHUKLA_SAPTAMI"
    SHUKLA_ASHTAMI = "SHUKLA_ASHTAMI"
    SHUKLA_NAVAMI = "SHUKLA_NAVAMI"
    SHUKLA_DASHAMI = "SHUKLA_DASHAMI"
    SHUKLA_EKADASHI = "SHUKLA_EKADASHI"
    SHUKLA_DVADASHI = "SHUKLA_DVADASHI"
    SHUKLA_TRAYODASHI = "SHUKLA_TRAYODASHI"
    SHUKLA_CHATURDASHI = "SHUKLA_CHATURDASHI"
    PURNIMA = "PURNIMA"
    KRISHNA_PRATIPADA = "KRISHNA_PRATIPADA"
    KRISHNA_DVITIYA = "KRISHNA_DVITIYA"
    KRISHNA_TRITIYA = "KRISHNA_TRITIYA"
    KRISHNA_CHATURTHI = "KRISHNA_CHATURTHI"
    KRISHNA_PANCHAMI = "KRISHNA_PANCHAMI"
    KRISHNA_SHASHTHI = "KRISHNA_SHASHTHI"
    KRISHNA_SAPTAMI = "KRISHNA_SAPTAMI"
    KRISHNA_ASHTAMI = "KRISHNA_ASHTAMI"
    KRISHNA_NAVAMI = "KRISHNA_NAVAMI"
    KRISHNA_DASHAMI = "KRISHNA_DASHAMI"
    KRISHNA_EKADASHI = "KRISHNA_EKADASHI"
    KRISHNA_DVADASHI = "KRISHNA_DVADASHI"
    KRISHNA_TRAYODASHI = "KRISHNA_TRAYODASHI"
    KRISHNA_CHATURDASHI = "KRISHNA_CHATURDASHI"
    AMANTHA = "AMANTHA"


class Var(StrEnum):
    """The 7 weekdays (vara) of the Panchanga."""

    SUNDAY = "SUNDAY"
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class Yoga(StrEnum):
    """The 27 yogas (samyoga) of the Panchanga."""

    VISHKAMBHA = "VISHKAMBHA"
    PRITI = "PRITI"
    AYUSHMAN = "AYUSHMAN"
    SOUBHAGYA = "SOUBHAGYA"
    SHOBHANA = "SHOBHANA"
    ATIGANDA = "ATIGANDA"
    SUKARMA = "SUKARMA"
    DHRTI = "DHRTI"
    SHULA = "SHULA"
    GANDA = "GANDA"
    VRIDDHI = "VRIDDHI"
    dhruva = "DHRUVA"
    VYAGHATA = "VYAGHATA"
    HARSHANA = "HARSHANA"
    VAJRA = "VAJRA"
    SIDDHI = "SIDDHI"
    VYATIPATA = "VYATIPATA"
    VARIGHA = "VARIGHA"
    PARIGHA = "PARIGHA"
    SHIVA = "SHIVA"
    SIDDHA = "SIDDHA"
    SADHYA = "SADHYA"
    SUBHA = "SUBHA"
    SHUKLA = "SHUKLA"
    BRAHMA = "BRAHMA"
    INDENDRA = "INDRA"
    VAIDHRITI = "VAIDHRITI"


class Karana(StrEnum):
    """The 11 karanas (half-tithi) of the Panchanga."""

    BALAVA = "BALAVA"
    BAVALA = "BAVALA"
    KAILAVA = "KAILAVA"
    TAITILA = "TAITILA"
    GARJA = "GARJA"
    VANIJA = "VANIJA"
    VISHTI = "VISHTI"
    SHAKUNI = "SHAKUNI"
    CHATUSHPADA = "CHATUSHPADA"
    NAGAVA = "NAGAVA"
    KIMSTUGHNA = "KIMSTUGHNA"


class MuhurtaCategory(StrEnum):
    """Standard Muhurta (electional) query categories."""

    MARRIAGE = "MARRIAGE"
    TRAVEL = "TRAVEL"
    BUSINESS = "BUSINESS"
    EDUCATION = "EDUCATION"
    HOUSEWARMING = "HOUSEWARMING"
    VEHICLE_PURCHASE = "VEHICLE_PURCHASE"
    MEDICAL = "MEDICAL"
    LITIGATION = "LITIGATION"
    COMMENCEMENT = "COMMENCEMENT"
    GENERAL = "GENERAL"


# --------------------------------------------------------------------------- #
# Inauspicious elements (from config-driven rules)
# --------------------------------------------------------------------------- #

#: Default inauspicious tithis (Rikta tithis).
DEFAULT_INAUSPICIOUS_TITHIS: frozenset[Tithi] = frozenset({
    Tithi.SHUKLA_CHATURTHI,
    Tithi.SHUKLA_NAVAMI,
    Tithi.SHUKLA_CHATURDASHI,
    Tithi.KRISHNA_PRATIPADA,
    Tithi.KRISHNA_SHASHTHI,
    Tithi.KRISHNA_EKADASHI,
})

#: Default inauspicious karanas.
DEFAULT_INAUSPICIOUS_KARANAS: frozenset[Karana] = frozenset({
    Karana.VISHTI,
    Karana.SHAKUNI,
})

#: Default inauspicious yogas.
DEFAULT_INAUSPICIOUS_YOGAS: frozenset[Yoga] = frozenset({
    Yoga.VISHKAMBHA,
    Yoga.ATIGANDA,
    Yoga.SHULA,
    Yoga.GANDA,
    Yoga.VYATIPATA,
    Yoga.VAIDHRITI,
})

#: Var (weekday) to its natural lord (BodyId).
VARA_LORD: dict[Var, BodyId] = {
    Var.SUNDAY: BodyId.SUN,
    Var.MONDAY: BodyId.MOON,
    Var.TUESDAY: BodyId.MARS,
    Var.WEDNESDAY: BodyId.MERCURY,
    Var.THURSDAY: BodyId.JUPITER,
    Var.FRIDAY: BodyId.VENUS,
    Var.SATURDAY: BodyId.SATURN,
}


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PanchangaState:
    """The Panchanga (five-limbed) state at a given time."""

    tithi: Tithi
    vara: Var
    nakshatra: NakshatraId
    yoga: Yoga
    karana: Karana

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class MuhurtaWindow:
    """A time window to evaluate for electional fitness."""

    start_utc: str  # ISO-UTC string
    end_utc: str  # ISO-UTC string

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class MuhurtaEvaluation:
    """Structural evaluation of a time window for a specific Muhurta category."""

    window: MuhurtaWindow
    panchanga: PanchangaState
    structural_flags: tuple[str, ...]
    fitness_score: float  # 0.0 to 1.0
    category: MuhurtaCategory
    version: str = MUHURTA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class CategoryRule:
    """Structural rule for a Muhurta category."""

    required_nakshatras: tuple[NakshatraId, ...] = ()
    avoided_tithis: tuple[Tithi, ...] = ()
    avoided_karanas: tuple[Karana, ...] = ()
    avoided_yogas: tuple[Yoga, ...] = ()
    avoided_vars: tuple[Var, ...] = ()
    preferred_vars: tuple[Var, ...] = ()
    weight_required: float = 0.3
    weight_avoided: float = 0.5
    weight_preferred: float = 0.2

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class MuhurtaConfig:
    """Immutable JRE-020 configuration."""

    version: str = MUHURTA_VERSION
    inauspicious_tithis: tuple[Tithi, ...] = tuple(DEFAULT_INAUSPICIOUS_TITHIS)
    inauspicious_karanas: tuple[Karana, ...] = tuple(DEFAULT_INAUSPICIOUS_KARANAS)
    inauspicious_yogas: tuple[Yoga, ...] = tuple(DEFAULT_INAUSPICIOUS_YOGAS)
    category_rules: dict[str, CategoryRule] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #

RASHI_LIST: list[RashiId] = list(RashiId)


def rashi_of_longitude(longitude: float) -> RashiId:
    """Map a sidereal longitude to its RashiId."""
    idx = int(longitude / 30.0) % 12
    return RASHI_LIST[idx]


def evaluate_panchanga(
    panchanga: PanchangaState,
    category: MuhurtaCategory,
    config: MuhurtaConfig,
) -> tuple[str, ...]:
    """Evaluate structural flags for a Panchanga state against a category.

    Parameters
    ----------
    panchanga : PanchangaState
        The Panchanga state at the window start.
    category : MuhurtaCategory
        The electional category.
    config : MuhurtaConfig
        Configuration with inauspicious elements and category rules.

    Returns
    -------
    tuple of str
        Structural flag strings describing findings.
    """
    flags: list[str] = []

    # Check inauspicious tithis
    if panchanga.tithi in config.inauspicious_tithis:
        flags.append(f"Inauspicious tithi: {panchanga.tithi.value}")

    # Check inauspicious karanas
    if panchanga.karana in config.inauspicious_karanas:
        flags.append(f"Inauspicious karana: {panchanga.karana.value}")

    # Check inauspicious yogas
    if panchanga.yoga in config.inauspicious_yogas:
        flags.append(f"Inauspicious yoga: {panchanga.yoga.value}")

    # Check category-specific rules
    cat_rule = config.category_rules.get(category.value)
    if cat_rule is not None:
        # Required nakshatras
        if cat_rule.required_nakshatras:
            if panchanga.nakshatra in cat_rule.required_nakshatras:
                flags.append(
                    f"Favorable nakshatra for {category.value}: "
                    f"{panchanga.nakshatra.value}"
                )
            else:
                flags.append(
                    f"Unfavorable nakshatra for {category.value}: "
                    f"{panchanga.nakshatra.value}"
                )

        # Avoided tithis
        if panchanga.tithi in cat_rule.avoided_tithis:
            flags.append(
                f"Avoided tithi for {category.value}: {panchanga.tithi.value}"
            )

        # Avoided karanas
        if panchanga.karana in cat_rule.avoided_karanas:
            flags.append(
                f"Avoided karana for {category.value}: {panchanga.karana.value}"
            )

        # Avoided yogas
        if panchanga.yoga in cat_rule.avoided_yogas:
            flags.append(
                f"Avoided yoga for {category.value}: {panchanga.yoga.value}"
            )

        # Avoided vars
        if panchanga.vara in cat_rule.avoided_vars:
            flags.append(
                f"Avoided vara for {category.value}: {panchanga.vara.value}"
            )

        # Preferred vars
        if panchanga.vara in cat_rule.preferred_vars:
            flags.append(
                f"Preferred vara for {category.value}: {panchanga.vara.value}"
            )

    return tuple(flags)


def compute_fitness_score(
    structural_flags: tuple[str, ...],
    category: MuhurtaCategory,
    config: MuhurtaConfig,
) -> float:
    """Compute a deterministic fitness score (0.0 to 1.0) from structural flags.

    The score starts at 1.0 and is penalized by the presence of
    inauspicious or avoided elements, or boosted by favorable elements.

    Parameters
    ----------
    structural_flags : tuple of str
        The structural flags from evaluate_panchanga.
    category : MuhurtaCategory
        The electional category.
    config : MuhurtaConfig
        Configuration with weights.

    Returns
    -------
    float
        Fitness score in [0.0, 1.0].
    """
    score = 1.0

    for flag in structural_flags:
        if flag.startswith("Inauspicious"):
            score -= 0.15
        elif flag.startswith("Avoided"):
            score -= 0.20
        elif flag.startswith("Unfavorable"):
            score -= 0.15
        elif flag.startswith("Favorable"):
            score += 0.10
        elif flag.startswith("Preferred"):
            score += 0.05

    return max(0.0, min(1.0, score))


def derive_planet_rashi(
    planet_states: tuple[PlanetState, ...],
    body: BodyId,
) -> RashiId | None:
    """Find the rashi occupied by a specific planet.

    Parameters
    ----------
    planet_states : tuple of PlanetState
        Planet positions.
    body : BodyId
        The planet to look up.

    Returns
    -------
    RashiId or None
        The rashi if found, else None.
    """
    for state in planet_states:
        if state.body == body:
            return state.rashi
    return None


def check_planet_in_house(
    planet_states: tuple[PlanetState, ...],
    body: BodyId,
    target_rashi: RashiId,
) -> bool:
    """Check if a planet occupies a specific rashi (house).

    Parameters
    ----------
    planet_states : tuple of PlanetState
        Planet positions.
    body : BodyId
        The planet to check.
    target_rashi : RashiId
        The target rashi.

    Returns
    -------
    bool
        True if the planet is in the target rashi.
    """
    rashi = derive_planet_rashi(planet_states, body)
    return rashi == target_rashi


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
