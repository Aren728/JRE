"""Unit tests for JRE-009 Research Worker models."""

import pytest
from research.models import (
    Evidence,
    ResearchConfig,
    ResearchReport,
    ResearchTask,
    TaskStatus,
    compute_deterministic_id,
)
from research.errors import InvalidResearchRequestError


class TestResearchTask:
    """Tests for ResearchTask model."""

    def test_valid_task(self, sample_task: ResearchTask) -> None:
        """Test that a valid task is created correctly."""
        assert sample_task.task_id == "test-task-001"
        assert sample_task.query == "Find information about jyotish"
        assert sample_task.target_concepts == ("jyotish", "astrology")
        assert sample_task.source_directories == ("tests/fixtures/research/",)
        assert sample_task.status == TaskStatus.PENDING

    def test_task_to_dict(self, sample_task: ResearchTask) -> None:
        """Test task serialization to dict."""
        data = sample_task.to_dict()
        assert data["task_id"] == "test-task-001"
        assert data["query"] == "Find information about jyotish"
        assert data["target_concepts"] == ["jyotish", "astrology"]
        assert data["source_directories"] == ["tests/fixtures/research/"]
        assert data["status"] == "PENDING"

    def test_task_from_dict(self, sample_task: ResearchTask) -> None:
        """Test task deserialization from dict."""
        data = sample_task.to_dict()
        restored = ResearchTask.from_dict(data)
        assert restored.task_id == sample_task.task_id
        assert restored.query == sample_task.query
        assert restored.target_concepts == sample_task.target_concepts
        assert restored.source_directories == sample_task.source_directories
        assert restored.status == sample_task.status

    def test_task_invalid_empty_task_id(self) -> None:
        """Test that empty task_id raises error."""
        with pytest.raises(InvalidResearchRequestError, match="task_id"):
            ResearchTask(
                task_id="",
                query="test",
                target_concepts=("concept",),
                source_directories=("dir/",),
            )

    def test_task_invalid_empty_query(self) -> None:
        """Test that empty query raises error."""
        with pytest.raises(InvalidResearchRequestError, match="query"):
            ResearchTask(
                task_id="task-1",
                query="",
                target_concepts=("concept",),
                source_directories=("dir/",),
            )

    def test_task_invalid_empty_concepts(self) -> None:
        """Test that empty target_concepts raises error."""
        with pytest.raises(InvalidResearchRequestError, match="target_concepts"):
            ResearchTask(
                task_id="task-1",
                query="test",
                target_concepts=(),
                source_directories=("dir/",),
            )

    def test_task_invalid_empty_directories(self) -> None:
        """Test that empty source_directories raises error."""
        with pytest.raises(InvalidResearchRequestError, match="source_directories"):
            ResearchTask(
                task_id="task-1",
                query="test",
                target_concepts=("concept",),
                source_directories=(),
            )


class TestEvidence:
    """Tests for Evidence model."""

    def test_valid_evidence(self) -> None:
        """Test that valid evidence is created correctly."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="Line above\nTest line\nLine below",
            confidence=1.0,
        )
        assert evidence.evidence_id == "ev-001"
        assert evidence.task_id == "task-001"
        assert evidence.source_file == "test.md"
        assert evidence.excerpt == "Test line"
        assert evidence.line_number == 10
        assert evidence.context == "Line above\nTest line\nLine below"
        assert evidence.confidence == 1.0

    def test_evidence_to_dict(self) -> None:
        """Test evidence serialization to dict."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="Line above\nTest line\nLine below",
            confidence=0.95,
        )
        data = evidence.to_dict()
        assert data["evidence_id"] == "ev-001"
        assert data["task_id"] == "task-001"
        assert data["source_file"] == "test.md"
        assert data["excerpt"] == "Test line"
        assert data["line_number"] == 10
        assert data["confidence"] == 0.95

    def test_evidence_from_dict(self) -> None:
        """Test evidence deserialization from dict."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="Line above\nTest line\nLine below",
            confidence=1.0,
        )
        data = evidence.to_dict()
        restored = Evidence.from_dict(data)
        assert restored.evidence_id == evidence.evidence_id
        assert restored.task_id == evidence.task_id
        assert restored.source_file == evidence.source_file
        assert restored.excerpt == evidence.excerpt
        assert restored.line_number == evidence.line_number
        assert restored.context == evidence.context
        assert restored.confidence == evidence.confidence

    def test_evidence_invalid_line_number(self) -> None:
        """Test that invalid line_number raises error."""
        with pytest.raises(InvalidResearchRequestError, match="line_number"):
            Evidence(
                evidence_id="ev-001",
                task_id="task-001",
                source_file="test.md",
                excerpt="Test line",
                line_number=0,
                context="",
                confidence=1.0,
            )

    def test_evidence_invalid_confidence(self) -> None:
        """Test that invalid confidence raises error."""
        with pytest.raises(InvalidResearchRequestError, match="confidence"):
            Evidence(
                evidence_id="ev-001",
                task_id="task-001",
                source_file="test.md",
                excerpt="Test line",
                line_number=1,
                context="",
                confidence=1.5,
            )


class TestResearchReport:
    """Tests for ResearchReport model."""

    def test_valid_report(self) -> None:
        """Test that valid report is created correctly."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="",
            confidence=1.0,
        )
        report = ResearchReport(
            task_id="task-001",
            query="test query",
            status=TaskStatus.COMPLETED,
            evidence=(evidence,),
            summary="Found 1 evidence",
            generated_at="2024-01-01T00:00:00+00:00",
        )
        assert report.task_id == "task-001"
        assert report.query == "test query"
        assert report.status == TaskStatus.COMPLETED
        assert len(report.evidence) == 1
        assert report.summary == "Found 1 evidence"

    def test_report_to_dict(self) -> None:
        """Test report serialization to dict."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="",
            confidence=1.0,
        )
        report = ResearchReport(
            task_id="task-001",
            query="test query",
            status=TaskStatus.COMPLETED,
            evidence=(evidence,),
            summary="Found 1 evidence",
            generated_at="2024-01-01T00:00:00+00:00",
        )
        data = report.to_dict()
        assert data["task_id"] == "task-001"
        assert data["query"] == "test query"
        assert data["status"] == "COMPLETED"
        assert len(data["evidence"]) == 1
        assert data["summary"] == "Found 1 evidence"

    def test_report_from_dict(self) -> None:
        """Test report deserialization from dict."""
        evidence = Evidence(
            evidence_id="ev-001",
            task_id="task-001",
            source_file="test.md",
            excerpt="Test line",
            line_number=10,
            context="",
            confidence=1.0,
        )
        report = ResearchReport(
            task_id="task-001",
            query="test query",
            status=TaskStatus.COMPLETED,
            evidence=(evidence,),
            summary="Found 1 evidence",
            generated_at="2024-01-01T00:00:00+00:00",
        )
        data = report.to_dict()
        restored = ResearchReport.from_dict(data)
        assert restored.task_id == report.task_id
        assert restored.query == report.query
        assert restored.status == report.status
        assert len(restored.evidence) == len(report.evidence)
        assert restored.summary == report.summary
        assert restored.generated_at == report.generated_at


class TestResearchConfig:
    """Tests for ResearchConfig model."""

    def test_valid_config(self, sample_config: ResearchConfig) -> None:
        """Test that valid config is created correctly."""
        assert sample_config.catalog_version == "0.1.0"
        assert sample_config.version == "0.1.0"
        assert sample_config.default_source_dir == "tests/fixtures/research/"
        assert sample_config.default_output_dir == "tests/fixtures/research/output/"
        assert sample_config.supported_extensions == (".md", ".txt")

    def test_config_to_dict(self, sample_config: ResearchConfig) -> None:
        """Test config serialization to dict."""
        data = sample_config.to_dict()
        assert data["catalog_version"] == "0.1.0"
        assert data["version"] == "0.1.0"
        assert data["default_source_dir"] == "tests/fixtures/research/"
        assert data["default_output_dir"] == "tests/fixtures/research/output/"
        assert data["supported_extensions"] == [".md", ".txt"]

    def test_config_from_dict(self, sample_config: ResearchConfig) -> None:
        """Test config deserialization from dict."""
        data = sample_config.to_dict()
        restored = ResearchConfig.from_dict(data)
        assert restored.catalog_version == sample_config.catalog_version
        assert restored.version == sample_config.version
        assert restored.default_source_dir == sample_config.default_source_dir
        assert restored.default_output_dir == sample_config.default_output_dir
        assert restored.supported_extensions == sample_config.supported_extensions


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self) -> None:
        """Test that TaskStatus has correct values."""
        assert TaskStatus.PENDING.value == "PENDING"
        assert TaskStatus.RUNNING.value == "RUNNING"
        assert TaskStatus.COMPLETED.value == "COMPLETED"
        assert TaskStatus.FAILED.value == "FAILED"

    def test_task_status_from_string(self) -> None:
        """Test creating TaskStatus from string."""
        assert TaskStatus("PENDING") == TaskStatus.PENDING
        assert TaskStatus("RUNNING") == TaskStatus.RUNNING
        assert TaskStatus("COMPLETED") == TaskStatus.COMPLETED
        assert TaskStatus("FAILED") == TaskStatus.FAILED


class TestDeterministicId:
    """Tests for deterministic identity computation."""

    def test_deterministic_id_consistency(self) -> None:
        """Test that same input produces same id."""
        data = {"key": "value", "number": 42}
        id1 = compute_deterministic_id("test-domain", data)
        id2 = compute_deterministic_id("test-domain", data)
        assert id1 == id2

    def test_deterministic_id_different_domains(self) -> None:
        """Test that different domains produce different ids."""
        data = {"key": "value"}
        id1 = compute_deterministic_id("domain1", data)
        id2 = compute_deterministic_id("domain2", data)
        assert id1 != id2

    def test_deterministic_id_different_data(self) -> None:
        """Test that different data produces different ids."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        id1 = compute_deterministic_id("test-domain", data1)
        id2 = compute_deterministic_id("test-domain", data2)
        assert id1 != id2
