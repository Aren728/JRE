"""Unit tests for RI-008 Phase 1: Nakshatra-Lord Transit Intelligence Rules.

Each test verifies that specific fact combinations deterministically trigger
the correct temporal modifiers, and that classification metadata is preserved.

The 14 rules are loaded from config/temporal/nakshatra_transit.toml and
evaluated against JRE facts (JRE-003, JRE-026, JRE-010).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

# ── TOML Loader (self-contained for testing) ─────────────────────────────────


def _load_transit_rules(
    path: Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Load nakshatra transit rules from TOML config.

    Returns a tuple of rule dictionaries with all fields preserved.
    """
    config_path = path or (
        Path(__file__).resolve()
        .parent.parent.parent.parent.parent
        / "config" / "temporal" / "nakshatra_transit.toml"
    )
    if not config_path.exists():
        raise FileNotFoundError(f"Transit config not found: {config_path}")

    with config_path.open("rb") as f:
        raw: dict[str, Any] = tomllib.load(f)

    section = raw.get("nakshatra_transit")
    if not isinstance(section, dict):
        raise ValueError("Missing [nakshatra_transit] section")

    rules_raw = section.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ValueError("rules must be a list")

    return tuple(rules_raw)


def _get_rule_by_id(
    rules: tuple[dict[str, Any], ...],
    rule_id: str,
) -> dict[str, Any] | None:
    """Return a rule dict matching a specific rule_id."""
    for rule in rules:
        if rule.get("rule_id") == rule_id:
            return rule
    return None


def _evaluate_condition(condition: str, facts: dict[str, Any]) -> bool:
    """Evaluate a single condition against facts (simplified evaluator)."""
    condition = condition.strip()

    # Equality check
    has_eq = "=" in condition
    no_ne = "!=" not in condition
    no_le = "<=" not in condition
    no_ge = ">=" not in condition
    if has_eq and no_ne and no_le and no_ge:
        parts = condition.split("=", 1)
        fact_name = parts[0].strip()
        target = parts[1].strip().strip("'\"")
        fact_val = facts.get(fact_name)
        return str(fact_val).lower() == target.lower() if fact_val is not None else False

    # Truthy check
    fact_val = facts.get(condition)
    return bool(fact_val) if fact_val is not None else False


def _evaluate_rule(
    rule: dict[str, Any],
    facts: dict[str, Any],
) -> bool:
    """Evaluate a rule's conditions against facts. All must be satisfied (AND)."""
    conditions = rule.get("condition_facts", [])
    if not isinstance(conditions, list):
        return False
    return all(_evaluate_condition(c, facts) for c in conditions)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestTransitRuleLoading:
    """Tests for TOML rule loading and structure."""

    def test_all_14_rules_loaded(self) -> None:
        """Exactly 14 rules should be present in the config."""
        rules = _load_transit_rules()
        assert len(rules) == 14

    def test_unique_rule_ids(self) -> None:
        """All rule IDs should be unique."""
        rules = _load_transit_rules()
        ids = [r["rule_id"] for r in rules]
        assert len(ids) == len(set(ids))

    def test_all_rules_have_classification(self) -> None:
        """Every rule must include a classification field."""
        rules = _load_transit_rules()
        valid_classifications = {
            "CLASSICAL_PRIMARY",
            "COMMENTARY_DEPENDENT",
            "LATER_TRADITION",
        }
        for rule in rules:
            assert "classification" in rule, f"Rule {rule['rule_id']} missing classification"
            assert rule["classification"] in valid_classifications, (
                f"Rule {rule['rule_id']} has invalid classification: {rule['classification']}"
            )

    def test_all_rules_have_source(self) -> None:
        """Every rule must include a source field."""
        rules = _load_transit_rules()
        for rule in rules:
            assert "source" in rule, f"Rule {rule['rule_id']} missing source"
            assert rule["source"], f"Rule {rule['rule_id']} has empty source"

    def test_all_rules_have_condition_facts(self) -> None:
        """Every rule must include condition_facts."""
        rules = _load_transit_rules()
        for rule in rules:
            assert "condition_facts" in rule, f"Rule {rule['rule_id']} missing condition_facts"
            assert isinstance(rule["condition_facts"], list), (
                f"Rule {rule['rule_id']}: condition_facts must be a list"
            )

    def test_all_rules_have_strength(self) -> None:
        """Every rule must include a strength field."""
        rules = _load_transit_rules()
        for rule in rules:
            assert "strength" in rule, f"Rule {rule['rule_id']} missing strength"
            assert 0.0 <= rule["strength"] <= 1.0, (
                f"Rule {rule['rule_id']}: strength must be in [0, 1]"
            )


class TestTransitRuleClassifications:
    """Tests that classification metadata is correct for each rule."""

    def test_classical_primary_rules(self) -> None:
        """Rules R-TRANSIT-001, 002, 003 are CLASSICAL_PRIMARY."""
        rules = _load_transit_rules()
        classical_ids = {"R-TRANSIT-001", "R-TRANSIT-002", "R-TRANSIT-003"}
        for rule_id in classical_ids:
            rule = _get_rule_by_id(rules, rule_id)
            assert rule is not None, f"Rule {rule_id} not found"
            assert rule["classification"] == "CLASSICAL_PRIMARY", (
                f"Rule {rule_id} should be CLASSICAL_PRIMARY, got {rule['classification']}"
            )

    def test_commentary_dependent_rules(self) -> None:
        """Rules R-TRANSIT-004, 005, 006, 007, 014 are COMMENTARY_DEPENDENT."""
        rules = _load_transit_rules()
        commentary_ids = {"R-TRANSIT-004", "R-TRANSIT-005", "R-TRANSIT-006",
                          "R-TRANSIT-007", "R-TRANSIT-014"}
        for rule_id in commentary_ids:
            rule = _get_rule_by_id(rules, rule_id)
            assert rule is not None, f"Rule {rule_id} not found"
            assert rule["classification"] == "COMMENTARY_DEPENDENT", (
                f"Rule {rule_id} should be COMMENTARY_DEPENDENT, got {rule['classification']}"
            )

    def test_later_tradition_rules(self) -> None:
        """Rules R-TRANSIT-008 through 013 are LATER_TRADITION."""
        rules = _load_transit_rules()
        later_ids = {f"R-TRANSIT-{i:03d}" for i in range(8, 14)}
        for rule_id in later_ids:
            rule = _get_rule_by_id(rules, rule_id)
            assert rule is not None, f"Rule {rule_id} not found"
            assert rule["classification"] == "LATER_TRADITION", (
                f"Rule {rule_id} should be LATER_TRADITION, got {rule['classification']}"
            )

    def test_classification_distribution(self) -> None:
        """Verify the correct number of rules per classification."""
        rules = _load_transit_rules()
        counts: dict[str, int] = {}
        for rule in rules:
            c = rule["classification"]
            counts[c] = counts.get(c, 0) + 1
        assert counts.get("CLASSICAL_PRIMARY", 0) == 3
        assert counts.get("COMMENTARY_DEPENDENT", 0) == 5
        assert counts.get("LATER_TRADITION", 0) == 6


class TestTransitRuleEvaluation:
    """Tests that rules fire correctly when facts match."""

    def test_transit_in_moon_nakshatra_fires(self) -> None:
        """R-TRANSIT-001: transit_in_moon_nakshatra=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-001")
        assert rule is not None
        facts = {"transit_in_moon_nakshatra": True}
        assert _evaluate_rule(rule, facts) is True

    def test_transit_in_moon_nakshatra_no_fire_when_false(self) -> None:
        """R-TRANSIT-001: transit_in_moon_nakshatra=false → no fire."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-001")
        assert rule is not None
        facts = {"transit_in_moon_nakshatra": False}
        assert _evaluate_rule(rule, facts) is False

    def test_transit_in_abhijit_fires(self) -> None:
        """R-TRANSIT-002: transit_in_abhijit_nakshatra=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-002")
        assert rule is not None
        facts = {"transit_in_abhijit_nakshatra": True}
        assert _evaluate_rule(rule, facts) is True

    def test_transit_in_moon_nakshatra_with_antardasha_fires(self) -> None:
        """R-TRANSIT-003: both conditions must be true."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-003")
        assert rule is not None
        facts = {"transit_in_moon_nakshatra": True, "antardasha_active": True}
        assert _evaluate_rule(rule, facts) is True

    def test_transit_in_moon_nakshatra_without_antardasha_no_fire(self) -> None:
        """R-TRANSIT-003: missing antardasha → no fire."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-003")
        assert rule is not None
        facts = {"transit_in_moon_nakshatra": True, "antardasha_active": False}
        assert _evaluate_rule(rule, facts) is False

    def test_friendly_lord_fires(self) -> None:
        """R-TRANSIT-004: transit_nakshatra_lord_friendly=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-004")
        assert rule is not None
        facts = {"transit_nakshatra_lord_friendly": True}
        assert _evaluate_rule(rule, facts) is True

    def test_enemy_lord_fires(self) -> None:
        """R-TRANSIT-005: transit_nakshatra_lord_enemy=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-005")
        assert rule is not None
        facts = {"transit_nakshatra_lord_enemy": True}
        assert _evaluate_rule(rule, facts) is True

    def test_benefic_conjunction_fires(self) -> None:
        """R-TRANSIT-006: transit_nakshatra_lord_conjunct_benefic=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-006")
        assert rule is not None
        facts = {"transit_nakshatra_lord_conjunct_benefic": True}
        assert _evaluate_rule(rule, facts) is True

    def test_malefic_conjunction_fires(self) -> None:
        """R-TRANSIT-007: transit_nakshatra_lord_conjunct_malefic=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-007")
        assert rule is not None
        facts = {"transit_nakshatra_lord_conjunct_malefic": True}
        assert _evaluate_rule(rule, facts) is True

    def test_exalted_lord_fires(self) -> None:
        """R-TRANSIT-008: nakshatra_lord_exalted=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-008")
        assert rule is not None
        facts = {"nakshatra_lord_exalted": True}
        assert _evaluate_rule(rule, facts) is True

    def test_debilitated_lord_fires(self) -> None:
        """R-TRANSIT-009: nakshatra_lord_debilitated=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-009")
        assert rule is not None
        facts = {"nakshatra_lord_debilitated": True}
        assert _evaluate_rule(rule, facts) is True

    def test_kendra_trikona_lord_fires(self) -> None:
        """R-TRANSIT-010: nakshatra_lord_in_kendra_or_trikona=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-010")
        assert rule is not None
        facts = {"nakshatra_lord_in_kendra_or_trikona": True}
        assert _evaluate_rule(rule, facts) is True

    def test_dusthana_lord_fires(self) -> None:
        """R-TRANSIT-011: nakshatra_lord_in_dusthana=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-011")
        assert rule is not None
        facts = {"nakshatra_lord_in_dusthana": True}
        assert _evaluate_rule(rule, facts) is True

    def test_retrograde_lord_fires(self) -> None:
        """R-TRANSIT-012: nakshatra_lord_retrograde=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-012")
        assert rule is not None
        facts = {"nakshatra_lord_retrograde": True}
        assert _evaluate_rule(rule, facts) is True

    def test_combust_lord_fires(self) -> None:
        """R-TRANSIT-013: nakshatra_lord_combust=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-013")
        assert rule is not None
        facts = {"nakshatra_lord_combust": True}
        assert _evaluate_rule(rule, facts) is True

    def test_dasha_lord_equals_transit_fires(self) -> None:
        """R-TRANSIT-014: dasha_lord_equals_transit_planet=true → fires."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-014")
        assert rule is not None
        facts = {"dasha_lord_equals_transit_planet": True}
        assert _evaluate_rule(rule, facts) is True


class TestTransitRuleFalsePositivePrevention:
    """Tests that rules do NOT fire when facts are absent."""

    def test_empty_facts_no_rules_fire(self) -> None:
        """With no facts, zero rules should fire."""
        rules = _load_transit_rules()
        fired = [r for r in rules if _evaluate_rule(r, {})]
        assert len(fired) == 0

    def test_wrong_fact_name_no_fire(self) -> None:
        """Wrong fact names should not trigger any rule."""
        rules = _load_transit_rules()
        facts = {"wrong_fact_name": True}
        fired = [r for r in rules if _evaluate_rule(r, facts)]
        assert len(fired) == 0

    def test_transit_in_moon_nakshatra_only_fires_001(self) -> None:
        """Only R-TRANSIT-001 should fire from transit_in_moon_nakshatra alone."""
        rules = _load_transit_rules()
        facts = {"transit_in_moon_nakshatra": True}
        fired = [r for r in rules if _evaluate_rule(r, facts)]
        fired_ids = {r["rule_id"] for r in fired}
        assert "R-TRANSIT-001" in fired_ids
        # R-TRANSIT-003 requires antardasha_active too
        assert "R-TRANSIT-003" not in fired_ids


class TestTransitRuleEvidenceWeights:
    """Tests that evidence weights are correct for each rule."""

    def test_classical_primary_weights_higher(self) -> None:
        """CLASSICAL_PRIMARY rules should have higher evidence weights."""
        rules = _load_transit_rules()
        classical_weights = [
            r["evidence_weight"]
            for r in rules
            if r["classification"] == "CLASSICAL_PRIMARY"
        ]
        later_weights = [
            r["evidence_weight"]
            for r in rules
            if r["classification"] == "LATER_TRADITION"
        ]
        assert classical_weights  # non-empty
        assert later_weights  # non-empty
        assert min(classical_weights) >= min(later_weights)

    def test_all_evidence_weights_bounded(self) -> None:
        """All evidence weights should be between 0.0 and 1.0."""
        rules = _load_transit_rules()
        for rule in rules:
            ew = rule.get("evidence_weight", 0.0)
            assert 0.0 <= ew <= 1.0, (
                f"Rule {rule['rule_id']}: evidence_weight {ew} out of range"
            )


class TestTransitRuleMultiConditionEvaluation:
    """Tests for multi-condition rules with AND logic."""

    def test_both_conditions_required_for_003(self) -> None:
        """R-TRANSIT-003 requires both transit_in_moon_nakshatra AND antardasha_active."""
        rules = _load_transit_rules()
        rule = _get_rule_by_id(rules, "R-TRANSIT-003")
        assert rule is not None

        # Only first condition
        facts1 = {"transit_in_moon_nakshatra": True, "antardasha_active": False}
        assert _evaluate_rule(rule, facts1) is False

        # Only second condition
        facts2 = {"transit_in_moon_nakshatra": False, "antardasha_active": True}
        assert _evaluate_rule(rule, facts2) is False

        # Both conditions
        facts3 = {"transit_in_moon_nakshatra": True, "antardasha_active": True}
        assert _evaluate_rule(rule, facts3) is True

    def test_multiple_rules_can_fire_simultaneously(self) -> None:
        """Multiple rules can fire from a single fact set."""
        rules = _load_transit_rules()
        facts = {
            "transit_in_moon_nakshatra": True,
            "antardasha_active": True,
            "transit_nakshatra_lord_friendly": True,
            "nakshatra_lord_exalted": True,
        }
        fired = [r for r in rules if _evaluate_rule(r, facts)]
        fired_ids = {r["rule_id"] for r in fired}
        assert len(fired) >= 4
        assert "R-TRANSIT-001" in fired_ids
        assert "R-TRANSIT-003" in fired_ids
        assert "R-TRANSIT-004" in fired_ids
        assert "R-TRANSIT-008" in fired_ids


class TestTransitRuleDeterministicOutput:
    """Tests for deterministic rule evaluation."""

    def test_same_facts_same_results(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        rules = _load_transit_rules()
        facts = {
            "transit_in_moon_nakshatra": True,
            "transit_nakshatra_lord_friendly": True,
        }
        fired1 = [r["rule_id"] for r in rules if _evaluate_rule(r, facts)]
        fired2 = [r["rule_id"] for r in rules if _evaluate_rule(r, facts)]
        assert fired1 == fired2

    def test_rule_ordering_stable(self) -> None:
        """Rules are loaded in stable order."""
        rules1 = _load_transit_rules()
        rules2 = _load_transit_rules()
        ids1 = [r["rule_id"] for r in rules1]
        ids2 = [r["rule_id"] for r in rules2]
        assert ids1 == ids2
