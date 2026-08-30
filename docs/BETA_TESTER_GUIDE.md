# JRE Beta Testing Guide

**Version:** 1.0.0 | **Date:** August 2026

---

## Overview

The **Jyotish Reasoning Engine (JRE)** is a deterministic, rule-based system for evaluating classical Jyotish yogas from birth data. It implements a 5-layer reasoning pipeline based on authoritative texts (BPHS, Phaladeepika, Saravali).

### What the Engine Does

1. **Structural Detection (Layer 1):** Identifies classical yoga formations (Raja, Dhana, Gajakesari, Pancha Mahapurusha, etc.) from planetary positions
2. **Chain Evaluation (Layer 1.5):** Computes dispositorship chain impact on yoga strength
3. **Modifier Pipeline (Layer 2):** Applies 5-tier affliction checks (combustion, debilitation, planetary war, retrograde, node influence)
4. **Temporal Evaluation (Layer 3):** Combines Vimshottari Dasha activation with real Ashtakavarga transit bindus
5. **Varga Confirmation (Layer 4):** Validates yoga strength through D9 (Navamsha) confirmation

### Empirical Validation

Tested against 50 historical charts (150 known life events):

| Metric | Value |
|--------|-------|
| **Precision** | 78.0% |
| **Recall** | 67.5% |
| **F1 Score** | 0.723 |
| **Hit Rate** | 56.7% (95% CI: 48.7%–64.6%) |

---

## Known Limitations

We transparently document these so beta testers can set appropriate expectations:

### 1. HEALTH Domain False Positives (16 of 24 FPs)
Career-relevant yogas (Raja, Gajakesari) sometimes activate during death/health events due to Dasha coincidence. This is neutral behavior, not a false prediction — classical death timing requires Maraka Dasha analysis (not yet implemented).

### 2. Strict Dasha Activation
A yoga is only "activated" when the Mahadasha/Antardasha/Pratyantardasha lord IS one of the yoga's involved planets. This is strict — the engine doesn't consider dispositorship or aspect relationships for Dasha matching.

### 3. Missing Advanced Yogas
Some charts (Picasso, Tolstoy, Beethoven, de Gaulle, Ford) have zero yogas detected because their planetary configurations don't match any currently implemented yoga patterns. Additional detectors are needed.

### 4. Transit Layer Limitations
The transit layer computes real Ashtakavarga bindus but uses natal planet positions as an approximation for transit positions. Full ephemeris-based transit computation would improve accuracy.

### 5. No Maraka Dasha / Ayurdaya
Death timing and longevity calculations are not yet implemented. The engine focuses on yoga evaluation, not life-span prediction.

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd JRE

# Build and start the API server
docker-compose up --build

# The API is now available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### Option 2: Local Python

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
pip install fastapi uvicorn httpx

# Start the API server
uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Run Tests

```bash
# Run the full test suite
pytest tests/unit/jrs/ -q

# Run API tests only
pytest tests/unit/jrs/api/ -v
```

---

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
# {"status": "healthy", "version": "1.0.0"}
```

### List Available Charts
```bash
curl http://localhost:8000/api/v1/fixtures
# {"count": 50, "fixtures": ["chart_001_pilot", "chart_002_curie", ...]}
```

### Evaluate a Pre-computed Chart
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

### Evaluate Custom Birth Data
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/custom \
  -H "Content-Type: application/json" \
  -d '{
    "date": "1990-01-15",
    "time": "14:30:00",
    "latitude": 40.7128,
    "longitude": -74.006,
    "timezone": "America/New_York"
  }'
```

### Generate a Report
```bash
# Markdown format
curl -X POST http://localhost:8000/api/v1/report/fixture \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'

# HTML format
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=html" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

### Submit Feedback
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "fixture_id": "chart_001_pilot",
    "event_date": "1921-11-09",
    "expected_outcome": "Nobel Prize — career peak",
    "actual_outcome": "Engine predicted Malavya yoga activated",
    "notes": "Prediction matches well"
  }'
```

---

## Interpreting Results

### Yoga Status
- **FORMED:** Yoga conditions are fully met. The yoga is active in the chart.
- **WEAKENED:** Yoga conditions are partially met but some affliction applies.
- **CANCELLED:** Yoga conditions are met but a modifier (combustion, debilitation) cancels it.

### Strength Scores
- **static_strength:** Score after modifier pipeline (0.0–1.0). Higher = stronger yoga.
- **dynamic_strength:** Score after Dasha + Transit multipliers. This is the final ranking score.
- **dasha_multiplier:** How well the current Dasha aligns with the yoga (0.4–1.5).
- **transit_multiplier:** Transit Ashtakavarga adjustment (0.75–1.15).

### Activation Status
- **ACTIVATED:** The Dasha lord matches a yoga planet. The yoga is "live" at this time.
- **DORMANT:** The Dasha lord doesn't match. The yoga exists but isn't currently manifesting.

### Reading the Markdown Report

The report groups yogas by outcome domain:
- **Career & Professional Life** — Raja, Gajakesari, Pancha Mahapurusha yogas
- **Wealth & Financial Prosperity** — Dhana yogas
- **Arts & Creative Expression** — Malavya, Saraswati yogas
- **Relationships & Partnerships** — Sunapha, Anapha yogas

Each yoga includes:
- Classical description (what it means)
- Strength assessment (how strong it is)
- Timing context (when it manifests via Dasha)

---

## Providing Feedback

We value your feedback! Please use the `/api/v1/feedback` endpoint to report:

1. **Incorrect predictions:** Where the engine got the yoga or timing wrong
2. **Missing yogas:** Classical yogas that should be detected but aren't
3. **Report quality:** Suggestions for improving the Markdown/HTML reports
4. **API usability:** Issues with the API interface or documentation

### Feedback Categories

| Category | Description |
|----------|-------------|
| `false_negative` | Engine missed a yoga that should have been detected |
| `false_positive` | Engine detected a yoga that shouldn't exist |
| `timing_error` | Yoga activation timing is wrong |
| `report_quality` | Report formatting or content suggestions |
| `api_issue` | API usability or documentation issues |

---

## Architecture Reference

```
┌─────────────────────────────────────────────────────────────┐
│                    JRE 5-Layer Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Structural Detection                             │
│    → Conjunctions, aspects, dispositorship, exchanges       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1.5: Chain Evaluator                                │
│    → Multi-hop dispositorship chain impact                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Modifier Pipeline (5-tier priority)              │
│    → Combustion → Debilitation → War → Retrograde → Nodes  │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Temporal Evaluation                              │
│    → Vimshottari Dasha (activation) + Ashtakavarga (bindus)│
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Varga Confirmation                               │
│    → D9 (Navamsha) validation + Vargottama detection       │
└─────────────────────────────────────────────────────────────┘
```

---

## Classical Sources

| Component | Primary Source |
|-----------|---------------|
| Yoga Detection | BPHS Ch 33 (Dispositorship), Ch 41 (Yoga Yoga) |
| Modifiers | BPHS Ch 7 (Combustion), Ch 43 (Debilitation) |
| Dasha | BPHS Ch 44 (Vimshottari) |
| Ashtakavarga | BPHS Ch 3 (Ashtakavarga) |
| Varga | BPHS Ch 35 (Navamsha), Ch 54 (Varga Confirmation) |

---

## Support

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** http://localhost:8000/api/v1/health
- **Bug Reports:** Use the feedback endpoint or open a GitHub issue
