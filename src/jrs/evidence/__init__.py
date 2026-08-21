"""JRS Evidence Graph — Classical Evidence & Domain Framework.

Public API
----------
- ``EvidenceService``        – registry and chain resolver
- ``ClassicalSource``        – classical text authority
- ``EvidenceRecord``         – a single piece of evidence
- ``RuleCatalogEntry``       – a rule in the classical catalog
- ``EvidenceChain``          – resolved evidence chain
- ``EvidenceConfig``         – framework configuration
- ``load_evidence_config``   – TOML config loader
"""

from __future__ import annotations

from .config import load_evidence_config
from .errors import (
    CircularReferenceError,
    DuplicateEvidenceError,
    EvidenceError,
    EvidenceNotFoundError,
    InvalidEvidenceConfigError,
    InvalidEvidenceRecordError,
)
from .models import (
    STRENGTH_VALUES,
    ClassicalSource,
    EvidenceChain,
    EvidenceConfig,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
    RuleCatalogEntry,
    detect_circular_references,
    resolve_evidence_chain,
)
from .serialize import (
    classical_source_from_dict,
    evidence_chain_from_dict,
    evidence_config_from_dict,
    evidence_record_from_dict,
    record_to_json,
    result_to_dict,
    result_to_json,
    rule_catalog_entry_from_dict,
)
from .service import EvidenceService

__all__: tuple[str, ...] = (
    # Errors
    "EvidenceError",
    "InvalidEvidenceConfigError",
    "InvalidEvidenceRecordError",
    "CircularReferenceError",
    "EvidenceNotFoundError",
    "DuplicateEvidenceError",
    # Enums
    "EvidenceDirection",
    "EvidenceStrength",
    "STRENGTH_VALUES",
    # Models
    "ClassicalSource",
    "EvidenceRecord",
    "RuleCatalogEntry",
    "EvidenceChain",
    "EvidenceConfig",
    "detect_circular_references",
    "resolve_evidence_chain",
    # Config
    "load_evidence_config",
    # Serialize
    "classical_source_from_dict",
    "evidence_record_from_dict",
    "rule_catalog_entry_from_dict",
    "evidence_chain_from_dict",
    "evidence_config_from_dict",
    "result_to_dict",
    "result_to_json",
    "record_to_json",
    # Service
    "EvidenceService",
)
