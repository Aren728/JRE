"""Static gate 4b: ``src/jyotish`` (JRE-003) is byte-for-byte untouched.

The file set and public ``__all__`` are pinned; CODING (JRE-004) must not
change them (SPEC §18, ADR-007). Mirrors the existing JRE-003 gate.
"""

from __future__ import annotations

from pathlib import Path

import jyotish

SRC = Path(jyotish.__file__).resolve().parent

EXPECTED_FILES = {
    "__init__.py",
    "config.py",
    "dms.py",
    "eclipse.py",
    "errors.py",
    "geometry.py",
    "houses.py",
    "lagna.py",
    "models.py",
    "nakshatra.py",
    "position.py",
    "rashi.py",
    "serialize.py",
    "service.py",
    "swisseph/__init__.py",
    "swisseph/constants.py",
    "swisseph/eclipse.py",
    "swisseph/houses.py",
    "transit.py",
}

EXPECTED_PUBLIC_API = {
    "JyotishService",
    "default_house_registry",
    "default_eclipse_registry",
    "get_house_provider",
    "get_eclipse_provider",
    "JyotishConfig",
    "ZodiacMode",
    "load_config",
    "BodyId",
    "RetrogradeState",
    "RashiId",
    "NakshatraId",
    "Pada",
    "DmsValue",
    "PlanetState",
    "derive_planet_state",
    "classify_longitude",
    "RASHI_CATALOG_VERSION",
    "RASHI_ORDER",
    "rashi_of",
    "degree_in_rashi",
    "sign_lord_of",
    "NAKSHATRA_CATALOG_VERSION",
    "NAKSHATRA_ORDER",
    "nakshatra_of",
    "degree_in_nakshatra",
    "lord_of",
    "pada_of",
    "AspectKind",
    "ApplyingSeparating",
    "AspectRelationship",
    "PairGeometry",
    "ASPECT_IDEAL_ANGLES",
    "angular_separation_deg",
    "normalized_separation_deg",
    "pair_geometry",
    "all_pairs",
    "HouseSystem",
    "HouseCuspProvider",
    "HouseCuspRegistry",
    "HouseCuspResult",
    "HouseProviderMetadata",
    "SWISSEPH_HOUSE_PROVIDER_ID",
    "whole_sign_cusps",
    "compute_bhavas",
    "bhava_containing_longitude",
    "Bhava",
    "LagnaState",
    "derive_lagna",
    "NatalChart",
    "BirthData",
    "TransitEventKind",
    "TransitReferencePoint",
    "TransitEvent",
    "TransitThroughHouses",
    "HouseTransitEntry",
    "SearchMetadata",
    "ContinuousTransitEngine",
    "iso_utc_to_jd",
    "jd_to_iso_utc",
    "EclipseKind",
    "EclipseClassification",
    "EclipseContact",
    "GeographicVisibility",
    "EclipseEvent",
    "EclipseProvider",
    "EclipseRegistry",
    "SWISSEPH_ECLIPSE_PROVIDER_ID",
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "birth_from_dict",
    "planetary_request_from_dict",
    "transit_query_from_dict",
    "eclipse_query_from_dict",
    "JyotishError",
    "InvalidBirthDataError",
    "InvalidConfigError",
    "InvalidOrbError",
    "UnsupportedHouseSystemError",
    "UnsupportedReferencePointError",
    "TransitSearchError",
    "EclipseError",
    "ProviderCompatibilityError",
}


def test_jyotish_file_set_unchanged():
    files = {
        str(path.relative_to(SRC)) for path in SRC.rglob("*.py") if "__pycache__" not in str(path)
    }
    assert files == EXPECTED_FILES


def test_jyotish_public_api_unchanged():
    assert set(jyotish.__all__) == EXPECTED_PUBLIC_API
