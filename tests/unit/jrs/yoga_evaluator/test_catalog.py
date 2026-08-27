"""JRS-088 Yoga Catalog Rules unit tests.

Tests that the YogaEvaluatorService correctly evaluates classical yogas
defined in the config/yoga/rules.toml catalog.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService

# Path to the yoga rules TOML config
_CONFIG_DIR = Path(__file__).resolve().parents[4] / "config" / "yoga"
_RULES_TOML = _CONFIG_DIR / "rules.toml"


def _load_yoga_rules() -> list[dict]:
    """Load yoga rules from the TOML config file."""
    with open(_RULES_TOML, "rb") as f:
        data = tomllib.load(f)
    return data.get("yoga", {}).get("rules", [])


class TestYogaCatalog:
    """Tests for classical yoga rules loaded from config/yoga/rules.toml."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        """Load rules from TOML and instantiate the service."""
        self.rules = _load_yoga_rules()
        self.service = YogaEvaluatorService()

    def _get_rules_by_name(self, yoga_name: str) -> list[dict]:
        """Get all rules for a specific yoga name."""
        return [r for r in self.rules if r["yoga_name"] == yoga_name]

    # ── Chandra Mangala Yoga Tests ──────────────────────────────────────────

    def test_chandra_mangala_conjunction_forms(self) -> None:
        """Chandra Mangala: Moon + Mars conjunction -> FORMED."""
        rules = self._get_rules_by_name("Chandra Mangala")
        assert len(rules) >= 1, "Chandra Mangala rules must exist in catalog"

        rule = next(r for r in rules if r["formation_type"] == "CONJUNCTION")
        assert rule["outcome"] == "WEALTH_ACCUMULATION"

        facts = {
            "planets": {
                "MOON": {"house": 7, "combust": False, "debilitated": False},
                "MARS": {"house": 7, "combust": False, "debilitated": False},
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=rule["involved_planets"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.yoga_name == "Chandra Mangala"

    def test_chandra_mangala_combust_cancels(self) -> None:
        """Chandra Mangala: Moon combust -> CANCELLED."""
        rules = self._get_rules_by_name("Chandra Mangala")
        rule = next(r for r in rules if r["formation_type"] == "CONJUNCTION")

        facts = {
            "planets": {
                "MOON": {"house": 7, "combust": True, "debilitated": False},
                "MARS": {"house": 7, "combust": False, "debilitated": False},
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=rule["involved_planets"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.CANCELLED
        assert result.cancellation_reason == "MOON is combust"

    def test_chandra_mangala_outcome_in_toml(self) -> None:
        """Chandra Mangala TOML rule specifies WEALTH_ACCUMULATION."""
        rules = self._get_rules_by_name("Chandra Mangala")
        for rule in rules:
            assert rule["outcome"] == "WEALTH_ACCUMULATION"

    # ── Budhaditya Yoga Tests ───────────────────────────────────────────────

    def test_budhaditya_conjunction_forms(self) -> None:
        """Budhaditya: Sun + Mercury conjunction -> FORMED."""
        rules = self._get_rules_by_name("Budhaditya")
        assert len(rules) >= 1, "Budhaditya rules must exist in catalog"

        rule = next(r for r in rules if r["formation_type"] == "CONJUNCTION")
        assert rule["outcome"] == "CAREER_PROMINENCE"

        facts = {
            "planets": {
                "SUN": {"house": 10, "combust": False, "debilitated": False},
                "MERCURY": {"house": 10, "combust": False, "debilitated": False},
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=rule["involved_planets"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.yoga_name == "Budhaditya"

    def test_budhaditya_debilitated_cancels(self) -> None:
        """Budhaditya: Mercury debilitated -> CANCELLED."""
        rules = self._get_rules_by_name("Budhaditya")
        rule = next(r for r in rules if r["formation_type"] == "CONJUNCTION")

        facts = {
            "planets": {
                "SUN": {"house": 10, "combust": False, "debilitated": False},
                "MERCURY": {"house": 10, "combust": False, "debilitated": True},
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=rule["involved_planets"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.CANCELLED
        assert "MERCURY" in result.cancellation_reason
        assert "debilitated" in result.cancellation_reason.lower()

    def test_budhaditya_outcome_in_toml(self) -> None:
        """Budhaditya TOML rule specifies CAREER_PROMINENCE (INTELLECTUAL_DEPTH mapped)."""
        rules = self._get_rules_by_name("Budhaditya")
        for rule in rules:
            assert rule["outcome"] == "CAREER_PROMINENCE"

    # ── Lakshmi Yoga Tests ──────────────────────────────────────────────────

    def test_lakshmi_lords_in_kendra_forms(self) -> None:
        """Lakshmi: Lagna lord + 9th lord in Kendra -> FORMED."""
        rules = self._get_rules_by_name("Lakshmi")
        assert len(rules) >= 1, "Lakshmi rules must exist in catalog"

        rule = next(r for r in rules if r["formation_type"] == "LORDS_IN_KENDRA")
        assert rule["outcome"] == "WEALTH_ACCUMULATION"

        facts = {
            "planets": {
                "MARS": {"house": 1, "combust": False, "debilitated": False},  # Lagna lord in Kendra
                "JUPITER": {"house": 4, "combust": False, "debilitated": False},  # 9th lord in Kendra
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=rule["involved_planets"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.yoga_name == "Lakshmi"

    def test_lakshmi_involved_planet_in_dusthana_weakens(self) -> None:
        """Lakshmi: involved planet in dusthana (6th) -> WEAKENED."""
        rules = self._get_rules_by_name("Lakshmi")
        rule = next(r for r in rules if r["formation_type"] == "LORDS_IN_KENDRA")

        # Use actual planet names that the service can look up
        facts = {
            "planets": {
                "MARS": {"house": 6, "combust": False, "debilitated": False},  # in dusthana
                "JUPITER": {"house": 4, "combust": False, "debilitated": False},
            }
        }
        result = self.service.evaluate_formation(
            yoga_name=rule["yoga_name"],
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.WEAKENED

    def test_lakshmi_outcome_in_toml(self) -> None:
        """Lakshmi TOML rule specifies WEALTH_ACCUMULATION."""
        rules = self._get_rules_by_name("Lakshmi")
        for rule in rules:
            assert rule["outcome"] == "WEALTH_ACCUMULATION"

    # ── Catalog Structure Tests ─────────────────────────────────────────────

    def test_all_rules_have_required_fields(self) -> None:
        """Every rule in the catalog must have all required metadata fields."""
        required_fields = {
            "rule_id", "yoga_name", "description", "formation_type",
            "involved_planets", "involved_houses", "condition_facts",
            "outcome", "direction", "strength", "source_id", "location",
        }
        for rule in self.rules:
            missing = required_fields - set(rule.keys())
            assert not missing, f"Rule {rule.get('rule_id', '?')} missing: {missing}"

    def test_catalog_contains_all_three_yogas(self) -> None:
        """Catalog must contain Chandra Mangala, Budhaditya, and Lakshmi."""
        yoga_names = {r["yoga_name"] for r in self.rules}
        assert "Chandra Mangala" in yoga_names
        assert "Budhaditya" in yoga_names
        assert "Lakshmi" in yoga_names
