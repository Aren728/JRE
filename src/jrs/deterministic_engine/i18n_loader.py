"""JRE i18n — Internationalization loader for narrative tokens.

Provides language-aware loading of token registries with graceful
English fallback when a translation is missing.

Supported languages:
  en (English), hi (Hindi), ta (Tamil), ml (Malayalam), te (Telugu),
  kn (Kannada), mr (Marathi), bn (Bengali), as (Assamese),
  or (Odia), pa (Punjabi), gu (Gujarati)

Technical astrological terms (Rashi, Nakshatra, Yoga names) are kept
in English/Sanskrit transliteration across all languages for consistency.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# ── Supported Languages ───────────────────────────────────
SUPPORTED_LANGUAGES: frozenset[str] = frozenset(
    {
        "en",
        "hi",
        "ta",
        "ml",
        "te",
        "kn",
        "mr",
        "bn",
        "as",
        "or",
        "pa",
        "gu",
    }
)

# ── Language Display Names ────────────────────────────────
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "ta": "தமிழ் (Tamil)",
    "ml": "മലയാളം (Malayalam)",
    "te": "తెలుగు (Telugu)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "mr": "मराठी (Marathi)",
    "bn": "বাংলা (Bengali)",
    "as": "অসমীয়া (Assamese)",
    "or": "ଓଡ଼ିଆ (Odia)",
    "pa": "ਪੰਜਾਬੀ (Punjabi)",
    "gu": "ગુજરાતી (Gujarati)",
}

# ── Locale directory ──────────────────────────────────────
_LOCALES_DIR = Path(__file__).parent / "locales"


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning empty dict on error."""
    try:
        with path.open(encoding="utf-8") as f:
            loaded: dict[str, Any] = json.load(f)
            return loaded
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=16)
def _load_language(lang: str) -> dict[str, Any]:
    """Load and cache a language file."""
    path = _LOCALES_DIR / f"{lang}.json"
    return _load_json(path)


def get_narrative(token: str, lang: str = "en") -> dict[str, Any]:
    """Get a narrative token with graceful English fallback.

    Args:
        token: The token key (e.g., 'ASHLESHA_SARPA_HIGH_HEALING').
        lang: Language code (e.g., 'en', 'hi', 'ta').

    Returns:
        Dictionary with narrative sections. Falls back to English
        if the token is missing in the requested language.
    """
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    # Try requested language first
    data = _load_language(lang)
    if token in data:
        narrative: dict[str, Any] = data[token]
        return narrative

    # Fallback to English if not 'en'
    if lang != "en":
        en_data = _load_language("en")
        if token in en_data:
            en_narrative: dict[str, Any] = en_data[token]
            return en_narrative

    return {}


def get_all_tokens(lang: str = "en") -> dict[str, Any]:
    """Get all tokens for a language with English fallback.

    Returns a merged dictionary where the requested language's tokens
    override English, and English fills any gaps.
    """
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    # Start with English as base
    base = _load_language("en")

    if lang == "en":
        return base

    # Overlay requested language
    target = _load_language(lang)
    merged = dict(base)
    for key, value in target.items():
        if value:  # Only override if non-empty
            merged[key] = value

    return merged


def reload_languages() -> None:
    """Clear the language cache (useful after adding new translations)."""
    _load_language.cache_clear()


def get_supported_languages() -> list[dict[str, str]]:
    """Return list of supported languages with display names."""
    return [
        {"code": code, "name": LANGUAGE_NAMES.get(code, code)}
        for code in sorted(SUPPORTED_LANGUAGES)
    ]
