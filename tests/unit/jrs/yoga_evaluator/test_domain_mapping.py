"""Phase E6g: Multi-domain yoga outcome mapping tests.

Verifies that each yoga maps to multiple relevant outcome domains,
and that the blind evaluation's domain matching logic works correctly.
"""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.models import YogaOutcome
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestMapOutcomeBackwardCompatibility:
    """Verify map_outcome still returns a single primary domain (backward compat)."""

    def setup_method(self) -> None:
        self.svc = YogaEvaluatorService()

    def test_malavya_primary_domain(self) -> None:
        assert self.svc.map_outcome("MALAVYA") == YogaOutcome.RELATIONSHIP_HARMONY

    def test_sunapha_primary_domain(self) -> None:
        assert self.svc.map_outcome("SUNAPHA") == YogaOutcome.WEALTH_ACCUMULATION

    def test_raja_primary_domain(self) -> None:
        assert self.svc.map_outcome("RAJA") == YogaOutcome.CAREER_PROMINENCE

    def test_gajakesari_primary_domain(self) -> None:
        assert self.svc.map_outcome("GAJAKESARI") == YogaOutcome.GENERAL_IMPROVEMENT

    def test_unknown_yoga_primary_domain(self) -> None:
        assert self.svc.map_outcome("UNKNOWN_YOGA") == YogaOutcome.GENERAL_IMPROVEMENT


class TestGetPossibleOutcomes:
    """Phase E6g: Verify each yoga maps to multiple outcome domains."""

    def setup_method(self) -> None:
        self.svc = YogaEvaluatorService()

    def test_malavya_multi_domain(self) -> None:
        """Malavya should include CAREER_PROMINENCE, not just RELATIONSHIP_HARMONY."""
        outcomes = self.svc.get_possible_outcomes("MALAVYA")
        assert YogaOutcome.RELATIONSHIP_HARMONY in outcomes
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert YogaOutcome.ARTISTIC_EXCELLENCE in outcomes
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert len(outcomes) >= 3

    def test_sunapha_multi_domain(self) -> None:
        """Sunapha should include MENTAL_STRENGTH, not just WEALTH_ACCUMULATION."""
        outcomes = self.svc.get_possible_outcomes("SUNAPHA")
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert YogaOutcome.MENTAL_STRENGTH in outcomes
        assert YogaOutcome.EMOTIONAL_STABILITY in outcomes
        assert YogaOutcome.PUBLIC_RECOGNITION in outcomes
        assert len(outcomes) >= 3

    def test_raja_multi_domain(self) -> None:
        """Raja should include POLITICAL_POWER, SOCIAL_STATUS, LEADERSHIP."""
        outcomes = self.svc.get_possible_outcomes("RAJA")
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert YogaOutcome.POLITICAL_POWER in outcomes
        assert YogaOutcome.SOCIAL_STATUS in outcomes
        assert YogaOutcome.LEADERSHIP in outcomes
        assert len(outcomes) >= 3

    def test_gajakesari_multi_domain(self) -> None:
        """Gajakesari should include WISDOM_ACCUMULATION, POLITICAL_POWER, etc."""
        outcomes = self.svc.get_possible_outcomes("GAJAKESARI")
        assert YogaOutcome.WISDOM_ACCUMULATION in outcomes
        assert YogaOutcome.POLITICAL_POWER in outcomes
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert YogaOutcome.TEACHING_ABILITY in outcomes
        assert YogaOutcome.GENERAL_IMPROVEMENT in outcomes
        assert len(outcomes) >= 3

    def test_vipareeta_raja_multi_domain(self) -> None:
        """Vipareeta Raja should include RECOVERY_FROM_ADVERSITY, CRISIS_MANAGEMENT."""
        outcomes = self.svc.get_possible_outcomes("VIPAREETA RAJA")
        assert YogaOutcome.RECOVERY_FROM_ADVERSITY in outcomes
        assert YogaOutcome.CRISIS_MANAGEMENT in outcomes
        assert YogaOutcome.POLITICAL_POWER in outcomes
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert len(outcomes) >= 3

    def test_bhadra_multi_domain(self) -> None:
        """Bhadra should include INTELLECTUAL_EXCELLENCE, COMMUNICATION_SKILLS."""
        outcomes = self.svc.get_possible_outcomes("BHADRA")
        assert YogaOutcome.INTELLECTUAL_EXCELLENCE in outcomes
        assert YogaOutcome.COMMUNICATION_SKILLS in outcomes
        assert YogaOutcome.BUSINESS_ACUMEN in outcomes
        assert len(outcomes) >= 3

    def test_hamsa_multi_domain(self) -> None:
        """Hamsa should include WISDOM_ACCUMULATION, TEACHING_ABILITY."""
        outcomes = self.svc.get_possible_outcomes("HAMSA")
        assert YogaOutcome.WISDOM_ACCUMULATION in outcomes
        assert YogaOutcome.TEACHING_ABILITY in outcomes
        assert YogaOutcome.SOCIAL_STATUS in outcomes
        assert len(outcomes) >= 3

    def test_ruchaka_multi_domain(self) -> None:
        """Ruchaka should include POLITICAL_POWER, LEADERSHIP."""
        outcomes = self.svc.get_possible_outcomes("RUCHAKA")
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert YogaOutcome.POLITICAL_POWER in outcomes
        assert YogaOutcome.LEADERSHIP in outcomes
        assert len(outcomes) >= 3

    def test_sasa_multi_domain(self) -> None:
        """Sasa should include POLITICAL_POWER, LEADERSHIP."""
        outcomes = self.svc.get_possible_outcomes("SASA")
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert YogaOutcome.POLITICAL_POWER in outcomes
        assert YogaOutcome.LEADERSHIP in outcomes
        assert len(outcomes) >= 3

    def test_anapha_multi_domain(self) -> None:
        """Anapha should include MENTAL_STRENGTH, PUBLIC_RECOGNITION."""
        outcomes = self.svc.get_possible_outcomes("ANAPHA")
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert YogaOutcome.MENTAL_STRENGTH in outcomes
        assert YogaOutcome.PUBLIC_RECOGNITION in outcomes
        assert len(outcomes) >= 3

    def test_dhudhara_multi_domain(self) -> None:
        """Dhudhara should include MENTAL_STRENGTH, PUBLIC_RECOGNITION."""
        outcomes = self.svc.get_possible_outcomes("DHUDHARA")
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert YogaOutcome.MENTAL_STRENGTH in outcomes
        assert YogaOutcome.PUBLIC_RECOGNITION in outcomes
        assert len(outcomes) >= 3

    def test_neecha_bhangra_multi_domain(self) -> None:
        """Neecha Bhanga should include RECOVERY_FROM_ADVERSITY."""
        outcomes = self.svc.get_possible_outcomes("NEECHA BHANGA")
        assert YogaOutcome.RECOVERY_FROM_ADVERSITY in outcomes
        assert YogaOutcome.GENERAL_IMPROVEMENT in outcomes
        assert len(outcomes) >= 2

    def test_dhana_multi_domain(self) -> None:
        """Dhana should include BUSINESS_ACUMEN."""
        outcomes = self.svc.get_possible_outcomes("DHANA")
        assert YogaOutcome.WEALTH_ACCUMULATION in outcomes
        assert YogaOutcome.BUSINESS_ACUMEN in outcomes
        assert YogaOutcome.CAREER_PROMINENCE in outcomes
        assert len(outcomes) >= 3

    def test_unknown_yoga_returns_general(self) -> None:
        """Unknown yoga returns GENERAL_IMPROVEMENT as default."""
        outcomes = self.svc.get_possible_outcomes("UNKNOWN_YOGA")
        assert outcomes == {YogaOutcome.GENERAL_IMPROVEMENT}

    def test_all_yogas_have_at_least_3_domains(self) -> None:
        """Every mapped yoga should have at least 3 possible outcome domains."""
        yogas = [
            "RAJA", "DHANA", "GAJAKESARI", "VIPAREETA RAJA", "NEECHA BHANGA",
            "RUCHAKA", "BHADRA", "HAMSA", "MALAVYA", "SASA",
            "ANAPHA", "SUNAPHA", "DHUDHARA",
        ]
        for yoga in yogas:
            outcomes = self.svc.get_possible_outcomes(yoga)
            assert len(outcomes) >= 3, f"{yoga} has only {len(outcomes)} domains (need >= 3)"

    def test_primary_domain_is_subset_of_possible(self) -> None:
        """The primary domain from map_outcome should always be in get_possible_outcomes."""
        yogas = [
            "RAJA", "DHANA", "GAJAKESARI", "VIPAREETA RAJA", "NEECHA BHANGA",
            "RUCHAKA", "BHADRA", "HAMSA", "MALAVYA", "SASA",
            "ANAPHA", "SUNAPHA", "DHUDHARA",
        ]
        for yoga in yogas:
            primary = self.svc.map_outcome(yoga)
            possible = self.svc.get_possible_outcomes(yoga)
            assert primary in possible, (
                f"{yoga}: primary={primary} not in possible={[p.value for p in possible]}"
            )


class TestDomainRelevanceMatching:
    """Test that the domain relevance matching logic works correctly."""

    def test_career_event_matches_career_domains(self) -> None:
        """CAREER events should match CAREER_PROMINENCE, POLITICAL_POWER, etc."""
        from scripts.blind_evaluation_cohort import _DOMAIN_RELEVANCE

        career_domains = _DOMAIN_RELEVANCE.get("CAREER", set())
        assert "CAREER_PROMINENCE" in career_domains
        assert "POLITICAL_POWER" in career_domains
        assert "SOCIAL_STATUS" in career_domains
        assert "LEADERSHIP" in career_domains

    def test_health_event_matches_health_domains(self) -> None:
        """HEALTH events should match RECOVERY_FROM_ADVERSITY, etc."""
        from scripts.blind_evaluation_cohort import _DOMAIN_RELEVANCE

        health_domains = _DOMAIN_RELEVANCE.get("HEALTH", set())
        assert "RECOVERY_FROM_ADVERSITY" in health_domains
        assert "CRISIS_MANAGEMENT" in health_domains

    def test_malavya_matches_career_event(self) -> None:
        """Malavya's domains should overlap with CAREER event domains."""
        from scripts.blind_evaluation_cohort import _DOMAIN_RELEVANCE

        svc = YogaEvaluatorService()
        malavya_domains = svc.get_possible_outcomes("MALAVYA")
        malavya_domain_values = {d.value for d in malavya_domains}
        career_domains = _DOMAIN_RELEVANCE.get("CAREER", set())

        assert malavya_domain_values & career_domains, (
            f"Malavya domains {[d.value for d in malavya_domains]} "
            f"don't overlap with CAREER domains {career_domains}"
        )

    def test_sunapha_matches_career_event(self) -> None:
        """Sunapha's domains should overlap with CAREER event domains."""
        from scripts.blind_evaluation_cohort import _DOMAIN_RELEVANCE

        svc = YogaEvaluatorService()
        sunapha_domains = svc.get_possible_outcomes("SUNAPHA")
        sunapha_domain_values = {d.value for d in sunapha_domains}
        career_domains = _DOMAIN_RELEVANCE.get("CAREER", set())

        assert sunapha_domain_values & career_domains, (
            f"Sunapha domains {[d.value for d in sunapha_domains]} "
            f"don't overlap with CAREER domains {career_domains}"
        )

    def test_gajakesari_matches_career_event(self) -> None:
        """Gajakesari's domains should overlap with CAREER event domains."""
        from scripts.blind_evaluation_cohort import _DOMAIN_RELEVANCE

        svc = YogaEvaluatorService()
        gk_domains = svc.get_possible_outcomes("GAJAKESARI")
        gk_domain_values = {d.value for d in gk_domains}
        career_domains = _DOMAIN_RELEVANCE.get("CAREER", set())

        assert gk_domain_values & career_domains, (
            f"Gajakesari domains {[d.value for d in gk_domains]} "
            f"don't overlap with CAREER domains {career_domains}"
        )
