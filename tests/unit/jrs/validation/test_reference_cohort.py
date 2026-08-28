"""JRS-089: Unit tests for Historical Reference Dataset (12-Chart Cohort).

Verifies provenance integrity, zero target leakage, ISO-8601 timezone
awareness, JSON round-trip fidelity, and full pipeline integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import pytest

from jrs.validation.datasets import DatasetLoader, REFERENCE_COHORT_12
from jrs.validation.datasets.reference_cohort import REFERENCE_COHORT_12
from jrs.validation.models import (
    BirthProvenance,
    ChartSubject,
    DomainType,
    HistoricalEvent,
    RoddenRating,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def loader() -> DatasetLoader:
    """Provide a DatasetLoader instance."""
    return DatasetLoader()


@pytest.fixture()
def cohort() -> List[Tuple[ChartSubject, HistoricalEvent]]:
    """Provide the reference cohort."""
    return list(REFERENCE_COHORT_12)


# ── 1. Provenance Integrity: All charts must have Rodden AA ──────────────────


class TestProvenanceIntegrity:
    """Verify that all 12 reference subjects have explicit Rodden AA ratings."""

    def test_cohort_size(self, cohort: List[Tuple[ChartSubject, HistoricalEvent]]) -> None:
        """Dataset contains exactly 12 chart-event pairs."""
        assert len(cohort) == 12

    def test_all_charts_have_aa_rating(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Every ChartSubject must have RoddenRating.AA."""
        for subject, event in cohort:
            assert subject.provenance.rodden_rating == RoddenRating.AA, (
                f"{subject.chart_id} has rating "
                f"{subject.provenance.rodden_rating.value}, expected AA"
            )

    def test_all_provenance_have_astro_databank_source(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Every provenance source must reference Astro-Databank."""
        for subject, event in cohort:
            assert "astro-databank" in subject.provenance.source.lower(), (
                f"{subject.chart_id} provenance source "
                f"'{subject.provenance.source}' does not reference Astro-Databank"
            )

    def test_all_birth_times_confident(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """AA-rated charts should have zero confidence uncertainty."""
        for subject, event in cohort:
            assert subject.provenance.birth_time_confidence_minutes == 0, (
                f"{subject.chart_id} has non-zero confidence minutes: "
                f"{subject.provenance.birth_time_confidence_minutes}"
            )

    def test_all_chart_ids_unique(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Every chart_id must be unique."""
        ids = [subject.chart_id for subject, _ in cohort]
        assert len(ids) == len(set(ids)), f"Duplicate chart IDs found: {ids}"

    def test_all_event_ids_unique(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Every event_id must be unique."""
        ids = [event.event_id for _, event in cohort]
        assert len(ids) == len(set(ids)), f"Duplicate event IDs found: {ids}"


# ── 2. Zero Target Leakage: No astrological keywords in events ───────────────


class TestZeroTargetLeakage:
    """Ensure event records contain zero astrological descriptors."""

    ASTRO_KEYWORDS = [
        "dasha", "mahadasha", "antardasha", "pratyantardasha",
        "jupiter", "saturn", "mars", "venus", "mercury", "sun", "moon",
        "rahu", "ketu", "yoga", "kendra", "trikona", "exalted",
        "debilitated", "retrograde", "combust", "aspects",
        "transit", "gochar", "maha_purusha", "gajakesari",
        "parivartana", "nakshatra", "rashi", "lagna",
    ]

    def test_no_astro_keywords_in_event_descriptions(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Event descriptions must not contain astrological terms."""
        for subject, event in cohort:
            desc_lower = event.description.lower()
            for keyword in self.ASTRO_KEYWORDS:
                assert keyword not in desc_lower, (
                    f"{event.event_id}: description contains astrological "
                    f"keyword '{keyword}': {event.description}"
                )

    def test_no_astro_keywords_in_event_ids(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Event IDs must not contain astrological terms."""
        for subject, event in cohort:
            eid_lower = event.event_id.lower()
            for keyword in self.ASTRO_KEYWORDS:
                assert keyword not in eid_lower, (
                    f"Event ID '{event.event_id}' contains "
                    f"astrological keyword '{keyword}'"
                )

    def test_chart_subjects_have_no_event_data(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """ChartSubject must contain zero event-related fields."""
        for subject, event in cohort:
            subject_dict = subject.to_dict()
            # Must not have event-related keys
            forbidden_keys = {"event_id", "domain", "start_date", "end_date",
                              "description", "event_certainty"}
            found = forbidden_keys.intersection(subject_dict.keys())
            assert not found, (
                f"{subject.chart_id} has event keys in subject: {found}"
            )

    def test_events_have_no_birth_data(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """HistoricalEvent must not contain birth-related fields."""
        for subject, event in cohort:
            event_dict = event.to_dict()
            forbidden_keys = {"birth_timestamp", "latitude", "longitude",
                              "timezone", "provenance"}
            found = forbidden_keys.intersection(event_dict.keys())
            assert not found, (
                f"{event.event_id} has birth keys in event: {found}"
            )


# ── 3. ISO-8601 Timezone Awareness ───────────────────────────────────────────


class TestTimezoneAwareness:
    """Verify all timestamps use ISO-8601 with timezone offsets."""

    def test_birth_timestamps_contain_offset(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """All birth_timestamps must include timezone offset (+/-HH:MM or Z)."""
        import re
        offset_pattern = re.compile(r"[+-]\d{2}:\d{2}$")
        for subject, event in cohort:
            ts = subject.birth_timestamp
            has_offset = ts.endswith("Z") or bool(offset_pattern.search(ts))
            assert has_offset, (
                f"{subject.chart_id}: birth_timestamp '{ts}' "
                f"missing timezone offset"
            )

    def test_event_start_dates_are_iso8601_utc(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """All event start_dates must be ISO-8601 UTC format."""
        for subject, event in cohort:
            sd = event.start_date
            assert sd.endswith("Z"), (
                f"{event.event_id}: start_date '{sd}' "
                f"not in UTC (missing Z suffix)"
            )
            # Must contain T separator
            assert "T" in sd, (
                f"{event.event_id}: start_date '{sd}' "
                f"missing T separator"
            )

    def test_event_end_dates_are_iso8601_utc_or_none(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """All event end_dates must be ISO-8601 UTC or None."""
        for subject, event in cohort:
            ed = event.end_date
            if ed is not None:
                assert ed.endswith("Z"), (
                    f"{event.event_id}: end_date '{ed}' "
                    f"not in UTC (missing Z suffix)"
                )

    def test_birth_coordinates_in_valid_range(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """Birth lat/long must be within valid geographic ranges."""
        for subject, event in cohort:
            assert -90.0 <= subject.latitude <= 90.0, (
                f"{subject.chart_id}: invalid latitude {subject.latitude}"
            )
            assert -180.0 <= subject.longitude <= 180.0, (
                f"{subject.chart_id}: invalid longitude {subject.longitude}"
            )

    def test_event_certainties_in_valid_range(
        self, cohort: List[Tuple[ChartSubject, HistoricalEvent]],
    ) -> None:
        """All event_certainty values must be between 0.0 and 1.0."""
        for subject, event in cohort:
            assert 0.0 <= event.event_certainty <= 1.0, (
                f"{event.event_id}: invalid certainty {event.event_certainty}"
            )


# ── 4. JSON Export/Import Round-Trip Fidelity ─────────────────────────────────


class TestJsonRoundTrip:
    """Verify JSON export/import preserves all data faithfully."""

    def test_export_creates_valid_json(
        self, loader: DatasetLoader, tmp_path: Path,
    ) -> None:
        """Exported JSON must be valid and parseable."""
        dest = tmp_path / "cohort.json"
        loader.export_cohort_to_json(dest)
        assert dest.exists()
        raw = dest.read_text()
        data = json.loads(raw)
        assert data["version"] == "1.0"
        assert data["dataset"] == "REFERENCE_COHORT_12"
        assert data["count"] == 12
        assert len(data["records"]) == 12

    def test_round_trip_preserves_all_charts(
        self, loader: DatasetLoader, tmp_path: Path,
    ) -> None:
        """Export then import must return the same 12 chart-event pairs."""
        dest = tmp_path / "cohort.json"
        original = loader.get_reference_cohort()

        loader.export_cohort_to_json(dest)
        loaded = loader.load_cohort_from_json(dest)

        assert len(loaded) == len(original)

        for (orig_subj, orig_evt), (load_subj, load_evt) in zip(
            original, loaded,
        ):
            assert orig_subj.chart_id == load_subj.chart_id
            assert orig_subj.latitude == load_subj.latitude
            assert orig_subj.longitude == load_subj.longitude
            assert orig_subj.birth_timestamp == load_subj.birth_timestamp
            assert orig_subj.timezone == load_subj.timezone
            assert orig_subj.provenance.rodden_rating == load_subj.provenance.rodden_rating
            assert orig_evt.event_id == load_evt.event_id
            assert orig_evt.domain == load_evt.domain
            assert orig_evt.start_date == load_evt.start_date
            assert orig_evt.end_date == load_evt.end_date
            assert orig_evt.event_certainty == load_evt.event_certainty
            assert orig_evt.description == load_evt.description

    def test_round_trip_preserves_event_certainty(
        self, loader: DatasetLoader, tmp_path: Path,
    ) -> None:
        """Event certainty must survive round-trip without float drift."""
        dest = tmp_path / "cohort.json"
        original = loader.get_reference_cohort()

        loader.export_cohort_to_json(dest)
        loaded = loader.load_cohort_from_json(dest)

        for (_, orig_evt), (_, load_evt) in zip(original, loaded):
            assert orig_evt.event_certainty == pytest.approx(
                load_evt.event_certainty,
            )

    def test_double_round_trip_idempotent(
        self, loader: DatasetLoader, tmp_path: Path,
    ) -> None:
        """Two successive export/import cycles must produce identical data."""
        path1 = tmp_path / "cohort1.json"
        path2 = tmp_path / "cohort2.json"

        loader.export_cohort_to_json(path1)
        loaded1 = loader.load_cohort_from_json(path1)

        # Re-export from loaded data
        records = []
        for subj, evt in loaded1:
            records.append({
                "subject": subj.to_dict(),
                "event": evt.to_dict(),
            })
        payload = {
            "version": "1.0",
            "dataset": "REFERENCE_COHORT_12",
            "count": len(records),
            "records": records,
        }
        path2.write_text(json.dumps(payload, sort_keys=True, indent=2))

        loaded2 = loader.load_cohort_from_json(path2)
        assert loaded1 == loaded2


# ── 5. Integration: DatasetLoader.get_reference_cohort() returns all 12 ──────


class TestDatasetLoaderIntegration:
    """Verify DatasetLoader provides correct data access."""

    def test_loader_returns_12_entries(self, loader: DatasetLoader) -> None:
        """get_reference_cohort must return exactly 12 entries."""
        cohort = loader.get_reference_cohort()
        assert len(cohort) == 12

    def test_loader_entries_are_tuple_of_correct_types(
        self, loader: DatasetLoader,
    ) -> None:
        """Each entry must be a (ChartSubject, HistoricalEvent) tuple."""
        cohort = loader.get_reference_cohort()
        for entry in cohort:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert isinstance(entry[0], ChartSubject)
            assert isinstance(entry[1], HistoricalEvent)

    def test_loader_entries_match_reference_constant(
        self, loader: DatasetLoader,
    ) -> None:
        """Loader output must match REFERENCE_COHORT_12 constant."""
        cohort = loader.get_reference_cohort()
        assert cohort == list(REFERENCE_COHORT_12)

    def test_each_chart_has_corresponding_event(
        self, loader: DatasetLoader,
    ) -> None:
        """Each ChartSubject.chart_id must match its HistoricalEvent.chart_id."""
        cohort = loader.get_reference_cohort()
        for subject, event in cohort:
            assert subject.chart_id == event.chart_id, (
                f"Mismatch: subject={subject.chart_id}, event={event.event_id} "
                f"references chart {event.chart_id}"
            )

    def test_all_events_are_valid_domain_types(
        self, loader: DatasetLoader,
    ) -> None:
        """All events must use valid DomainType enum values."""
        valid_domains = {dt.value for dt in DomainType}
        cohort = loader.get_reference_cohort()
        for subject, event in cohort:
            assert event.domain.value in valid_domains, (
                f"{event.event_id}: invalid domain '{event.domain.value}'"
            )


# ── 6. Named Historical Figures Verification ──────────────────────────────────


class TestHistoricalFigures:
    """Verify the 12 named historical figures are present with correct events."""

    EXPECTED_FIGURES = {
        "EINSTEIN_1879": DomainType.CAREER_PEAK,
        "ELIZABETH_II_1926": DomainType.CAREER_PEAK,
        "JOBS_1955": DomainType.WEALTH_EVENT,
        "CURIE_1867": DomainType.CAREER_PEAK,
        "FDR_1882": DomainType.CAREER_PEAK,
        "DIANA_1961": DomainType.MARRIAGE,
        "JFK_1917": DomainType.CAREER_PEAK,
        "MONROE_1926": DomainType.CAREER_PEAK,
        "CHURCHILL_1874": DomainType.CAREER_PEAK,
        "GANDHI_1869": DomainType.CAREER_PEAK,
        "DISNEY_1901": DomainType.WEALTH_EVENT,
        "ROBERTS_1967": DomainType.CAREER_PEAK,
    }

    def test_all_expected_figures_present(
        self, loader: DatasetLoader,
    ) -> None:
        """All 12 expected historical figures must be in the cohort."""
        cohort = loader.get_reference_cohort()
        found_ids = {subj.chart_id for subj, _ in cohort}
        for chart_id in self.EXPECTED_FIGURES:
            assert chart_id in found_ids, f"Missing expected figure: {chart_id}"

    def test_figures_have_correct_event_domains(
        self, loader: DatasetLoader,
    ) -> None:
        """Each figure must have the expected event domain."""
        cohort = loader.get_reference_cohort()
        by_id = {subj.chart_id: (subj, evt) for subj, evt in cohort}
        for chart_id, expected_domain in self.EXPECTED_FIGURES.items():
            _, event = by_id[chart_id]
            assert event.domain == expected_domain, (
                f"{chart_id}: expected domain {expected_domain.value}, "
                f"got {event.domain.value}"
            )

    def test_einstein_event_description_mentions_nobel(
        self, loader: DatasetLoader,
    ) -> None:
        """Einstein's event must mention Nobel Prize."""
        cohort = loader.get_reference_cohort()
        for subj, evt in cohort:
            if subj.chart_id == "EINSTEIN_1879":
                assert "Nobel" in evt.description
                break

    def test_diana_event_is_marriage_domain(
        self, loader: DatasetLoader,
    ) -> None:
        """Princess Diana's event must be in MARRIAGE domain."""
        cohort = loader.get_reference_cohort()
        for subj, evt in cohort:
            if subj.chart_id == "DIANA_1961":
                assert evt.domain == DomainType.MARRIAGE
                assert "Marriage" in evt.description or "Charles" in evt.description
                break

    def test_jobs_event_is_wealth_domain(
        self, loader: DatasetLoader,
    ) -> None:
        """Steve Jobs' event must be in WEALTH_EVENT domain."""
        cohort = loader.get_reference_cohort()
        for subj, evt in cohort:
            if subj.chart_id == "JOBS_1955":
                assert evt.domain == DomainType.WEALTH_EVENT
                assert "Apple" in evt.description
                break
