#!/usr/bin/env python3
"""Test script to verify aspect engine produces 12+ aspects."""

import importlib.util
import os
import sys

# Direct import to avoid __init__.py issues
spec = importlib.util.spec_from_file_location(
    "aspects", "/home/abhyram/JRE/src/jrs/prediction_engine/aspects.py"
)
aspects_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aspects_module)
AspectMatrixEngine = aspects_module.AspectMatrixEngine

# Sample Meena (Pisces) Lagna chart positions
# This is a hypothetical chart for testing
planet_signs = {
    "SUN": "KUMBHA",  # Sun in Aquarius (12th from Pisces)
    "MOON": "MEENA",  # Moon in Pisces (1st - Lagna)
    "MARS": "DHANUSHA",  # Mars in Sagittarius (10th from Pisces)
    "MERCURY": "KUMBHA",  # Mercury in Aquarius (12th from Pisces)
    "JUPITER": "MEENA",  # Jupiter in Pisces (1st - Lagna)
    "VENUS": "MAKARA",  # Venus in Capricorn (11th from Pisces)
    "SATURN": "VRISHCHIKA",  # Saturn in Scorpio (9th from Pisces)
    "RAHU": "SIMHA",  # Rahu in Leo (6th from Pisces)
    "KETU": "KUMBHA",  # Ketu in Aquarius (12th from Pisces)
}

lagna = "MEENA"  # Pisces Lagna

engine = AspectMatrixEngine()
result = engine.compute(planet_signs=planet_signs, lagna=lagna)

print(f"\n{'=' * 60}")
print(f"ASPECT MATRIX TEST - {lagna} (Pisces) Lagna")
print(f"{'=' * 60}")
print(f"\nTotal aspects found: {result.total_aspects}")
print(f"Exact aspects: {result.exact_aspects}")

print(f"\n{'─' * 60}")
print("ALL ASPECTS:")
print(f"{'─' * 60}")

for i, aspect in enumerate(result.all_aspects, 1):
    print(
        f"{i:2d}. {aspect.aspecter:8s} ({aspect.source_house:2d}th) ──[{aspect.aspect_type:4s}]──▶ {aspect.aspected:8s} ({aspect.target_house:2d}th)  strength={aspect.strength:.2f}"
    )

print(f"\n{'─' * 60}")
print("PER-PLANET SUMMARY:")
print(f"{'─' * 60}")

for summary in result.planet_summaries:
    if summary.total_aspects > 0:
        print(
            f"{summary.planet:8s}: {summary.total_aspects} aspects received, strongest from {summary.strongest_aspecter}"
        )

# Verify we have at least 12 aspects
if result.total_aspects >= 12:
    print(f"\n✅ PASS: Found {result.total_aspects} aspects (>= 12 required)")
else:
    print(f"\n❌ FAIL: Only found {result.total_aspects} aspects (< 12 required)")
    sys.exit(1)
