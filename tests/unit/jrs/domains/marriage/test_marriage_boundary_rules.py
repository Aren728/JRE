"""Unit tests for JRS-059: Relationship Boundary Rules (R-MARR-BOUND-* rules).

Each test verifies that a specific fact combination deterministically triggers
the correct MarriageOutcomeTaxonomy and EvidenceDirection for one of the 9
boundary rules added in config/domains/marriage.toml.

Tests also explicitly verify that unsupported configurations do NOT trigger
false positives.
"""

from __future__ import annotations

from pathlib import Path

from jrs.domains.marriage.service import MarriageDomainService
from jrs.evidence.models import EvidenceDirection, EvidenceRecord

# Path to the TOML config for full-service loading tests.
_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "marriage.toml"
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_records_for_rule(
    records: tuple[EvidenceRecord, ...],
    rule_id: str,
) -> list[EvidenceRecord]:
    """Return evidence records matching a specific rule_id."""
    return [r for r in records if r.rule_id == rule_id]


# ── Subsequent Unions / Remarriage ──────────────────────────────────────────


class TestRemarriageAfterDivorce:
    """Tests for remarriage-after-divorce boundary rules (BOUND-001, BOUND-002)."""

    def test_7th_lord_6th_rahu_divorce_remarriage(self) -> None:
        """BOUND-001: 7th lord in 6th + Rahu aspect → REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_6th": True,
            "rahu_aspects_7th_lord": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-001")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_lord_6th_no_rahu_no_fire(self) -> None:
        """BOUND-001: 7th lord in 6th but no Rahu → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_6th": True,
            "rahu_aspects_7th_lord": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-001")
        assert len(matches) == 0

    def test_rahu_aspect_no_6th_lord_no_fire(self) -> None:
        """BOUND-001: Rahu aspect without 7th lord in 6th → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_6th": False,
            "rahu_aspects_7th_lord": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-001")
        assert len(matches) == 0

    def test_venus_debilitated_ketu_divorce_remarriage(self) -> None:
        """BOUND-002: Venus debilitated + Ketu to 7th → REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_debilitated": True,
            "ketu_7th_connection": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-002")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_venus_strong_ketu_no_fire(self) -> None:
        """BOUND-002: Venus strong with Ketu → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_debilitated": False,
            "ketu_7th_connection": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-002")
        assert len(matches) == 0

    def test_venus_debilitated_no_ketu_no_fire(self) -> None:
        """BOUND-002: Venus debilitated without Ketu → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_debilitated": True,
            "ketu_7th_connection": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-002")
        assert len(matches) == 0


class TestRemarriageAfterSpouseDeath:
    """Tests for remarriage-after-spouse-death boundary rules (BOUND-003)."""

    def test_7th_8th_saturn_2nd_spouse_death(self) -> None:
        """BOUND-003: 7th lord in 8th + Saturn aspect + 2nd lord → REMARRIAGE_AFTER_SPOUSE_DEATH."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_8th": True,
            "saturn_aspects_7th_lord": True,
            "2nd_lord_connected_to_7th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-003")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_SPOUSE_DEATH"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_8th_saturn_no_2nd_no_fire(self) -> None:
        """BOUND-003: Missing 2nd lord connection → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_8th": True,
            "saturn_aspects_7th_lord": True,
            "2nd_lord_connected_to_7th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-003")
        assert len(matches) == 0

    def test_7th_8th_no_saturn_no_fire(self) -> None:
        """BOUND-003: Missing Saturn aspect → rule should not fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_8th": True,
            "saturn_aspects_7th_lord": False,
            "2nd_lord_connected_to_7th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-003")
        assert len(matches) == 0

    def test_only_one_condition_no_fire(self) -> None:
        """BOUND-003: Only 7th lord in 8th → rule should not fire (needs all 3)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_8th": True,
            "saturn_aspects_7th_lord": False,
            "2nd_lord_connected_to_7th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-003")
        assert len(matches) == 0


# ── Separation / Prolonged Distance ─────────────────────────────────────────


class TestSeparationRules:
    """Tests for separation boundary rules (BOUND-004 through BOUND-007)."""

    def test_rahu_ketu_axis_combust_separation(self) -> None:
        """BOUND-004: Rahu-Ketu axis 1/7 + combust 7th lord → SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_ketu_axis_1_7": True,
            "7th_lord_combust": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-004")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SEPARATION"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_rahu_ketu_axis_no_combust_no_fire(self) -> None:
        """BOUND-004: Rahu-Ketu axis but 7th lord not combust → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_ketu_axis_1_7": True,
            "7th_lord_combust": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-004")
        assert len(matches) == 0

    def test_combust_no_axis_no_fire(self) -> None:
        """BOUND-004: Combust 7th lord but no Rahu-Ketu axis → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_ketu_axis_1_7": False,
            "7th_lord_combust": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-004")
        assert len(matches) == 0

    def test_saturn_mars_no_jupiter_separation(self) -> None:
        """BOUND-005: Saturn in 7th + Mars aspect + no Jupiter → SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "mars_aspects_7th": True,
            "jupiter_aspects_7th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-005")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SEPARATION"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_saturn_mars_with_jupiter_no_fire(self) -> None:
        """BOUND-005: Saturn in 7th + Mars + Jupiter present → no fire (mitigated)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "mars_aspects_7th": True,
            "jupiter_aspects_7th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-005")
        assert len(matches) == 0

    def test_saturn_no_mars_no_fire(self) -> None:
        """BOUND-005: Saturn in 7th without Mars aspect → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "mars_aspects_7th": False,
            "jupiter_aspects_7th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-005")
        assert len(matches) == 0

    def test_7th_12th_rahu_separation(self) -> None:
        """BOUND-006: 7th lord in 12th + Rahu aspect → SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_12th": True,
            "rahu_aspects_7th_lord": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-006")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SEPARATION"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_12th_no_rahu_no_fire(self) -> None:
        """BOUND-006: 7th lord in 12th without Rahu → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_12th": True,
            "rahu_aspects_7th_lord": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-006")
        assert len(matches) == 0

    def test_7th_12th_saturn_separation(self) -> None:
        """BOUND-007: 7th lord in 12th + Saturn aspect → SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_12th": True,
            "saturn_aspects_7th_lord": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-007")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SEPARATION"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_12th_no_saturn_no_fire(self) -> None:
        """BOUND-007: 7th lord in 12th without Saturn aspect → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_12th": True,
            "saturn_aspects_7th_lord": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-007")
        assert len(matches) == 0


# ── Unusual / Cross-Cultural Unions ─────────────────────────────────────────


class TestCrossCulturalUnion:
    """Tests for unusual union boundary rules (BOUND-008)."""

    def test_rahu_7th_saturn_1st_cross_cultural(self) -> None:
        """BOUND-008: Rahu in 7th + Saturn in 1st → CROSS_CULTURAL_MARRIAGE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_in_7th": True,
            "saturn_in_1st": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-008")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "CROSS_CULTURAL_MARRIAGE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_rahu_7th_no_saturn_no_fire(self) -> None:
        """BOUND-008: Rahu in 7th without Saturn in 1st → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_in_7th": True,
            "saturn_in_1st": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-008")
        assert len(matches) == 0

    def test_saturn_1st_no_rahu_no_fire(self) -> None:
        """BOUND-008: Saturn in 1st without Rahu in 7th → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_in_7th": False,
            "saturn_in_1st": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-008")
        assert len(matches) == 0


# ── Mitigation (Boundary) ───────────────────────────────────────────────────


class TestBoundaryMitigation:
    """Tests for the boundary mitigation rule (BOUND-009)."""

    def test_jupiter_mitigates_saturn_mars_separation(self) -> None:
        """BOUND-009: Saturn + Mars + Jupiter → MITIGATE for SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "mars_aspects_7th": True,
            "jupiter_aspects_7th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-BOUND-009")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SEPARATION"
        assert rec.direction is EvidenceDirection.MITIGATE

    def test_mitigation_alongside_support(self) -> None:
        """BOUND-009 + BOUND-005: Both MITIGATE and SUPPORT can fire from facts
        when Jupiter is present (mitigation) but BOUND-005 requires Jupiter absent."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        # With Jupiter present, BOUND-005 won't fire (needs jupiter=false),
        # but BOUND-009 fires as MITIGATE.
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "mars_aspects_7th": True,
            "jupiter_aspects_7th": True,
        })
        bound_005 = _get_records_for_rule(records, "R-MARR-BOUND-005")
        bound_009 = _get_records_for_rule(records, "R-MARR-BOUND-009")
        assert len(bound_005) == 0  # BOUND-005 requires jupiter=false
        assert len(bound_009) == 1
        assert bound_009[0].direction is EvidenceDirection.MITIGATE


# ── False Positive Prevention ───────────────────────────────────────────────


class TestFalsePositivePrevention:
    """Explicit tests that unsupported configurations do NOT trigger false positives."""

    def test_7th_lord_6th_without_rahu_not_remarriage(self) -> None:
        """7th lord in 6th alone should not trigger REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_6th": True,
        })
        divorce_records = [
            r for r in records
            if r.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
            and r.rule_id == "R-MARR-BOUND-001"
        ]
        assert len(divorce_records) == 0

    def test_venus_debilitated_alone_not_remarriage(self) -> None:
        """Venus debilitated alone should not trigger REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_debilitated": True,
        })
        divorce_records = [
            r for r in records
            if r.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
            and r.rule_id == "R-MARR-BOUND-002"
        ]
        assert len(divorce_records) == 0

    def test_7th_lord_8th_alone_not_spouse_death_remarriage(self) -> None:
        """7th lord in 8th alone should not trigger REMARRIAGE_AFTER_SPOUSE_DEATH (BOUND-003)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_8th": True,
        })
        spouse_death_records = [
            r for r in records
            if r.outcome_taxonomy == "REMARRIAGE_AFTER_SPOUSE_DEATH"
            and r.rule_id == "R-MARR-BOUND-003"
        ]
        assert len(spouse_death_records) == 0

    def test_rahu_ketu_axis_alone_not_separation(self) -> None:
        """Rahu-Ketu axis alone should not trigger SEPARATION (BOUND-004)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_ketu_axis_1_7": True,
        })
        separation_records = [
            r for r in records
            if r.outcome_taxonomy == "SEPARATION"
            and r.rule_id == "R-MARR-BOUND-004"
        ]
        assert len(separation_records) == 0

    def test_saturn_7th_alone_not_separation(self) -> None:
        """Saturn in 7th alone should not trigger SEPARATION (BOUND-005)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
        })
        separation_records = [
            r for r in records
            if r.outcome_taxonomy == "SEPARATION"
            and r.rule_id == "R-MARR-BOUND-005"
        ]
        assert len(separation_records) == 0

    def test_7th_12th_alone_not_separation(self) -> None:
        """7th lord in 12th alone should not trigger SEPARATION (BOUND-006/007)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_12th": True,
        })
        separation_records = [
            r for r in records
            if r.outcome_taxonomy == "SEPARATION"
            and r.rule_id in ("R-MARR-BOUND-006", "R-MARR-BOUND-007")
        ]
        assert len(separation_records) == 0

    def test_rahu_7th_alone_not_cross_cultural(self) -> None:
        """Rahu in 7th alone should not trigger CROSS_CULTURAL_MARRIAGE (BOUND-008)."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "rahu_in_7th": True,
        })
        cross_cultural = [
            r for r in records
            if r.outcome_taxonomy == "CROSS_CULTURAL_MARRIAGE"
            and r.rule_id == "R-MARR-BOUND-008"
        ]
        assert len(cross_cultural) == 0

    def test_empty_facts_no_boundary_rules_fire(self) -> None:
        """With no facts, zero boundary rules should fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({})
        boundary_records = [
            r for r in records if r.rule_id.startswith("R-MARR-BOUND-")
        ]
        assert len(boundary_records) == 0

    def test_divorce_indicator_does_not_trigger_false_separation(self) -> None:
        """A divorce fact should not falsely trigger SEPARATION rules."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_6th": True,
            "rahu_aspects_7th_lord": True,
        })
        # BOUND-001 fires (REMARRIAGE_AFTER_DIVORCE), but no SEPARATION should fire
        separation_records = [
            r for r in records if r.outcome_taxonomy == "SEPARATION"
        ]
        assert len(separation_records) == 0

    def test_unsupported_kinship_config_no_false_positive(self) -> None:
        """Facts that might suggest kinship but have no source-pinned rule → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "5th_lord_connected_to_7th": True,
            "sibling_karaka_active": True,
        })
        boundary_records = [
            r for r in records if r.rule_id.startswith("R-MARR-BOUND-")
        ]
        assert len(boundary_records) == 0


# ── Integration / Cross-Rule Tests ──────────────────────────────────────────


class TestBoundaryRulesIntegration:
    """Integration tests: multiple boundary rules firing together."""

    def test_all_boundary_rules_loaded(self) -> None:
        """All 9 boundary rules should be present in the catalog."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        boundary_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-MARR-BOUND-")
        ]
        assert len(boundary_rules) == 9

    def test_unique_rule_ids(self) -> None:
        """All rule IDs across the full catalog should be unique."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_multi_boundary_firing(self) -> None:
        """Multiple boundary rules can fire from a single fact set."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            # BOUND-001: remarriage after divorce
            "7th_lord_in_6th": True,
            "rahu_aspects_7th_lord": True,
            # BOUND-006: separation (distance)
            "7th_lord_in_12th": True,
            # BOUND-008: cross-cultural
            "rahu_in_7th": True,
            "saturn_in_1st": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        boundary_records = [
            r for r in records if r.rule_id.startswith("R-MARR-BOUND-")
        ]
        assert len(boundary_records) >= 3
        outcomes = {r.outcome_taxonomy for r in boundary_records}
        assert "REMARRIAGE_AFTER_DIVORCE" in outcomes
        assert "CROSS_CULTURAL_MARRIAGE" in outcomes

    def test_deterministic_output(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            "saturn_in_7th": True,
            "mars_aspects_7th": True,
            "jupiter_aspects_7th": True,
        }
        r1 = svc.evaluate_marriage_facts(facts)
        r2 = svc.evaluate_marriage_facts(facts)
        ids1 = [e.rule_id for e in r1]
        ids2 = [e.rule_id for e in r2]
        assert ids1 == ids2

    def test_boundary_rules_coexist_with_existing_rules(self) -> None:
        """Boundary rules should fire alongside existing marriage rules."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            # Existing rule: formation
            "7th_lord_in_kendra_or_trikona": True,
            # Boundary rule: BOUND-008
            "rahu_in_7th": True,
            "saturn_in_1st": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        all_rule_ids = [r.rule_id for r in records]
        # Both existing and boundary rules should be present
        assert "R-MARR-FORM-001" in all_rule_ids
        assert "R-MARR-BOUND-008" in all_rule_ids

    def test_records_have_correct_fields(self) -> None:
        """All boundary evidence records have correct fields populated."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            "7th_lord_in_6th": True,
            "rahu_aspects_7th_lord": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        boundary_records = [
            r for r in records if r.rule_id.startswith("R-MARR-BOUND-")
        ]
        for record in boundary_records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)
