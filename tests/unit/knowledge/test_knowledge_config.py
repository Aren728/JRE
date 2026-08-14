"""Configuration tests (TEST-PLAN §3, SPEC §13)."""

from __future__ import annotations

import pytest

from knowledge import (
    KnowledgeConfig,
    KnowledgeService,
    load_config,
    validate_config,
)
from knowledge.errors import (
    CatalogIntegrityError,
    InvalidConfigError,
    UnknownProfileError,
)
from knowledge.models import ConflictPolicy


def test_toml_loads_with_explicit_defaults():
    config = load_config()
    assert config.default_profile_id == "bphs-classical"
    assert config.default_conflict_policy is ConflictPolicy.FIRST_WINS
    assert config.enforce_provenance is True
    assert config.verify_checksums is True
    assert config.max_rules_per_synthesis == 200
    assert config.credibility_authority_weight == 0.55
    assert config.credibility_provenance_weight == 0.30
    assert config.credibility_specificity_weight == 0.15
    assert config.provenance_completeness == {
        "full": 1.0,
        "verse": 0.85,
        "chapter": 0.7,
        "source": 0.5,
    }


def test_config_round_trip():
    config = load_config()
    from knowledge import config_from_dict

    rebuilt = config_from_dict(
        {
            "default_profile_id": config.default_profile_id,
            "default_conflict_policy": config.default_conflict_policy.value,
            "source_catalog_version": config.source_catalog_version,
            "rule_catalog_versions": config.rule_catalog_versions,
            "profile_catalog_version": config.profile_catalog_version,
            "enforce_provenance": config.enforce_provenance,
            "verify_checksums": config.verify_checksums,
            "max_rules_per_synthesis": config.max_rules_per_synthesis,
            "provenance_completeness": config.provenance_completeness,
        }
    )
    assert rebuilt == config


def test_validation_rejects_bad_values():
    with pytest.raises(InvalidConfigError):
        validate_config(KnowledgeConfig(max_rules_per_synthesis=0))
    with pytest.raises(InvalidConfigError):
        validate_config(
            KnowledgeConfig(
                credibility_authority_weight=0.9,
                credibility_provenance_weight=0.9,
                credibility_specificity_weight=0.15,
            )
        )
    with pytest.raises(InvalidConfigError):
        validate_config(KnowledgeConfig(provenance_completeness={"full": 1.0, "verse": 0.85}))


def test_unknown_default_profile_at_construction():
    config = KnowledgeConfig(default_profile_id="ghost-profile")
    with pytest.raises(UnknownProfileError):
        KnowledgeService(config=config)


def test_version_pin_enforced_at_construction():
    config = KnowledgeConfig(source_catalog_version="9.9.9")
    with pytest.raises(CatalogIntegrityError):
        KnowledgeService(config=config)


def test_config_echoed_in_result(service):
    from _kb_helpers import yoga_snapshot

    from knowledge.models import RuleDomain, RuleQuery

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    assert result.config.default_profile_id == "bphs-classical"
    assert result.config.max_rules_per_synthesis == 200
