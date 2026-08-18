"""JRE-009 ResearchWorker service facade.

``ResearchWorker.execute_task`` is the canonical entry point: it validates
the task, searches source directories for evidence, records provenance,
and outputs a structured ``ResearchReport``.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from .config import load_config
from .errors import InvalidResearchRequestError, ResearchComputationError
from .models import (
    Evidence,
    ResearchConfig,
    ResearchReport,
    ResearchTask,
    TaskStatus,
    compute_deterministic_id,
)


class ResearchWorker:
    """Deterministic Research Worker facade."""

    def __init__(self, config: ResearchConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> ResearchConfig:
        return self._config

    def execute_task(self, task: ResearchTask) -> ResearchReport:
        """Execute a research task and return a structured report.

        1. Validates the task.
        2. Iterates through task.source_directories.
        3. Finds files matching config.supported_extensions.
        4. Reads files line-by-line.
        5. Searches for task.target_concepts (case-insensitive substring match).
        6. Extracts the matching line and 1 line of context above/below.
        7. Creates an Evidence object for each match.
        8. Compiles into a ResearchReport with status COMPLETED.
        """
        self._validate_task(task)

        evidence_list: list[Evidence] = []
        source_dirs = task.source_directories

        for source_dir in source_dirs:
            dir_path = Path(source_dir)
            if not dir_path.is_dir():
                continue

            for file_path in self._find_files(dir_path):
                try:
                    file_evidence = self._search_file(file_path, task)
                    evidence_list.extend(file_evidence)
                except OSError as exc:
                    raise ResearchComputationError(
                        f"failed to read {file_path} ({type(exc).__name__}): {exc}"
                    ) from exc

        evidence = tuple(evidence_list)
        summary = self._generate_summary(task, evidence)
        generated_at = datetime.datetime.now(datetime.UTC).isoformat()

        return ResearchReport(
            task_id=task.task_id,
            query=task.query,
            status=TaskStatus.COMPLETED,
            evidence=evidence,
            summary=summary,
            generated_at=generated_at,
        )

    def _validate_task(self, task: ResearchTask) -> None:
        """Validate a research task."""
        if not isinstance(task, ResearchTask):
            raise InvalidResearchRequestError(
                f"task must be a ResearchTask, got {type(task).__name__}"
            )

    def _find_files(self, directory: Path) -> list[Path]:
        """Find files in directory matching supported extensions."""
        files: list[Path] = []
        try:
            for item in sorted(directory.iterdir()):
                if item.is_file() and item.suffix in self._config.supported_extensions:
                    files.append(item)
        except OSError as exc:
            raise ResearchComputationError(
                f"failed to list directory {directory} ({type(exc).__name__}): {exc}"
            ) from exc
        return files

    def _search_file(self, file_path: Path, task: ResearchTask) -> list[Evidence]:
        """Search a file for evidence matching target concepts."""
        evidence_list: list[Evidence] = []
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ResearchComputationError(
                f"failed to read {file_path} ({type(exc).__name__}): {exc}"
            ) from exc

        for line_num, line in enumerate(lines, start=1):
            for concept in task.target_concepts:
                if concept.lower() in line.lower():
                    context_lines = self._extract_context(lines, line_num - 1)
                    context = "\n".join(context_lines)
                    evidence_id = compute_deterministic_id(
                        "jre009:evidence",
                        {
                            "task_id": task.task_id,
                            "source_file": str(file_path),
                            "line_number": line_num,
                            "excerpt": line,
                        },
                    )
                    evidence = Evidence(
                        evidence_id=evidence_id,
                        task_id=task.task_id,
                        source_file=str(file_path),
                        excerpt=line,
                        line_number=line_num,
                        context=context,
                        confidence=1.0,
                    )
                    evidence_list.append(evidence)
                    break  # One evidence per line, even if multiple concepts match
        return evidence_list

    def _extract_context(self, lines: list[str], match_index: int) -> list[str]:
        """Extract 1 line of context above and below the match."""
        context_start = max(0, match_index - 1)
        context_end = min(len(lines), match_index + 2)
        return lines[context_start:context_end]

    def _generate_summary(self, task: ResearchTask, evidence: tuple[Evidence, ...]) -> str:
        """Generate a human-readable summary of findings."""
        if not evidence:
            return (
                f"No evidence found for query '{task.query}' "
                f"with concepts {task.target_concepts}"
            )

        source_files = sorted(set(ev.source_file for ev in evidence))
        return (
            f"Found {len(evidence)} evidence item(s) for query '{task.query}' "
            f"matching concepts {task.target_concepts} in {len(source_files)} file(s)"
        )
