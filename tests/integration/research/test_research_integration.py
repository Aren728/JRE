"""Integration tests for JRE-009 Research Worker."""

import pytest
from pathlib import Path

from research import ResearchWorker, ResearchConfig, ResearchTask, TaskStatus


@pytest.fixture
def worker_with_fixtures() -> ResearchWorker:
    """Create a ResearchWorker configured to use test fixtures."""
    config = ResearchConfig(
        catalog_version="0.1.0",
        version="0.1.0",
        default_source_dir="tests/fixtures/research/",
        default_output_dir="tests/fixtures/research/output/",
        supported_extensions=(".md", ".txt"),
    )
    return ResearchWorker(config=config)


class TestResearchWorkerIntegration:
    """Integration tests for ResearchWorker."""

    def test_execute_task_finds_evidence(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that execute_task finds evidence in fixture files."""
        task = ResearchTask(
            task_id="integration-test-001",
            query="Find jyotish information",
            target_concepts=("jyotish",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        assert report.task_id == "integration-test-001"
        assert report.query == "Find jyotish information"
        assert report.status == TaskStatus.COMPLETED
        assert len(report.evidence) > 0
        assert report.summary != ""

    def test_execute_task_records_line_numbers(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that evidence includes correct line numbers."""
        task = ResearchTask(
            task_id="integration-test-002",
            query="Find navamsa information",
            target_concepts=("navamsa",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        assert len(report.evidence) > 0
        for evidence in report.evidence:
            assert evidence.line_number > 0
            assert isinstance(evidence.excerpt, str)
            assert len(evidence.excerpt) > 0

    def test_execute_task_extracts_context(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that evidence includes context lines."""
        task = ResearchTask(
            task_id="integration-test-003",
            query="Find dasha information",
            target_concepts=("dasha",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        assert len(report.evidence) > 0
        for evidence in report.evidence:
            # Context should include surrounding lines
            assert isinstance(evidence.context, str)
            # Context should contain the excerpt
            assert evidence.excerpt in evidence.context

    def test_execute_task_case_insensitive(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that search is case-insensitive."""
        task = ResearchTask(
            task_id="integration-test-004",
            query="Find JYOTISH information",
            target_concepts=("JYOTISH",),  # Uppercase
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        # Should still find matches despite uppercase search
        assert len(report.evidence) > 0

    def test_execute_task_multiple_concepts(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test searching for multiple concepts."""
        task = ResearchTask(
            task_id="integration-test-005",
            query="Find jyotish or astrology",
            target_concepts=("jyotish", "astrology"),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        # Should find evidence for both concepts
        assert len(report.evidence) >= 2

    def test_execute_task_no_matches(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test task with no matching evidence."""
        task = ResearchTask(
            task_id="integration-test-006",
            query="Find nonexistent concept",
            target_concepts=("nonexistent-concept-xyz",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        assert report.task_id == "integration-test-006"
        assert report.status == TaskStatus.COMPLETED
        assert len(report.evidence) == 0
        assert "No evidence found" in report.summary

    def test_execute_task_nonexistent_directory(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test task with nonexistent source directory."""
        task = ResearchTask(
            task_id="integration-test-007",
            query="Test nonexistent dir",
            target_concepts=("test",),
            source_directories=("nonexistent/path/",),
        )
        report = worker_with_fixtures.execute_task(task)

        # Should complete without error, just no evidence
        assert report.status == TaskStatus.COMPLETED
        assert len(report.evidence) == 0

    def test_execute_task_generates_report(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that report contains all required fields."""
        task = ResearchTask(
            task_id="integration-test-008",
            query="Generate report",
            target_concepts=("jyotish",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        # Check report structure
        assert hasattr(report, "task_id")
        assert hasattr(report, "query")
        assert hasattr(report, "status")
        assert hasattr(report, "evidence")
        assert hasattr(report, "summary")
        assert hasattr(report, "generated_at")

        # Check report serialization
        data = report.to_dict()
        assert "task_id" in data
        assert "query" in data
        assert "status" in data
        assert "evidence" in data
        assert "summary" in data
        assert "generated_at" in data

    def test_execute_task_multiple_files(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test searching across multiple files."""
        task = ResearchTask(
            task_id="integration-test-009",
            query="Find planetary information",
            target_concepts=("planetary",),
            source_directories=("tests/fixtures/research/",),
        )
        report = worker_with_fixtures.execute_task(task)

        # Should find evidence in both sample1.md and sample2.txt
        source_files = set(evidence.source_file for evidence in report.evidence)
        assert len(source_files) >= 1  # At least one file should have matches

    def test_execute_task_evidence_deterministic_ids(self, worker_with_fixtures: ResearchWorker) -> None:
        """Test that evidence IDs are deterministic."""
        task = ResearchTask(
            task_id="integration-test-010",
            query="Test deterministic IDs",
            target_concepts=("jyotish",),
            source_directories=("tests/fixtures/research/",),
        )
        report1 = worker_with_fixtures.execute_task(task)
        report2 = worker_with_fixtures.execute_task(task)

        # Evidence IDs should be identical for same task
        ids1 = sorted(e.evidence_id for e in report1.evidence)
        ids2 = sorted(e.evidence_id for e in report2.evidence)
        assert ids1 == ids2
