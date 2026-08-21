"""Integration tests for JRS Orchestrator — full routing and evidence collection."""

from __future__ import annotations

import json

import pytest

from jrs.config import load_jrs_config
from jrs.models import (
    EvidencePacket,
    QueryCategory,
    QueryIntent,
    route_query_intent,
)
from jrs.serialize import (
    evidence_packet_from_dict,
    query_intent_from_dict,
    result_to_json,
)
from jrs.service import OrchestratorService


@pytest.fixture
def svc() -> OrchestratorService:
    """Create an OrchestratorService with the real config."""
    return OrchestratorService()


class TestCareerQueryRouting:
    """Integration tests for CAREER query routing."""

    def test_career_engines(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-career-001",
            category=QueryCategory.CAREER,
        )
        packet = svc.route_query(intent)
        engine_names = {eo.engine_name for eo in packet.engine_outputs}
        assert "bhava" in engine_names
        assert "bala" in engine_names
        assert "dasha" in engine_names
        assert "yoga" in engine_names
        assert "karaka" in engine_names

    def test_career_houses(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-career-002",
            category=QueryCategory.CAREER,
        )
        request = svc.resolve_request(intent)
        assert 10 in request.required_houses
        assert 6 in request.required_houses

    def test_career_research_topics(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-career-003",
            category=QueryCategory.CAREER,
        )
        request = svc.resolve_request(intent)
        assert "career_indicators" in request.required_research_topics

    def test_career_packet_query_id(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-career-004",
            category=QueryCategory.CAREER,
        )
        packet = svc.route_query(intent)
        assert packet.query_id == "int-career-004"


class TestMarriageQueryRouting:
    """Integration tests for MARRIAGE query routing."""

    def test_marriage_includes_drik_and_avastha(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-marriage-001",
            category=QueryCategory.MARRIAGE,
        )
        packet = svc.route_query(intent)
        engine_names = {eo.engine_name for eo in packet.engine_outputs}
        assert "drik" in engine_names
        assert "avastha" in engine_names

    def test_marriage_houses(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-marriage-002",
            category=QueryCategory.MARRIAGE,
        )
        request = svc.resolve_request(intent)
        assert 7 in request.required_houses
        assert 2 in request.required_houses

    def test_marriage_engine_count(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-marriage-003",
            category=QueryCategory.MARRIAGE,
        )
        packet = svc.route_query(intent)
        # MARRIAGE has 7 engines
        assert len(packet.engine_outputs) == 7


class TestAllCategoriesRoute:
    """Integration test: every category produces a valid packet."""

    @pytest.mark.parametrize("category", list(QueryCategory))
    def test_category_routes(
        self,
        svc: OrchestratorService,
        category: QueryCategory,
    ) -> None:
        intent = QueryIntent(
            query_id=f"int-all-{category.value.lower()}",
            category=category,
        )
        packet = svc.route_query(intent)
        assert packet.query_id == intent.query_id
        assert len(packet.engine_outputs) > 0
        assert len(packet.research_evidence) > 0


class TestContextHouseMerging:
    """Integration tests for context-supplied house merging."""

    def test_career_with_extra_houses(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-ctx-001",
            category=QueryCategory.CAREER,
            context={"houses": "3,5"},
        )
        request = svc.resolve_request(intent)
        # Default (10,6) + context (3,5) = (3,5,6,10)
        assert request.required_houses == (3, 5, 6, 10)

    def test_marriage_with_extra_house(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-ctx-002",
            category=QueryCategory.MARRIAGE,
            context={"houses": "1"},
        )
        request = svc.resolve_request(intent)
        # Default (7,2) + context (1) = (1,2,7)
        assert request.required_houses == (1, 2, 7)


class TestSerializationRoundTrip:
    """Integration tests for serialization round-trip."""

    def test_intent_round_trip(self) -> None:
        intent = QueryIntent(
            query_id="int-rt-001",
            category=QueryCategory.WEALTH,
            context={"focus": "jupiter"},
        )
        d = intent.to_dict()
        restored = query_intent_from_dict(d)
        assert restored.query_id == intent.query_id
        assert restored.category is intent.category
        assert restored.context == intent.context

    def test_packet_json_serializable(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-rt-002",
            category=QueryCategory.CAREER,
        )
        packet = svc.route_query(intent)
        json_str = result_to_json(packet)
        parsed = json.loads(json_str)
        assert parsed["query_id"] == "int-rt-002"
        assert len(parsed["engine_outputs"]) > 0

    def test_packet_deterministic_json(self, svc: OrchestratorService) -> None:
        intent = QueryIntent(
            query_id="int-rt-003",
            category=QueryCategory.HEALTH,
        )
        p1 = svc.route_query(intent)
        p2 = svc.route_query(intent)
        # Same engine names -> same JSON structure (minus timestamps)
        json1 = json.loads(result_to_json(p1))
        json2 = json.loads(result_to_json(p2))
        names1 = [eo["engine_name"] for eo in json1["engine_outputs"]]
        names2 = [eo["engine_name"] for eo in json2["engine_outputs"]]
        assert names1 == names2


class TestEngineOutputNoDuplicates:
    """Integration test: no duplicate engine outputs in a packet."""

    def test_no_duplicate_engines(self, svc: OrchestratorService) -> None:
        for category in QueryCategory:
            intent = QueryIntent(
                query_id=f"int-dup-{category.value.lower()}",
                category=category,
            )
            packet = svc.route_query(intent)
            names = [eo.engine_name for eo in packet.engine_outputs]
            assert len(names) == len(set(names)), (
                f"Duplicate engines in {category.value}: {names}"
            )
