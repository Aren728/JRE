"""JRE-009 Research Worker unit test configuration."""

import pytest
from pathlib import Path

from research.models import ResearchConfig, ResearchTask, TaskStatus


@pytest.fixture
def sample_config() -> ResearchConfig:
    """A sample ResearchConfig for testing."""
    return ResearchConfig(
        catalog_version="0.1.0",
        version="0.1.0",
        default_source_dir="tests/fixtures/research/",
        default_output_dir="tests/fixtures/research/output/",
        supported_extensions=(".md", ".txt"),
    )


@pytest.fixture
def sample_task() -> ResearchTask:
    """A sample ResearchTask for testing."""
    return ResearchTask(
        task_id="test-task-001",
        query="Find information about jyotish",
        target_concepts=("jyotish", "astrology"),
        source_directories=("tests/fixtures/research/",),
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path("tests/fixtures/research/")
