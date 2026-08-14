"""Focused tests for the additive public type exports ``BodyId`` / ``RetrogradeState``.

JRE-005 second blocker resolution (OPTION A): expose the existing canonical
type symbols through the public ``jyotish`` root so downstream layers can
annotate and compare body identity and retrograde state without importing
internal modules or ``astronomy`` directly.

Requirements verified: module attributes exist; both are in ``__all__``; the
exported objects ARE the existing canonical types (identity with the
astronomy/models definitions); enum members/values unchanged; behavior
unchanged.
"""

from __future__ import annotations

import jyotish
from astronomy.models import BodyId as AstroBodyId
from astronomy.models import RetrogradeState as AstroRetrogradeState


def test_body_id_exposed_on_public_root() -> None:
    assert hasattr(jyotish, "BodyId")


def test_retrograde_state_exposed_on_public_root() -> None:
    assert hasattr(jyotish, "RetrogradeState")


def test_both_in_public_all() -> None:
    assert "BodyId" in jyotish.__all__
    assert "RetrogradeState" in jyotish.__all__


def test_exported_types_are_the_canonical_types() -> None:
    assert jyotish.BodyId is AstroBodyId
    assert jyotish.RetrogradeState is AstroRetrogradeState


def test_enum_members_unchanged() -> None:
    assert jyotish.BodyId.SUN.value == "SUN"
    assert jyotish.BodyId.RAHU.value == "RAHU"
    assert jyotish.RetrogradeState.DIRECT.value == "DIRECT"
    assert jyotish.RetrogradeState.RETROGRADE.value == "RETROGRADE"
    assert jyotish.RetrogradeState.STATIONARY.value == "STATIONARY"


def test_member_sets_match_canonical() -> None:
    assert set(jyotish.BodyId) == set(AstroBodyId)
    assert set(jyotish.RetrogradeState) == set(AstroRetrogradeState)
