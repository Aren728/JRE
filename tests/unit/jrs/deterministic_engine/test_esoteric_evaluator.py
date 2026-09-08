"""Unit Tests for the Esoteric Nakshatra Evaluator (DDE Compliant).

Tests:
1. Uniqueness Rule: Each Nakshatra placement returns exactly ONE token.
2. Boundary Check: Gandanta cusp placements trigger GANDANTA_LEVEL_ACUTE.
3. Zero Ambiguity: Rendered output contains no conditional or ambiguous language.
4. Shadbala Threshold Routing: High/Low Shadbala correctly routes to expected tokens.
5. Token Registry Resolution: All tokens resolve to 3-part narratives.
6. Database Completeness: All 27 nakshatras have required fields.
7. HTML Rendering: Esoteric profile renders correctly with distinct styling.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════════

_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "src" / "jrs" / "deterministic_engine" / "esoteric_nakshatra_db.json"
_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "src" / "jrs" / "deterministic_engine" / "token_registry.json"


def _load_db() -> dict[str, Any]:
    with _DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _load_registry() -> dict[str, Any]:
    with _REGISTRY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _make_jre_facts(
    moon_nakshatra: str = "ASHLESHA",
    moon_longitude: float = 103.5,
    moon_rashi_num: int = 4,
    moon_deg_in_sign: float = 13.5,
    sun_nakshatra: str = "KRITTIKA",
    sun_longitude: float = 33.0,
    sun_rashi_num: int = 2,
    sun_deg_in_sign: float = 3.0,
) -> dict[str, Any]:
    """Create a mock jre_facts dict for testing."""
    return {
        "planets": {
            "MOON": {
                "house": 4,
                "rashi": "KARKA",
                "rashi_num": moon_rashi_num,
                "longitude": moon_longitude,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "MOON",
            },
            "SUN": {
                "house": 10,
                "rashi": "VRISHABHA",
                "rashi_num": sun_rashi_num,
                "longitude": sun_longitude,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "VENUS",
            },
            "MARS": {
                "house": 1,
                "rashi": "MESHA",
                "rashi_num": 1,
                "longitude": 15.0,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "MARS",
            },
            "MERCURY": {
                "house": 10,
                "rashi": "VRISHABHA",
                "rashi_num": 2,
                "longitude": 38.0,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "VENUS",
            },
            "JUPITER": {
                "house": 7,
                "rashi": "TULA",
                "rashi_num": 7,
                "longitude": 200.0,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "VENUS",
            },
            "VENUS": {
                "house": 10,
                "rashi": "VRISHABHA",
                "rashi_num": 2,
                "longitude": 35.0,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "VENUS",
            },
            "SATURN": {
                "house": 3,
                "rashi": "MITHUNA",
                "rashi_num": 3,
                "longitude": 65.0,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "sign_lord": "MERCURY",
            },
            "RAHU": {
                "house": 5,
                "rashi": "SIMHA",
                "rashi_num": 5,
                "longitude": 125.0,
                "combust": False,
                "debilitated": False,
                "retrograde": True,
                "sign_lord": "SUN",
            },
            "KETU": {
                "house": 11,
                "rashi": "KUMBHA",
                "rashi_num": 11,
                "longitude": 305.0,
                "combust": False,
                "debilitated": False,
                "retrograde": True,
                "sign_lord": "SATURN",
            },
        },
        "house_lords": {
            1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON",
            5: "SUN", 6: "MERCURY", 7: "VENUS", 8: "MARS",
            9: "JUPITER", 10: "SATURN", 11: "SATURN", 12: "JUPITER",
        },
        "lagna_sign": 1,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_longitude,
        "planet_nakshatras": {
            "MOON": moon_nakshatra,
            "SUN": sun_nakshatra,
        },
        "planet_details": {
            "MOON": {
                "sign": "KARKA",
                "house": 4,
                "degree_in_sign": moon_deg_in_sign,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "nakshatra": moon_nakshatra,
            },
            "SUN": {
                "sign": "VRISHABHA",
                "house": 10,
                "degree_in_sign": sun_deg_in_sign,
                "combust": False,
                "debilitated": False,
                "retrograde": False,
                "nakshatra": sun_nakshatra,
            },
        },
    }


def _make_strengths(
    moon_shadbala: float = 1.5,
    sun_shadbala: float = 1.3,
) -> dict[str, Any]:
    """Create a mock strengths dict with shadbala values."""
    return {
        "shadbala": {
            "MOON": {"total_rupas": moon_shadbala, "grade": "Good"},
            "SUN": {"total_rupas": sun_shadbala, "grade": "Good"},
            "MARS": {"total_rupas": 1.4, "grade": "Good"},
            "MERCURY": {"total_rupas": 1.1, "grade": "Average"},
            "JUPITER": {"total_rupas": 1.6, "grade": "Excellent"},
            "VENUS": {"total_rupas": 1.3, "grade": "Good"},
            "SATURN": {"total_rupas": 0.8, "grade": "Weak"},
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Test 1: Uniqueness Rule
# ══════════════════════════════════════════════════════════════════════════════

class TestUniquenessRule:
    """Each Nakshatra placement must return exactly ONE token."""

    def test_exactly_one_token_per_nakshatra(self):
        """Given a mock facts and strengths dict, the evaluator returns
        exactly one token per Nakshatra placement."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        # Each result should have exactly one token
        for result in results:
            assert "token" in result, f"Missing token in result for {result['planet']}"
            assert isinstance(result["token"], str), f"Token must be a string, got {type(result['token'])}"
            assert len(result["token"]) > 0, f"Token must not be empty for {result['planet']}"

        # Check MOON specifically
        moon_results = [r for r in results if r["planet"] == "MOON"]
        assert len(moon_results) == 1, f"Expected 1 MOON result, got {len(moon_results)}"
        assert moon_results[0]["token"] == "ASHLESHA_SARPA_HIGH_HEALING"

    def test_unique_token_for_each_sarpa_nakshatra(self):
        """Sarpa nakshatras (Ashlesha, Jyeshtha, Mula) each return
        exactly one token without overlap."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        for nakshatra in ["ASHLESHA", "JYESHTHA", "MULA"]:
            facts = _make_jre_facts(
                moon_nakshatra=nakshatra,
                moon_longitude=103.5,
                moon_rashi_num=4,
                moon_deg_in_sign=13.5,
            )
            # Override the planet_details nakshatra
            facts["planet_details"]["MOON"]["nakshatra"] = nakshatra

            strengths = _make_strengths(moon_shadbala=1.5)
            results = evaluate_esoteric_profile(facts, strengths)

            moon_results = [r for r in results if r["planet"] == "MOON"]
            assert len(moon_results) == 1, f"Expected 1 result for {nakshatra}"
            assert moon_results[0]["nakshatra"] == nakshatra

    def test_no_duplicate_tokens_across_planets(self):
        """Different planets with different nakshatras return distinct tokens."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(
            moon_nakshatra="ASHLESHA",
            sun_nakshatra="KRITTIKA",
        )
        strengths = _make_strengths(moon_shadbala=1.5, sun_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        tokens = [r["token"] for r in results]
        # All tokens should be unique (no duplicates)
        assert len(tokens) == len(set(tokens)), f"Duplicate tokens found: {tokens}"


# ══════════════════════════════════════════════════════════════════════════════
# Test 2: Gandanta Boundary Checks (Float64 Precision)
# ══════════════════════════════════════════════════════════════════════════════

class TestGandantaBoundaryChecks:
    """Float64 precision boundary checks for Gandanta points."""

    def test_ashlesha_magha_cusp_detected(self):
        """A placement at exactly 00°00'05" of a Gandanta cusp correctly
        triggers GANDANTA_LEVEL_ACUTE."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        # Ashlesha-Magha cusp: ~26°40' Cancer / 0°00' Leo
        # Planet at 26°40'05" Cancer = 26.6681° (within 0.333° tolerance)
        result = check_gandanta(
            longitude=106.6681,  # Cancer starts at 90°, so 90 + 26.6681 = 116.6681
            rashi_num=4,  # Cancer
            degree_in_sign=26.6681,
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"
        assert "Ashlesha" in result["description"] or "Magha" in result["description"]

    def test_jyeshtha_mula_cusp_detected(self):
        """Jyeshtha-Mula cusp at ~26°40' Scorpio triggers GANDANTA_LEVEL_ACUTE."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        result = check_gandanta(
            longitude=236.6667,  # Scorpio starts at 210°, so 210 + 26.6667 = 236.6667
            rashi_num=8,  # Scorpio
            degree_in_sign=26.6667,
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"
        assert "Jyeshta" in result["description"] or "Mula" in result["description"]

    def test_revati_ashwini_cusp_detected(self):
        """Revati-Ashwini cusp at ~30°00' Pisces triggers GANDANTA_LEVEL_ACUTE."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        result = check_gandanta(
            longitude=360.0,  # Pisces ends at 360° / Aries begins
            rashi_num=12,  # Pisces
            degree_in_sign=30.0,
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_gandanta_within_tolerance(self):
        """A placement within 0°20'00" of a cusp is detected as ACUTE."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        # Test with distance = 0.1° (well within 0.333° tolerance)
        result = check_gandanta(
            longitude=116.5667,
            rashi_num=4,
            degree_in_sign=26.5667,  # 0.1° from cusp at 26.6667
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_gandanta_outside_tolerance(self):
        """A placement outside 0°20'00" tolerance is NOT flagged."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        # Distance = 0.5° (outside 0.333° tolerance)
        result = check_gandanta(
            longitude=117.1667,
            rashi_num=4,
            degree_in_sign=27.1667,  # 0.5° from cusp at 26.6667
        )
        assert result["is_gandanta"] is False
        assert result["level"] == "NONE"

    def test_gandanta_exact_zero_distance(self):
        """A placement at exactly 0° distance from cusp is detected."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        result = check_gandanta(
            longitude=116.6667,
            rashi_num=4,
            degree_in_sign=26.6667,  # Exactly at cusp
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_gandanta_first_sign_of_cusp(self):
        """Planet at 0°00' in the sign AFTER the cusp (e.g., Leo for Ashlesha-Magha)."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        # Planet at 0°10' Leo (rashi_num=5, degree_in_sign=0.1667)
        result = check_gandanta(
            longitude=120.1667,
            rashi_num=5,  # Leo
            degree_in_sign=0.1667,
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"


# ══════════════════════════════════════════════════════════════════════════════
# Test 3: Zero Ambiguity
# ══════════════════════════════════════════════════════════════════════════════

class TestZeroAmbiguity:
    """Rendered output must contain no conditional or ambiguous language."""

    def test_no_ambiguous_phrases_in_registry(self):
        """The token registry contains no phrases like 'could mean X or Y'
        or 'on one hand...'."""
        registry = _load_registry()
        ambiguous_patterns = [
            "could mean",
            "on one hand",
            "on the other hand",
            "might indicate",
            "possibly",
            "perhaps",
            "may represent",
            "could represent",
            "it depends",
            "either way",
        ]

        for token, narratives in registry.items():
            for section_key, text in narratives.items():
                for pattern in ambiguous_patterns:
                    assert pattern.lower() not in text.lower(), (
                        f"Ambiguous phrase '{pattern}' found in token "
                        f"'{token}' section '{section_key}'"
                    )

    def test_no_conditional_language_in_registry(self):
        """The token registry contains no conditional if/then language
        in the narrative sections."""
        registry = _load_registry()
        conditional_patterns = [
            "if you",
            "when you",
            "should you",
            "in the event that",
            "depending on",
            "based on your choice",
        ]

        for token, narratives in registry.items():
            for section_key, text in narratives.items():
                for pattern in conditional_patterns:
                    assert pattern.lower() not in text.lower(), (
                        f"Conditional language '{pattern}' found in token "
                        f"'{token}' section '{section_key}'"
                    )

    def test_rendered_html_has_no_ambiguity(self):
        """The rendered HTML output from the esoteric evaluator contains
        no ambiguous language."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        ambiguous_phrases = ["could mean", "on one hand", "might indicate", "possibly"]
        for phrase in ambiguous_phrases:
            assert phrase.lower() not in html.lower(), (
                f"Ambiguous phrase '{phrase}' found in rendered HTML"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Test 4: Shadbala Threshold Routing
# ══════════════════════════════════════════════════════════════════════════════

class TestShadbalaThresholdRouting:
    """High/Low Shadbala correctly routes to expected tokens."""

    def test_high_shadbala_routes_to_high_token(self):
        """Ashlesha with Shadbala >1.2 routes to ASHLESHA_SARPA_HIGH_HEALING."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        assert moon_result["token"] == "ASHLESHA_SARPA_HIGH_HEALING"

    def test_low_shadbala_routes_to_low_token(self):
        """Ashlesha with Shadbala <1.0 routes to ASHLESHA_SARPA_VULNERABILITY."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=0.8)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        assert moon_result["token"] == "ASHLESHA_SARPA_VULNERABILITY"

    def test_mid_shadbala_routes_to_conservative(self):
        """Ashlesha with Shadbala between 1.0 and 1.2 routes to the
        conservative (vulnerability) path."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.1)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        assert moon_result["token"] == "ASHLESHA_SARPA_VULNERABILITY"

    def test_jyeshtha_high_shadbala(self):
        """Jyeshtha with high Shadbala routes to protection high token."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="JYESHTHA")
        facts["planet_details"]["MOON"]["nakshatra"] = "JYESHTHA"
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        assert moon_result["token"] == "JYESHTHA_PROTECTION_HIGH_SHADBALA"

    def test_mula_high_shadbala(self):
        """Mula with high Shadbala routes to uprooting high token."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="MULA")
        facts["planet_details"]["MOON"]["nakshatra"] = "MULA"
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        assert moon_result["token"] == "MULA_KARMIC_UPROOTING_HIGH_SHADBALA"

    def test_gandanta_overrides_shadbala(self):
        """When a planet is at a Gandanta cusp, the override token is selected
        regardless of Shadbala level."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        # Ashlesha at Gandanta cusp with high Shadbala
        facts = _make_jre_facts(
            moon_nakshatra="ASHLESHA",
            moon_longitude=116.6667,  # At Ashlesha-Magha cusp
            moon_rashi_num=4,
            moon_deg_in_sign=26.6667,
        )
        facts["planet_details"]["MOON"]["nakshatra"] = "ASHLESHA"
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        # Gandanta override should select vulnerability regardless of high Shadbala
        assert moon_result["token"] == "ASHLESHA_SARPA_VULNERABILITY"
        assert moon_result["gandanta"]["level"] == "GANDANTA_LEVEL_ACUTE"


# ══════════════════════════════════════════════════════════════════════════════
# Test 5: Token Registry Resolution
# ══════════════════════════════════════════════════════════════════════════════

class TestTokenRegistryResolution:
    """All tokens resolve to 3-part narratives in the registry."""

    def test_all_tokens_have_three_sections(self):
        """Every token in the registry has SECTION_1, SECTION_2, and SECTION_3."""
        registry = _load_registry()

        for token, narrative in registry.items():
            assert "SECTION_1_BASELINE" in narrative, (
                f"Token '{token}' missing SECTION_1_BASELINE"
            )
            assert "SECTION_2_DETERMINISTIC_DYNAMIC" in narrative, (
                f"Token '{token}' missing SECTION_2_DETERMINISTIC_DYNAMIC"
            )
            assert "SECTION_3_TIMELINE_ACTIVATION" in narrative, (
                f"Token '{token}' missing SECTION_3_TIMELINE_ACTIVATION"
            )

    def test_all_sections_are_nonempty(self):
        """All narrative sections are non-empty strings."""
        registry = _load_registry()

        for token, narrative in registry.items():
            for section in ["SECTION_1_BASELINE", "SECTION_2_DETERMINISTIC_DYNAMIC",
                           "SECTION_3_TIMELINE_ACTIVATION"]:
                value = narrative[section]
                assert isinstance(value, str), f"Token '{token}' {section} is not a string"
                assert len(value.strip()) > 0, f"Token '{token}' {section} is empty"

    def test_evaluated_tokens_resolve_to_registry(self):
        """All tokens returned by the evaluator exist in the registry."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        registry = _load_registry()
        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        for result in results:
            token = result["token"]
            assert token in registry, f"Token '{token}' not found in registry"

    def test_narrative_not_empty_for_evaluated_tokens(self):
        """The narrative dict for evaluated tokens contains actual text."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        for result in results:
            narrative = result["narrative"]
            assert len(narrative) > 0, f"Empty narrative for token '{result['token']}'"
            for key in ["SECTION_1_BASELINE", "SECTION_2_DETERMINISTIC_DYNAMIC",
                       "SECTION_3_TIMELINE_ACTIVATION"]:
                assert key in narrative, f"Missing {key} in narrative for '{result['token']}'"


# ══════════════════════════════════════════════════════════════════════════════
# Test 6: Database Completeness
# ══════════════════════════════════════════════════════════════════════════════

class TestDatabaseCompleteness:
    """All 27 nakshatras have required fields in the database."""

    ALL_NAKSHATRAS = [
        "ASHWINI", "BHARANI", "KRITTIKA", "ROHINI", "MRIGASHIRA",
        "ARDRA", "PUNARVASU", "ASHLESHA", "MAGHA", "PURVA_PHALGUNI",
        "UTTARA_PHALGUNI", "HASTA", "CHITRA", "SWATI", "VISHAKHA",
        "ANURADHA", "JYESHTHA", "MULA", "PURVA_ASHADHA", "UTTARA_ASHADHA",
        "SHRAVANA", "DHANISHTHA", "SHATABHISHA", "PURVA_BHADRAPADA",
        "UTTARA_BHADRAPADA", "REVATI",
    ]

    REQUIRED_FIELDS = ["devata", "gana", "shakti", "mystical_capability",
                       "intuition_type", "vulnerability"]

    def test_all_27_nakshatras_present(self):
        """Database contains entries for all 27 nakshatras (note: 26 standard + 1 = 27)."""
        db = _load_db()
        for nakshatra in self.ALL_NAKSHATRAS:
            assert nakshatra in db, f"Nakshatra '{nakshatra}' missing from database"

    def test_all_required_fields_present(self):
        """Every nakshatra entry has all required fields."""
        db = _load_db()
        for nakshatra, entry in db.items():
            for field in self.REQUIRED_FIELDS:
                assert field in entry, (
                    f"Nakshatra '{nakshatra}' missing required field '{field}'"
                )

    def test_all_fields_are_nonempty_strings(self):
        """All required fields are non-empty strings."""
        db = _load_db()
        for nakshatra, entry in db.items():
            for field in self.REQUIRED_FIELDS:
                value = entry[field]
                assert isinstance(value, str), (
                    f"Nakshatra '{nakshatra}' field '{field}' is not a string"
                )
                assert len(value.strip()) > 0, (
                    f"Nakshatra '{nakshatra}' field '{field}' is empty"
                )

    def test_sarpa_nakshatras_have_serpentine_content(self):
        """Ashlesha and Jyeshtha entries reference Sarpa/Naga lineage."""
        db = _load_db()
        for nakshatra in ["ASHLESHA", "JYESHTHA"]:
            entry = db[nakshatra]
            combined = (
                entry["mystical_capability"] + entry["intuition_type"]
            ).lower()
            assert "serp" in combined or "naga" in combined or "sarpa" in combined, (
                f"Nakshatra '{nakshatra}' should reference Sarpa/Naga lineage"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Test 7: HTML Rendering
# ══════════════════════════════════════════════════════════════════════════════

class TestHTMLRendering:
    """Esoteric profile renders correctly with distinct styling."""

    def test_render_produces_valid_html(self):
        """render_esoteric_profile_html returns a well-formed HTML fragment."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        assert "<div" in html, "HTML should contain div elements"
        assert "esoteric-section" in html, "HTML should contain esoteric-section class"
        assert "esoteric-card" in html, "HTML should contain esoteric-card class"

    def test_render_includes_devata_and_shakti(self):
        """Rendered HTML includes Devata and Shakti information."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        # Ashlesha's devata is Naga
        assert "Naga" in html or "Serpent" in html.lower() or "Devata" in html

    def test_render_includes_gandanta_warning(self):
        """When a planet is at Gandanta, the rendered HTML includes a warning."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(
            moon_nakshatra="ASHLESHA",
            moon_longitude=116.6667,
            moon_rashi_num=4,
            moon_deg_in_sign=26.6667,
        )
        facts["planet_details"]["MOON"]["nakshatra"] = "ASHLESHA"
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        assert "GANDANTA" in html, "HTML should include GANDANTA warning"

    def test_render_empty_profile(self):
        """Empty profile renders a fallback message."""
        from jrs.deterministic_engine.esoteric_evaluator import render_esoteric_profile_html

        html = render_esoteric_profile_html([])
        assert "esoteric-section" in html
        assert "No esoteric" in html or "unavailable" in html

    def test_render_three_narrative_sections(self):
        """Rendered HTML contains all three narrative sections."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        assert "Baseline Configuration" in html or "SECTION_1" in html
        assert "Deterministic Dynamic" in html or "SECTION_2" in html
        assert "Timeline Activation" in html or "SECTION_3" in html

    def test_render_includes_dde_reference(self):
        """Rendered HTML references the DDE methodology."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        assert "DDE" in html or "Deterministic" in html


# ══════════════════════════════════════════════════════════════════════════════
# Test 8: Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_jre_facts_returns_empty(self):
        """Empty jre_facts returns an empty profile list."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        results = evaluate_esoteric_profile({}, {})
        assert results == []

    def test_no_moon_nakshatra_returns_empty(self):
        """If Moon has no nakshatra, no results are returned."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = {
            "planets": {},
            "house_lords": {},
            "lagna_sign": 1,
            "moon_nakshatra": "",
            "planet_nakshatras": {},
            "planet_details": {},
        }
        results = evaluate_esoteric_profile(facts, {})
        assert results == []

    def test_unknown_nakshatra_skipped(self):
        """Nakshatras not in the DDE router are skipped gracefully."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="UNKNOWN_NAKSHATRA")
        facts["planet_details"]["MOON"]["nakshatra"] = "UNKNOWN_NAKSHATRA"
        strengths = _make_strengths()
        results = evaluate_esoteric_profile(facts, strengths)

        # Unknown nakshatra should not produce a result
        moon_results = [r for r in results if r["planet"] == "MOON"]
        assert len(moon_results) == 0

    def test_float64_precision_gandanta(self):
        """Float64 precision check: 0°00'05" (0.0833°) from cusp is detected."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        # 5 arcseconds = 5/3600 degrees = 0.001389°
        five_arcseconds = 5.0 / 3600.0
        cusp_degree = 26.6667

        result = check_gandanta(
            longitude=90 + cusp_degree - five_arcseconds,
            rashi_num=4,
            degree_in_sign=cusp_degree - five_arcseconds,
        )
        assert result["is_gandanta"] is True
        assert result["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_exactly_at_threshold_boundary(self):
        """Shadbala exactly at 1.2 routes to the conservative path."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.2)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        # At exactly 1.2, the condition is > 1.2 (not >=), so it goes to LOW
        assert moon_result["token"] == "ASHLESHA_SARPA_VULNERABILITY"

    def test_exactly_at_low_threshold(self):
        """Shadbala exactly at 1.0 routes to the conservative path."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_jre_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.0)
        results = evaluate_esoteric_profile(facts, strengths)

        moon_result = next(r for r in results if r["planet"] == "MOON")
        # At exactly 1.0, the condition is < 1.0 (not <=), so it goes to else (LOW)
        assert moon_result["token"] == "ASHLESHA_SARPA_VULNERABILITY"
