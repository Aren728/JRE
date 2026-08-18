"""JRE-009 Research Worker models (core data structures).

JRE-009 defines a lightweight, deterministic Research Worker that ingests
a research task, searches local text/markdown sources for evidence, records
provenance, and outputs a structured JSON report.

Core Models:
- ``ResearchTask``: task_id, query, target_concepts, source_directories, status
- ``Evidence``: evidence_id, task_id, source_file, excerpt, line_number, context, confidence
- ``ResearchReport``: task_id, query, status, evidence, summary, generated_at
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from .errors import InvalidResearchRequestError

#: Pinned package version (same policy as JRE-002/003/004/005/006/007/008).
RESEARCH_VERSION = "0.1.0"

#: Pinned catalog version.
RESEARCH_CATALOG_VERSION = "0.1.0"


@dataclass(frozen=True)
class ResearchConfig:
    """Immutable JRE-009 configuration. TOML is authoritative; every default
    is declared in ``config/research.toml`` (no hidden defaults).
    Programmatic construction is explicitly validated at construction.
    """

    catalog_version: str = RESEARCH_CATALOG_VERSION
    version: str = RESEARCH_VERSION
    default_source_dir: str = "data/research_sources/"
    default_output_dir: str = "data/research_reports/"
    supported_extensions: tuple[str, ...] = (".md", ".txt")

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchConfig:
        config = cls(
            catalog_version=_as_string(data.get("catalog_version"), "catalog_version"),
            version=_as_string(data.get("version"), "version"),
            default_source_dir=_as_string(data.get("default_source_dir"), "default_source_dir"),
            default_output_dir=_as_string(data.get("default_output_dir"), "default_output_dir"),
            supported_extensions=_as_tuple_of_strings(
                data.get("supported_extensions"), "supported_extensions"
            ),
        )
        return config


class TaskStatus(StrEnum):
    """The status of a research task (frozen V1 lifecycle)."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ResearchTask:
    """A research task to be executed by the ResearchWorker.

    ``task_id`` is a deterministic identifier for the task.
    ``query`` is the search query (human-readable description of what to find).
    ``target_concepts`` are the case-insensitive substring patterns to search for.
    ``source_directories`` are the directories to search for evidence.
    ``status`` tracks the task lifecycle.
    """

    task_id: str
    query: str
    target_concepts: tuple[str, ...]
    source_directories: tuple[str, ...]
    status: TaskStatus = TaskStatus.PENDING

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or self.task_id == "":
            raise InvalidResearchRequestError(
                f"task_id must be a non-empty string, got {self.task_id!r}"
            )
        if not isinstance(self.query, str) or self.query == "":
            raise InvalidResearchRequestError(
                f"query must be a non-empty string, got {self.query!r}"
            )
        if not isinstance(self.target_concepts, tuple) or not self.target_concepts:
            raise InvalidResearchRequestError(
                f"target_concepts must be a non-empty tuple, got {self.target_concepts!r}"
            )
        for concept in self.target_concepts:
            if not isinstance(concept, str) or concept == "":
                raise InvalidResearchRequestError(
                    f"target_concepts must contain non-empty strings, got {concept!r}"
                )
        if not isinstance(self.source_directories, tuple) or not self.source_directories:
            raise InvalidResearchRequestError(
                f"source_directories must be a non-empty tuple, got {self.source_directories!r}"
            )
        for directory in self.source_directories:
            if not isinstance(directory, str) or directory == "":
                raise InvalidResearchRequestError(
                    f"source_directories must contain non-empty strings, got {directory!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchTask:
        return cls(
            task_id=_as_string(data.get("task_id"), "task_id"),
            query=_as_string(data.get("query"), "query"),
            target_concepts=_as_tuple_of_strings(data.get("target_concepts"), "target_concepts"),
            source_directories=_as_tuple_of_strings(
                data.get("source_directories"), "source_directories"
            ),
            status=TaskStatus(_as_string(data.get("status", TaskStatus.PENDING.value), "status")),
        )


@dataclass(frozen=True)
class Evidence:
    """A single piece of evidence found during research.

    ``evidence_id`` is a deterministic identifier for this evidence.
    ``task_id`` references the parent task.
    ``source_file`` is the path to the file containing the evidence.
    ``excerpt`` is the matching line content.
    ``line_number`` is the 1-based line number of the match.
    ``context`` is the surrounding lines for additional context.
    ``confidence`` is a confidence score between 0.0 and 1.0.
    """

    evidence_id: str
    task_id: str
    source_file: str
    excerpt: str
    line_number: int
    context: str
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or self.evidence_id == "":
            raise InvalidResearchRequestError(
                f"evidence_id must be a non-empty string, got {self.evidence_id!r}"
            )
        if not isinstance(self.task_id, str) or self.task_id == "":
            raise InvalidResearchRequestError(
                f"task_id must be a non-empty string, got {self.task_id!r}"
            )
        if not isinstance(self.source_file, str) or self.source_file == "":
            raise InvalidResearchRequestError(
                f"source_file must be a non-empty string, got {self.source_file!r}"
            )
        if not isinstance(self.excerpt, str) or self.excerpt == "":
            raise InvalidResearchRequestError(
                f"excerpt must be a non-empty string, got {self.excerpt!r}"
            )
        if not isinstance(self.line_number, int) or self.line_number < 1:
            raise InvalidResearchRequestError(
                f"line_number must be a positive integer, got {self.line_number!r}"
            )
        if not isinstance(self.context, str):
            raise InvalidResearchRequestError(
                f"context must be a string, got {self.context!r}"
            )
        if not isinstance(self.confidence, (int, float)):
            raise InvalidResearchRequestError(
                f"confidence must be a number, got {self.confidence!r}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidResearchRequestError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Evidence:
        return cls(
            evidence_id=_as_string(data.get("evidence_id"), "evidence_id"),
            task_id=_as_string(data.get("task_id"), "task_id"),
            source_file=_as_string(data.get("source_file"), "source_file"),
            excerpt=_as_string(data.get("excerpt"), "excerpt"),
            line_number=_as_int(data.get("line_number"), "line_number"),
            context=_as_optional_string(data.get("context"), "context"),
            confidence=_as_float(data.get("confidence"), "confidence"),
        )


@dataclass(frozen=True)
class ResearchReport:
    """The structured JSON report output from a research task.

    ``task_id`` references the original task.
    ``query`` is the search query that was executed.
    ``status`` is the final status of the task.
    ``evidence`` is the tuple of Evidence objects found.
    ``summary`` is a human-readable summary of the findings.
    ``generated_at`` is the ISO-8601 UTC timestamp of report generation.
    """

    task_id: str
    query: str
    status: TaskStatus
    evidence: tuple[Evidence, ...]
    summary: str
    generated_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or self.task_id == "":
            raise InvalidResearchRequestError(
                f"task_id must be a non-empty string, got {self.task_id!r}"
            )
        if not isinstance(self.query, str) or self.query == "":
            raise InvalidResearchRequestError(
                f"query must be a non-empty string, got {self.query!r}"
            )
        if not isinstance(self.status, TaskStatus):
            raise InvalidResearchRequestError(
                f"status must be a TaskStatus, got {self.status!r}"
            )
        if not isinstance(self.evidence, tuple):
            raise InvalidResearchRequestError(
                f"evidence must be a tuple, got {self.evidence!r}"
            )
        for item in self.evidence:
            if not isinstance(item, Evidence):
                raise InvalidResearchRequestError(
                    f"evidence must contain Evidence objects, got {type(item).__name__}"
                )
        if not isinstance(self.summary, str):
            raise InvalidResearchRequestError(
                f"summary must be a string, got {self.summary!r}"
            )
        if not isinstance(self.generated_at, str) or self.generated_at == "":
            raise InvalidResearchRequestError(
                f"generated_at must be a non-empty string, got {self.generated_at!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchReport:
        evidence_raw = data.get("evidence", ())
        if not isinstance(evidence_raw, (list, tuple)):
            raise InvalidResearchRequestError(
                f"evidence must be a list or tuple, got {type(evidence_raw).__name__}"
            )
        evidence = tuple(Evidence.from_dict(item) for item in evidence_raw)
        return cls(
            task_id=_as_string(data.get("task_id"), "task_id"),
            query=_as_string(data.get("query"), "query"),
            status=TaskStatus(_as_string(data.get("status"), "status")),
            evidence=evidence,
            summary=_as_string(data.get("summary"), "summary"),
            generated_at=_as_string(data.get("generated_at"), "generated_at"),
        )


# --------------------------------------------------------------------------- #
# Deterministic Identity / Hashing
# --------------------------------------------------------------------------- #


def compute_deterministic_id(domain: str, data: Any) -> str:
    """Compute a deterministic SHA-256 hash for a domain and data payload."""
    serialized = json.dumps(
        _model_to_dict(data),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    hasher = hashlib.sha256()
    hasher.update(f"{domain}:".encode())
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> ``.value``; tuples -> lists; ``-0.0`` -> ``0.0``)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {key: _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        if model != model or model in (float("inf"), float("-inf")):
            raise ValueError("NaN and Infinity are not allowed in deterministic serialization")
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)


def _as_string(raw: Any, field: str) -> str:
    if raw is None:
        raise InvalidResearchRequestError(f"{field} must be a non-empty string, got None")
    if not isinstance(raw, str) or raw == "":
        raise InvalidResearchRequestError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def _as_optional_string(raw: Any, field: str) -> str:
    if raw is None:
        raise InvalidResearchRequestError(f"{field} must be a string, got None")
    if not isinstance(raw, str):
        raise InvalidResearchRequestError(f"{field} must be a string, got {raw!r}")
    return raw


def _as_int(raw: Any, field: str) -> int:
    if raw is None:
        raise InvalidResearchRequestError(f"{field} must be an integer, got None")
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise InvalidResearchRequestError(f"{field} must be an integer, got {raw!r}")
    return raw


def _as_float(raw: Any, field: str) -> float:
    if raw is None:
        raise InvalidResearchRequestError(f"{field} must be a number, got None")
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise InvalidResearchRequestError(f"{field} must be a number, got {raw!r}")
    return float(raw)


def _as_tuple_of_strings(raw: Any, field: str) -> tuple[str, ...]:
    if raw is None:
        raise InvalidResearchRequestError(
            f"{field} must be a non-empty tuple, got None"
        )
    if not isinstance(raw, (list, tuple)):
        raise InvalidResearchRequestError(
            f"{field} must be a list or tuple, got {type(raw).__name__}"
        )
    result: list[str] = []
    for item in raw:
        if not isinstance(item, str) or item == "":
            raise InvalidResearchRequestError(
                f"{field} must contain non-empty strings, got {item!r}"
            )
        result.append(item)
    if not result:
        raise InvalidResearchRequestError(
            f"{field} must be a non-empty tuple"
        )
    return tuple(result)
