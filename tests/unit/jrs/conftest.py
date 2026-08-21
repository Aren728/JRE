"""Shared test fixtures and builders for JRS unit tests."""

from __future__ import annotations

from typing import Any

import pytest

from jrs.models import (
    EvidencePacket,
    EngineOutput,
    EvidenceRequest,
    JRSConfig,
    QueryCategory,
    QueryIntent,
    RoutingRule,
)


@pytest.fixture
def sample_routing() -> dict[str, RoutingRule]:
    """A minimal routing matrix for testing."""
    return {
        "CAREER": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka"),
            research_topics=("career_indicators",),
            required_houses=(10, 6),
        ),
        "WEALTH": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka"),
            research_topics=("wealth_indicators",),
            required_houses=(2, 11),
        ),
        "MARRIAGE": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "drik", "yoga", "karaka", "avastha"),
            research_topics=("marriage_indicators",),
            required_houses=(7, 2),
        ),
        "HEALTH": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka", "avastha"),
            research_topics=("health_indicators",),
            required_houses=(1, 6, 8),
        ),
        "EDUCATION": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka"),
            research_topics=("education_indicators",),
            required_houses=(4, 5, 9),
        ),
        "PROPERTY": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka"),
            research_topics=("property_indicators",),
            required_houses=(4, 11),
        ),
        "CHILDREN": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "drik", "yoga", "karaka"),
            research_topics=("children_indicators",),
            required_houses=(5, 11),
        ),
        "LITIGATION": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "drik", "yoga", "karaka"),
            research_topics=("litigation_indicators",),
            required_houses=(6, 12),
        ),
        "TRAVEL": RoutingRule(
            required_engines=("bhava", "dasha", "yoga", "karaka"),
            research_topics=("travel_indicators",),
            required_houses=(9, 12),
        ),
        "GENERAL": RoutingRule(
            required_engines=("bhava", "bala", "dasha", "yoga", "karaka"),
            research_topics=("general_chart_analysis",),
            required_houses=(1,),
        ),
    }


@pytest.fixture
def sample_config(sample_routing: dict[str, RoutingRule]) -> JRSConfig:
    """A minimal JRSConfig for testing."""
    return JRSConfig(
        version="1.0",
        default_research_depth="standard",
        routing=sample_routing,
        engine_hints={"tajika_if_annual": True},
    )


def make_query_intent(
    query_id: str = "test-001",
    category: QueryCategory = QueryCategory.CAREER,
    context: dict[str, str] | None = None,
) -> QueryIntent:
    """Builder for QueryIntent test objects."""
    return QueryIntent(
        query_id=query_id,
        category=category,
        context=context or {},
    )


def make_engine_output(
    engine_name: str = "bhava",
    result: Any = None,
) -> EngineOutput:
    """Builder for EngineOutput test objects."""
    return EngineOutput(engine_name=engine_name, result=result)


def make_evidence_packet(
    query_id: str = "test-001",
    engine_names: tuple[str, ...] = ("bhava", "bala"),
    research_topics: tuple[str, ...] = ("career_indicators",),
) -> EvidencePacket:
    """Builder for EvidencePacket test objects."""
    outputs = tuple(make_engine_output(name) for name in engine_names)
    return EvidencePacket(
        query_id=query_id,
        engine_outputs=outputs,
        research_evidence=research_topics,
    )
