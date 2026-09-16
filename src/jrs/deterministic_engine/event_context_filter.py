"""
src/jrs/deterministic_engine/event_context_filter.py

Tier 2 Event Context Filtering Layer for JRE/JRS Engine.
Filters Tier 1 Composite Detection Tokens based on temporal Scope and
Dasha/Bhukti planetary period activations.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from jrs.deterministic_engine.esoteric_evaluator import (
    CompositeYogaDetection,
    RuleScope,
)


@dataclass
class EventContext:
    """Represents the temporal and planetary parameters for a specific event date."""

    event_date: str  # ISO format: YYYY-MM-DD
    dasha_lord: str  # Maha Dasha ruling planet
    bhukti_lord: str  # Antar Dasha / Bhukti ruling planet
    pratyantardasha_lord: Optional[str] = None
    active_transits: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def active_rulers(self) -> Set[str]:
        """Returns normalized set of all active temporal ruling planets."""
        rulers = {self.dasha_lord.strip().title(), self.bhukti_lord.strip().title()}
        if self.pratyantardasha_lord:
            rulers.add(self.pratyantardasha_lord.strip().title())
        return rulers


class EventContextFilter:
    """
    Tier 2 Contextual Filter.
    Takes Tier 1 composite detections and filters/ranks them for event-focused evaluation.
    """

    def __init__(self, require_dasha_activation_for_natal: bool = True):
        self.require_dasha_activation_for_natal = require_dasha_activation_for_natal

    def filter_detections(
        self,
        composite_detections: List[CompositeYogaDetection],
        context: EventContext,
    ) -> List[CompositeYogaDetection]:
        """
        Evaluates Tier 1 composite detections against event temporal parameters.

        Filtering Rules:
        1. DASHA_BOUND / TRANSIT_BOUND: Passed through directly as active temporal triggers.
        2. NATAL_PERMANENT: Passed ONLY if at least one participating planet matches
           the current Dasha, Bhukti, or Pratyantardasha ruling lords.
        """
        active_rulers = context.active_rulers
        filtered: List[CompositeYogaDetection] = []

        for detection in composite_detections:
            if detection.scope in (RuleScope.DASHA_BOUND, RuleScope.TRANSIT_BOUND):
                # Always retain time-bound event triggers
                filtered.append(detection)
                continue

            if detection.scope == RuleScope.NATAL_PERMANENT:
                if not self.require_dasha_activation_for_natal:
                    filtered.append(detection)
                    continue

                # Check if any participating planet in the natal yoga matches active dasha lords
                participating_normalized = {
                    p.strip().title() for p in detection.participating_planets if p
                }

                # Match against active period rulers
                if participating_normalized.intersection(active_rulers):
                    filtered.append(detection)

        return filtered


def evaluate_event_context(
    tier1_output: Dict[str, Any],
    event_context_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pipeline entry point for executing Tier 2 filtering on Tier 1 results.
    """

    # 1. Parse raw composite detections back into objects
    raw_composites = tier1_output.get("composite_detections", [])
    composite_objects: List[CompositeYogaDetection] = []

    for item in raw_composites:
        scope_enum = RuleScope(item.get("scope", RuleScope.NATAL_PERMANENT.value))
        obj = CompositeYogaDetection(
            yoga_type=item["yoga_type"],
            canonical_token=item["canonical_token"],
            scope=scope_enum,
            occurrence_count=item["occurrence_count"],
            composite_impact_score=item["impact_score"],
            participating_planets=item.get("participating_planets", []),
            participating_houses=item.get("participating_houses", []),
            dasha_contexts=item.get("dasha_contexts", []),
            instance_metadata=item.get("instance_metadata", []),
        )
        composite_objects.append(obj)

    # 2. Build EventContext
    context = EventContext(
        event_date=event_context_data.get("event_date", ""),
        dasha_lord=event_context_data.get("dasha_lord", ""),
        bhukti_lord=event_context_data.get("bhukti_lord", ""),
        pratyantardasha_lord=event_context_data.get("pratyantardasha_lord"),
    )

    # 3. Apply Tier 2 Filter
    filter_engine = EventContextFilter()
    filtered_objects = filter_engine.filter_detections(composite_objects, context)

    filtered_tokens = [cd.canonical_token for cd in filtered_objects]

    return {
        "tier1_total_tokens": len(composite_objects),
        "tier2_filtered_tokens_count": len(filtered_objects),
        "suppressed_tokens_count": len(composite_objects) - len(filtered_objects),
        "active_dasha_rulers": list(context.active_rulers),
        "event_tokens": filtered_tokens,
        "filtered_composite_detections": [cd.to_dict() for cd in filtered_objects],
    }
