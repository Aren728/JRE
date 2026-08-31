"""JRE API — Pydantic schemas for request/response validation.

Strict typing for all API inputs and outputs. No engine logic here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Constants ───────────────────────────────────────────────────────────────

ENGINE_VERSION = "v1.0.0-beta"

LEGAL_DISCLAIMER = (
    "DISCLAIMER: This output is a computational interpretation based on "
    "classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided "
    "for informational and research purposes only. It does not constitute "
    "medical, financial, legal, or guaranteed predictive advice."
)


# ── Request Schemas ─────────────────────────────────────────────────────────

class BirthDataInput(BaseModel):
    """Birth data for custom chart evaluation."""

    date: str = Field(
        ...,
        description="Birth date in ISO format (YYYY-MM-DD)",
        examples=["1990-01-15"],
    )
    time: str = Field(
        ...,
        description="Birth time in ISO format (HH:MM:SS)",
        examples=["14:30:00"],
    )
    latitude: float = Field(
        ...,
        description="Birth latitude in decimal degrees",
        ge=-90.0,
        le=90.0,
        examples=[40.7128],
    )
    longitude: float = Field(
        ...,
        description="Birth longitude in decimal degrees",
        ge=-180.0,
        le=180.0,
        examples=[-74.0060],
    )
    timezone: str = Field(
        ...,
        description="IANA timezone string",
        examples=["America/New_York"],
    )
    ayanamsa: str = Field(
        default="LAHIRI",
        description="Ayanamsa method",
        examples=["LAHIRI"],
    )


class FixtureInput(BaseModel):
    """Request to evaluate a pre-computed chart fixture."""

    fixture_id: str = Field(
        ...,
        description="Fixture filename without .json extension",
        examples=["chart_001_pilot"],
    )


# ── Response Schemas ────────────────────────────────────────────────────────

class YogaProvenance(BaseModel):
    """Provenance and explainability data for a yoga evaluation."""

    formation_evidence: str = Field(
        default="",
        description="Classical rule that triggered this yoga",
    )
    chain_evidence: float | None = Field(
        default=None,
        description="Net chain impact score from dispositorship analysis",
    )
    temporal_evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Dasha and transit details (MD/AD/PD, transit multiplier)",
    )
    varga_evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="D9/D10 confirmation status",
    )


class YogaResult(BaseModel):
    """Single yoga evaluation result."""

    yoga_name: str = Field(..., description="Name of the detected yoga")
    category: str = Field(
        default="",
        description="Yoga category (e.g., RAJA, DHANA, PANCHAMAHAPURUSHA)",
    )
    status: str = Field(
        ...,
        description="Yoga status: FORMED, WEAKENED, or CANCELLED",
    )
    static_strength: float = Field(
        default=0.0,
        description="Static strength score after modifier pipeline",
    )
    dynamic_strength: float | None = Field(
        default=None,
        description="Dynamic strength after temporal evaluation",
    )
    domains: list[str] = Field(
        default_factory=list,
        description="Outcome domains this yoga influences",
    )
    involved_planets: list[str] = Field(
        default_factory=list,
        description="Planets involved in this yoga",
    )
    cancellation_reason: str | None = Field(
        default=None,
        description="Reason for cancellation (if status is CANCELLED)",
    )
    chain_impact: float | None = Field(
        default=None,
        description="Chain impact score from dispositorship analysis",
    )
    dasha_multiplier: float | None = Field(
        default=None,
        description="Dasha multiplier for temporal activation",
    )
    transit_multiplier: float | None = Field(
        default=None,
        description="Transit Ashtakavarga multiplier",
    )
    provenance: YogaProvenance = Field(
        default_factory=YogaProvenance,
        description="Provenance and explainability data",
    )


class EvaluationResponse(BaseModel):
    """Response from yoga evaluation endpoint."""

    evaluation_id: str = Field(
        default="",
        description=(
            "Deterministic SHA-256 evaluation identifier for reproducibility. "
            "Hash of fixture_id + engine_version."
        ),
    )
    subject: str = Field(
        default="Custom",
        description="Subject name or identifier",
    )
    lagna: str = Field(
        ...,
        description="Lagna (ascendant) rashi",
    )
    moon_nakshatra: str = Field(
        default="",
        description="Moon's nakshatra",
    )
    yogas: list[YogaResult] = Field(
        default_factory=list,
        description="List of detected yogas",
    )
    yoga_count: int = Field(
        default=0,
        description="Total number of yogas detected",
    )
    formed_count: int = Field(
        default=0,
        description="Number of formed yogas",
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Processing time in milliseconds",
    )
    engine_version: str = Field(
        default=ENGINE_VERSION,
        description="Engine version used for this evaluation",
    )
    disclaimer: str = Field(
        default=LEGAL_DISCLAIMER,
        description="Legal and computational disclaimer",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="1.0.0", description="API version")


# ── Feedback Schema ─────────────────────────────────────────────────────────

class FeedbackEntry(BaseModel):
    """Structured feedback from beta testers.

    Strictly typed to enable systematic analysis of expert feedback
    across multiple dimensions (agreement, error types, domain).
    """

    evaluation_id: str = Field(
        ...,
        description="Tied to the specific evaluation manifest",
    )
    expert_id: str = Field(
        ...,
        description="Anonymized expert identifier (e.g., 'EXPERT_A')",
    )
    domain: str = Field(
        ...,
        description="Event domain (e.g., 'CAREER', 'HEALTH', 'MARRIAGE')",
    )

    # Structured Taxonomy (boolean flags)
    expert_agreement: bool = Field(
        default=False,
        description="Expert agrees with the engine's overall assessment",
    )
    expert_disagreement: bool = Field(
        default=False,
        description="Expert disagrees with the engine's overall assessment",
    )
    missing_yoga: bool = Field(
        default=False,
        description="A classical yoga should have been detected but wasn't",
    )
    false_positive: bool = Field(
        default=False,
        description="Engine detected a yoga that shouldn't exist or is irrelevant",
    )
    false_negative: bool = Field(
        default=False,
        description="Engine missed a yoga that should have been activated",
    )
    timing_issue: bool = Field(
        default=False,
        description="Dasha activation timing is incorrect for this event",
    )
    interpretation_issue: bool = Field(
        default=False,
        description="Classical interpretation of the yoga is incorrect",
    )
    astronomical_issue: bool = Field(
        default=False,
        description="Underlying astronomical calculation is wrong (positions, Dasha)",
    )
    other: bool = Field(
        default=False,
        description="Other issue not covered by the above categories",
    )

    free_text: str = Field(
        default="",
        description="Optional detailed notes or explanation",
    )
