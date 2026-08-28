"""JRS-089: Dataset Loader Driver.

Provides DatasetLoader for accessing, exporting, and importing the
reference cohort data with full JSON serialization round-trip support.

Usage::

    loader = DatasetLoader()
    cohort = loader.get_reference_cohort()
    loader.export_cohort_to_json(Path("cohort.json"))
    loaded = loader.load_cohort_from_json(Path("cohort.json"))
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from jrs.validation.models import (
    BirthProvenance,
    ChartSubject,
    DomainType,
    HistoricalEvent,
    RoddenRating,
)


def _chart_subject_to_dict(subject: ChartSubject) -> dict:
    """Serialize ChartSubject to a JSON-compatible dict."""
    return subject.to_dict()


def _historical_event_to_dict(event: HistoricalEvent) -> dict:
    """Serialize HistoricalEvent to a JSON-compatible dict."""
    return event.to_dict()


def _dict_to_chart_subject(d: dict) -> ChartSubject:
    """Deserialize a dict to ChartSubject."""
    prov = d.get("provenance", {})
    return ChartSubject(
        chart_id=d["chart_id"],
        latitude=float(d["latitude"]),
        longitude=float(d["longitude"]),
        birth_timestamp=d["birth_timestamp"],
        timezone=d.get("timezone", "UTC"),
        provenance=BirthProvenance(
            source=prov.get("source", "unknown"),
            rodden_rating=RoddenRating(prov.get("rodden_rating", "C")),
            birth_time_confidence_minutes=prov.get("birth_time_confidence_minutes", 0),
        ),
    )


def _dict_to_historical_event(d: dict) -> HistoricalEvent:
    """Deserialize a dict to HistoricalEvent."""
    return HistoricalEvent(
        event_id=d["event_id"],
        chart_id=d["chart_id"],
        domain=DomainType(d["domain"]),
        start_date=d["start_date"],
        end_date=d.get("end_date"),
        event_certainty=float(d.get("event_certainty", 1.0)),
        description=d.get("description", ""),
    )


class DatasetLoader:
    """Driver for loading, exporting, and importing reference cohort data.

    Provides access to the REFERENCE_COHORT_12 dataset and supports
    JSON round-trip serialization for persistence and interchange.

    Usage::

        loader = DatasetLoader()
        cohort = loader.get_reference_cohort()
        assert len(cohort) == 12
    """

    def get_reference_cohort(
        self,
    ) -> List[Tuple[ChartSubject, HistoricalEvent]]:
        """Return the full 12-chart reference cohort.

        Returns:
            List of (ChartSubject, HistoricalEvent) tuples.
        """
        from .reference_cohort import REFERENCE_COHORT_12

        return list(REFERENCE_COHORT_12)

    def export_cohort_to_json(
        self,
        destination_path: Path,
    ) -> None:
        """Export the reference cohort to a JSON file.

        Each entry is serialized as {"subject": {...}, "event": {...}}.

        Args:
            destination_path: Path to write the JSON file.
        """
        cohort = self.get_reference_cohort()
        records = []
        for subject, event in cohort:
            records.append({
                "subject": _chart_subject_to_dict(subject),
                "event": _historical_event_to_dict(event),
            })

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "dataset": "REFERENCE_COHORT_12",
            "count": len(records),
            "records": records,
        }
        destination_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2),
            encoding="utf-8",
        )

    def load_cohort_from_json(
        self,
        source_path: Path,
    ) -> List[Tuple[ChartSubject, HistoricalEvent]]:
        """Load a cohort from a previously exported JSON file.

        Verifies JSON structure and reconstructs ChartSubject and
        HistoricalEvent objects from serialized data.

        Args:
            source_path: Path to the JSON file.

        Returns:
            List of (ChartSubject, HistoricalEvent) tuples.

        Raises:
            FileNotFoundError: If the source file does not exist.
            KeyError: If required fields are missing from records.
            ValueError: If domain or rodden_rating enums are invalid.
        """
        raw = source_path.read_text(encoding="utf-8")
        payload = json.loads(raw)

        records = payload.get("records", [])
        cohort: List[Tuple[ChartSubject, HistoricalEvent]] = []

        for record in records:
            subject = _dict_to_chart_subject(record["subject"])
            event = _dict_to_historical_event(record["event"])
            cohort.append((subject, event))

        return cohort
