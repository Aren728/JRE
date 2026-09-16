"""
src/jrs/api/routes/event_evaluator.py

FastAPI endpoint exposing Tier 2 Event Context Filtering for JRE/JRS v1.0.0.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from jrs.deterministic_engine.esoteric_evaluator import evaluate_and_deduplicate_chart
from jrs.deterministic_engine.event_context_filter import evaluate_event_context

router = APIRouter(prefix="/api/v1/events", tags=["Event Evaluator"])


# --- Request/Response Models ---

class EventContextInput(BaseModel):
    event_date: str = Field(
        ...,
        description="ISO event date (YYYY-MM-DD)",
        json_schema_extra={"example": "2024-01-15"},
    )
    dasha_lord: str = Field(
        ...,
        description="Active Maha Dasha ruling planet",
        json_schema_extra={"example": "Saturn"},
    )
    bhukti_lord: str = Field(
        ...,
        description="Active Antar Dasha / Bhukti ruling planet",
        json_schema_extra={"example": "Jupiter"},
    )
    pratyantardasha_lord: Optional[str] = Field(
        None,
        description="Optional Pratyantardasha lord",
        json_schema_extra={"example": "Venus"},
    )


class EvaluateEventRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(
        ...,
        description="Raw planetary/chart data dictionary for Tier 1 evaluation",
    )
    event_context: EventContextInput = Field(
        ...,
        description="Temporal parameters for the target evaluation date",
    )


class EvaluateEventResponse(BaseModel):
    tier1_total_tokens: int
    tier2_filtered_tokens_count: int
    suppressed_tokens_count: int
    active_dasha_rulers: List[str]
    event_tokens: List[str]
    filtered_composite_detections: List[Dict[str, Any]]


# --- Endpoint Route ---


@router.post(
    "/evaluate",
    response_model=EvaluateEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate event context against birth chart",
    description="Executes Tier 1 chart evaluation and applies Tier 2 Dasha-gated context filtering.",
)
async def evaluate_event_context_endpoint(
    payload: EvaluateEventRequest,
) -> Dict[str, Any]:
    try:
        # Step 1: Run Tier 1 Evaluation and Deduplication
        tier1_output = evaluate_and_deduplicate_chart(payload.chart_data)

        # Step 2: Apply Tier 2 Event Context Filter
        tier2_result = evaluate_event_context(
            tier1_output=tier1_output,
            event_context_data=payload.event_context.model_dump(),
        )

        return tier2_result

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event evaluation failed: {str(err)}",
        )
