"""JRE-027 Birth Panchanga & Signature Context — deterministic fact layer.

Deterministic, interpretation-free birth signature facts assembled from
existing JRE-002/JRE-003 positions:

- Panchanga factors: Tithi, Karana, Yoga, Vara, Hora
- Positional facts: Lagna rashi, Sun rashi, Moon rashi, Nakshatra, Pada
- Temporal facts: Day/Night, AM/PM

This engine performs NO interpretation: no personality traits, no
temperament claims, no predictions.  Those belong to future engines.

Public API:
- BirthSignatureService — the deterministic facade
- BirthSignature — a single birth signature fact
- Enums: Tithi, Karana, Yoga, Vara, HoraPeriod, DayNightPeriod, AmPm
"""

from .errors import (
    BirthSignatureError,
    InvalidSignatureRequestError,
    SignatureComputationError,
)
from .models import (
    BIRTH_SIGNATURE_VERSION,
    AmPm,
    BirthSignature,
    DayNightPeriod,
    HoraPeriod,
    Karana,
    Tithi,
    Vara,
    Yoga,
    compute_am_pm,
    compute_day_night,
    compute_hora,
    compute_karana,
    compute_tithi,
    compute_vara,
    compute_yoga,
    to_dict_value,
)
from .service import BirthSignatureService

__version__ = BIRTH_SIGNATURE_VERSION

__all__ = [
    # service
    "BirthSignatureService",
    # models
    "BirthSignature",
    "Tithi",
    "Karana",
    "Yoga",
    "Vara",
    "HoraPeriod",
    "DayNightPeriod",
    "AmPm",
    "BIRTH_SIGNATURE_VERSION",
    "to_dict_value",
    # computation functions
    "compute_tithi",
    "compute_karana",
    "compute_yoga",
    "compute_vara",
    "compute_hora",
    "compute_am_pm",
    "compute_day_night",
    # errors
    "BirthSignatureError",
    "InvalidSignatureRequestError",
    "SignatureComputationError",
]
