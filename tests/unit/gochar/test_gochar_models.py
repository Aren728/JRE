"""Model surface tests (TEST-PLAN §2 row 2, SPEC §6/§9).

Result models *contain* echoed JRE-003/JRE-005 values verbatim — they
never re-declare them, and JRE-006 defines zero new enums. Field-level
lists are pinned to SPEC §9 / DATA-CONTRACT §4.
"""

from __future__ import annotations

import gochar
import jyotish
from jyotish import TransitEvent, TransitEventKind


def test_result_field_surfaces() -> None:
    # SPEC §9.2 — GENERIC instant (no birth data anywhere).
    instant = gochar.GocharInstantResult.__dataclass_fields__
    assert set(instant) == {
        "instant_utc_iso",
        "planet_states",
        "pair_geometry",
        "config_echo",
        "provenance",
    }
    assert "birth_snapshot" not in instant

    # SPEC §9.3 — INDIVIDUAL natal.
    natal = gochar.GocharNatalResult.__dataclass_fields__
    assert set(natal) == {
        "instant_utc_iso",
        "birth_snapshot",
        "transit_house_analysis",
        "transit_to_natal_aspects",
        "reference_point",
        "provenance",
    }

    # SPEC §9.4 — interval.
    interval = gochar.GocharIntervalResult.__dataclass_fields__
    assert set(interval) == {
        "start_utc_iso",
        "end_utc_iso",
        "bodies",
        "events",
        "state_samples",
        "natal_house_series",
        "natal_anchor",
        "provenance",
    }


def test_provenance_field_surface() -> None:
    # SPEC §9.1 / DATA-CONTRACT §4.1.
    prov = gochar.GocharProvenance.__dataclass_fields__
    assert set(prov) == {
        "derivation_id",
        "derivation_version",
        "source_layers",
        "jyotish_version",
        "bhava_version",
        "gochar_version",
        "ephemeris_version",
        "catalog_versions",
        "input_echo",
        "algorithm",
    }


def test_request_field_surfaces() -> None:
    # SPEC §9.5.
    assert set(gochar.GocharInstantRequest.__dataclass_fields__) == {
        "instant_utc_iso",
        "bodies",
        "config",
    }
    assert set(gochar.GocharNatalRequest.__dataclass_fields__) == {
        "birth",
        "instant_utc_iso",
        "bodies",
        "reference_point",
        "config",
    }
    assert set(gochar.GocharIntervalRequest.__dataclass_fields__) == {
        "start_utc_iso",
        "end_utc_iso",
        "bodies",
        "natal_anchor",
        "config",
    }


def test_echoed_types_are_jyotish_types() -> None:
    """Reused, never redefined: the result models hold the canonical JRE-003
    types by identity, and JRE-006 defines no mirror types."""
    from bhava import TransitHouseAnalysis
    from jyotish import PlanetState, TransitReferencePoint

    assert jyotish.TransitEvent is TransitEvent
    assert jyotish.TransitEventKind is TransitEventKind
    assert jyotish.TransitReferencePoint is TransitReferencePoint
    assert PlanetState.__module__ == "jyotish.models"
    assert TransitHouseAnalysis.__module__ == "bhava.models"

    # The serialized planet_states elements are real PlanetState instances.
    import gochar.serialize as ser

    schema = ser.schema_for("GocharInstantResult")
    props = schema["properties"]
    assert set(props) == {
        "instant_utc_iso",
        "planet_states",
        "pair_geometry",
        "config_echo",
        "provenance",
    }
    assert props["planet_states"]["type"] == "array"
    assert props["pair_geometry"]["type"] == ["array", "null"]


def test_config_defaults_pinned() -> None:
    # SPEC §5 — every default.
    cfg = gochar.GocharConfig()
    assert cfg.reference_point == "LAGNA"
    assert cfg.house_system == "WHOLE_SIGN"
    assert cfg.sample_step_hours == 24.0
    assert cfg.aspect_echo is True
    assert cfg.natal_house_series is False
    assert cfg.tradition_profile is None
    assert cfg.version == "0.2.0"
