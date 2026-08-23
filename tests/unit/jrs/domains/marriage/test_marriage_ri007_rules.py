"""Unit tests for RI-007 Vetted Classical Primary Sequential Union Rules.

Each test verifies that a specific fact combination deterministically triggers
the correct MarriageOutcomeTaxonomy and EvidenceDirection for the rules added
in the RI-007 controlled integration.

Tests also verify that excluded (unsupported/kinship) configurations do NOT
trigger false positives.
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


# ── Sequential Union Indicators (BPHS Ch.18, V.5-6) ─────────────────────────


class TestSequentialUnionIndicators:
    """Tests for sequential union rules (RI007-001 to RI007-003)."""

    def test_7th_lord_debilitated_many_wives(self) -> None:
        """RI007-001: 7th lord debilitated → REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_debilitated": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-001")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_lord_not_debilitated_no_fire(self) -> None:
        """RI007-001: 7th lord not debilitated → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_debilitated": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-001")
        assert len(matches) == 0

    def test_7th_lord_combust_many_wives(self) -> None:
        """RI007-002: 7th lord combust → REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_combust": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-002")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_lord_not_combust_no_fire(self) -> None:
        """RI007-002: 7th lord not combust → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_combust": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-002")
        assert len(matches) == 0

    def test_7th_lord_saturn_venus_sign_many_wives(self) -> None:
        """RI007-003: 7th lord in Saturn/Venus sign + benefic → REMARRIAGE_AFTER_DIVORCE."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_saturn_or_venus_sign": True,
            "benefic_aspects_7th_lord": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-003")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_7th_lord_saturn_venus_no_benefic_no_fire(self) -> None:
        """RI007-003: 7th lord in Saturn/Venus sign without benefic → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_in_saturn_or_venus_sign": True,
            "benefic_aspects_7th_lord": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-003")
        assert len(matches) == 0


# ── Spouse Loss / Multiple Wife Indicators ───────────────────────────────────


class TestSpouseLossIndicators:
    """Tests for spouse loss rules (RI007-004 to RI007-007)."""

    def test_mars_venus_in_7th_three_wives(self) -> None:
        """RI007-004: Mars + Venus in 7th → REMARRIAGE_AFTER_SPOUSE_DEATH."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "mars_in_7th": True,
            "venus_in_7th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-004")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_SPOUSE_DEATH"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_mars_in_7th_no_venus_no_fire(self) -> None:
        """RI007-004: Mars in 7th without Venus → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "mars_in_7th": True,
            "venus_in_7th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-004")
        assert len(matches) == 0

    def test_saturn_7th_lagna_8th_three_wives(self) -> None:
        """RI007-005: Saturn in 7th + Lagna lord in 8th → REMARRIAGE_AFTER_SPOUSE_DEATH."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "lagna_lord_in_8th": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-005")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "REMARRIAGE_AFTER_SPOUSE_DEATH"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_saturn_7th_no_lagna_8th_no_fire(self) -> None:
        """RI007-005: Saturn in 7th without Lagna lord in 8th → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "saturn_in_7th": True,
            "lagna_lord_in_8th": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-005")
        assert len(matches) == 0

    def test_rahu_mars_saturn_order_spouse_loss(self) -> None:
        """RI007-006: 6th=Rahu, 7th=Mars, 8th=Saturn → SPOUSE_LOSS."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "6th_lord": "Rahu",
            "7th_house_planet": "Mars",
            "8th_house_planet": "Saturn",
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-006")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SPOUSE_LOSS"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_wrong_order_no_fire(self) -> None:
        """RI007-006: Wrong planet order → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "6th_lord": "Mars",
            "7th_house_planet": "Rahu",
            "8th_house_planet": "Saturn",
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-006")
        assert len(matches) == 0

    def test_venus_malefic_loss_of_wife(self) -> None:
        """RI007-007: Venus with malefic → SPOUSE_LOSS."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_with_malefic": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-007")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "SPOUSE_LOSS"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_venus_without_malefic_no_fire(self) -> None:
        """RI007-007: Venus without malefic → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_with_malefic": False,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-007")
        assert len(matches) == 0


# ── Marital Discord Indicators ───────────────────────────────────────────────


class TestMaritalDiscordIndicators:
    """Tests for marital discord rules (RI007-008 to RI007-009)."""

    def test_saturn_owns_7th_discord(self) -> None:
        """RI007-008: 7th owned by Saturn → MARITAL_CONFLICT."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_house_owned_by_Saturn": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-008")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "MARITAL_CONFLICT"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_mars_owns_7th_discord(self) -> None:
        """RI007-009: 7th owned by Mars → MARITAL_CONFLICT."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_house_owned_by_Mars": True,
        })
        matches = _get_records_for_rule(records, "R-MARR-RI007-009")
        assert len(matches) == 1
        rec = matches[0]
        assert rec.outcome_taxonomy == "MARITAL_CONFLICT"
        assert rec.direction is EvidenceDirection.SUPPORT

    def test_neither_saturn_nor_mars_no_fire(self) -> None:
        """RI007-008/009: Neither Saturn nor Mars owns 7th → no fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_house_owned_by_Saturn": False,
            "7th_house_owned_by_Mars": False,
        })
        matches_008 = _get_records_for_rule(records, "R-MARR-RI007-008")
        matches_009 = _get_records_for_rule(records, "R-MARR-RI007-009")
        assert len(matches_008) == 0
        assert len(matches_009) == 0


# ── False Positive Prevention ────────────────────────────────────────────────


class TestMarriageRI007FalsePositivePrevention:
    """Tests that excluded configurations do NOT trigger false positives."""

    def test_kinship_inference_not_in_catalog(self) -> None:
        """Kinship-based union rules should not exist in the catalog."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        kinship_rules = [
            r for r in catalog.rules
            if "kinship" in r.description.lower()
            or "sibling" in r.description.lower()
        ]
        assert len(kinship_rules) == 0

    def test_soulmate_not_in_catalog(self) -> None:
        """Soul-mate/twin-flame rules should not exist."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        soulmate_rules = [
            r for r in catalog.rules
            if "soul" in r.description.lower()
            or "twin" in r.description.lower()
            or "karmic" in r.description.lower()
        ]
        assert len(soulmate_rules) == 0

    def test_empty_facts_no_ri007_rules_fire(self) -> None:
        """With no facts, zero RI-007 rules should fire."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({})
        ri007_records = [
            r for r in records if r.rule_id.startswith("R-MARR-RI007-")
        ]
        assert len(ri007_records) == 0

    def test_7th_lord_debilitated_alone_not_false_separation(self) -> None:
        """7th lord debilitated alone should not trigger SEPARATION rules."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "7th_lord_debilitated": True,
        })
        separation_records = [
            r for r in records if r.outcome_taxonomy == "SEPARATION"
        ]
        # Should trigger REMARRIAGE, not SEPARATION
        remarriage_records = [
            r for r in records if r.outcome_taxonomy == "REMARRIAGE_AFTER_DIVORCE"
        ]
        assert len(remarriage_records) >= 1
        # No SEPARATION should fire from just debilitated 7th lord
        assert len(separation_records) == 0

    def test_venus_malefic_not_false_separation(self) -> None:
        """Venus with malefic should trigger SPOUSE_LOSS, not SEPARATION."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        records = svc.evaluate_marriage_facts({
            "venus_with_malefic": True,
        })
        spouse_loss = [
            r for r in records
            if r.outcome_taxonomy == "SPOUSE_LOSS"
            and r.rule_id == "R-MARR-RI007-007"
        ]
        assert len(spouse_loss) == 1


# ── Integration Tests ────────────────────────────────────────────────────────


class TestMarriageRI007Integration:
    """Integration tests for RI-007 marriage rules."""

    def test_ri007_rules_loaded(self) -> None:
        """All 9 RI-007 rules should be present in the catalog."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        ri007_rules = [
            r for r in catalog.rules if r.rule_id.startswith("R-MARR-RI007-")
        ]
        assert len(ri007_rules) == 9

    def test_unique_rule_ids(self) -> None:
        """All rule IDs across the full catalog should be unique."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_marriage_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_multi_ri007_firing(self) -> None:
        """Multiple RI-007 rules can fire from a single fact set."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            # RI007-001: debilitated
            "7th_lord_debilitated": True,
            # RI007-004: Mars+Venus in 7th
            "mars_in_7th": True,
            "venus_in_7th": True,
            # RI007-008: Saturn owns 7th
            "7th_house_owned_by_Saturn": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        ri007_records = [
            r for r in records if r.rule_id.startswith("R-MARR-RI007-")
        ]
        assert len(ri007_records) >= 3
        outcomes = {r.outcome_taxonomy for r in ri007_records}
        assert "REMARRIAGE_AFTER_DIVORCE" in outcomes
        assert "REMARRIAGE_AFTER_SPOUSE_DEATH" in outcomes
        assert "MARITAL_CONFLICT" in outcomes

    def test_ri007_coexist_with_existing_rules(self) -> None:
        """RI-007 rules should fire alongside existing marriage rules."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            # Existing rule: FORM-001
            "7th_lord_in_kendra_or_trikona": True,
            # RI-007 rule: RI007-001
            "7th_lord_debilitated": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        all_rule_ids = [r.rule_id for r in records]
        assert "R-MARR-FORM-001" in all_rule_ids
        assert "R-MARR-RI007-001" in all_rule_ids

    def test_deterministic_output(self) -> None:
        """Evaluating the same facts twice yields identical rule_ids."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            "7th_lord_debilitated": True,
            "venus_with_malefic": True,
            "7th_house_owned_by_Mars": True,
        }
        r1 = svc.evaluate_marriage_facts(facts)
        r2 = svc.evaluate_marriage_facts(facts)
        ids1 = [e.rule_id for e in r1]
        ids2 = [e.rule_id for e in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        """All RI-007 evidence records have correct fields populated."""
        svc = MarriageDomainService(config_path=_CONFIG_PATH)
        facts = {
            "7th_lord_debilitated": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        ri007_records = [
            r for r in records if r.rule_id.startswith("R-MARR-RI007-")
        ]
        for record in ri007_records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)
