# JRE — Jyotish Reasoning Engine

**JRS v1.0** — Deterministic astrological evidence framework with 8 validated domains, traceable CLI, and classical source citations.

A modular computational reasoning framework for Jyotisha that separates astronomical calculations, astrological classification, knowledge representation, rule execution, and evidence aggregation into independent, testable layers.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the CLI
python -m jrs.cli \
  --birth-date "28-09-1979" \
  --birth-time "18:24" \
  --place "Mumbai, India" \
  --query "career"

# JSON output
python -m jrs.cli \
  --birth-date "28-09-1979" \
  --birth-time "18:24" \
  --place "Mumbai, India" \
  --query "wealth" \
  --json
```

## Architecture

JRE separates concerns into 8 layers:

1. **Astronomical calculations** (JRE-002) — Swiss Ephemeris adapter
2. **Astrological classification** (JRE-003) — Coordinate/state layer
3. **Knowledge representation** (JRE-004) — Classical rules & fact vocabulary
4. **Rule execution** — Condition evaluation engine
5. **Dynamic state calculation** — Bhava, Gochar, Dasha engines
6. **Evidence aggregation** — Domain rule catalogs → EvidenceRecords
7. **Inference** — Temporal windows → Convergence assessment
8. **Explanation** — Traceable reports with classical source citations

## Domains (JRS v1.0 — 8 Tier 1 Domains)

| Domain | Outcomes | Status |
|--------|----------|--------|
| Marriage | MARRIAGE_FORMATION, MARITAL_HARMONY, DELAYED_MARRIAGE, SEPARATION | ✅ Validated |
| Career | CAREER_ASCENT, GOVERNMENT_SERVICE, SUCCESSFUL_BUSINESS, ENTREPRENEURSHIP | ✅ Validated |
| Wealth | WEALTH_ACCUMULATION, INHERITANCE, DEBT_BURDEN, BUSINESS_WEALTH, SPECULATIVE_GAINS | ✅ Validated |
| Progeny | EASY_CONCEPTION, DELAYED_PROGENY, MULTIPLE_CHILDREN, CHALLENGES_WITH_CHILDREN | ✅ Validated |
| Migration | FOREIGN_SETTLEMENT, SHORT_TERM_TRAVEL, MIGRATION_DELAY, VISA_OBSTACLES | ✅ Validated |
| Education | HIGHER_EDUCATION, EDUCATION_DISRUPTION, FOREIGN_EDUCATION, RESEARCH_ACADEMIA | ✅ Validated |
| Property | PROPERTY_ACQUISITION, REAL_ESTATE_WEALTH, DISPUTES_OVER_PROPERTY, FOREIGN_PROPERTY | ✅ Validated |
| Transitions | LIFE_PHASE_SHIFT, SUDDEN_UPHEAVAL, GRADUAL_EVOLUTION, SPIRITUAL_AWAKENING | ✅ Validated |

## Running Tests

```bash
# Unit tests
pytest tests/unit/jrs/ -v

# Integration tests
pytest tests/integration/jrs/ -v

# Type checking
mypy src/jrs/ --strict

# Linting
ruff check src/jrs/
```

## Hardware Target

Designed for low-resource systems:

- 2 CPU cores
- ~4 GB RAM
- Linux
- Python 3.12

Heavy AI inference is not required for the core engine.
