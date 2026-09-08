# JRE Beta Tester Onboarding Guide

**Version:** v1.0.0-beta | **Date:** August 2026

---

## 1. Welcome & Purpose

Welcome to the **Jyotish Reasoning Engine (JRE) Beta Testing Program**.

> **System Status:** This is a **technically production-ready beta platform with preliminary empirical validation**. The reasoning engine is frozen at v1.0.0-beta. No reasoning logic changes will be made during the beta period.

### What Is the JRE?

The JRE is a deterministic, rule-based system for evaluating classical Jyotish yogas from birth data. It implements a **5-layer reasoning pipeline** based on authoritative Sanskrit texts (Brihat Parashara Hora Shastra, Phaladeepika, Saravali):

| Layer | Function |
|-------|----------|
| **Layer 1** | Structural Detection — Identifies classical yoga formations from planetary positions |
| **Layer 1.5** | Chain Evaluator — Computes multi-hop dispositorship impact on yoga strength |
| **Layer 2** | Modifier Pipeline — 5-tier affliction checks (combustion, debilitation, war, retrograde, nodes) |
| **Layer 3** | Temporal Evaluation — Vimshottari Dasha activation + Ashtakavarga transit bindus |
| **Layer 4** | Varga Confirmation — D9 (Navamsha) validation |

### What We're Testing

We need domain experts to evaluate whether the engine's outputs are:

1. **Astronomically correct** — Planetary positions, Lagna, Nakshatra, Dasha periods
2. **Classically sound** — Yoga formations follow BPHS/Phaladeepika rules accurately
3. **Temporally aligned** — Dasha activation timing matches real-life event windows
4. **Domain-appropriate** — Yoga interpretations match the correct life domain

### What We Need From You

**Structured, scientifically useful feedback** on accuracy, classical alignment, and usability. Every piece of feedback helps us improve the engine's predictive capability.

### ⚠️ Golden Governance Rule

> Your feedback populates the **Evidence Dataset** for v1.1.0-dev research proposals. No live rules will be changed based on individual requests. All feedback is systematically analyzed and routed through the formal research proposal process.

### 📋 Evaluation Protocol

Before submitting feedback, please read the **[Beta Evaluation Protocol](BETA_EVALUATION_PROTOCOL.md)** — it provides the structured taxonomy (CE/RE/MC/DE/NE) and standardized feedback forms required for all submissions.

---

## 2. Quick Start (5-Minute Setup)

### Option A: Docker (Recommended)

```bash
# 1. Clone the repository
git clone [repo-url]
cd JRE

# 2. Start the staging environment
docker-compose -f docker-compose.staging.yml up -d

# 3. Verify it's running
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

### Option B: Local Python

```bash
# 1. Clone and set up
git clone [repo-url]
cd JRE
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install fastapi uvicorn httpx

# 2. Start the server
uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000

# 3. Verify (in another terminal)
curl http://localhost:8000/api/v1/health
```

### Verify API Access

```bash
curl -H "X-API-Key: jre-beta-key-alpha" http://localhost:8000/api/v1/fixtures | head -5
# Expected: {"count":50,"fixtures":["chart_001_pilot",...]}
```

---

## 3. API Access

| Item | Value |
|------|-------|
| **Base URL** | `http://localhost:8000` |
| **Swagger UI** | `http://localhost:8000/docs` |
| **API Docs** | `http://localhost:8000/redoc` |

### Your API Keys

| Key | Tester | 
|-----|--------|
| `jre-beta-key-alpha` | Tester A |
| `jre-beta-key-beta` | Tester B |
| `jre-beta-key-gamma` | Tester C |

### Rate Limits

- **10 requests per minute** per API key
- Exceeding the limit returns HTTP 429 with `Retry-After` header
- Limits reset automatically after 60 seconds

### Authentication

All endpoints (except `/health`) require the `X-API-Key` header:

```bash
curl -H "X-API-Key: jre-beta-key-alpha" http://localhost:8000/api/v1/fixtures
```

---

## 4. Core Endpoints

### 4.1 Evaluate a Pre-Computed Chart

Run the full evaluation pipeline on a historical chart fixture:

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "X-API-Key: [YOUR_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

**Response includes:**
- `evaluation_id` — Unique identifier for this evaluation (for feedback)
- `yogas` — Array of detected yogas with status, strength, and timing
- `engine_version` — Engine version used
- `disclaimer` — Legal disclaimer

### 4.2 Evaluate Custom Birth Data

Evaluate any birth data (not in the fixture database):

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/custom \
  -H "X-API-Key: [YOUR_KEY]" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "1988-11-05",
    "time": "17:20",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata"
  }'
```

### 4.3 Generate Human-Readable Report

Get a formatted Markdown or HTML report:

```bash
# Markdown
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=markdown" \
  -H "X-API-Key: [YOUR_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_051_kohli"}'

# HTML
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=html" \
  -H "X-API-Key: [YOUR_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_051_kohli"}'
```

### 4.4 List Available Charts

See all 50+ fixtures in the validation database:

```bash
curl -H "X-API-Key: [YOUR_KEY]" http://localhost:8000/api/v1/fixtures
```

---

## 5. Structured Feedback Protocol

### Why Structured Feedback?

Your feedback is the primary data source for improving the engine. Structured taxonomy flags enable systematic analysis across multiple dimensions — we can identify patterns (e.g., "80% of HEALTH domain feedback flags timing issues") that would be impossible with free-text alone.

### The Feedback Schema

```json
POST /api/v1/feedback
{
  "evaluation_id": "[from evaluation response]",
  "expert_id": "YOUR_INITIALS",
  "domain": "CAREER|WEALTH|HEALTH|MARRIAGE|ARTISTIC|EDUCATION|OTHER",

  "expert_agreement": true/false,
  "expert_disagreement": true/false,
  "missing_yoga": true/false,
  "false_positive": true/false,
  "false_negative": true/false,
  "timing_issue": true/false,
  "interpretation_issue": true/false,
  "astronomical_issue": true/false,
  "other": true/false,

  "free_text": "Detailed explanation of your assessment..."
}
```

### Field Definitions

| Field | When to Set True |
|-------|-----------------|
| `expert_agreement` | You agree with the engine's overall assessment |
| `expert_disagreement` | You disagree with the engine's overall assessment |
| `missing_yoga` | A classical yoga should have been detected but wasn't |
| `false_positive` | Engine detected a yoga that shouldn't exist or is irrelevant |
| `false_negative` | Engine missed a yoga that should have been activated |
| `timing_issue` | Dasha activation timing is incorrect for this event |
| `interpretation_issue` | Classical interpretation of the yoga is wrong |
| `astronomical_issue` | Underlying astronomical calculation is wrong (positions, Dasha) |
| `other` | Issue not covered by the above categories |

### How to Submit Feedback

1. **Evaluate a chart** using `/api/v1/evaluate/fixture` or `/api/v1/evaluate/custom`
2. **Copy the `evaluation_id`** from the response
3. **Review the output** against your domain expertise
4. **Submit feedback** using the schema above
5. **Include `evaluation_id`** — this ties your feedback to the exact engine output

---

## 6. Example Workflow: Virat Kohli

Let's walk through a complete evaluation and feedback cycle.

### Step 1: Evaluate the Chart

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "X-API-Key: jre-beta-key-alpha" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_051_kohli"}'
```

### Step 2: Get the Human-Readable Report

```bash
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=markdown" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_051_kohli"}'
```

The report shows:
- **Raja Yoga** — Active (SATURN, JUPITER), Dynamic Strength: 1.50
- **Malavya Yoga** — Active (VENUS), Dynamic Strength: 0.92
- Dasha alignment with Jupiter MD

### Step 3: Review Against Domain Knowledge

For Kohli's 2018 Peak Ranking:
- Raja Yoga (Kendra-Trikona connection) is classically appropriate for career peaks
- Jupiter MD + Venus AD aligns with the event timeframe
- The engine's prediction appears accurate

### Step 4: Submit Feedback

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "X-API-Key: jre-beta-key-alpha" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "[from step 1 response]",
    "expert_id": "EXPERT_A",
    "domain": "CAREER",
    "expert_agreement": true,
    "expert_disagreement": false,
    "missing_yoga": false,
    "false_positive": false,
    "false_negative": false,
    "timing_issue": false,
    "interpretation_issue": false,
    "astronomical_issue": false,
    "other": false,
    "free_text": "Raja Yoga activation during 2018 peak is classically sound. Jupiter MD alignment correct."
  }'
```

---

## 7. What to Look For

### Astronomical Issues
- Incorrect planetary positions (longitude, retrograde status)
- Wrong Lagna (Ascendant) or Nakshatra
- Incorrect Dasha period calculation
- Wrong house assignments

### Formation Issues
- Yoga should form but doesn't (missing detection)
- Yoga detected that shouldn't exist (false positive)
- Incorrect status (FORMED vs WEAKENED vs CANCELLED)

### Timing Issues
- Dasha activation timing seems wrong for the event
- MD/AD/PD lords don't match expected period
- Activation multiplier seems too high or too low

### Domain Issues
- Yoga activated for wrong life domain
- Career yoga firing during health event
- Wealth yoga misinterpreted as career yoga

### Missing Yogas
- Classical yoga not detected (e.g., Saraswati, Gajakesari)
- Pancha Mahapurusha yoga missing from formation
- Neecha Bhanga not recognized

### Modifier Issues
- Combustion detected incorrectly
- Debilitation cancellation missed
- Retrograde status wrong

---

## 8. Support & Communication

| Channel | Details |
|---------|---------|
| **GitHub Issues** | [repo-url]/issues — For bugs, feature requests, technical questions |
| **Email** | [your-email] — For private feedback or sensitive findings |
| **Response Time** | Within 48 hours for all inquiries |

### What to Include in Bug Reports

1. **`evaluation_id`** from the API response
2. **Expected behavior** — What should the engine have done?
3. **Actual behavior** — What did it actually do?
4. **Steps to reproduce** — API call used
5. **Your expertise** — Brief note on your background (optional but helpful)

---

## Appendix: Available Chart Fixtures

The validation database contains 50+ historical charts across multiple eras and domains:

| Category | Example Subjects |
|----------|-----------------|
| **Historical Leaders** | Lincoln, Churchill, Mandela, Gandhi, de Gaulle |
| **Scientists** | Einstein, Curie, Newton, Darwin, Tesla |
| **Artists** | Mozart, Beethoven, Picasso, van Gogh |
| **Modern Personalities** | Kohli, Williams, Musk, Ambani, Modi |
| **Writers** | Tolstoy, Rowling, Roy, Chekhov |

Use `/api/v1/fixtures` to see the complete list.

---

*This onboarding guide is part of the JRE v1.0.0-beta beta testing program. Engine is frozen — no reasoning logic changes will be made during the beta period.*
