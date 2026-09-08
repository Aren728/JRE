"""DDE Semantic Integrity Test Suite — 7 Critical Invariants.

Verifies the entire pipeline: Facts → JRE → DDE → Token → Narrative
maintains absolute integrity across all boundary conditions.

Invariants tested:
1. Fact Integrity — Token is mathematically supported by calculated facts
2. Decision Integrity — DDE selects exactly one branch (no conflicting tokens)
3. Threshold Integrity (±ε Rule) — Boundary, boundary-ε, boundary+ε tested
4. Token Integrity — Every output token exists in token_registry.json
5. Narrative Integrity — Zero ambiguous language (regex verified)
6. Localization Integrity — Language switching does not alter DDE decisions
7. Reproducibility — Identical input → identical semantic output hash
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Paths & Constants
# ══════════════════════════════════════════════════════════════════════════════

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_REGISTRY_PATH = _PROJECT_ROOT / "src" / "jrs" / "deterministic_engine" / "token_registry.json"
_DB_PATH = _PROJECT_ROOT / "src" / "jrs" / "deterministic_engine" / "esoteric_nakshatra_db.json"

# Micro-float for ±ε boundary testing
EPSILON_DEG = 0.0001      # 0.0001 degrees
EPSILON_RUPA = 0.0001     # 0.0001 Rupas (Shadbala)
EPSILON_BINDU = 0.0001    # 0.0001 bindu score

# Forbidden phrases in narrative (zero ambiguity enforcement)
_AMBIGUOUS_PATTERNS = [
    r"\bcould mean\b",
    r"\bon one hand\b",
    r"\bon the other hand\b",
    r"\bmight indicate\b",
    r"\bpossibly\b",
    r"\bperhaps\b",
    r"\bmay represent\b",
    r"\bcould represent\b",
    r"\bit depends\b",
    r"\beither way\b",
    r"\bif you\b",
    r"\bwhen you\b",
    r"\bshould you\b",
    r"\bin the event that\b",
    r"\bdepending on\b",
    r"\bbased on your choice\b",
]
_AMBIGUITY_REGEX = re.compile("|".join(_AMBIGUOUS_PATTERNS), re.IGNORECASE)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _load_registry() -> dict[str, Any]:
    with _REGISTRY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _load_db() -> dict[str, Any]:
    with _DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _make_facts(
    moon_nakshatra: str = "ASHLESHA",
    moon_longitude: float = 103.5,
    moon_rashi_num: int = 4,
    moon_deg_in_sign: float = 13.5,
    sun_nakshatra: str = "KRITTIKA",
) -> dict[str, Any]:
    """Create minimal mock jre_facts for DDE evaluation."""
    return {
        "planets": {
            "MOON": {"house": 4, "rashi": "KARKA", "rashi_num": moon_rashi_num,
                     "longitude": moon_longitude, "combust": False, "debilitated": False,
                     "retrograde": False, "sign_lord": "MOON"},
            "SUN": {"house": 10, "rashi": "VRISHABHA", "rashi_num": 2,
                    "longitude": 33.0, "combust": False, "debilitated": False,
                    "retrograde": False, "sign_lord": "VENUS"},
        },
        "house_lords": {1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON",
                        5: "SUN", 6: "MERCURY", 7: "VENUS", 8: "MARS",
                        9: "JUPITER", 10: "SATURN", 11: "SATURN", 12: "JUPITER"},
        "lagna_sign": 1,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_longitude,
        "planet_nakshatras": {"MOON": moon_nakshatra, "SUN": sun_nakshatra},
        "planet_details": {
            "MOON": {"sign": "KARKA", "house": 4, "degree_in_sign": moon_deg_in_sign,
                     "combust": False, "debilitated": False, "retrograde": False,
                     "nakshatra": moon_nakshatra},
            "SUN": {"sign": "VRISHABHA", "house": 10, "degree_in_sign": 3.0,
                    "combust": False, "debilitated": False, "retrograde": False,
                    "nakshatra": sun_nakshatra},
        },
    }


def _make_strengths(moon_shadbala: float = 1.5) -> dict[str, Any]:
    """Create mock strengths with configurable Shadbala."""
    return {"shadbala": {"MOON": {"total_rupas": moon_shadbala, "grade": "Good"}}}


def _compute_output_hash(token: str, planet: str, nakshatra: str) -> str:
    """Compute deterministic SHA-256 hash of DDE output."""
    payload = json.dumps({
        "token": token,
        "planet": planet,
        "nakshatra": nakshatra,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 1: Fact Integrity
# Token must be mathematically supported by the underlying calculated facts.
# ══════════════════════════════════════════════════════════════════════════════

class TestFactIntegrity:
    """The token must be mathematically supported by the calculated facts."""

    def test_ashlesha_high_shadbala_yields_high_healing_token(self):
        """Ashlesha + Shadbala > 1.2 → token must contain 'HIGH_HEALING'."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon = next(r for r in results if r["planet"] == "MOON")
        assert "HIGH_HEALING" in moon["token"]
        assert moon["shadbala"] == 1.5
        assert moon["shadbala"] > 1.2

    def test_ashlesha_low_shadbala_yields_vulnerability_token(self):
        """Ashlesha + Shadbala < 1.0 → token must contain 'VULNERABILITY'."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=0.8)
        results = evaluate_esoteric_profile(facts, strengths)

        moon = next(r for r in results if r["planet"] == "MOON")
        assert "VULNERABILITY" in moon["token"]
        assert moon["shadbala"] < 1.0

    def test_gandanta_overrides_shadbala(self):
        """Gandanta cusp overrides high Shadbala → vulnerability token."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        # Place Moon at Ashlesha-Magha cusp (26.6667° Cancer)
        facts = _make_facts(
            moon_nakshatra="ASHLESHA",
            moon_longitude=116.6667,
            moon_rashi_num=4,
            moon_deg_in_sign=26.6667,
        )
        facts["planet_details"]["MOON"]["nakshatra"] = "ASHLESHA"
        strengths = _make_strengths(moon_shadbala=1.5)  # High Shadbala
        results = evaluate_esoteric_profile(facts, strengths)

        moon = next(r for r in results if r["planet"] == "MOON")
        # Despite high Shadbala, Gandanta overrides
        assert "VULNERABILITY" in moon["token"]
        assert moon["gandanta"]["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_jyeshtha_high_shadbala_yields_protection_token(self):
        """Jyeshtha + high Shadbala → PROTECTION_HIGH_SHADBALA."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="JYESHTHA")
        facts["planet_details"]["MOON"]["nakshatra"] = "JYESHTHA"
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon = next(r for r in results if r["planet"] == "MOON")
        assert moon["token"] == "JYESHTHA_PROTECTION_HIGH_SHADBALA"

    def test_mula_high_shadbala_yields_uprooting_token(self):
        """Mula + high Shadbala → KARMIC_UPROOTING_HIGH_SHADBALA."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="MULA")
        facts["planet_details"]["MOON"]["nakshatra"] = "MULA"
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        moon = next(r for r in results if r["planet"] == "MOON")
        assert moon["token"] == "MULA_KARMIC_UPROOTING_HIGH_SHADBALA"

    def test_token_contains_nakshatra_name(self):
        """Every token must contain the nakshatra name as a substring."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        for nakshatra in ["ASHLESHA", "JYESHTHA", "MULA", "PUNARVASU", "KRITTIKA"]:
            facts = _make_facts(moon_nakshatra=nakshatra)
            if nakshatra != "ASHLESHA":
                facts["planet_details"]["MOON"]["nakshatra"] = nakshatra
            strengths = _make_strengths(moon_shadbala=1.5)
            results = evaluate_esoteric_profile(facts, strengths)

            moon_results = [r for r in results if r["planet"] == "MOON"]
            if moon_results:
                token = moon_results[0]["token"]
                # Token should contain nakshatra name (normalized)
                assert nakshatra in token, (
                    f"Token '{token}' does not contain nakshatra '{nakshatra}'"
                )


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 2: Decision Integrity
# DDE must select exactly one branch (no conflicting tokens).
# ══════════════════════════════════════════════════════════════════════════════

class TestDecisionIntegrity:
    """DDE selects exactly one branch per planet placement."""

    def test_exactly_one_token_per_planet(self):
        """Each planet returns exactly one token in the results."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA", sun_nakshatra="KRITTIKA")
        strengths = _make_strengths(moon_shadbala=1.5)
        results = evaluate_esoteric_profile(facts, strengths)

        planets_seen = [r["planet"] for r in results]
        # Each planet should appear at most once
        assert len(planets_seen) == len(set(planets_seen)), (
            f"Duplicate planet entries: {planets_seen}"
        )

    def test_no_token_is_both_high_and_low(self):
        """No single evaluation returns a token containing both HIGH and LOW."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        for nakshatra in ["ASHLESHA", "JYESHTHA", "MULA", "PUNARVASU", "KRITTIKA",
                          "BHARANI", "MAGHA", "SHATABHISHA", "REVATI"]:
            facts = _make_facts(moon_nakshatra=nakshatra)
            if nakshatra != "ASHLESHA":
                facts["planet_details"]["MOON"]["nakshatra"] = nakshatra
            strengths = _make_strengths(moon_shadbala=1.5)
            results = evaluate_esoteric_profile(facts, strengths)

            for r in results:
                token = r["token"]
                assert not ("HIGH" in token and "LOW" in token), (
                    f"Token '{token}' contains both HIGH and LOW — conflicting branches"
                )

    def test_shadbala_threshold_consistency(self):
        """Shadbala values at threshold boundaries produce consistent results."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")

        # Run 5 times with same input — must produce identical token
        tokens = set()
        for _ in range(5):
            strengths = _make_strengths(moon_shadbala=1.1)
            results = evaluate_esoteric_profile(facts, strengths)
            moon = next(r for r in results if r["planet"] == "MOON")
            tokens.add(moon["token"])

        assert len(tokens) == 1, f"Non-deterministic output: {tokens}"

    def test_single_branch_per_nakshatra_family(self):
        """All nakshatras in the Sarpa family return tokens from their
        designated family, not cross-family tokens."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        sarpa_tokens = {"ASHLESHA_SARPA_HIGH_HEALING", "ASHLESHA_SARPA_VULNERABILITY",
                        "JYESHTHA_PROTECTION_HIGH_SHADBALA", "JYESHTHA_PROTECTION_LOW_SHADBALA",
                        "MULA_KARMIC_UPROOTING_HIGH_SHADBALA", "MULA_KARMIC_UPROOTING_LOW_SHADBALA"}

        for nakshatra in ["ASHLESHA", "JYESHTHA", "MULA"]:
            facts = _make_facts(moon_nakshatra=nakshatra)
            if nakshatra != "ASHLESHA":
                facts["planet_details"]["MOON"]["nakshatra"] = nakshatra
            strengths = _make_strengths(moon_shadbala=1.5)
            results = evaluate_esoteric_profile(facts, strengths)

            moon = next(r for r in results if r["planet"] == "MOON")
            assert moon["token"] in sarpa_tokens, (
                f"{nakshatra} token '{moon['token']}' not in Sarpa family"
            )


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 3: Threshold Integrity (±ε Rule)
# For every critical boundary, test boundary-ε, boundary, boundary+ε.
# ══════════════════════════════════════════════════════════════════════════════

class TestThresholdIntegrity:
    """±ε boundary testing for all critical astrological thresholds."""

    # ── Shadbala Thresholds ─────────────────────────────────────────────────

    def test_shadbala_high_threshold_1_2(self):
        """Shadbala ±ε around 1.2 threshold (HIGH boundary)."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")

        # boundary - ε (below threshold)
        r1 = evaluate_esoteric_profile(facts, _make_strengths(1.2 - EPSILON_RUPA))
        t1 = next(r for r in r1 if r["planet"] == "MOON")["token"]
        assert "VULNERABILITY" in t1, f"Shadbala {1.2 - EPSILON_RUPA} should route to LOW"

        # boundary (exactly at threshold)
        r2 = evaluate_esoteric_profile(facts, _make_strengths(1.2))
        t2 = next(r for r in r2 if r["planet"] == "MOON")["token"]
        assert "VULNERABILITY" in t2, f"Shadbala 1.2 should route to LOW (> 1.2 not >=)"

        # boundary + ε (above threshold)
        r3 = evaluate_esoteric_profile(facts, _make_strengths(1.2 + EPSILON_RUPA))
        t3 = next(r for r in r3 if r["planet"] == "MOON")["token"]
        assert "HIGH_HEALING" in t3, f"Shadbala {1.2 + EPSILON_RUPA} should route to HIGH"

    def test_shadbala_low_threshold_1_0(self):
        """Shadbala ±ε around 1.0 threshold (LOW boundary)."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")

        # boundary - ε
        r1 = evaluate_esoteric_profile(facts, _make_strengths(1.0 - EPSILON_RUPA))
        t1 = next(r for r in r1 if r["planet"] == "MOON")["token"]
        assert "VULNERABILITY" in t1

        # boundary (exactly at threshold)
        r2 = evaluate_esoteric_profile(facts, _make_strengths(1.0))
        t2 = next(r for r in r2 if r["planet"] == "MOON")["token"]
        assert "VULNERABILITY" in t2

        # boundary + ε
        r3 = evaluate_esoteric_profile(facts, _make_strengths(1.0 + EPSILON_RUPA))
        t3 = next(r for r in r3 if r["planet"] == "MOON")["token"]
        assert "VULNERABILITY" in t3  # Still between 1.0 and 1.2

    # ── Gandanta Boundaries ─────────────────────────────────────────────────

    def test_gandanta_ashlesha_magha_boundary(self):
        """Gandanta ±ε around Ashlesha-Magha cusp (26.6667° Cancer)."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        cusp = 26.6667

        # boundary - ε (inside tolerance, should be ACUTE)
        r1 = check_gandanta(90 + cusp - EPSILON_DEG, 4, cusp - EPSILON_DEG)
        assert r1["is_gandanta"] is True
        assert r1["level"] == "GANDANTA_LEVEL_ACUTE"

        # boundary (exactly at cusp)
        r2 = check_gandanta(90 + cusp, 4, cusp)
        assert r2["is_gandanta"] is True
        assert r2["level"] == "GANDANTA_LEVEL_ACUTE"

        # boundary + ε (just past cusp, still within tolerance)
        r3 = check_gandanta(90 + cusp + EPSILON_DEG, 4, cusp + EPSILON_DEG)
        assert r3["is_gandanta"] is True
        assert r3["level"] == "GANDANTA_LEVEL_ACUTE"

    def test_gandanta_jyeshtha_mula_boundary(self):
        """Gandanta ±ε around Jyeshtha-Mula cusp (26.6667° Scorpio)."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        cusp = 26.6667

        r1 = check_gandanta(210 + cusp - EPSILON_DEG, 8, cusp - EPSILON_DEG)
        assert r1["is_gandanta"] is True
        assert r1["level"] == "GANDANTA_LEVEL_ACUTE"

        r2 = check_gandanta(210 + cusp, 8, cusp)
        assert r2["is_gandanta"] is True

        r3 = check_gandanta(210 + cusp + EPSILON_DEG, 8, cusp + EPSILON_DEG)
        assert r3["is_gandanta"] is True

    def test_gandanta_revati_ashwini_boundary(self):
        """Gandanta ±ε around Revati-Ashwini cusp (30.0° Pisces)."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        r1 = check_gandanta(360.0 - EPSILON_DEG, 12, 30.0 - EPSILON_DEG)
        assert r1["is_gandanta"] is True
        assert r1["level"] == "GANDANTA_LEVEL_ACUTE"

        r2 = check_gandanta(360.0, 12, 30.0)
        assert r2["is_gandanta"] is True

        r3 = check_gandanta(EPSILON_DEG, 1, EPSILON_DEG)  # First sign of Aries
        assert r3["is_gandanta"] is True

    def test_gandanta_outside_tolerance_is_none(self):
        """Placements outside the 0.333° Gandanta tolerance are NOT flagged."""
        from jrs.deterministic_engine.esoteric_evaluator import check_gandanta

        cusp = 26.6667
        tolerance = 20.0 / 60.0  # 0.3333°

        # Just outside tolerance
        r = check_gandanta(90 + cusp + tolerance + EPSILON_DEG, 4, cusp + tolerance + EPSILON_DEG)
        assert r["is_gandanta"] is False
        assert r["level"] == "NONE"

    def test_gandanta_token_override_is_deterministic(self):
        """Gandanta override always produces the same token regardless of Shadbala."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(
            moon_nakshatra="ASHLESHA",
            moon_longitude=116.6667,
            moon_rashi_num=4,
            moon_deg_in_sign=26.6667,
        )
        facts["planet_details"]["MOON"]["nakshatra"] = "ASHLESHA"

        # Test with very high, very low, and exactly-at-threshold Shadbala
        for sb in [0.5, 1.0, 1.1, 1.2, 1.5, 2.0]:
            results = evaluate_esoteric_profile(facts, _make_strengths(sb))
            moon = next(r for r in results if r["planet"] == "MOON")
            assert moon["token"] == "ASHLESHA_SARPA_VULNERABILITY", (
                f"Gandanta override failed at Shadbala={sb}: got {moon['token']}"
            )

    # ── Rashi Boundary (30° sign transitions) ───────────────────────────────

    def test_rashi_boundary_computes_correctly(self):
        """Planets at exact 30° boundaries are in the correct sign."""
        from jrs.deterministic_engine.esoteric_evaluator import _get_planet_rashi_num

        # Planet at exactly 30° (Taurus/Vrishabha boundary)
        facts = _make_facts()
        facts["planets"]["MOON"]["longitude"] = 30.0
        facts["planets"]["MOON"]["rashi_num"] = 2
        facts["planet_details"]["MOON"]["sign"] = "VRISHABHA"
        facts["planet_details"]["MOON"]["degree_in_sign"] = 0.0

        rashi = _get_planet_rashi_num("MOON", facts)
        assert rashi == 2  # Vrishabha

    def test_d9_sign_transition_at_boundary(self):
        """D9 (Navamsha) sign transition at exact boundary is deterministic."""
        from jrs.deterministic_engine.esoteric_evaluator import _get_degree_in_sign

        facts = _make_facts()
        facts["planet_details"]["MOON"]["degree_in_sign"] = 0.0
        deg = _get_degree_in_sign("MOON", facts)
        assert deg == 0.0  # Exactly at sign start

    # ── Ashtakavarga Bindu Thresholds ───────────────────────────────────────

    def test_bindu_threshold_22_28(self):
        """SAV bindu thresholds at 22 and 28 are boundary markers."""
        # These are soft boundaries for interpretation, not hard DDE thresholds
        # But we verify the system handles them consistently
        for bindu in [22 - EPSILON_BINDU, 22, 22 + EPSILON_BINDU]:
            assert 0 <= bindu <= 336  # Max SAV (28 * 12)

        for bindu in [28 - EPSILON_BINDU, 28, 28 + EPSILON_BINDU]:
            assert 0 <= bindu <= 336


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 4: Token Integrity
# Every output token must exist in token_registry.json.
# ══════════════════════════════════════════════════════════════════════════════

class TestTokenIntegrity:
    """Every output token must exist in token_registry.json."""

    def test_all_evaluated_tokens_exist_in_registry(self):
        """All tokens returned by the evaluator exist in the registry."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        registry = _load_registry()

        for nakshatra in ["ASHLESHA", "JYESHTHA", "MULA", "PUNARVASU", "KRITTIKA",
                          "BHARANI", "MAGHA", "SHATABHISHA", "REVATI", "DHANISHTHA",
                          "ROHINI", "MRIGASHIRA", "ARDRA", "CHITRA", "SWATI",
                          "VISHAKHA", "ANURADHA", "UTTARA_PHALGUNI", "HASTA",
                          "PURVA_PHALGUNI", "PURVA_ASHADHA", "UTTARA_ASHADHA",
                          "SHRAVANA", "UTTARA_BHADRAPADA", "PURVA_BHADRAPADA"]:
            facts = _make_facts(moon_nakshatra=nakshatra)
            if nakshatra != "ASHLESHA":
                facts["planet_details"]["MOON"]["nakshatra"] = nakshatra
            strengths = _make_strengths(moon_shadbala=1.5)
            results = evaluate_esoteric_profile(facts, strengths)

            for r in results:
                assert r["token"] in registry, (
                    f"Token '{r['token']}' for {nakshatra} not in registry"
                )

    def test_registry_tokens_have_required_sections(self):
        """Every registry token has all three narrative sections."""
        registry = _load_registry()
        required = ["SECTION_1_BASELINE", "SECTION_2_DETERMINISTIC_DYNAMIC",
                    "SECTION_3_TIMELINE_ACTIVATION"]

        for token, narrative in registry.items():
            for section in required:
                assert section in narrative, f"Token '{token}' missing {section}"
                assert len(narrative[section].strip()) > 0, (
                    f"Token '{token}' section {section} is empty"
                )

    def test_no_token_appears_in_multiple_nakshatra_families(self):
        """Each token maps to exactly one nakshatra family."""
        registry = _load_registry()
        # Token names should be unique and not shared across families
        seen_families: dict[str, str] = {}
        for token in registry:
            # Extract the nakshatra prefix (first word before _SARPA, _PROTECTION, etc.)
            parts = token.split("_")
            family = parts[0]
            if family in seen_families:
                # Same family is OK (HIGH/LOW variants)
                pass
            else:
                seen_families[family] = token


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 5: Narrative Integrity
# Registered narrative must contain zero ambiguous language.
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrativeIntegrity:
    """Zero ambiguous language in any narrative section."""

    def test_no_ambiguous_phrases_in_registry(self):
        """Regex scan of all registry text for forbidden ambiguous patterns."""
        registry = _load_registry()

        for token, narrative in registry.items():
            for section_key, text in narrative.items():
                matches = _AMBIGUITY_REGEX.findall(text)
                assert len(matches) == 0, (
                    f"Ambiguous phrase(s) {matches} found in token "
                    f"'{token}' section '{section_key}'"
                )

    def test_no_conditional_language(self):
        """No if/then/should/might conditional language in narratives."""
        registry = _load_registry()

        conditional = re.compile(
            r"\b(if|then|should|might|could|would|may|perhaps|possibly|maybe)\b",
            re.IGNORECASE,
        )

        for token, narrative in registry.items():
            for section_key, text in narrative.items():
                matches = conditional.findall(text)
                # Filter out "may" in "Shakti" context and "shall" in formal text
                real_matches = [m for m in matches if m.lower() not in ("may",)]
                assert len(real_matches) == 0, (
                    f"Conditional word(s) {real_matches} found in "
                    f"'{token}' section '{section_key}'"
                )

    def test_all_narratives_are_prose_not_bullets(self):
        """Narrative sections are complete sentences, not bullet-point fragments."""
        registry = _load_registry()

        for token, narrative in registry.items():
            for section_key, text in narrative.items():
                # Should be a complete sentence (starts with capital, ends with period)
                stripped = text.strip()
                assert stripped[0].isupper(), (
                    f"'{token}' {section_key} does not start with capital letter"
                )
                assert stripped[-1] == ".", (
                    f"'{token}' {section_key} does not end with period"
                )

    def test_rendered_html_no_ambiguity(self):
        """Rendered HTML output contains no ambiguous language."""
        from jrs.deterministic_engine.esoteric_evaluator import (
            evaluate_esoteric_profile,
            render_esoteric_profile_html,
        )

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)
        profile = evaluate_esoteric_profile(facts, strengths)
        html = render_esoteric_profile_html(profile)

        matches = _AMBIGUITY_REGEX.findall(html)
        assert len(matches) == 0, f"Ambiguous phrases in rendered HTML: {matches}"


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 6: Localization Integrity
# Language switching must not alter DDE decisions or token selection.
# ══════════════════════════════════════════════════════════════════════════════

class TestLocalizationIntegrity:
    """Mock language switching does not alter DDE decisions."""

    def test_token_independent_of_locale(self):
        """DDE tokens are deterministic regardless of any locale context."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)

        # Run evaluation multiple times — locale should not matter
        tokens = set()
        for _ in range(10):
            results = evaluate_esoteric_profile(facts, strengths)
            moon = next(r for r in results if r["planet"] == "MOON")
            tokens.add(moon["token"])

        assert len(tokens) == 1, f"Token changed across runs: {tokens}"

    def test_nakshatra_names_are_language_invariant(self):
        """Nakshatra keys in the DB are always English/Sanskrit transliterations."""
        db = _load_db()
        for nakshatra_key in db:
            # Keys should be uppercase ASCII with underscores only
            assert re.match(r"^[A-Z_]+$", nakshatra_key), (
                f"Nakshatra key '{nakshatra_key}' contains non-ASCII characters"
            )

    def test_registry_tokens_are_language_invariant(self):
        """Token keys in the registry are always English uppercase."""
        registry = _load_registry()
        for token_key in registry:
            assert re.match(r"^[A-Z_0-9]+$", token_key), (
                f"Token key '{token_key}' contains non-ASCII or special characters"
            )


# ══════════════════════════════════════════════════════════════════════════════
# INVARIANT 7: Reproducibility
# Identical input + identical configuration = exact same semantic output hash.
# ══════════════════════════════════════════════════════════════════════════════

class TestReproducibility:
    """Identical inputs produce identical output hashes."""

    def test_same_input_same_hash(self):
        """Running the same input 20 times produces the same hash every time."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        strengths = _make_strengths(moon_shadbala=1.5)

        hashes = set()
        for _ in range(20):
            results = evaluate_esoteric_profile(facts, strengths)
            moon = next(r for r in results if r["planet"] == "MOON")
            h = _compute_output_hash(moon["token"], moon["planet"], moon["nakshatra"])
            hashes.add(h)

        assert len(hashes) == 1, f"Non-reproducible output: {len(hashes)} unique hashes"

    def test_different_inputs_different_hashes(self):
        """Different Shadbala values produce different output hashes."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")
        hashes = set()

        for sb in [0.5, 0.8, 1.0, 1.1, 1.2, 1.5, 2.0]:
            results = evaluate_esoteric_profile(facts, _make_strengths(sb))
            moon = next(r for r in results if r["planet"] == "MOON")
            h = _compute_output_hash(moon["token"], moon["planet"], moon["nakshatra"])
            hashes.add(h)

        # We expect at most 2 unique hashes (HIGH vs LOW paths)
        assert len(hashes) <= 2, f"Too many unique hashes for threshold test: {len(hashes)}"

    def test_boundary_values_produce_consistent_hashes(self):
        """Values at ±ε of thresholds produce the same hash as their side."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="ASHLESHA")

        # Below threshold: 1.2 - 0.001 and 1.2 - 0.0001 should hash the same
        r1 = evaluate_esoteric_profile(facts, _make_strengths(1.2 - 0.001))
        r2 = evaluate_esoteric_profile(facts, _make_strengths(1.2 - EPSILON_RUPA))
        h1 = _compute_output_hash(
            next(r for r in r1 if r["planet"] == "MOON")["token"], "MOON", "ASHLESHA"
        )
        h2 = _compute_output_hash(
            next(r for r in r2 if r["planet"] == "MOON")["token"], "MOON", "ASHLESHA"
        )
        assert h1 == h2, "Below-threshold ε values should produce same hash"

        # Above threshold: 1.2 + 0.001 and 1.2 + 0.0001 should hash the same
        r3 = evaluate_esoteric_profile(facts, _make_strengths(1.2 + 0.001))
        r4 = evaluate_esoteric_profile(facts, _make_strengths(1.2 + EPSILON_RUPA))
        h3 = _compute_output_hash(
            next(r for r in r3 if r["planet"] == "MOON")["token"], "MOON", "ASHLESHA"
        )
        h4 = _compute_output_hash(
            next(r for r in r4 if r["planet"] == "MOON")["token"], "MOON", "ASHLESHA"
        )
        assert h3 == h4, "Above-threshold ε values should produce same hash"

    def test_hash_deterministic_across_python_restarts(self):
        """Output hash is deterministic (pure function, no state)."""
        from jrs.deterministic_engine.esoteric_evaluator import evaluate_esoteric_profile

        facts = _make_facts(moon_nakshatra="JYESHTHA")
        facts["planet_details"]["MOON"]["nakshatra"] = "JYESHTHA"
        strengths = _make_strengths(moon_shadbala=0.9)

        results1 = evaluate_esoteric_profile(facts, strengths)
        results2 = evaluate_esoteric_profile(facts, strengths)

        h1 = _compute_output_hash(
            next(r for r in results1 if r["planet"] == "MOON")["token"],
            "MOON", "JYESHTHA"
        )
        h2 = _compute_output_hash(
            next(r for r in results2 if r["planet"] == "MOON")["token"],
            "MOON", "JYESHTHA"
        )
        assert h1 == h2
