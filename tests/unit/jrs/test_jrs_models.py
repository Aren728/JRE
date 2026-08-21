"""Unit tests for JRS orchestrator models and routing logic."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.conftest import make_query_intent
from jrs.models import (
    ALL_ENGINES,
    EvidencePacket,
    EvidenceRequest,
    EngineOutput,
    JRSConfig,
    QueryCategory,
    QueryIntent,
    RoutingRule,
    route_query_intent,
)


class TestQueryCategory:
    """Tests for the QueryCategory enum."""

    def test_all_categories_have_string_values(self) -> None:
        for cat in QueryCategory:
            assert isinstance(cat.value, str)
            assert cat.value == cat.name

    def test_category_count(self) -> None:
        assert len(QueryCategory) == 10

    def test_category_from_value(self) -> None:
        assert QueryCategory("CAREER") is QueryCategory.CAREER
        assert QueryCategory("WEALTH") is QueryCategory.WEALTH

    def test_invalid_category(self) -> None:
        with pytest.raises(ValueError):
            QueryCategory("INVALID")


class TestQueryIntent:
    """Tests for the QueryIntent model."""

    def test_creation(self) -> None:
        intent = make_query_intent(query_id="q-001", category=QueryCategory.HEALTH)
        assert intent.query_id == "q-001"
        assert intent.category is QueryCategory.HEALTH
        assert intent.context == {}

    def test_frozen(self) -> None:
        intent = make_query_intent()
        with pytest.raises(AttributeError):
            intent.query_id = "changed"  # type: ignore[misc]

    def test_to_dict_deterministic(self) -> None:
        intent = make_query_intent(context={"houses": "10,6", "focus": "saturn"})
        d1 = intent.to_dict()
        d2 = intent.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_to_dict_sorted_context(self) -> None:
        intent = make_query_intent(context={"z": "1", "a": "2"})
        d = intent.to_dict()
        keys = list(d["context"].keys())
        assert keys == sorted(keys)

    def test_to_dict_structure(self) -> None:
        intent = make_query_intent(query_id="q-042", category=QueryCategory.MARRIAGE)
        d = intent.to_dict()
        assert d["query_id"] == "q-042"
        assert d["category"] == "MARRIAGE"
        assert isinstance(d["context"], dict)


class TestRoutingRule:
    """Tests for the RoutingRule model."""

    def test_defaults(self) -> None:
        rule = RoutingRule()
        assert rule.required_engines == ()
        assert rule.research_topics == ()
        assert rule.required_houses == ()

    def test_frozen(self) -> None:
        rule = RoutingRule(required_engines=("bhava",))
        with pytest.raises(AttributeError):
            rule.required_engines = ()  # type: ignore[misc]

    def test_equality(self) -> None:
        r1 = RoutingRule(required_engines=("bhava",), required_houses=(10,))
        r2 = RoutingRule(required_engines=("bhava",), required_houses=(10,))
        assert r1 == r2


class TestRouteQueryIntent:
    """Tests for the route_query_intent routing function."""

    def test_career_routing(self, sample_routing: dict[str, RoutingRule]) -> None:
        intent = make_query_intent(category=QueryCategory.CAREER)
        request = route_query_intent(intent, sample_routing)
        assert "bhava" in request.required_engines
        assert "bala" in request.required_engines
        assert 10 in request.required_houses
        assert 6 in request.required_houses
        assert "career_indicators" in request.required_research_topics

    def test_marriage_routing(self, sample_routing: dict[str, RoutingRule]) -> None:
        intent = make_query_intent(category=QueryCategory.MARRIAGE)
        request = route_query_intent(intent, sample_routing)
        assert "drik" in request.required_engines
        assert "avastha" in request.required_engines
        assert 7 in request.required_houses

    def test_context_houses_merged(self, sample_routing: dict[str, RoutingRule]) -> None:
        intent = make_query_intent(
            category=QueryCategory.CAREER,
            context={"houses": "3,5"},
        )
        request = route_query_intent(intent, sample_routing)
        # Original houses (10,6) + context houses (3,5) merged and sorted
        assert request.required_houses == (3, 5, 6, 10)

    def test_unknown_category_raises(self) -> None:
        intent = make_query_intent(category=QueryCategory.CAREER)
        with pytest.raises(KeyError):
            route_query_intent(intent, {})

    def test_general_routing(self, sample_routing: dict[str, RoutingRule]) -> None:
        intent = make_query_intent(category=QueryCategory.GENERAL)
        request = route_query_intent(intent, sample_routing)
        assert 1 in request.required_houses
        assert "bhava" in request.required_engines

    def test_travel_uses_fewer_engines(self, sample_routing: dict[str, RoutingRule]) -> None:
        intent = make_query_intent(category=QueryCategory.TRAVEL)
        request = route_query_intent(intent, sample_routing)
        # Travel uses fewer engines than MARRIAGE
        marriage_intent = make_query_intent(category=QueryCategory.MARRIAGE)
        marriage_request = route_query_intent(marriage_intent, sample_routing)
        assert len(request.required_engines) < len(marriage_request.required_engines)


class TestEvidenceRequest:
    """Tests for the EvidenceRequest model."""

    def test_creation(self) -> None:
        intent = make_query_intent()
        request = EvidenceRequest(
            intent=intent,
            required_engines=("bhava",),
            required_research_topics=("career_indicators",),
            required_houses=(10,),
        )
        assert request.intent is intent
        assert request.required_engines == ("bhava",)

    def test_to_dict(self) -> None:
        intent = make_query_intent(query_id="q-100")
        request = EvidenceRequest(
            intent=intent,
            required_engines=("bhava", "bala"),
            required_houses=(10, 6),
        )
        d = request.to_dict()
        assert d["intent"]["query_id"] == "q-100"
        assert d["required_engines"] == ["bhava", "bala"]
        assert d["required_houses"] == [10, 6]

    def test_frozen(self) -> None:
        intent = make_query_intent()
        request = EvidenceRequest(intent=intent)
        with pytest.raises(AttributeError):
            request.required_engines = ()  # type: ignore[misc]


class TestEngineOutput:
    """Tests for the EngineOutput model."""

    def test_creation(self) -> None:
        eo = EngineOutput(engine_name="bhava", result={"test": True})
        assert eo.engine_name == "bhava"
        assert eo.result == {"test": True}

    def test_to_dict(self) -> None:
        eo = EngineOutput(engine_name="dasha")
        d = eo.to_dict()
        assert d["engine_name"] == "dasha"
        assert "computed_at" in d

    def test_frozen(self) -> None:
        eo = EngineOutput(engine_name="bhava")
        with pytest.raises(AttributeError):
            eo.engine_name = "changed"  # type: ignore[misc]


class TestEvidencePacket:
    """Tests for the EvidencePacket model."""

    def test_creation(self) -> None:
        outputs = (
            EngineOutput(engine_name="bhava"),
            EngineOutput(engine_name="bala"),
        )
        packet = EvidencePacket(
            query_id="q-001",
            engine_outputs=outputs,
            research_evidence=("career_indicators",),
        )
        assert packet.query_id == "q-001"
        assert len(packet.engine_outputs) == 2

    def test_to_dict_deterministic(self) -> None:
        outputs = (EngineOutput(engine_name="bhava"),)
        packet = EvidencePacket(
            query_id="q-001",
            engine_outputs=outputs,
        )
        d1 = packet.to_dict()
        d2 = packet.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_empty_packet(self) -> None:
        packet = EvidencePacket(query_id="q-empty")
        d = packet.to_dict()
        assert d["engine_outputs"] == []
        assert d["research_evidence"] == []

    def test_frozen(self) -> None:
        packet = EvidencePacket(query_id="q-001")
        with pytest.raises(AttributeError):
            packet.query_id = "changed"  # type: ignore[misc]


class TestJRSConfig:
    """Tests for the JRSConfig model."""

    def test_defaults(self) -> None:
        config = JRSConfig()
        assert config.version == "1.0"
        assert config.routing == {}
        assert config.engine_hints == {}

    def test_with_routing(self, sample_routing: dict[str, RoutingRule]) -> None:
        config = JRSConfig(routing=sample_routing)
        assert "CAREER" in config.routing
        assert "WEALTH" in config.routing


class TestAllEngines:
    """Tests for the ALL_ENGINES constant."""

    def test_contains_expected_engines(self) -> None:
        expected = {"bhava", "bala", "dasha", "drik", "yoga", "karaka",
                    "avastha", "ashtakavarga", "tajika", "jaimini",
                    "synthesis", "jyotish", "astronomy"}
        assert expected.issubset(set(ALL_ENGINES))

    def test_is_tuple(self) -> None:
        assert isinstance(ALL_ENGINES, tuple)

    def test_no_duplicates(self) -> None:
        assert len(ALL_ENGINES) == len(set(ALL_ENGINES))
