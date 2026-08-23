"""JRS Cross-Domain Event Reasoning Engine — deterministic fact clustering.

Outputs EventCluster facts (NOT final predictions or interpretations).
Ingests DomainAssessment objects paired with temporal windows and
identifies intersections where multiple domains show timing convergence
in overlapping windows.

Public API
----------
- ``CrossDomainService``          – cluster identification from assessments
- ``EventCluster``                – a deterministic cross-domain cluster
- ``CrossDomainEventType``        – high-level event type classification
- ``TemporalWindow``              – bounded time interval
- ``CrossDomainAssessment``       – DomainAssessment + temporal window
"""

from __future__ import annotations

from .errors import (
    ClusterComputationError,
    CrossDomainError,
    InvalidClusterInputError,
)
from .models import (
    CrossDomainAssessment,
    CrossDomainEventType,
    EventCluster,
    TemporalWindow,
    classify_event_type,
)
from .service import CrossDomainService

__all__: tuple[str, ...] = (
    # Errors
    "CrossDomainError",
    "InvalidClusterInputError",
    "ClusterComputationError",
    # Enums
    "CrossDomainEventType",
    # Models
    "TemporalWindow",
    "CrossDomainAssessment",
    "EventCluster",
    "classify_event_type",
    # Service
    "CrossDomainService",
)
