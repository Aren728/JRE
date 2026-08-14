"""Tradition profile tests (TEST-PLAN requirement 5, SPEC §14, ADR-010)."""

from __future__ import annotations

import pytest
from _kb_helpers import write_catalog

from knowledge.errors import (
    InvalidConfigError,
    RuleSchemaError,
    UnknownProfileError,
    UnknownSourceError,
)
from knowledge.sources import load_sources
from knowledge.traditions import load_profiles

EXPECTED_PRIORITY = {
    "bphs-classical": ["bphs", "brihat-jataka", "jataka-parijata", "phaladeepika"],
    "brihat-jataka": ["brihat-jataka", "bphs", "jataka-parijata", "phaladeepika"],
    "jataka-parijata": ["jataka-parijata", "brihat-jataka", "phaladeepika", "bphs"],
    "phaladeepika": ["phaladeepika", "jataka-parijata", "brihat-jataka", "bphs"],
    "surya-siddhanta-vedanga": ["surya-siddhanta"],
    "regional-kerala": ["prasna-marga", "bphs", "phaladeepika"],
    "regional-north-indian": ["saravali", "bphs", "brihat-jataka"],
}


def test_seven_profiles_with_explicit_priority(service):
    profiles = {profile.profile_id: profile for profile in service.profiles()}
    assert set(profiles) == set(EXPECTED_PRIORITY)
    for profile_id, priority in EXPECTED_PRIORITY.items():
        assert profiles[profile_id].source_priority == tuple(priority)
        assert profiles[profile_id].included_sources == tuple(priority)


def test_conflict_policies(service):
    profiles = {profile.profile_id: profile for profile in service.profiles()}
    assert profiles["bphs-classical"].conflict_policy.value == "FIRST_WINS"
    assert profiles["surya-siddhanta-vedanga"].conflict_policy.value == "REPORT_ALL"


def test_domains_none_means_all(service):
    for profile in service.profiles():
        assert profile.domains is None


def test_passthrough_echoed_and_validated(service):
    profiles = {profile.profile_id: profile for profile in service.profiles()}
    assert profiles["bphs-classical"].passthrough_config == {
        "ayanamsa": "LAHIRI",
        "house_system": "WHOLE_SIGN",
    }
    assert profiles["regional-kerala"].passthrough_config == {"ayanamsa": "RAMAN"}


def test_unknown_profile(service):
    with pytest.raises(UnknownProfileError):
        service.get_profile("nope")


def test_profile_unknown_source_rejected(tmp_path):
    sources = load_sources()
    path = write_catalog(
        tmp_path,
        "profiles",
        [
            {
                "profile_id": "ghost-profile",
                "name": "Ghost",
                "version": "1.0.0",
                "description": "x",
                "included_sources": ["ghost"],
                "source_priority": ["ghost"],
                "conflict_policy": "FIRST_WINS",
                "domains": None,
                "passthrough_config": {},
            }
        ],
    )
    with pytest.raises(UnknownSourceError):
        load_profiles(path, sources=sources)


def test_profile_priority_not_included_rejected(tmp_path):
    sources = load_sources()
    path = write_catalog(
        tmp_path,
        "profiles",
        [
            {
                "profile_id": "bad-priority",
                "name": "Bad",
                "version": "1.0.0",
                "description": "x",
                "included_sources": ["bphs"],
                "source_priority": ["bphs", "saravali"],
                "conflict_policy": "FIRST_WINS",
                "domains": None,
                "passthrough_config": {},
            }
        ],
    )
    with pytest.raises(RuleSchemaError):
        load_profiles(path, sources=sources)


def test_bad_passthrough_rejected(tmp_path):
    sources = load_sources()
    path = write_catalog(
        tmp_path,
        "profiles",
        [
            {
                "profile_id": "bad-passthrough",
                "name": "Bad",
                "version": "1.0.0",
                "description": "x",
                "included_sources": ["bphs"],
                "source_priority": ["bphs"],
                "conflict_policy": "FIRST_WINS",
                "domains": None,
                "passthrough_config": {"ayanamsa": "PLUTO"},
            }
        ],
    )
    with pytest.raises(InvalidConfigError):
        load_profiles(path, sources=sources)


def test_regional_profiles_require_regional_source(service):
    for profile in service.profiles():
        for source_id in profile.included_sources:
            source = {item.source_id: item for item in service.sources()}[source_id]
            assert source.editions, source_id
