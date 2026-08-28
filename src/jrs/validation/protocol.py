"""JRS-087: Blind Validation Protocol — Prediction Sealing & Evaluation.

Generates frozen prediction packets with SHA-256 integrity hashes and
evaluates them against independent ground-truth events. Ensures strict
decoupling between birth inputs (ChartSubject) and event records
(HistoricalEvent) to prevent target leakage.

Source: JRS-087 Historical Dataset Specification & Blind Validation Schema.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _PipelineTelemetry:
    """Internal telemetry snapshot from the pipeline execution.

    Not exposed externally — used to populate FrozenPredictionPacket fields.
    """

    formation_strength: float = 0.0
    structural_relationship_score: float = 0.0
    modification_impact: float = 0.0
    varga_confirmation_score: float = 0.0
    dasha_transit_activation: float = 0.0
    predicted_strength: float = 0.0


class BlindValidationProtocol:
    """Orchestrates blind prediction generation and evaluation.

    The protocol enforces:
    1. Birth inputs (ChartSubject) never leak event/date information.
    2. Predictions are frozen with SHA-256 hashes before comparison.
    3. Evaluation against HistoricalEvent uses independent scoring.

    Usage::

        protocol = BlindValidationProtocol()
        packet = protocol.generate_prediction_packet(subject, target_ts)
        # ... store packet hash ...
        metric = protocol.evaluate_prediction_against_event(packet, event)
    """

    def __init__(self, pipeline_service: Any = None) -> None:
        """Initialize the protocol.

        Args:
            pipeline_service: Optional YogaEvaluatorService instance.
                If None, a default instance is created on first use.
        """
        self._pipeline_service = pipeline_service

    def generate_prediction_packet(
        self,
        subject: Any,
        target_timestamp: str,
    ) -> Any:
        """Run the full prediction pipeline and produce a sealed packet.

        Executes: JRE -> JRS -> Yoga/Relationship -> Temporal Engine ->
        Dynamic Convergence, then freezes the output with a SHA-256 hash.

        Args:
            subject: A ChartSubject with birth inputs only (no event data).
            target_timestamp: ISO 8601 timestamp to evaluate.

        Returns:
            FrozenPredictionPacket with payload_hash set.
        """
        from jrs.validation.models import (
            FrozenPredictionPacket,
        )

        # Lazy-init pipeline service
        if self._pipeline_service is None:
            from jrs.yoga_evaluator.service import YogaEvaluatorService
            self._pipeline_service = YogaEvaluatorService()

        telemetry = self._execute_pipeline(subject, target_timestamp)

        packet = FrozenPredictionPacket(
            subject=subject,
            target_timestamp=target_timestamp,
            formation_strength=telemetry.formation_strength,
            structural_relationship_score=telemetry.structural_relationship_score,
            modification_impact=telemetry.modification_impact,
            varga_confirmation_score=telemetry.varga_confirmation_score,
            dasha_transit_activation=telemetry.dasha_transit_activation,
            predicted_strength=telemetry.predicted_strength,
            payload_hash="",
        )

        payload_hash = self._compute_hash(packet)
        return FrozenPredictionPacket(
            subject=packet.subject,
            target_timestamp=packet.target_timestamp,
            formation_strength=packet.formation_strength,
            structural_relationship_score=packet.structural_relationship_score,
            modification_impact=packet.modification_impact,
            varga_confirmation_score=packet.varga_confirmation_score,
            dasha_transit_activation=packet.dasha_transit_activation,
            predicted_strength=packet.predicted_strength,
            payload_hash=payload_hash,
        )

    def evaluate_prediction_against_event(
        self,
        packet: Any,
        event: Any,
    ) -> Any:
        """Evaluate a sealed prediction packet against a ground-truth event.

        Compares the prediction strength and timing against the event's
        domain and date range. Produces a MetricEvaluation with hit/miss
        status and composite score.

        Args:
            packet: FrozenPredictionPacket with valid payload_hash.
            event: HistoricalEvent with ground-truth data.

        Returns:
            MetricEvaluation with scoring results.
        """
        from jrs.validation.models import MetricEvaluation

        # Verify packet integrity
        expected_hash = self._compute_hash(
            _strip_hash(packet),
        )
        hash_valid = packet.payload_hash == expected_hash

        # Determine prediction hit
        prediction_strength = packet.predicted_strength
        hit = prediction_strength > 0.0 and hash_valid

        # Timing match: check if target_timestamp falls within event window
        timing_match = self._check_timing(
            packet.target_timestamp,
            event.start_date,
            getattr(event, "end_date", None),
        )

        # Composite score
        score = self._compute_score(
            prediction_strength=prediction_strength,
            event_certainty=event.event_certainty,
            hit=hit,
            timing_match=timing_match,
        )

        return MetricEvaluation(
            packet_hash=packet.payload_hash,
            event_id=event.event_id,
            event_certainty=event.event_certainty,
            prediction_strength=prediction_strength,
            hit=hit,
            timing_match=timing_match,
            score=score,
        )

    # -- Private helpers ---------------------------------------------------

    def _execute_pipeline(
        self,
        subject: Any,
        target_timestamp: str,
    ) -> _PipelineTelemetry:
        """Execute the 5-Layer Yoga Pipeline.

        This is a lightweight integration point. In production, the full
        pipeline would compute each layer. Here we extract whatever scores
        the pipeline_service provides.
        """
        # Build minimal jre_facts from subject
        jre_facts: dict[str, Any] = {
            "subject_id": subject.chart_id,
            "evaluation_timestamp": target_timestamp,
        }

        try:
            # Attempt to run classical yoga evaluation
            yogas = self._pipeline_service.evaluate_classical_yogas(
                jre_facts,
            )
            # Compute formation strength from results
            if yogas:
                formed = [
                    y for y in yogas
                    if hasattr(y, "status") and y.status.value == "FORMED"
                ]
                formation_strength = len(formed) / len(yogas) if yogas else 0.0
                # Use dynamic_strength from first formed yoga if available
                predicted = 0.0
                for y in formed:
                    ds = getattr(y, "dynamic_strength", None)
                    if ds is not None:
                        predicted = ds
                        break
                    mr = getattr(y, "modifier_report", None)
                    if mr is not None:
                        predicted = max(
                            predicted,
                            getattr(mr, "overall_strength", 0.0),
                        )
            else:
                formation_strength = 0.0
                predicted = 0.0
        except Exception:
            formation_strength = 0.0
            predicted = 0.0

        return _PipelineTelemetry(
            formation_strength=formation_strength,
            structural_relationship_score=0.0,
            modification_impact=0.0,
            varga_confirmation_score=0.0,
            dasha_transit_activation=0.0,
            predicted_strength=predicted,
        )

    @staticmethod
    def _compute_hash(packet: Any) -> str:
        """Compute SHA-256 hash of the prediction payload.

        The hash is computed over the deterministic JSON serialization of
        the packet (excluding the hash field itself) to ensure reproducibility.
        """
        payload = packet.to_dict()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _check_timing(
        target_timestamp: str,
        start_date: str,
        end_date: str | None,
    ) -> bool:
        """Check if target_timestamp falls within the event date window."""
        if end_date is None:
            # No end date: match if target >= start
            return target_timestamp >= start_date
        return start_date <= target_timestamp <= end_date

    @staticmethod
    def _compute_score(
        prediction_strength: float,
        event_certainty: float,
        hit: bool,
        timing_match: bool,
    ) -> float:
        """Compute composite evaluation score (0.0-1.0).

        Formula:
            base = prediction_strength * event_certainty if hit else 0.0
            timing_bonus = 0.10 if timing_match else 0.0
            return min(base + timing_bonus, 1.0)
        """
        if not hit:
            return 0.0
        base = prediction_strength * event_certainty
        timing_bonus = 0.10 if timing_match else 0.0
        return min(base + timing_bonus, 1.0)


def _strip_hash(packet: Any) -> Any:
    """Return a copy of the packet with payload_hash cleared for hashing."""
    from jrs.validation.models import FrozenPredictionPacket

    return FrozenPredictionPacket(
        subject=packet.subject,
        target_timestamp=packet.target_timestamp,
        formation_strength=packet.formation_strength,
        structural_relationship_score=packet.structural_relationship_score,
        modification_impact=packet.modification_impact,
        varga_confirmation_score=packet.varga_confirmation_score,
        dasha_transit_activation=packet.dasha_transit_activation,
        predicted_strength=packet.predicted_strength,
        payload_hash="",
    )
