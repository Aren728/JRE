# JRE Beta Testing Guide

**Version:** 1.0.0-beta | **Date:** August 2026 | **Engine:** v1.0.0-beta (frozen)

---

## Overview

The **Jyotish Reasoning Engine (JRE)** is a deterministic, rule-based system for evaluating classical Jyotish yogas from birth data. It implements a 5-layer reasoning pipeline based on authoritative texts (BPHS, Phaladeepika, Saravali).

### What the Engine Does

1. **Structural Detection (Layer 1):** Identifies classical yoga formations (Raja, Dhana, Gajakesari, Pancha Mahapurusha, etc.) from planetary positions
2. **Chain Evaluation (Layer 1.5):** Computes dispositorship chain impact on yoga strength
3. **Modifier Pipeline (Layer 2):** Applies 5-tier affliction checks (combustion, debilitation, planetary war, retrograde, node influence)
4. **Temporal Evaluation (Layer 3):** Combines Vimshottari Dasha activation with real Ashtakavarga transit bindus
5. **Varga Confirmation (Layer 4):** Validates yoga strength through D9 (Navamsha) confirmation

### Empirical Validation (HOLDOUT)

| Metric | Value |
|--------|-------|
| **Precision** | 82.6% |
| **Recall** | 73.1% |
| **F1 Score** | 0.776 |
| **Hit Rate** | 63.3% (95% CI: 46.1%–80.6%) |

---

## ⚠️ Legal & Computational Disclaimer

> **DISCLAIMER:** This output is a computational interpretation based on classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided for informational and research purposes only. It does not constitute medical, financial, legal, or guaranteed predictive advice.

All API responses and generated reports include this disclaimer. By using this API, you acknowledge that the output is a deterministic computational model, not a prediction service.

---

## API Authentication

All `/api/v1/` endpoints (except `/health`) require an API key via the `X-API-Key` header.

### Your Beta API Keys

| Key | Name | Tier |
|-----|------|------|
| `jre-beta-key-alpha` | Beta Tester A | Standard |
| `jre-beta-key-beta` | Beta Tester B | Standard |
| `jre-beta-key-gamma` | Beta Tester C | Standard |

### Rate Limits

- **10 requests per minute** per API key
- Exceeding the limit returns HTTP 429 with `Retry-After` header
- Rate limits reset automatically after the sliding window expires

### Authentication Example

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

---

## Known Limitations

We transparently document these so beta testers can set appropriate expectations:

### 1. HEALTH Domain False Positives (16 of 24 FPs)
Career-relevant yogas (Raja, Gajakesari) sometimes activate during death/health events due to Dasha coincidence. This is neutral behavior, not a false prediction — classical death timing requires Maraka Dasha analysis (not yet implemented).

### 2. Strict Dasha Activation
A yoga is only "activated" when the Mahadasha/Antardasha/Pratyantardasha lord IS one of the yoga's involved planets. This is strict — the engine doesn't consider dispositorship or aspect relationships for Dasha matching.

### 3. Missing Advanced Yogas
Some charts have zero yogas detected because their planetary configurations don't match any currently implemented yoga patterns. Additional detectors are needed.

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

# Build and start the staging API server
docker-compose -f docker-compose.staging.yml up --build

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

---

## API Endpoints

### Health Check (No Auth Required)
```bash
curl http://localhost:8000/api/v1/health
# {"status": "healthy", "version": "1.0.0"}
```

### List Available Charts
```bash
curl http://localhost:8000/api/v1/fixtures \
  -H "X-API-Key: jre-beta-key-alpha"
# {"count": 50, "fixtures": ["chart_001_pilot", "chart_002_curie", ...]}
```

### Evaluate a Pre-computed Chart
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

### Evaluate Custom Birth Data
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/custom \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
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
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}'

# HTML format
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=html" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

---

## Submitting Structured Feedback

We use a **structured feedback taxonomy** to enable systematic analysis. Each feedback submission must include:

### FeedbackEntry Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evaluation_id` | string | ✅ | The `evaluation_id` from the API response |
| `expert_id` | string | ✅ | Your anonymized ID (e.g., "EXPERT_A") |
| `domain` | string | ✅ | Event domain (CAREER, HEALTH, MARRIAGE, etc.) |
| `expert_agreement` | bool | — | You agree with the engine's assessment |
| `expert_disagreement` | bool | — | You disagree with the engine's assessment |
| `missing_yoga` | bool | — | A yoga should have been detected but wasn't |
| `false_positive` | bool | — | Engine detected a yoga that shouldn't exist |
| `false_negative` | bool | — | Engine missed a yoga that should have been activated |
| `timing_issue` | bool | — | Dasha activation timing is incorrect |
| `interpretation_issue` | bool | — | Classical interpretation is wrong |
| `astronomical_issue` | bool | — | Underlying astronomical calculation is wrong |
| `other` | bool | — | Other issue |
| `free_text` | string | — | Optional detailed notes |

### Feedback Submission Example

```bash
# First, get the evaluation_id from the API response
EVAL_ID=$(curl -s -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}' | jq -r '.evaluation_id')

# Then submit feedback
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d "{
    \"evaluation_id\": \"$EVAL_ID\",
    \"expert_id\": \"EXPERT_A\",
    \"domain\": \"CAREER\",
    \"expert_agreement\": true,
    \"missing_yoga\": false,
    \"false_positive\": false,
    \"false_negative\": false,
    \"timing_issue\": false,
    \"interpretation_issue\": false,
    \"astronomical_issue\": false,
    \"other\": false,
    \"free_text\": \"Raja yoga activation during JUPITER MD aligns well with the career peak.\"
  }"
```

### Feedback Guidelines

1. **Always include `evaluation_id`** — This ties your feedback to the exact engine output for reproducibility.
2. **Use your `expert_id`** — Consistent IDs allow us to track inter-rater reliability.
3. **Set only relevant flags** — Multiple flags can be true if applicable.
4. **Be specific in `free_text`** — The more detail, the better for post-analysis.

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

### Evaluation ID
Every API response includes a deterministic `evaluation_id` — a SHA-256 hash of the fixture ID and engine version. This allows exact reproducibility: the same input will always produce the same `evaluation_id`.

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
- **Evaluation ID:** Include this in any support request for exact reproducibility
