"""JRE API — Pydantic schemas for request/response validation.

Strict typing for all API inputs and outputs. No engine logic here.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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


class EvaluationResponse(BaseModel):
    """Response from yoga evaluation endpoint."""

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


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="1.0.0", description="API version")
