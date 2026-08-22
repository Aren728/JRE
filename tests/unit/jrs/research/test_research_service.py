"""Unit tests for ResearchService."""

from __future__ import annotations

import pytest

from jrs.research.errors import CitationNotFoundError
from jrs.research.models import RuleCitation
from jrs.research.service import ResearchService


class TestResearchServiceInit:
    """Tests for ResearchService initialization."""

    def test_default_config(self) -> None:
        svc = ResearchService()
        assert svc.config is not None
        assert svc.config.version == "1.0"


class TestResearchServiceCitationLookup:
    """Tests for citation lookup methods."""

    def test_get_citation(self) -> None:
        svc = ResearchService()
        citation = svc.get_citation("R-BPHS-14-05")
        assert isinstance(citation, RuleCitation)
        assert citation.rule_id == "R-BPHS-14-05"
        assert citation.source == "BPHS"
        assert citation.domain == "wealth"

    def test_get_citation_not_found(self) -> None:
        svc = ResearchService()
        with pytest.raises(CitationNotFoundError, match="No citation found"):
            svc.get_citation("R-NONEXISTENT-000")

    def test_get_citations_for_domain(self) -> None:
        svc = ResearchService()
        wealth_citations = svc.get_citations_for_domain("wealth")
        assert len(wealth_citations) > 0
        for c in wealth_citations:
            assert c.domain == "wealth"

    def test_get_all_citations(self) -> None:
        svc = ResearchService()
        all_citations = svc.get_all_citations()
        assert len(all_citations) > 0

    def test_get_citation_ids(self) -> None:
        svc = ResearchService()
        ids = svc.get_citation_ids()
        assert len(ids) > 0
        assert "R-BPHS-14-05" in ids

    def test_citation_count(self) -> None:
        svc = ResearchService()
        assert svc.citation_count > 0

    def test_caching(self) -> None:
        svc = ResearchService()
        c1 = svc.get_citation("R-BPHS-14-05")
        c2 = svc.get_citation("R-BPHS-14-05")
        assert c1.rule_id == c2.rule_id

    def test_citation_to_citation_string(self) -> None:
        svc = ResearchService()
        citation = svc.get_citation("R-BPHS-14-05")
        s = citation.to_citation_string()
        assert "Brihat Parashara Hora Shastra" in s
        assert "Chapter 14, Verse 5" in s

    def test_multiple_domains(self) -> None:
        svc = ResearchService()
        domains = {c.domain for c in svc.get_all_citations()}
        assert len(domains) >= 4


class TestResearchServiceDeterminism:
    """Tests for deterministic output."""

    def test_deterministic_citation_lookup(self) -> None:
        svc = ResearchService()
        c1 = svc.get_citation("R-BPHS-14-05")
        c2 = svc.get_citation("R-BPHS-14-05")
        assert c1.to_dict() == c2.to_dict()

    def test_deterministic_all_citations(self) -> None:
        svc = ResearchService()
        ids1 = svc.get_citation_ids()
        ids2 = svc.get_citation_ids()
        assert ids1 == ids2
