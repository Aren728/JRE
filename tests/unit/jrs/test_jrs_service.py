"""Unit tests for JRS OrchestratorService."""

from __future__ import annotations

import pytest

from tests.unit.jrs.conftest import make_query_intent
from jrs.errors import EngineExecutionError, InvalidQueryError
from jrs.models import (
    JRSConfig,
    QueryCategory,
    RoutingRule,
)
from jrs.service import OrchestratorService


class TestOrchestratorServiceInit:
    """Tests for OrchestratorService initialization."""

    def test_default_config(self) -> None:
        svc = OrchestratorService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        assert svc.config is sample_config


class TestOrchestratorServiceResolveRequest:
    """Tests for the resolve_request method."""

    def test_career_request(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.CAREER)
        request = svc.resolve_request(intent)
        assert "bhava" in request.required_engines
        assert 10 in request.required_houses

    def test_wealth_request(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.WEALTH)
        request = svc.resolve_request(intent)
        assert "bhava" in request.required_engines
        assert 2 in request.required_houses

    def test_marriage_request(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.MARRIAGE)
        request = svc.resolve_request(intent)
        assert "drik" in request.required_engines
        assert "avastha" in request.required_engines
        assert 7 in request.required_houses

    def test_health_request(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.HEALTH)
        request = svc.resolve_request(intent)
        assert "avastha" in request.required_engines
        assert 8 in request.required_houses

    def test_unknown_category_raises(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        # Create a mock intent with a category not in the routing matrix
        # We need to bypass the enum validation, so we test via route_query
        config_no_career = JRSConfig(
            routing={"WEALTH": RoutingRule(required_engines=("bhava",))},
        )
        svc2 = OrchestratorService(config=config_no_career)
        intent = make_query_intent(category=QueryCategory.CAREER)
        with pytest.raises(InvalidQueryError, match="Unknown query category"):
            svc2.resolve_request(intent)


class TestOrchestratorServiceRouteQuery:
    """Tests for the route_query method."""

    def test_routes_and_collects(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.CAREER)
        packet = svc.route_query(intent)
        assert packet.query_id == "test-001"
        assert len(packet.engine_outputs) > 0
        assert "career_indicators" in packet.research_evidence

    def test_empty_query_id_raises(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(query_id="")
        with pytest.raises(InvalidQueryError, match="query_id must not be empty"):
            svc.route_query(intent)

    def test_packet_has_correct_engine_count(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.CAREER)
        packet = svc.route_query(intent)
        # CAREER routing has 5 engines
        assert len(packet.engine_outputs) == 5

    def test_engine_names_match_routing(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.CAREER)
        packet = svc.route_query(intent)
        engine_names = {eo.engine_name for eo in packet.engine_outputs}
        expected = {"bhava", "bala", "dasha", "yoga", "karaka"}
        assert engine_names == expected

    def test_deterministic_output(self, sample_config: JRSConfig) -> None:
        """Same input produces same engine names (timestamps differ but names don't)."""
        svc = OrchestratorService(config=sample_config)
        intent = make_query_intent(category=QueryCategory.WEALTH)
        p1 = svc.route_query(intent)
        p2 = svc.route_query(intent)
        names1 = [eo.engine_name for eo in p1.engine_outputs]
        names2 = [eo.engine_name for eo in p2.engine_outputs]
        assert names1 == names2

    def test_unknown_category_in_route_query(self, sample_config: JRSConfig) -> None:
        svc = OrchestratorService(config=sample_config)
        config_empty = JRSConfig(routing={})
        svc2 = OrchestratorService(config=config_empty)
        intent = make_query_intent(category=QueryCategory.CAREER)
        with pytest.raises(InvalidQueryError, match="Unknown query category"):
            svc2.route_query(intent)
