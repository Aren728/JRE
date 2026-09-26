"""JRE API — Pydantic schemas for request/response validation.

Strict typing for all API inputs and outputs. No engine logic here.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ── Constants ───────────────────────────────────────────────────────────────

ENGINE_VERSION = "v1.0.0"

LEGAL_DISCLAIMER = (
    "DISCLAIMER: This output is a computational interpretation based on "
    "classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided "
    "for informational and research purposes only. It does not constitute "
    "medical, financial, legal, or guaranteed predictive advice."
)


# ── Request Schemas ─────────────────────────────────────────────────────────


class BirthDataInput(BaseModel):
    """Birth data for custom chart evaluation.

    Phase 6 strict DTO contract: unknown fields are rejected (422) and
    extra values never silently enter the engine pipeline.
    """

    model_config = ConfigDict(extra="forbid")

    date: str = Field(
        ...,
        description="Birth date in ISO format (YYYY-MM-DD)",
        examples=["1990-01-15"],
    )
    time: str = Field(
        default="",
        description=(
            "Birth time in ISO format (HH:MM:SS). "
            "If omitted, empty, or 'unknown', noon (12:00) is used as a "
            "computational default and Lagna-dependent yogas are suspended."
        ),
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
    ayanamsha: str | None = Field(
        default=None,
        description="Ayanamsha method for sidereal calculations. "
        "Supported: lahiri, raman, kp. If omitted, the backend uses its default (Lahiri).",
        examples=["lahiri"],
    )
    language: str = Field(
        default="en",
        description=(
            "Language code for narrative output. "
            "Supported: en, hi, ta, ml, te, kn, mr, bn, as, or, pa, gu. "
            "Astrological terms remain in English/Sanskrit transliteration."
        ),
        examples=["en"],
    )


class FixtureInput(BaseModel):
    """Request to evaluate a pre-computed chart fixture."""

    fixture_id: str = Field(
        ...,
        description="Fixture filename without .json extension",
        examples=["chart_001_pilot"],
    )
    language: str = Field(
        default="en",
        description="Language code for narrative output",
        examples=["en"],
    )


class PersonInput(BaseModel):
    """Person data for compatibility matching."""

    nakshatra: str = Field(
        ...,
        description="Nakshatra (birth star) name",
        examples=["Ashwini"],
    )
    name: str = Field(
        default="",
        description="Optional person name for display",
        examples=["Person A"],
    )


class CompatibilityInput(BaseModel):
    """Request for Ashta Koota compatibility matching."""

    person_a: PersonInput = Field(
        ...,
        description="First person's data",
    )
    person_b: PersonInput = Field(
        ...,
        description="Second person's data",
    )


class NumerologyInput(BaseModel):
    """Request for numerology calculation."""

    birth_date: str = Field(
        ...,
        description="Birth date in ISO format (YYYY-MM-DD)",
        examples=["1990-05-15"],
    )
    full_name: str = Field(
        ...,
        description="Full name including first, middle, and last names",
        examples=["John Michael Smith"],
    )


class ChartRequest(BaseModel):
    """Input model for chart calculation and persistence (Phase 6 strict DTO)."""

    query_date: _date = Field(
        ...,
        description="Date to calculate the chart for (YYYY-MM-DD)",
        examples=["1990-01-15"],
    )
    query_time: str = Field(
        ...,
        description="Time to calculate the chart for (HH:MM:SS)",
        examples=["14:30:00"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees",
    )
    timezone: str = Field(
        ...,
        description="IANA timezone string",
        examples=["Asia/Kolkata"],
    )


# ── Response Schemas ────────────────────────────────────────────────────────


class EvidenceGraphNode(BaseModel):
    """One node of the evidence DAG (Phase 7 Observatory contract)."""

    node_id: str = Field(..., description="Stable node id (EV-/R-/F-/FD-…)")
    node_type: str = Field(
        ...,
        description=(
            "Node layer: EVALUATION, RULE, FACT, CITATION, TEMPORAL, or ANALYSIS"
        ),
    )
    labels: list[str] = Field(
        default_factory=list,
        description="Classification labels (e.g. FACT, VARGA, DASHA_TRANSIT)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Node payload (rule ids, fact ids, dignities, citations…)",
    )
    parent: str | None = Field(
        default=None,
        description="Parent node id when the node is a child in the DAG",
    )


class EvidenceGraphEdge(BaseModel):
    """One directed edge of the evidence DAG (Phase 7 Observatory contract)."""

    edge_id: str = Field(..., description="Stable edge id")
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    relationship: str = Field(
        ...,
        description=(
            "Relation type: ESTABLISHED_BY, DERIVES_FROM, SUPPORTS, AFFECTS, "
            "REL-GOCHARA-*, REL-VARGA-*, REL-DASHA-TRANSIT-*"
        ),
    )
    weight: float = Field(default=1.0, description="Edge weight")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Edge metadata (bands, dignities, decisions…)",
    )


class EvidenceGraphResponse(BaseModel):
    """Full evidence DAG for one chart (Phase 7 Observatory contract).

    The same deterministic graph the golden-state ``evidence_graph``
    stage hashes — what the Observatory renders is exactly what the
    regression gate verifies.
    """

    graph_id: str = Field(..., description="Deterministic graph identifier")
    fixture_id: str = Field(..., description="Fixture the graph was built from")
    node_count: int = Field(..., description="Total node count")
    edge_count: int = Field(..., description="Total edge count")
    nodes: list[EvidenceGraphNode] = Field(
        default_factory=list,
        description="All DAG nodes",
    )
    edges: list[EvidenceGraphEdge] = Field(
        default_factory=list,
        description="All directed DAG edges",
    )
    engine_version: str = Field(
        default=ENGINE_VERSION,
        description="Engine version used to build the graph",
    )


class LineageLayer(BaseModel):
    """One backward-chain layer of a prediction lineage (Phase 9D)."""

    available: bool = Field(
        ...,
        description="Whether the layer's supporting report/state was present",
    )
    reason: str | None = Field(
        default=None,
        description="Why the layer is unavailable (with enabling flag hint)",
    )
    summary: str = Field(..., description="One-line human summary of the layer")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Canonical detail payload (facts, decisions, raw floats)",
    )


class LineageResponse(BaseModel):
    """Full prediction lineage (Phase 9D Observatory contract).

    Ordered chain: PREDICTION → RULE → DASHA_GATE → TRANSIT → VARGA →
    YOGA → SAV → NATAL_LONGITUDES.
    """

    prediction_id: str = Field(..., description="The P-... prediction id traced")
    graph_id: str | None = Field(
        default=None,
        description="Evidence-graph id the lineage was built from",
    )
    chain_order: list[str] = Field(
        ...,
        description="Ordered layer names, shallowest to deepest",
    )
    chain: dict[str, LineageLayer] = Field(
        ...,
        description="Per-layer availability, summary, and details",
    )
    engine_version: str = Field(
        default=ENGINE_VERSION,
        description="Engine version used to build the lineage",
    )


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
    evidence_graph: dict[str, Any] = Field(
        default_factory=dict,
        description="Phase 3 evidence graph (provenance DAG) for this yoga: evaluation node, rule node, planetary state fact nodes, and temporal (dasha/transit) node with all directed edges.",
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
    dasha_activation: dict[str, Any] | None = Field(
        default=None,
        description="Dasha activation periods for this yoga (past, present, future)",
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
    language: str = Field(
        default="en",
        description="Language code used for narrative output",
    )
    disclaimer: str = Field(
        default=LEGAL_DISCLAIMER,
        description="Legal and computational disclaimer",
    )
    # ── Enrichment data (Phase I6) ─────────────────────────────────────────
    elemental_balance: dict[str, int] = Field(
        default_factory=dict,
        description="Count of planets in fire/earth/air/water elements",
    )
    modality_balance: dict[str, int] = Field(
        default_factory=dict,
        description="Count of planets in cardinal/fixed/mutable modalities",
    )
    dignity_map: dict[str, str] = Field(
        default_factory=dict,
        description="Planet → dignity label (Exalted, Own Sign, Friendly, etc.)",
    )
    aspect_matrix: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected Vedic aspects between planets",
    )
    planet_details: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-planet details: sign, element, modality, dignity, degree_in_sign",
    )
    birth_data_display: dict[str, str] = Field(
        default_factory=dict,
        description="Formatted birth data for report display",
    )
    lagna_longitude: float = Field(
        default=-1.0,
        description=(
            "Exact sidereal ascendant longitude in degrees (0-360). Enables "
            "exact D10/D9 lagna computations client-side. -1.0 means unavailable."
        ),
    )
    navamsha_lagna: str = Field(
        default="",
        description=(
            "Exact Navamsha (D9) lagna sign key (e.g. 'MESHA'), derived from the "
            "ascendant longitude. Empty string means unavailable."
        ),
    )
    arudha_padas: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Full Arudha Pada ladder A1–A12, keyed 'A1'..'A12' with sign keys "
            "(e.g. 'KARKA'). Computed classically from each house's sign lord: "
            "count from house to lord, then the same count onward; if the pada "
            "lands in the house itself or the 7th from it, take the 10th from "
            "the lord. A12 is the Upapada Lagna. Empty string for a pada means "
            "the lord's body was unavailable in the ephemeris."
        ),
    )

    # ── Unknown TOB fields ──────────────────────────────────────────────────
    lagna_confidence: str = Field(
        default="HIGH",
        description=(
            "Confidence level for the computed Lagna. "
            "'HIGH' when birth time is known, 'LOW' when time is approximate, "
            "'UNKNOWN' when birth time is missing and noon default was used."
        ),
    )
    unknown_tob: bool = Field(
        default=False,
        description=(
            "True when the birth time was missing, empty, or marked unknown. "
            "Noon (12:00) was used as a computational default. Lagna-dependent "
            "yogas have been suspended."
        ),
    )
    skipped_yogas: list[str] = Field(
        default_factory=list,
        description=(
            "Names of lagna-dependent yogas that were skipped because the birth time is unknown."
        ),
    )

    # ── Phase 2: Prediction Engine Data ────────────────────────────────────
    remedies: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Classical remedial measures from the Parihara engine "
            "(afflicted planets, detected doshas, general remedies). "
            "Empty dict when the engine is unavailable."
        ),
    )
    parivartana_yogas: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detected Parivartana (mutual exchange) Yogas",
    )
    parivartana_synthesis: dict[str, str] = Field(
        default_factory=dict,
        description="4-part Parivartana synthesis: rasi_analysis, nakshatra_analysis, inter_aspect_modifications, final_synthesis",
    )
    deep_dasha: dict[str, Any] = Field(
        default_factory=dict,
        description="Deep Vimshottari Dasha hierarchy (MD/AD/PD/SD)",
    )
    aspect_matrix_full: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Full Vedic aspect matrix with special aspects and orb",
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


# ── Varga & Analysis Schemas ────────────────────────────────────────────────


class VargaPosition(BaseModel):
    """Position in a divisional chart (varga).

    Used to report the same planet across multiple vargas
    (e.g. D1, D3, D9, D10, D60) in a uniform shape.
    """

    sign: str = Field(
        ...,
        description="Zodiac sign name, e.g., Kanya, Tula",
    )
    house: int = Field(
        ...,
        ge=1,
        le=12,
        description="House placement 1-12",
    )
    degree: float = Field(
        ...,
        ge=0.0,
        lt=30.0,
        description="Longitude within sign in degrees",
    )
    nakshatra: str = Field(
        ...,
        description="Nakshatra name, e.g., Vishakha, Hasta",
    )
    pada: int = Field(
        ...,
        ge=1,
        le=4,
        description="Nakshatra quarter 1-4",
    )


class PlanetAnalysis(BaseModel):
    """Per-planet varga and strength analysis.

    Combines D1/D3/D9/D10/D60 placements with shadbala and functional role.
    """

    planet_name: str = Field(
        ...,
        description="Name of the celestial body",
    )
    d1: VargaPosition
    d3: VargaPosition | None = None
    d9: VargaPosition
    d10: VargaPosition | None = None
    d60: VargaPosition | None = None
    shadbala_score: float | None = Field(
        None,
        description=(
            "Shadbala value expressed in Rupas or total strength ratio"
        ),
    )
    functional_role: str = Field(
        ...,
        description=(
            "Functional nature (e.g., Yogakaraka, Functional Benefic, Maraka)"
        ),
    )


class CoreAlignment(BaseModel):
    """Core chart alignment summary.

    Ascendant, Moon sign, and Moon nakshatra/pada plus a short
    psychological summary.
    """

    ascendant_sign: str
    moon_sign: str
    moon_nakshatra: str
    moon_pada: int
    psychological_summary: str


class DashaPeriod(BaseModel):
    """Active dasha period details.

    Supports Mahadasha, Antardasha, optional Pratyantardasha,
    and the period start/end dates.
    """

    mahadasha: str
    antardasha: str
    pratyantardasha: str | None = None
    start_date: str
    end_date: str


class JREAnalysisResponse(BaseModel):
    """Top-level response for a full JRE analysis.

    Combines core alignment, per-planet analysis, the active dasha
    period, and the complete generated Markdown blueprint report.
    """

    core_alignment: CoreAlignment
    planets: list[PlanetAnalysis]
    active_dasha: DashaPeriod
    synthesis_markdown: str = Field(
        ...,
        description="Complete generated Markdown blueprint report",
    )

