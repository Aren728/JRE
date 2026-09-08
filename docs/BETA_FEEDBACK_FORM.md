# JRE v1.0.0-beta — Expert Feedback Form

**Purpose:** Structured feedback collection for domain expert evaluation of JRE yoga detection accuracy.

**How to use:** Copy this template for each observation. Fill in all required fields. Submit via the Web UI, API, or append directly to `data/feedback_log.jsonl`.

---

## Feedback Entry Template

```json
{
  "evaluation_id": "<string: ID from the evaluation response>",
  "expert_id": "<string: Your anonymized identifier, e.g. EXPERT_A>",
  "domain": "<string: CAREER | HEALTH | MARRIAGE | WEALTH | EDUCATION | SPIRITUAL | GENERAL>",
  "expert_agreement": "<boolean: true if you agree with the overall assessment>",
  "expert_disagreement": "<boolean: true if you disagree with the overall assessment>",
  "missing_yoga": "<boolean: true if a classical yoga should have been detected but wasn't>",
  "false_positive": "<boolean: true if the engine detected a yoga that shouldn't exist>",
  "false_negative": "<boolean: true if the engine missed a yoga that should have been activated>",
  "timing_issue": "<boolean: true if Dasha activation timing is incorrect>",
  "interpretation_issue": "<boolean: true if the classical interpretation is wrong>",
  "astronomical_issue": "<boolean: true if the underlying astronomical calculation is wrong>",
  "other": "<boolean: true if the issue doesn't fit the above categories>",
  "free_text": "<string: Detailed notes, classical citations, and evidence>"
}
```

---

## Field Definitions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `evaluation_id` | string | The evaluation ID from the API response (e.g., `a1b2c3d4e5f6g7h8`) |
| `expert_id` | string | Your anonymized identifier. Use the same ID across all submissions. |
| `domain` | string | The life domain this feedback pertains to (see Domain Taxonomy below) |

### Boolean Flags (at least one should be true)

| Flag | When to Use |
|------|-------------|
| `expert_agreement` | You agree with the engine's overall yoga assessment for this chart |
| `expert_disagreement` | You disagree with the engine's overall yoga assessment |
| `missing_yoga` | A classical yoga should have been detected but the engine missed it |
| `false_positive` | The engine detected a yoga that should NOT exist per classical rules |
| `false_negative` | The engine missed a yoga that SHOULD have been detected |
| `timing_issue` | The Dasha/Transit temporal activation timing is incorrect |
| `interpretation_issue` | The yoga interpretation text is ambiguous, inaccurate, or misleading |
| `astronomical_issue` | The underlying planetary positions, degrees, or astronomical data are wrong |
| `other` | Issue doesn't fit the above categories — explain in `free_text` |

### Free Text

Provide detailed notes including:
- What you observed
- What the correct result should be (with classical citation if possible)
- The specific chart and yoga involved
- Any supporting evidence from BPHS, Phaladeepika, Saravali, or other classical texts

---

## 5-Category Taxonomy (CE/RE/MC/DE/NE)

Use this taxonomy in your `free_text` to categorize the specific error type:

### CE — Calculation Error
An astronomical fact is wrong. The underlying calculation produces incorrect data.

**Examples:**
- "Sun longitude shows 15° Aries but Swiss Ephemeris shows 16.2°"
- "Moon Nakshatra displayed as Rohini but actual Nakshatra is Mrigashira"
- "Dasha start date is off by 3 years from manual calculation"

**Evidence needed:** Reference Swiss Ephemeris, manual calculation, or authoritative source.

---

### RE — Reasoning Error
A classical rule is misapplied. The input data is correct, but the yoga formation logic is wrong.

**Examples:**
- "Gajakesari detected when Jupiter is NOT in Kendra from Moon (3 houses apart, not 4)"
- "Raja Yoga flagged but Kendra lord is NOT conjunct Trikona lord — they're in different houses"
- "Vipareeta Raja Yoga incorrectly formed — planet owns both Kendra and Trikona (excluded per BPHS Ch. 42)"

**Evidence needed:** Cite the specific classical rule and explain the misapplication.

---

### MC — Missing Coverage
The engine lacks a classical rule that should be implemented.

**Examples:**
- "Neecha Bhanga not detected when Saturn (debilitated in Aries) has Mars in Kendra"
- "Chamara Yoga not implemented — Saturn in 10th from Lagna with Venus in 4th"
- "No Arishta Dosha detection for Saturn-Mars conjunction in 8th house"

**Evidence needed:** Name the yoga, cite the classical source, provide the formation conditions.

---

### DE — DDE/Token Error
The deterministic dynamic evaluation (DDE) threshold routing is wrong. A yoga's status (FORMED/WEAKENED/CANCELLED) is incorrect.

**Examples:**
- "Adhi Yoga shows CANCELLED but should be FORMED — 3 benefics in 6th/7th/8th from Moon"
- "Malavya shown as WEAKENED but Venus is in own sign (Tula) in Kendra — should be FORMED"
- "Dynamic strength shows 1.0000 for a CANCELLED yoga — should be 0.0000"

**Evidence needed:** Specify the correct status and the reason the current status is wrong.

---

### NE — Narrative/Token Error
The interpretation text is ambiguous, inaccurate, or doesn't match the classical meaning.

**Examples:**
- "Gajakesari interpretation says 'wealth and reputation' but classical meaning is 'wisdom and learning'"
- "House 7 interpretation mentions 'partnership' but should specifically address 'spouse and marriage'"
- "Remedy suggests wearing pearl but Moon is debilitated — should suggest mantra instead"

**Evidence needed:** Provide the correct interpretation with classical source.

---

## Domain Taxonomy

| Domain | Code | Description |
|--------|------|-------------|
| Career & Status | `CAREER` | Professional life, promotions, recognition, authority |
| Wealth & Finance | `WEALTH` | Income, savings, investments, financial events |
| Health & Wellness | `HEALTH` | Physical health, medical events, recovery |
| Marriage & Relationships | `MARRIAGE` | Spouse, partnerships, romantic relationships |
| Education & Learning | `EDUCATION` | Academic achievement, knowledge, skills |
| Spiritual Growth | `SPIRITUAL` | Spiritual development, meditation, dharma |
| Children & Family | `FAMILY` | Children, family dynamics, inheritance |
| General Life | `GENERAL` | Overall life trajectory, personality |

---

## Severity Scale

| Level | Label | Description |
|-------|-------|-------------|
| **P0** | Critical | Astronomically wrong or major classical rule violation |
| **P1** | High | Incorrect yoga detection or significant reasoning error |
| **P2** | Medium | Minor interpretation issue or edge case missed |
| **P3** | Low | Cosmetic, wording, or minor timing discrepancy |

---

## Example Submissions

### Example 1: False Positive (P1)

```json
{
  "evaluation_id": "a1b2c3d4e5f6g7h8",
  "expert_id": "EXPERT_A",
  "domain": "CAREER",
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": false,
  "false_positive": true,
  "false_negative": false,
  "timing_issue": false,
  "interpretation_issue": false,
  "astronomical_issue": false,
  "other": false,
  "free_text": "CE/RE: Adhi Yoga detected but not present. Mercury is in 5th house, not 6th/7th/8th from Lagna or Moon. Jupiter is in 2nd house. Only Venus qualifies (in 7th). Engine requires 2+ benefics — only 1 is present. BPHS Ch. 40 requires minimum 2 benefics."
}
```

### Example 2: Missing Coverage (P2)

```json
{
  "evaluation_id": "x9y8z7w6v5u4t3s2",
  "expert_id": "EXPERT_B",
  "domain": "HEALTH",
  "expert_agreement": false,
  "expert_disagreement": false,
  "missing_yoga": true,
  "false_positive": false,
  "false_negative": false,
  "timing_issue": false,
  "interpretation_issue": false,
  "astronomical_issue": false,
  "other": false,
  "free_text": "MC: No Maraka Dosha detected. Saturn and Mars are conjunct in the 8th house, and Saturn also aspects the 2nd house (Maraka sthana). This should trigger Maraka Dosha per BPHS Ch. 45. Saturn's Dasha period is active, making this timing-relevant."
}
```

### Example 3: Timing Issue (P1)

```json
{
  "evaluation_id": "m3n4o5p6q7r8s9t0",
  "expert_id": "EXPERT_C",
  "domain": "CAREER",
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": false,
  "false_positive": false,
  "false_negative": false,
  "timing_issue": true,
  "interpretation_issue": false,
  "astronomical_issue": false,
  "other": false,
  "free_text": "DE: Raja Yoga is correctly detected but temporal activation shows Dasha multiplier of 1.2 (active) when the native actually experienced the career event during Saturn MD / Jupiter AD. Jupiter is not the current Dasha lord. Manual Vimshottari calculation confirms Saturn MD 2015-2034, Jupiter AD 2021-2023. The event occurred in 2022."
}
```

---

## Submission Checklist

Before submitting, verify:

- [ ] `evaluation_id` matches the chart you're reviewing
- [ ] `expert_id` is consistent across all your submissions
- [ ] At least one boolean flag is set to `true`
- [ ] `free_text` includes the taxonomy code (CE/RE/MC/DE/NE)
- [ ] `free_text` cites classical sources where applicable
- [ ] Domain is correctly categorized
- [ ] Severity is appropriate for the issue type

---

## Submitting

### Via Web UI
Navigate to http://localhost:3000/feedback and fill in the form.

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: jre-beta-key-alpha" \
  -d '<your JSON entry>'
```

### Via File
Append a single JSON line to `data/feedback_log.jsonl`.

---

*JRE v1.0.0-beta · September 2026*
