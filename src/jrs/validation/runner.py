"""JRS Phase A & JRS-088: Validation Runners.

HistoricalValidationRunner: Executes the non-blind 5-Layer Pipeline.
BlindValidationRunner: Executes isolated blind evaluation with SHA-256
    sealing and cryptographic verification.

Source: RI-010 Engine Architecture; BPHS Ch 7, 33, 35, 43, 45.
    JRS-088 Blind Historical Validation Runner Engine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jrs.temporal.models import windows_overlap
from jrs.varga.confirmation_service import (
    ConfirmationStatus,
    VargaConfirmationService,
)
from jrs.varga.saptavargaja_service import SaptavargajaBalaService
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService

from .models import (
    BatchValidationReport,
    BirthChart,
    ChartSubject,
    ChartValidationResult,
    CryptographicTamperError,
    DomainType,
    EventDomain,
    EventPredictionMatch,
    FrozenPredictionPacket,
    HistoricalEvent,
    KnownEvent,
    MetricEvaluation,
    PredictionVerdict,
    PredictedYoga,
    SingleValidationReport,
    TimingMatchStatus,
    TimingWindow,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


# ── Yoga-to-Domain Mapping ───────────────────────────────────────────────────

_YOGA_DOMAIN_MAP: dict[str, EventDomain] = {
    "GAJAKESARI": EventDomain.GENERAL,
    "RAJA": EventDomain.CAREER,
    "DHANA": EventDomain.WEALTH,
    "VIPAREETA RAJA": EventDomain.CAREER,
    "NEECHA BHANGA": EventDomain.GENERAL,
    # Pancha Mahapurusha
    "RUCHAKA": EventDomain.CAREER,
    "BHADRA": EventDomain.CAREER,
    "HAMSA": EventDomain.SPIRITUALITY,
    "MALAVYA": EventDomain.MARRIAGE,
    "SASA": EventDomain.CAREER,
    # Chandra
    "ANAPHA": EventDomain.WEALTH,
    "SUNAPHA": EventDomain.WEALTH,
    "DHUDHARA": EventDomain.WEALTH,
}


def _map_yoga_to_domain(yoga_name: str) -> EventDomain:
    """Map a yoga name to its primary domain."""
    key = yoga_name.upper().replace("_", " ")
    return _YOGA_DOMAIN_MAP.get(key, EventDomain.GENERAL)


def _determine_yoga_confidence(
    prediction: PredictedYoga,
) -> float:
    """Determine prediction confidence from pipeline outputs.

    Confidence is based on:
    - Yoga status (FORMED=1.0, WEAKENED=0.6, CANCELLED=0.1)
    - Overall multiplier (higher = more confident)
    """
    status_confidence = {
        "FORMED": 1.0,
        "WEAKENED": 0.6,
        "CANCELLED": 0.1,
    }
    base = status_confidence.get(prediction.predicted_status, 0.5)
    # Boost confidence if multiplier is high
    multiplier_boost = min(prediction.overall_multiplier / 3.0, 1.0) * 0.2
    return min(base + multiplier_boost, 1.0)


class HistoricalValidationRunner:
    """Runs synthetic charts through the 5-Layer Pipeline and compares
    predictions against verified life events.

    Usage::

        runner = HistoricalValidationRunner()
        chart = BirthChart(chart_id="...", birth_data=..., jre_facts=..., ...)
        result = runner.run_single_chart(chart)
        stats = evaluator.evaluate([result])
    """

    def __init__(self) -> None:
        """Initialize with all pipeline services."""
        self._evaluator = YogaEvaluatorService()
        self._varga_svc = VargaConfirmationService()
        self._saptavargaja_svc = SaptavargajaBalaService()

    def run_single_chart(self, chart: BirthChart) -> ChartValidationResult:
        """Execute the full pipeline for a single chart.

        Steps:
            1. Run YogaEvaluatorService.evaluate_classical_yogas() on jre_facts.
            2. For each formed/weakened yoga, evaluate D9 confirmation.
            3. Compute Saptavargaja Bala for involved planets.
            4. Build PredictedYoga objects with timing windows.
            5. Compare predictions against known events → matches.

        Args:
            chart: The BirthChart to validate.

        Returns:
            ChartValidationResult with predictions and matches.
        """
        # ── Layer 1-2-3: Yoga formation + modifiers + transit ──
        jre_facts = chart.jre_facts
        yoga_evals = self._evaluator.evaluate_classical_yogas(jre_facts)

        # ── Build PredictedYoga objects ──
        predicted_yogas: list[PredictedYoga] = []
        for eval_ in yoga_evals:
            yoga_name = eval_.yoga_name
            domain = _map_yoga_to_domain(yoga_name)

            # Determine involved planets from modifier report
            involved: tuple[str, ...] = ()
            if eval_.modifier_report is not None:
                involved = tuple(
                    pr.planet for pr in eval_.modifier_report.planet_results
                )

            # ── Layer 4: D9 confirmation ──
            varga_multiplier = 1.0
            cancellation_reason = eval_.cancellation_reason
            if (
                eval_.status != YogaStatus.CANCELLED
                and "planet_d9_house" in jre_facts
                and involved
            ):
                confirmation = self._varga_svc.evaluate_d9_confirmation(
                    list(involved), jre_facts,
                )
                if confirmation.confirmation_status == ConfirmationStatus.CANCELLED:
                    eval_status = "CANCELLED"
                    cancellation_reason = confirmation.cancellation_reason
                else:
                    eval_status = eval_.status.value
                    varga_multiplier = confirmation.net_strength_multiplier
            else:
                eval_status = eval_.status.value

            # ── Layer 5: Saptavargaja Bala ──
            # Compute average score across involved planets for multiplier
            saptavargaja_boost = 0.0
            if involved:
                scores = []
                for planet in involved:
                    p_data = jre_facts.get("planets", {}).get(planet, {})
                    if p_data:
                        score = self._saptavargaja_svc.evaluate_planet(
                            planet, p_data,
                        )
                        scores.append(score.total_score)
                if scores:
                    avg_score = sum(scores) / len(scores)
                    # Normalize: 35 max score → 1.0 max boost
                    saptavargaja_boost = min(avg_score / 35.0, 1.0) * 0.5

            # Net multiplier combines modifier, varga, and saptavargaja
            modifier_strength = 1.0
            if eval_.modifier_report is not None:
                modifier_strength = eval_.modifier_report.overall_strength
            overall_multiplier = (
                modifier_strength * varga_multiplier + saptavargaja_boost
            )

            # ── Timing windows from Dasha/Transit ──
            timing_windows = self._extract_timing_windows(
                jre_facts, involved,
            )

            prediction = PredictedYoga(
                yoga_name=yoga_name,
                predicted_status=eval_status,
                domain=domain,
                overall_multiplier=overall_multiplier,
                timing_windows=timing_windows,
                cancellation_reason=cancellation_reason,
                involved_planets=involved,
                confidence=_determine_yoga_confidence(PredictedYoga(
                    yoga_name=yoga_name,
                    predicted_status=eval_status,
                    overall_multiplier=overall_multiplier,
                )),
            )
            predicted_yogas.append(prediction)

        # ── Compare predictions against known events ──
        matches = self._compare_predictions(
            predicted_yogas, chart.known_events,
        )

        return ChartValidationResult(
            chart_id=chart.chart_id,
            predicted_yogas=tuple(predicted_yogas),
            matches=tuple(matches),
            total_known_events=len(chart.known_events),
            total_predicted_yogas=len(predicted_yogas),
            domain=chart.domain,
        )

    def run_batch(
        self,
        charts: list[BirthChart],
    ) -> list[ChartValidationResult]:
        """Run the pipeline on multiple charts.

        Args:
            charts: List of BirthCharts to validate.

        Returns:
            List of ChartValidationResult, one per chart.
        """
        return [self.run_single_chart(chart) for chart in charts]

    # ── Private helpers ──

    def _extract_timing_windows(
        self,
        jre_facts: dict[str, Any],
        involved_planets: tuple[str, ...],
    ) -> tuple[TimingWindow, ...]:
        """Extract timing windows from jre_facts Dasha/Transit data.

        Looks for:
        - ``dasha_periods``: list of {triggering_planet, start, end}
        - ``transits``: list of {triggering_planet, start, end}
        """
        windows: list[TimingWindow] = []

        # Dasha periods
        dasha_periods = jre_facts.get("dasha_periods", [])
        for d in dasha_periods:
            planet = d.get("triggering_planet", "")
            if planet in involved_planets:
                windows.append(TimingWindow(
                    yoga_name="",
                    window_start_utc=d.get("activation_start_utc", ""),
                    window_end_utc=d.get("activation_end_utc", ""),
                    dasha_lord=planet,
                    confidence=float(d.get("strength", 1.0)),
                ))

        # Transit activations
        transits = jre_facts.get("transits", [])
        for t in transits:
            planet = t.get("triggering_planet", "")
            if planet in involved_planets:
                windows.append(TimingWindow(
                    yoga_name="",
                    window_start_utc=t.get("activation_start_utc", ""),
                    window_end_utc=t.get("activation_end_utc", ""),
                    transit_planet=planet,
                    confidence=float(t.get("strength", 1.0)),
                ))

        return tuple(windows)

    def _compare_predictions(
        self,
        predictions: list[PredictedYoga],
        known_events: tuple[KnownEvent, ...],
    ) -> list[EventPredictionMatch]:
        """Compare predicted yogas against known events.

        For each known event:
        - Check if any prediction matches its yoga_types and domain.
        - Classify as TP (predicted + occurred), FP (predicted + didn't occur),
          TN (not predicted + didn't occur), FN (not predicted + occurred).
        - Compute timing overlap.
        """
        matches: list[EventPredictionMatch] = []

        for event in known_events:
            # Find predictions relevant to this event
            relevant_preds = [
                p for p in predictions
                if (
                    p.domain == event.domain
                    or p.yoga_name in event.yoga_types
                    or any(
                        pl in event.expected_planets
                        for pl in p.involved_planets
                    )
                )
            ]

            if relevant_preds:
                # At least one prediction matches this event → TRUE POSITIVE
                # (or FALSE POSITIVE if the yoga was cancelled)
                best_pred = max(
                    relevant_preds,
                    key=lambda p: p.confidence,
                )

                # Determine timing overlap
                timing_status, overlap_ratio = self._compute_timing_overlap(
                    best_pred.timing_windows, event,
                )

                # If yoga is CANCELLED, it's effectively not predicted
                if best_pred.predicted_status == "CANCELLED":
                    verdict = PredictionVerdict.FALSE_NEGATIVE
                else:
                    verdict = PredictionVerdict.TRUE_POSITIVE

                matches.append(EventPredictionMatch(
                    event_id=event.event_id,
                    yoga_name=best_pred.yoga_name,
                    verdict=verdict,
                    timing_status=timing_status,
                    timing_overlap_ratio=overlap_ratio,
                    confidence=best_pred.confidence,
                ))
            else:
                # No prediction for this event → FALSE NEGATIVE
                matches.append(EventPredictionMatch(
                    event_id=event.event_id,
                    yoga_name="",
                    verdict=PredictionVerdict.FALSE_NEGATIVE,
                    timing_status=TimingMatchStatus.ACTUAL_ONLY,
                    timing_overlap_ratio=0.0,
                    confidence=0.0,
                ))

        # Check for predictions that don't match any known event (FP)
        matched_yogas = {m.yoga_name for m in matches if m.yoga_name}
        for pred in predictions:
            if (
                pred.yoga_name not in matched_yogas
                and pred.predicted_status != "CANCELLED"
            ):
                # Find any event this prediction is relevant to
                # (domain match but not matched above = FP)
                domain_matches = [
                    e for e in known_events if e.domain == pred.domain
                ]
                if not domain_matches:
                    # No events in this domain — this is a prediction
                    # without ground truth; classify as FP conservatively
                    matches.append(EventPredictionMatch(
                        event_id=f"unmatched_{pred.yoga_name}",
                        yoga_name=pred.yoga_name,
                        verdict=PredictionVerdict.FALSE_POSITIVE,
                        timing_status=TimingMatchStatus.PREDICTED_ONLY,
                        timing_overlap_ratio=0.0,
                        confidence=pred.confidence,
                    ))

        return matches

    def _compute_timing_overlap(
        self,
        timing_windows: tuple[TimingWindow, ...],
        event: KnownEvent,
    ) -> tuple[TimingMatchStatus, float]:
        """Compute temporal overlap between predicted windows and event window.

        Returns:
            Tuple of (TimingMatchStatus, overlap_ratio).
        """
        if not timing_windows:
            return TimingMatchStatus.NO_OVERLAP, 0.0

        event_start = event.event_window_start_utc or event.event_date_utc
        event_end = event.event_window_end_utc or event.event_date_utc

        if not event_start or not event_end:
            return TimingMatchStatus.NO_OVERLAP, 0.0

        best_status = TimingMatchStatus.NO_OVERLAP
        best_ratio = 0.0

        for window in timing_windows:
            pred_start = window.window_start_utc
            pred_end = window.window_end_utc

            if not pred_start or not pred_end:
                continue

            # Use windows_overlap from temporal models
            if windows_overlap(pred_start, pred_end, event_start, event_end):
                # Compute overlap ratio
                from jrs.temporal.models import (
                    compute_overlap_window,
                    parse_iso_timestamp,
                )

                overlap_start, overlap_end = compute_overlap_window(
                    pred_start, pred_end, event_start, event_end,
                )

                if overlap_start and overlap_end:
                    pred_dt_start = parse_iso_timestamp(pred_start)
                    pred_dt_end = parse_iso_timestamp(pred_end)
                    evt_dt_start = parse_iso_timestamp(event_start)
                    evt_dt_end = parse_iso_timestamp(event_end)

                    if (
                        pred_dt_start is not None
                        and pred_dt_end is not None
                        and evt_dt_start is not None
                        and evt_dt_end is not None
                    ):
                        pred_duration = (pred_dt_end - pred_dt_start).total_seconds()
                        evt_duration = (evt_dt_end - evt_dt_start).total_seconds()
                        ovl_dt_start = parse_iso_timestamp(overlap_start)
                        ovl_dt_end = parse_iso_timestamp(overlap_end)

                        if ovl_dt_start is not None and ovl_dt_end is not None:
                            ovl_duration = (
                                ovl_dt_end - ovl_dt_start
                            ).total_seconds()
                            min_duration = min(pred_duration, evt_duration)
                            ratio = (
                                ovl_duration / min_duration
                                if min_duration > 0
                                else 0.0
                            )

                            if ratio >= 0.9:
                                best_status = TimingMatchStatus.OVERLAP
                            elif ratio > 0.0:
                                best_status = TimingMatchStatus.PARTIAL_OVERLAP
                            best_ratio = max(best_ratio, ratio)
            else:
                # No overlap with this window
                pass

        return best_status, best_ratio


# -- JRS-088: Blind Validation Runner Engine ---------------------------------


class BlindValidationRunner:
    """Isolated blind validation runner with cryptographic sealing.

    Enforces strict two-stage execution:
    1. Stage 1 (Prediction): Generate prediction, seal with SHA-256, persist.
    2. Stage 2 (Verification): Load from disk, verify hash, score against event.

    This ensures no in-process state sharing between the prediction engine
    and ground-truth event data.

    Usage::

        runner = BlindValidationRunner()
        metric = runner.run_blind_evaluation(
            subject=chart_subject,
            target_timestamp=target_dt,
            ground_truth_event=event,
            output_dir=Path("./output"),
        )
    """

    def __init__(
        self,
        pipeline_service: Any = None,
        packet_store: Any = None,
        protocol: Any = None,
    ) -> None:
        """Initialize with injectable dependencies.

        Args:
            pipeline_service: YogaEvaluatorService for prediction generation.
            packet_store: PredictionPacketStore for persistence.
            protocol: BlindValidationProtocol for sealing and scoring.
        """
        self._pipeline_service = pipeline_service
        self._packet_store = packet_store
        self._protocol = protocol

    def _ensure_dependencies(self) -> None:
        """Lazy-initialize dependencies if not injected."""
        if self._pipeline_service is None:
            self._pipeline_service = YogaEvaluatorService()
        if self._packet_store is None:
            from .storage import PredictionPacketStore
            self._packet_store = PredictionPacketStore()
        if self._protocol is None:
            from .protocol import BlindValidationProtocol
            self._protocol = BlindValidationProtocol(self._pipeline_service)

    def run_blind_evaluation(
        self,
        subject: ChartSubject,
        target_timestamp: str,
        ground_truth_event: HistoricalEvent,
        output_dir: Path,
    ) -> MetricEvaluation:
        """Execute a fully isolated blind evaluation.

        Stage 1: Generate prediction from subject only, seal with SHA-256,
            persist to disk, then clear prediction context.
        Stage 2: Load and verify packet from disk, score against event.

        Args:
            subject: Birth chart subject (no event data).
            target_timestamp: ISO 8601 evaluation timestamp.
            ground_truth_event: Independent ground-truth event.
            output_dir: Directory for packet persistence.

        Returns:
            MetricEvaluation with scoring results.

        Raises:
            CryptographicTamperError: If packet integrity check fails.
        """
        self._ensure_dependencies()

        # -- Stage 1: Prediction Generation & Sealing --
        packet = self._protocol.generate_prediction_packet(
            subject, target_timestamp,
        )

        # Persist sealed packet to disk
        packet_path = output_dir / f"{subject.chart_id}_packet.json"
        try:
            self._packet_store.save_packet(packet, packet_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to persist prediction packet: {exc}"
            ) from exc

        # Clear prediction context (simulate process isolation)
        del packet

        # -- Stage 2: Verification & Scoring --
        verified_packet = self._packet_store.load_and_verify(packet_path)

        metric = self._protocol.evaluate_prediction_against_event(
            verified_packet, ground_truth_event,
        )

        return metric

    def run_batch_evaluation(
        self,
        evaluation_pairs: list[
            tuple[ChartSubject, str, HistoricalEvent]
        ],
        output_dir: Path,
    ) -> BatchValidationReport:
        """Execute isolated evaluations across multiple charts.

        Each evaluation is independently sealed and verified. Failures
        in one chart do not affect others.

        Args:
            evaluation_pairs: List of (subject, target_timestamp, event) tuples.
            output_dir: Directory for packet persistence.

        Returns:
            BatchValidationReport with per-chart results.
        """
        self._ensure_dependencies()

        reports: list[SingleValidationReport] = []
        successes = 0
        failures = 0

        for subject, target_ts, event in evaluation_pairs:
            try:
                metric = self.run_blind_evaluation(
                    subject, target_ts, event, output_dir,
                )
                reports.append(SingleValidationReport(
                    chart_id=subject.chart_id,
                    status=ValidationStatus.SUCCESS,
                    metric_evaluation=metric,
                ))
                successes += 1
            except CryptographicTamperError as exc:
                reports.append(SingleValidationReport(
                    chart_id=subject.chart_id,
                    status=ValidationStatus.TAMPERED,
                    error_message=str(exc),
                ))
                failures += 1
            except Exception as exc:
                reports.append(SingleValidationReport(
                    chart_id=subject.chart_id,
                    status=ValidationStatus.PERSISTENCE_FAILED,
                    error_message=str(exc),
                ))
                failures += 1

        return BatchValidationReport(
            total_charts=len(evaluation_pairs),
            successful_evaluations=successes,
            failed_evaluations=failures,
            reports=tuple(reports),
        )
