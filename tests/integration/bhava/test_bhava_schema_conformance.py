"""JSON Schema conformance (TEST-PLAN §3, SPEC §26, DATA-CONTRACT §11).

Every object type is defined with ``additionalProperties: false`` — a
result payload must contain exactly the declared keys. The checker is
self-contained (no external schema library) and mirrors the normative
excerpts in DATA-CONTRACT §11.
"""

from __future__ import annotations

from bhava import result_to_dict

#: Allowed keys per object type (additionalProperties: false).
SCHEMA: dict[str, set[str]] = {
    "HouseAnalysisResult": {
        "birth_snapshot",
        "config",
        "analyses",
        "golden_version",
    },
    "HouseAnalysis": {
        "house_system",
        "chart_echo",
        "derived_houses",
        "planet_house_facts",
        "ownership_facts",
        "relative_house_table",
        "relative_house_facts",
        "aspects_to_houses",
        "empty_house_numbers",
        "occupied_house_numbers",
        "empty_house_count",
        "derivation",
    },
    "DerivedHouseFact": {
        "house_system",
        "house_number",
        "rashi",
        "lord",
        "occupancy_status",
        "occupants",
        "categories",
        "start_deg",
        "end_deg",
        "boundary_kind",
        "cusp_nakshatra",
        "cusp_proximate_bodies",
        "aspects_received",
        "lord_placement",
        "echoed_from",
        "derivation",
    },
    "PlanetHouseFact": {
        "house_system",
        "body",
        "house_number",
        "house_rule",
        "rashi",
        "degree_in_rashi",
        "retrograde",
        "is_node",
        "sign_lord",
        "house_lord",
        "own_sign",
        "own_house",
        "relative_house_by_reference",
        "echoed_from",
        "derivation",
    },
    "HouseOwnershipFact": {
        "house_system",
        "body",
        "lorded_signs",
        "lorded_houses",
        "derivation",
    },
    "RelativeHouseFact": {
        "house_system",
        "body",
        "reference",
        "reference_absolute_house",
        "relative_house_number",
        "derivation",
    },
    "AspectToHouseFact": {
        "house_system",
        "house_number",
        "target",
        "source_body",
        "kind",
        "exact_angle_deg",
        "distance_from_exact_deg",
        "within_orb",
        "applying_separating",
        "echoed_from",
        "derivation",
    },
    "DerivationBlock": {
        "id",
        "derivation_version",
        "inputs",
        "source_catalog_versions",
        "house_system",
    },
    "ChartEcho": {
        "house_system",
        "jyotish_config",
        "provider_metadata",
        "rashi_catalog_version",
        "nakshatra_catalog_version",
        "anchor_frame",
        "sign_grid_frame_supported",
        "cusp_proximity_orb_deg",
        "unplaced_body_behavior",
        "tradition_profile",
        "derivation_version",
        "golden_version",
    },
    "TransitHouseAnalysis": {
        "birth_snapshot",
        "config",
        "transit_instant_utc_iso",
        "reference",
        "transit_facts",
        "chart_echo",
        "golden_version",
    },
    "TransitHouseFact": {
        "frame",
        "body",
        "natal_house_number",
        "natal_house_rashi",
        "natal_house_lord",
        "natal_occupants",
        "aspects_to_natal",
        "relative_house_by_reference",
        "echoed_from",
        "derivation",
    },
    "BhavaConfig": {
        "cusp_proximity_orb_deg",
        "house_systems",
        "include_empty_houses",
        "unplaced_body_behavior",
        "tradition_profile",
        "anchor_frame",
        "derivation_version",
    },
}

#: Object-shaped keys per type (for recursion).
OBJECT_KEYS: dict[str, list[str]] = {
    "HouseAnalysisResult": ["birth_snapshot", "config"],
    "HouseAnalysis": ["chart_echo", "derivation"],
    "DerivedHouseFact": ["lord_placement", "derivation"],
    "PlanetHouseFact": ["derivation"],
    "HouseOwnershipFact": ["derivation"],
    "RelativeHouseFact": ["derivation"],
    "AspectToHouseFact": ["derivation"],
    "ChartEcho": ["jyotish_config"],
    "TransitHouseAnalysis": ["birth_snapshot", "config", "chart_echo"],
    "TransitHouseFact": ["derivation"],
}

LIST_OBJECT_KEYS: dict[str, list[str]] = {
    "HouseAnalysisResult": ["analyses"],
    "HouseAnalysis": ["derived_houses", "planet_house_facts", "ownership_facts",
                      "relative_house_facts", "aspects_to_houses"],
    "DerivedHouseFact": ["aspects_received"],
    "TransitHouseAnalysis": ["transit_facts"],
}


def _assert_additional_properties(obj: dict, type_name: str) -> None:
    extra = set(obj) - SCHEMA[type_name]
    assert not extra, f"{type_name} has undeclared keys: {sorted(extra)}"
    for key in OBJECT_KEYS.get(type_name, []):
        value = obj.get(key)
        if value is not None and key_type(key) in SCHEMA:
            _assert_additional_properties(value, key_type(key))
    for key in LIST_OBJECT_KEYS.get(type_name, []):
        for item in obj.get(key, []):
            if key_type(key) in SCHEMA:
                _assert_additional_properties(item, key_type(key))


def key_type(key: str) -> str:
    mapping = {
        # JRE-003 passthrough shapes (not bhava-owned objects).
        "birth_snapshot": "birth_snapshot",
        "jyotish_config": "jyotish_config",
        "provider_metadata": "provider_metadata",
        "config": "BhavaConfig",
        "chart_echo": "ChartEcho",
        "derivation": "DerivationBlock",
        "lord_placement": "PlanetHouseFact",
        "analyses": "HouseAnalysis",
        "derived_houses": "DerivedHouseFact",
        "planet_house_facts": "PlanetHouseFact",
        "ownership_facts": "HouseOwnershipFact",
        "relative_house_facts": "RelativeHouseFact",
        "aspects_to_houses": "AspectToHouseFact",
        "aspects_received": "AspectToHouseFact",
        "transit_facts": "TransitHouseFact",
    }
    return mapping[key]


def test_natal_result_schema_conformance(bhava_service, birth) -> None:
    result = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN",))
    payload = result_to_dict(result)
    _assert_additional_properties(payload, "HouseAnalysisResult")
    # birth_snapshot is the JRE-003 BirthData shape (declared keys only).
    assert set(payload["birth_snapshot"]) == {"date", "time", "timezone", "latitude", "longitude"}


def test_transit_result_schema_conformance(bhava_service, jyotish_service, birth) -> None:
    from datetime import date, time

    transit = jyotish_service.transit_through_houses(
        birth, date(2024, 6, 1), time(0, 0), "UTC"
    )
    natal = jyotish_service.chart(birth)
    analysis = bhava_service.analyze_transit(transit, natal)
    payload = result_to_dict(analysis)
    _assert_additional_properties(payload, "TransitHouseAnalysis")
