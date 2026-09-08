# JRE v1.0.0-beta — Controlled Beta Distribution Package

**Version:** v1.0.0-beta (Engine Frozen)
**Date:** September 2026
**Classification:** Internal Beta — External Expert Distribution

---

## 1. System Overview

The **Jyotish Reasoning Engine (JRE)** is a deterministic, rule-based system for evaluating classical Jyotish yogas from birth data. It implements a **5-layer computational pipeline** grounded in authoritative Sanskrit texts (Brihat Parashara Hora Shastra, Phaladeepika, Saravali).

### Current Validation Status

| Metric | Value |
|--------|-------|
| **Precision (Holdout)** | 82.6% |
| **Recall (Holdout)** | 73.1% |
| **F1 Score (Holdout)** | 0.776 |
| **Charts Validated** | 50+ historical fixtures |
| **Events Validated** | 150+ real-world events |
| **Engine Version** | v1.0.0-beta (frozen) |

### What This Beta Tests

We need domain experts to evaluate whether the engine's outputs are:

1. **Astronomically correct** — Planetary positions, Lagna, Nakshatra, Dasha periods
2. **Classically sound** — Yoga formations follow BPHS/Phaladeepika rules accurately
3. **Temporally aligned** — Dasha activation timing matches real-life event windows
4. **Domain-appropriate** — Yoga interpretations match the correct life domain

---

## 2. Access Instructions

### Web Interface (UI)

| Component | URL |
|-----------|-----|
| **Dashboard** | http://localhost:3000/dashboard |
| **Birth Chart Viewer** | http://localhost:3000/chart |
| **Report Viewer** | http://localhost:3000/report |
| **Evaluate (Custom Birth Data)** | http://localhost:3000/evaluate |
| **Evaluate (Historical Fixtures)** | http://localhost:3000/evaluate/fixture |
| **Transits & Dasha Timeline** | http://localhost:3000/transits |
| **Compatibility Check** | http://localhost:3000/compatibility |
| **Submit Feedback** | http://localhost:3000/feedback |

### API Access

| Endpoint | URL |
|----------|-----|
| **API Base** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/api/v1/health |

**API Key:** `jre-beta-key-alpha`

All API requests require the header:
```
X-API-Key: jre-beta-key-alpha
```

### Quick API Example (curl)

```bash
# Evaluate custom birth data
curl -X POST http://localhost:8000/api/v1/evaluate/custom \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{
    "date": "1987-06-10",
    "time": "08:11",
    "latitude": 25.6747,
    "longitude": 93.9722,
    "timezone": "Asia/Kolkata"
  }'

# List available fixtures
curl http://localhost:8000/api/v1/fixtures \
  -H "X-API-Key: jre-beta-key-alpha"

# Evaluate a fixture
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

---

## 3. The Golden Governance Rule

> **Individual feedback will NOT change the live v1.0.0-beta engine.**

All feedback populates the **Evidence Dataset** for the future **v1.1.0-dev** branch. This is a scientific governance model:

1. **Expert submits feedback** → Logged to `data/feedback_log.jsonl`
2. **Automated aggregation** → `scripts/generate_beta_summary.py` produces analysis reports
3. **Evidence review** → Feedback patterns are analyzed across all testers
4. **Research proposals** → Formal proposals (RI-XXX) are written for engine changes
5. **Implementation** → Approved changes are implemented in v1.1.0-dev branch
6. **Validation** → Changes must pass the full 70-chart regression corpus

**Why this matters:** Individual corrections may seem obvious in isolation, but could introduce regressions elsewhere. The Evidence Dataset ensures we make informed, systemic improvements.

---

## 4. Known Limitations

### Current Constraints (v1.0.0-beta)

| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| **Unknown Time of Birth** | Lagna-dependent yogas are suspended; Moon-based yogas only | Dasha-Lagna estimation in v1.1.0-dev |
| **Health Domain Coverage** | Limited Arishta/Maraka yoga detection | Expanded health yoga module in v1.1.0-dev |
| **Single-Division Validation** | D9 Navamsha confirmation only | D10, D7, D12 varga confirmation in v1.1.0-dev |
| **No Live Dasha Feed** | Vimshottari Dasha computed from natal positions only | Transit-linked Dasha refinement in v1.1.0-dev |
| **Western Charts** | Not supported in this beta | Western astrology module planned for v1.2.0-dev |

### What Works Well

- ✅ Gajakesari, Raja, Dhana, Pancha Mahapurusha yoga detection
- ✅ Chandra yogas (Sunapha, Anapha, Dhudhara)
- ✅ Budhaditya, Saraswati, Amala yogas
- ✅ Vipareeta Raja yoga with classical exclusions
- ✅ 5-tier modifier pipeline (combustion, debilitation, war, retrograde, nodes)
- ✅ Chain strength / dispositorship network analysis
- ✅ Ashtakavarga transit scoring
- ✅ PDF report generation (9-step comprehensive format)
- ✅ Interactive web UI with chart visualization

---

## 5. How to Submit Feedback

### Option A: Web UI (Recommended)

1. Navigate to http://localhost:3000/feedback
2. Select the evaluation ID you're reviewing
3. Fill in the structured feedback form (see [BETA_FEEDBACK_FORM.md](BETA_FEEDBACK_FORM.md))
4. Submit

### Option B: API (for batch submissions)

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '{
    "evaluation_id": "<id-from-evaluation>",
    "expert_id": "EXPERT_A",
    "domain": "CAREER",
    "expert_agreement": false,
    "expert_disagreement": true,
    "missing_yoga": false,
    "false_positive": true,
    "false_negative": false,
    "timing_issue": false,
    "interpretation_issue": true,
    "astronomical_issue": false,
    "other": false,
    "free_text": "Adhi Yoga detected but not present in classical chart."
  }'
```

### Option C: Direct File Append

Append a JSON line to `data/feedback_log.jsonl`:
```json
{"evaluation_id":"abc123","expert_id":"EXPERT_A","domain":"CAREER","expert_agreement":false,"expert_disagreement":true,"missing_yoga":false,"false_positive":true,"false_negative":false,"timing_issue":false,"interpretation_issue":true,"astronomical_issue":false,"other":false,"free_text":"...","timestamp":"2026-09-01T00:00:00Z","engine_version":"1.0.0-beta"}
```

---

## 6. Evaluation Workflow

### Recommended Process

1. **Start with the Evaluate page** — Enter a known chart (birth data you're familiar with)
2. **Check the Chart page** — Verify planetary positions and house placements
3. **Review the Report** — Toggle between Layman and Expert modes
4. **Check Transits** — Verify Dasha timeline and current transit positions
5. **Submit feedback** — Use the structured form for each observation

### Test Charts

| Chart | Birth Data | Notes |
|-------|-----------|-------|
| **Changtongya** | 1987-06-10, 08:11 IST, Nagaland | Known career events for validation |
| **Pilot Chart** | Use fixture `chart_001_pilot` | Pre-validated reference chart |
| **Custom** | Enter your own test cases | Compare with manual calculations |

---

## 7. Privacy & Disclaimer

### Data Privacy

- Birth data submitted through the API is processed in-memory and not stored permanently
- Feedback data is stored locally in `data/feedback_log.jsonl` on the host machine
- No data is transmitted to external servers
- All evaluation IDs are deterministic hashes (no PII)

### Legal Disclaimer

> This output is a computational interpretation based on classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided for informational and research purposes only. It does not constitute medical, financial, legal, or guaranteed predictive advice.

---

## 8. Document Index

| Document | Purpose |
|----------|---------|
| [BETA_DISTRIBUTION_PACKAGE.md](BETA_DISTRIBUTION_PACKAGE.md) | This document — distribution overview |
| [BETA_FEEDBACK_FORM.md](BETA_FEEDBACK_FORM.md) | Structured feedback template for experts |
| [BETA_EVALUATION_PROTOCOL.md](BETA_EVALUATION_PROTOCOL.md) | Detailed evaluation methodology |
| [BETA_ONBOARDING.md](BETA_ONBOARDING.md) | Technical setup and onboarding guide |
| [BETA_QUICK_REF.md](BETA_QUICK_REF.md) | Quick reference card |
| [BETA_TESTER_GUIDE.md](BETA_TESTER_GUIDE.md) | Comprehensive tester guide |
| [FEEDBACK_EXAMPLES.md](FEEDBACK_EXAMPLES.md) | Example feedback submissions |

---

## 9. Contact & Support

For technical issues (server not starting, API errors):
- Check the server logs in the terminal where you started the backend
- Verify the health endpoint: `curl http://localhost:8000/api/v1/health`

For evaluation methodology questions:
- Refer to [BETA_EVALUATION_PROTOCOL.md](BETA_EVALUATION_PROTOCOL.md)
- Consult classical texts: BPHS, Phaladeepika, Saravali

---

*Generated: September 2026 · JRE v1.0.0-beta*
