"""JRS Orchestrator service — routes queries and aggregates evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .config import load_jrs_config
from .errors import EngineExecutionError, InvalidQueryError
from .models import (
    ALL_ENGINES,
    EngineOutput,
    EvidencePacket,
    EvidenceRequest,
    JRSConfig,
    QueryIntent,
    route_query_intent,
)


class OrchestratorService:
    """JRS Orchestrator: routes queries to engines and aggregates evidence.

    Usage::

        svc = OrchestratorService()
        packet = svc.route_query(intent, natal_context)
    """

    def __init__(self, config: JRSConfig | None = None) -> None:
        """Initialize the orchestrator.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from
                    ``config/jrs.toml``.
        """
        self._config = config or load_jrs_config()

    def route_query(
        self,
        intent: QueryIntent,
        natal_context: Any = None,
    ) -> EvidencePacket:
        """Route a query intent to the required engines and collect outputs.

        Args:
            intent: The user's query intent.
            natal_context: Optional canonical context for engine execution.

        Returns:
            An EvidencePacket with all engine outputs aggregated.

        Raises:
            InvalidQueryError: If the query intent is malformed.
        """
        if not intent.query_id:
            raise InvalidQueryError("query_id must not be empty")

        try:
            evidence_request = route_query_intent(
                intent, self._config.routing,
            )
        except KeyError as exc:
            raise InvalidQueryError(
                f"Unknown query category: {intent.category.value}"
            ) from exc

        # Execute engines and collect outputs
        outputs = self._execute_engines(evidence_request)

        return EvidencePacket(
            query_id=intent.query_id,
            engine_outputs=outputs,
            research_evidence=evidence_request.required_research_topics,
            aggregated_at=datetime.now(UTC),
        )

    def resolve_request(self, intent: QueryIntent) -> EvidenceRequest:
        """Resolve a query intent to an EvidenceRequest (without executing engines).

        Useful for testing routing logic in isolation.

        Args:
            intent: The user's query intent.

        Returns:
            An EvidenceRequest specifying which engines to invoke.

        Raises:
            InvalidQueryError: If the query intent references an unknown category.
        """
        try:
            return route_query_intent(intent, self._config.routing)
        except KeyError as exc:
            raise InvalidQueryError(
                f"Unknown query category: {intent.category.value}"
            ) from exc

    def _execute_engines(
        self,
        request: EvidenceRequest,
    ) -> tuple[EngineOutput, ...]:
        """Execute the required engines and return their outputs.

        In v0.1, this returns placeholder outputs since individual engines
        are invoked by the calling context (e.g., the E2E pipeline).
        The actual engine execution happens at the integration layer.

        Args:
            request: The evidence request specifying which engines to invoke.

        Returns:
            A tuple of EngineOutput objects, one per required engine.
        """
        outputs: list[EngineOutput] = []
        now = datetime.now(UTC)

        for engine_name in request.required_engines:
            if engine_name not in ALL_ENGINES:
                raise EngineExecutionError(f"Unknown engine: {engine_name}")

            outputs.append(EngineOutput(
                engine_name=engine_name,
                result=None,  # Populated by the integration layer
                computed_at=now,
            ))

        return tuple(outputs)

    @property
    def config(self) -> JRSConfig:
        """Return the loaded configuration."""
        return self._config
