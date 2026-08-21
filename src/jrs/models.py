"""JRS Orchestrator data models and routing logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────

class QueryCategory(Enum):
    """Supported query categories for routing."""

    CAREER = "CAREER"
    WEALTH = "WEALTH"
    MARRIAGE = "MARRIAGE"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    PROPERTY = "PROPERTY"
    CHILDREN = "CHILDREN"
    LITIGATION = "LITIGATION"
    TRAVEL = "TRAVEL"
    GENERAL = "GENERAL"


# All valid engine module names
ALL_ENGINES: tuple[str, ...] = (
    "astronomy", "jyotish", "knowledge", "bhava", "gochar",
    "context", "varga", "research", "dasha", "bala", "drik",
    "yoga", "karaka", "avastha", "ashtakavarga", "tajika",
    "jaimini", "prashna", "muhurta", "rectification", "synthesis",
)


# ── Routing Rule (defined early for forward refs) ────────────────────────────

@dataclass(frozen=True)
class RoutingRule:
    """A single routing rule mapping a query category to engines and topics."""

    required_engines: tuple[str, ...] = ()
    research_topics: tuple[str, ...] = ()
    required_houses: tuple[int, ...] = ()


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class QueryIntent:
    """Structured user query identifying what analysis is requested."""

    query_id: str
    category: QueryCategory
    context: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "query_id": self.query_id,
            "category": self.category.value,
            "context": dict(sorted(self.context.items())),
        }


@dataclass(frozen=True)
class EvidenceRequest:
    """Resolved routing decision: which engines and research topics to invoke."""

    intent: QueryIntent
    required_engines: tuple[str, ...] = ()
    required_research_topics: tuple[str, ...] = ()
    required_houses: tuple[int, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "intent": self.intent.to_dict(),
            "required_engines": list(self.required_engines),
            "required_research_topics": list(self.required_research_topics),
            "required_houses": list(self.required_houses),
        }


@dataclass(frozen=True)
class EngineOutput:
    """A single engine's output stored in the EvidencePacket."""

    engine_name: str
    result: Any | None = None  # The engine's specific Report object
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "engine_name": self.engine_name,
            "computed_at": self.computed_at.isoformat(),
        }


@dataclass(frozen=True)
class EvidencePacket:
    """Aggregated outputs from all invoked engines for a query."""

    query_id: str
    engine_outputs: tuple[EngineOutput, ...] = ()
    research_evidence: tuple[str, ...] = ()
    aggregated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "query_id": self.query_id,
            "engine_outputs": [eo.to_dict() for eo in self.engine_outputs],
            "research_evidence": list(self.research_evidence),
            "aggregated_at": self.aggregated_at.isoformat(),
        }


# ── Orchestrator Config ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class JRSConfig:
    """Configuration for the Orchestrator including routing matrix."""

    version: str = "1.0"
    default_research_depth: str = "standard"
    routing: dict[str, RoutingRule] = field(default_factory=dict)
    engine_hints: dict[str, bool] = field(default_factory=dict)


# ── Routing Logic ────────────────────────────────────────────────────────────

def route_query_intent(
    intent: QueryIntent,
    routing: dict[str, RoutingRule],
) -> EvidenceRequest:
    """Resolve a QueryIntent to an EvidenceRequest using the routing matrix.

    This is the core routing function: it maps a user's query category to
    the specific set of engines and research topics that should be invoked.

    Args:
        intent: The user's query intent.
        routing: The routing matrix from configuration.

    Returns:
        An EvidenceRequest specifying which engines and topics to invoke.

    Raises:
        KeyError: If the intent's category is not in the routing matrix.
    """
    rule = routing[intent.category.value]

    # Merge context-supplied houses with rule defaults
    context_houses: tuple[int, ...] = ()
    if "houses" in intent.context:
        house_strs = intent.context["houses"].split(",")
        context_houses = tuple(int(h.strip()) for h in house_strs if h.strip())

    all_houses = tuple(sorted(set(rule.required_houses + context_houses)))

    return EvidenceRequest(
        intent=intent,
        required_engines=rule.required_engines,
        required_research_topics=rule.research_topics,
        required_houses=all_houses,
    )
