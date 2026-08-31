"""JRE Reporting — Unit tests for ReportGenerator.

Tests Markdown/HTML rendering, domain grouping, and the report API endpoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from jrs.api.main import app  # noqa: E402
from jrs.api.schemas import EvaluationResponse, YogaResult  # noqa: E402
from jrs.reporting.generator import ReportGenerator  # noqa: E402

client = TestClient(app)

# Test API key for authenticated endpoints
_TEST_API_KEY = "jre-beta-key-alpha"
_AUTH_HEADERS = {"X-API-Key": _TEST_API_KEY}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_yoga(
    name: str,
    status: str = "FORMED",
    planets: list[str] | None = None,
    domains: list[str] | None = None,
    static_strength: float = 0.8,
    category: str = "TEST",
) -> YogaResult:
    """Build a minimal YogaResult for testing."""
    return YogaResult(
        yoga_name=name,
        category=category,
        status=status,
        static_strength=static_strength,
        involved_planets=planets or ["JUPITER"],
        domains=domains or ["CAREER_PROMINENCE"],
    )


def _make_response(
    yogas: list[YogaResult] | None = None,
    subject: str = "Test Subject",
    lagna: str = "MESHA",
) -> EvaluationResponse:
    """Build a minimal EvaluationResponse for testing."""
    if yogas is None:
        yogas = []
    formed = sum(1 for y in yogas if y.status == "FORMED")
    return EvaluationResponse(
        subject=subject,
        lagna=lagna,
        moon_nakshatra="ASHWINI",
        yogas=yogas,
        yoga_count=len(yogas),
        formed_count=formed,
        processing_time_ms=12.5,
    )


# ── Markdown Rendering Tests ────────────────────────────────────────────────


class TestMarkdownRendering:
    """Tests for ReportGenerator.generate_markdown()."""

    def test_produces_valid_markdown_with_headers(self) -> None:
        """Markdown output contains expected section headers."""
        yogas = [
            _make_yoga("Malavya", domains=["ARTISTIC_EXCELLENCE"]),
            _make_yoga("Gajakesari", domains=["CAREER_PROMINENCE"]),
        ]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        assert "# Jyotish Yoga Report" in md
        assert "## Executive Summary" in md
        assert "## Arts & Creative Expression" in md
        assert "## Career & Professional Life" in md
        assert "## Complete Yoga Summary" in md

    def test_subject_name_in_title(self) -> None:
        """Report title includes the subject name."""
        response = _make_response(subject="Albert Einstein")
        gen = ReportGenerator(response)
        md = gen.generate_markdown()
        assert "Albert Einstein" in md

    def test_lagna_in_header(self) -> None:
        """Report includes the Lagna rashi."""
        response = _make_response(lagna="SIMHA")
        gen = ReportGenerator(response)
        md = gen.generate_markdown()
        assert "SIMHA" in md

    def test_domain_grouping_correct(self) -> None:
        """Yogas are grouped under correct domain sections."""
        yogas = [
            _make_yoga("Raja", domains=["CAREER_PROMINENCE", "POLITICAL_POWER"]),
            _make_yoga("Dhana", domains=["WEALTH_ACCUMULATION"]),
            _make_yoga("Malavya", domains=["ARTISTIC_EXCELLENCE"]),
        ]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        # Raja should appear under both Career and Political Power sections
        career_idx = md.index("## Career & Professional Life")
        political_idx = md.index("## Leadership & Political Influence")
        wealth_idx = md.index("## Wealth & Financial Prosperity")
        artistic_idx = md.index("## Arts & Creative Expression")

        assert career_idx < political_idx < wealth_idx < artistic_idx

    def test_cancelled_yogas_excluded_from_domain_sections(self) -> None:
        """Cancelled yogas don't appear in domain sections."""
        yogas = [
            _make_yoga("Raja", status="FORMED", domains=["CAREER_PROMINENCE"]),
            _make_yoga("Dhana", status="CANCELLED", domains=["WEALTH_ACCUMULATION"]),
        ]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        # Raja (formed) should appear in Career section
        assert "## Career & Professional Life" in md
        assert "### Raja" in md

        # Dhana (cancelled) should NOT have a domain section
        # (only cancelled yogas are excluded from grouping)
        assert "## Wealth & Financial Prosperity" not in md

        # But Dhana should appear in the summary table
        summary_idx = md.index("## Complete Yoga Summary")
        assert "Dhana" in md[summary_idx:]

    def test_summary_table_present(self) -> None:
        """Complete Yoga Summary table is generated."""
        yogas = [_make_yoga("Malavya"), _make_yoga("Gajakesari")]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        assert "| Yoga | Status | Planets | Strength |" in md
        assert "| Malavya |" in md
        assert "| Gajakesari |" in md

    def test_empty_yogas_produces_valid_report(self) -> None:
        """Report is valid even with no yogas detected."""
        response = _make_response(yogas=[])
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        assert "# Jyotish Yoga Report" in md
        assert "0" in md  # yoga count is 0

    def test_yoga_description_included(self) -> None:
        """Each yoga includes its plain-english description."""
        yogas = [_make_yoga("Malavya")]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        md = gen.generate_markdown()

        assert "Venus in own sign" in md

    def test_methodology_note_present(self) -> None:
        """Report includes a methodology disclaimer."""
        response = _make_response()
        gen = ReportGenerator(response)
        md = gen.generate_markdown()
        assert "## Methodology Note" in md
        assert "BPHS" in md


# ── HTML Rendering Tests ────────────────────────────────────────────────────


class TestHTMLRendering:
    """Tests for ReportGenerator.generate_html()."""

    def test_produces_valid_html(self) -> None:
        """HTML output is a complete HTML document."""
        yogas = [_make_yoga("Malavya")]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        html = gen.generate_html()

        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_html_contains_css(self) -> None:
        """HTML output includes inline CSS styling."""
        response = _make_response()
        gen = ReportGenerator(response)
        html = gen.generate_html()
        assert "<style>" in html
        assert "font-family" in html

    def test_html_contains_subject(self) -> None:
        """HTML title includes the subject name."""
        response = _make_response(subject="Marie Curie")
        gen = ReportGenerator(response)
        html = gen.generate_html()
        assert "Marie Curie" in html

    def test_html_has_table(self) -> None:
        """HTML output converts markdown tables to HTML tables."""
        yogas = [_make_yoga("Malavya"), _make_yoga("Gajakesari")]
        response = _make_response(yogas=yogas)
        gen = ReportGenerator(response)
        html = gen.generate_html()
        assert "<table>" in html
        assert "<th>" in html


# ── API Endpoint Tests ──────────────────────────────────────────────────────


class TestReportEndpoint:
    """Tests for POST /api/v1/report/fixture."""

    def test_report_markdown_returns_200(self) -> None:
        """Report endpoint returns 200 with markdown content."""
        response = client.post(
            "/api/v1/report/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "markdown"
        assert "content" in data
        assert len(data["content"]) > 100
        assert "Jyotish Yoga Report" in data["content"]

    def test_report_html_returns_200(self) -> None:
        """Report endpoint returns 200 with HTML content."""
        response = client.post(
            "/api/v1/report/fixture?format=html",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "html"
        assert "<!DOCTYPE html>" in data["content"]

    def test_report_not_found_returns_404(self) -> None:
        """Non-existent fixture returns 404."""
        response = client.post(
            "/api/v1/report/fixture",
            json={"fixture_id": "chart_999_nonexistent"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 404

    def test_report_invalid_format_returns_400(self) -> None:
        """Invalid format parameter returns 400."""
        response = client.post(
            "/api/v1/report/fixture?format=pdf",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 400

    def test_report_contains_yoga_names(self) -> None:
        """Report content includes detected yoga names."""
        response = client.post(
            "/api/v1/report/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        data = response.json()
        assert "Malavya" in data["content"]

    def test_report_subject_matches_fixture(self) -> None:
        """Report subject matches the fixture's subject name."""
        response = client.post(
            "/api/v1/report/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        data = response.json()
        assert data["subject"] == "Albert Einstein"
