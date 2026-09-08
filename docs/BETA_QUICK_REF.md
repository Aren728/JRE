# JRE Beta Quick Reference Card

**v1.0.0-beta** | Keep this handy while testing

> **System Status:** Technically production-ready beta platform with preliminary empirical validation.
> **Governance:** Feedback populates the Evidence Dataset — no live rules changed based on individual requests.
> **Protocol:** See [BETA_EVALUATION_PROTOCOL.md](BETA_EVALUATION_PROTOCOL.md) for the structured feedback taxonomy (CE/RE/MC/DE/NE).

---

## Connection

| Item | Value |
|------|-------|
| **Base URL** | `http://localhost:8000` |
| **Swagger UI** | `http://localhost:8000/docs` |
| **Health Check** | `GET /api/v1/health` (no auth needed) |
| **Rate Limit** | 10 requests/minute per key |

## Your API Key

```
X-API-Key: jre-beta-key-alpha    (Tester A)
X-API-Key: jre-beta-key-beta     (Tester B)
X-API-Key: jre-beta-key-gamma    (Tester C)
```

---

## 3 Core Endpoints

### 1. Evaluate a Chart

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

### 2. Evaluate Custom Birth Data

```bash
curl -X POST http://localhost:8000/api/v1/evaluate/custom \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "1988-11-05",
    "time": "17:20",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata"
  }'
```

### 3. Generate Report

```bash
curl -X POST "http://localhost:8000/api/v1/report/fixture?format=markdown" \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_051_kohli"}'
```

---

## Feedback Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "FROM_EVAL_RESPONSE",
    "expert_id": "YOUR_INITIALS",
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
    "free_text": "Your detailed assessment..."
  }'
```

---

## Feedback Flags

| Flag | Meaning |
|------|---------|
| `expert_agreement` | Engine got it right |
| `expert_disagreement` | Engine got it wrong |
| `missing_yoga` | Classical yoga not detected |
| `false_positive` | Yoga detected that shouldn't exist |
| `false_negative` | Yoga missed |
| `timing_issue` | Dasha timing wrong |
| `interpretation_issue` | Classical interpretation wrong |
| `astronomical_issue` | Calculation error |
| `other` | Something else |

---

## List Available Charts

```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/v1/fixtures
```

---

## Workflow

1. **Evaluate** → Get `evaluation_id` from response
2. **Review** → Check yogas, timing, strength against your expertise
3. **Feedback** → Submit structured feedback with `evaluation_id`

---

## Need Help?

- **Full Guide:** [BETA_ONBOARDING.md](BETA_ONBOARDING.md)
- **Evaluation Protocol:** [BETA_EVALUATION_PROTOCOL.md](BETA_EVALUATION_PROTOCOL.md)
- **Examples:** [FEEDBACK_EXAMPLES.md](FEEDBACK_EXAMPLES.md)
- **Detailed Docs:** [BETA_TESTER_GUIDE.md](BETA_TESTER_GUIDE.md)
- **Swagger UI:** http://localhost:8000/docs

---

*JRE v1.0.0-beta — Engine frozen. No reasoning logic changes during beta.*
