"""JRE-009 Research Worker — lightweight, deterministic research engine.

JRE-009 ingests a research task, searches local text/markdown sources for
evidence, records provenance, and outputs a structured JSON report. It fits
the existing JRE agent orchestration without autonomous loops or external
dependencies.

Strict Boundaries:
- IN SCOPE: src/research/, agents/research/, tests/unit/research/,
  tests/integration/research/.
- OUT OF SCOPE: No web scraping, no LLM APIs, no network calls, no
  autonomous loops. Do not modify merged modules (JRE-002 to JRE-008).

Core Models:
- ``ResearchTask``: task_id, query, target_concepts, source_directories, status
- ``Evidence``: evidence_id, task_id, source_file, excerpt, line_number, context, confidence
- ``ResearchReport``: task_id, query, status, evidence, summary, generated_at

Service Interface:
- ``ResearchWorker(config: ResearchConfig)``
- ``execute_task(task: ResearchTask) -> ResearchReport``
"""

from .config import load_config, validate
from .errors import (
    InvalidResearchConfigError,
    InvalidResearchRequestError,
    ResearchComputationError,
    ResearchError,
)
from .models import (
    RESEARCH_CATALOG_VERSION,
    RESEARCH_VERSION,
    Evidence,
    ResearchConfig,
    ResearchReport,
    ResearchTask,
    TaskStatus,
    compute_deterministic_id,
)
from .serialize import (
    SCHEMAS,
    research_config_from_dict,
    research_task_from_dict,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from .service import ResearchWorker

__version__ = RESEARCH_VERSION

__all__ = [
    # service
    "ResearchWorker",
    # config
    "load_config",
    "validate",
    "ResearchConfig",
    # models
    "ResearchTask",
    "Evidence",
    "ResearchReport",
    "TaskStatus",
    # registry / catalog
    "RESEARCH_VERSION",
    "RESEARCH_CATALOG_VERSION",
    # identity / hashing
    "compute_deterministic_id",
    # errors
    "ResearchError",
    "InvalidResearchConfigError",
    "InvalidResearchRequestError",
    "ResearchComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "research_config_from_dict",
    "research_task_from_dict",
    "schema_for",
    "validate_schema",
    "SCHEMAS",
]
