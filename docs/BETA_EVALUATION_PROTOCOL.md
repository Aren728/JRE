# JRE Beta Evaluation Protocol

**Version:** v1.0.0-beta | **Date:** August 2026
**Status:** Active — Required for all beta testers

---

## 1. Purpose

This protocol provides domain experts (professional Vedic astrologers, wellness-tech developers, or Jyotish researchers) with a **rigorous, categorized feedback mechanism** for evaluating the Jyotish Reasoning Engine (JRE).

**Your role:** You are not simply "reviewing output." You are providing scientifically structured evidence that will directly inform the v1.1.0-dev research proposals. Every piece of categorized feedback becomes a data point in the Evidence Dataset.

---

## 2. System Overview

The JRE is a **technically production-ready beta platform with preliminary empirical validation**. It processes:

```
Birth Data → Astronomical Facts → JRE Reasoning (Yogas) → Modifiers →
Temporal Evaluation → Varga Confirmation → DDE (Esoteric Profile) → Token Generation → Report
```

Each layer is independently testable. Your feedback should identify **which layer** produced the error.

---

## 3. Feedback Taxonomy

Every feedback entry must be classified into **exactly one primary category**. This is not optional — unclassified feedback cannot be systematically analyzed.

### Category 1: Calculation Error (CE)

**Definition:** The astronomical fact is wrong. The engine computed an incorrect planetary position, Lagna, Nakshatra, Dasha period, or house assignment.

**When to use:**
- Wrong Lagna (Ascendant) for a known birth time
- Incorrect planetary longitude (e.g., Moon at wrong degree)
- Wrong Nakshatra or Pada assignment
- Incorrect Dasha period calculation
- Wrong house assignment for a planet
- Retrograde status computed incorrectly

**Required evidence:**
- What the engine produced (with `evaluation_id`)
- What the correct value should be (with source, e.g., "Drik Panchang 2024" or "Lahiri ayanamsa ephemeris")
- The exact birth data used

**Example:**
```json
{
  "category": "CE",
  "evaluation_id": "abc123...",
  "chart_id": "chart_001_pilot",
  "description": "Moon Nakshatra computed as Jyeshta, should be Anuradha",
  "engine_output": "Moon at 23°45' Scorpio = Jyeshta",
  "correct_value": "Moon at 21°30' Scorpio = Anuradha (Drik Panchang verified)",
  "source": "Drik Panchang 2024, Lahiri ayanamsa"
}
```

### Category 2: Reasoning Error (RE)

**Definition:** The JRE applied the wrong classical rule. A yoga should or should not have formed based on correct astronomical facts, but the engine misapplied the logic.

**When to use:**
- Yoga detected that violates BPHS/Phaladeepika conditions
- Correct planetary positions but wrong yoga classification
- Modifier pipeline applied incorrectly (e.g., combustion detected when planet is >8° from Sun)
- Chain impact (dispositorship) computed wrong
- Varga confirmation incorrect

**Required evidence:**
- The specific classical rule that was violated (cite BPHS chapter/verse if possible)
- The correct classification according to classical texts
- The `evaluation_id` for exact reproduction

**Example:**
```json
{
  "category": "RE",
  "evaluation_id": "def456...",
  "chart_id": "chart_015_thatcher",
  "description": "Raja Yoga detected but Jupiter is debilitated in D9 — should be cancelled",
  "classical_rule": "BPHS Ch. 34: Raja Yoga requires functional benefics in Kendra/Trikona without debilitation",
  "engine_output": "Raja Yoga FORMED, strength 0.75",
  "correct_classification": "Raja Yoga CANCELLED due to Jupiter debilitation in D9 Navamsha"
}
```

### Category 3: Missing Coverage (MC)

**Definition:** The phenomenon exists classically, but the engine lacks the rule or yoga to detect it. This is a known limitation, not a bug.

**When to use:**
- A well-known classical yoga is completely absent from the engine's catalog
- A specific Dasha-transit combination should trigger an event but the engine has no rule for it
- A divisional chart (D10, D12, D24) should be consulted but isn't
- A specific nakshatra-based rule is missing

**Required evidence:**
- The classical yoga or rule that should exist
- Classical reference (BPHS, Phaladeepika, Saravali chapter)
- Why this omission matters for the specific chart

**Example:**
```json
{
  "category": "MC",
  "evaluation_id": null,
  "chart_id": "chart_051_kohli",
  "description": "Saraswati Yoga (BPHS Ch. 41) not detected — Jupiter in 2nd from Moon with Mercury in Kendra",
  "classical_rule": "BPHS Ch. 41: Saraswati Yoga — Jupiter in 2nd/4th/6th/8th/10th/12th from Moon, Mercury in Kendra, Venus in own sign or exalted",
  "impact": "Missed indicator of artistic/intellectual achievement"
}
```

### Category 4: DDE/Token Error (DE)

**Definition:** The astronomical facts are correct and the JRE reasoning is sound, but the DDE (Deterministic Determinant Engine) selected the wrong deterministic branch based on thresholds or boundary conditions.

**When to use:**
- Shadbala threshold routing produced the wrong esoteric token
- Gandanta boundary detection triggered incorrectly
- Token selection contradicts the mathematical facts
- The DDE's IF/THEN/ELSE logic produced an unexpected result

**Required evidence:**
- The input Shadbala value and threshold
- The expected vs actual token
- The specific DDE rule that should have fired

**Example:**
```json
{
  "category": "DE",
  "evaluation_id": "ghi789...",
  "chart_id": "chart_055_musk",
  "description": "Ashlesha Moon with Shadbala 1.25 routed to HIGH_HEALING — should be VULNERABILITY due to Gandanta proximity",
  "input_shadbala": 1.25,
  "gandanta_distance": "0.28° (within 0.333° tolerance)",
  "engine_token": "ASHLESHA_SARPA_HIGH_HEALING",
  "expected_token": "ASHLESHA_SARPA_VULNERABILITY",
  "dde_rule": "Gandanta override should take priority over Shadbala threshold"
}
```

### Category 5: Narrative/Token Error (NE)

**Definition:** The token is correct (the DDE made the right decision), but the rendered text in the token registry is poorly phrased, ambiguous, classically inaccurate, or contains conditional language.

**When to use:**
- Narrative text contains "could mean", "on one hand", "possibly", or similar ambiguity
- Classical interpretation is inaccurate or misleading
- The 3-part narrative doesn't match the token's meaning
- Cultural sensitivity concerns in the narrative
- The narrative is too vague to be useful

**Required evidence:**
- The specific token and which narrative section is problematic
- The exact problematic text
- Suggested correction (if possible)

**Example:**
```json
{
  "category": "NE",
  "evaluation_id": "jkl012...",
  "chart_id": "chart_062_mandela_modern",
  "token": "MULA_KARMIC_UPROOTING_HIGH_SHADBALA",
  "section": "SECTION_2_DETERMINISTIC_DYNAMIC",
  "problematic_text": "This energy could manifest as either spiritual liberation or destructive upheaval",
  "issue": "Contains 'could manifest as either' — violates zero-ambiguity rule",
  "suggested_fix": "This energy manifests as spiritual liberation through the radical uprooting of false foundations, channeled via sustained sadhana."
}
```

---

## 4. Feedback Submission Form

### 4.1 JSON Format (API Submission)

```json
{
  "evaluation_id": "[from API response]",
  "expert_id": "[YOUR_INITIALS]",
  "domain": "CAREER|WEALTH|HEALTH|MARRIAGE|ARTISTIC|EDUCATION|SPIRITUAL|OTHER",
  
  "feedback_category": "CE|RE|MC|DE|NE",
  
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": false,
  "false_positive": false,
  "false_negative": false,
  "timing_issue": false,
  "interpretation_issue": false,
  "astronomical_issue": true,
  "other": false,
  
  "chart_id": "[fixture_id or 'custom']",
  "free_text": "Detailed description of the issue, including engine output, correct value, and classical reference."
}
```

### 4.2 Markdown Format (GitHub Issues)

```markdown
## Feedback Entry

**Chart:** chart_001_pilot
**Category:** CE (Calculation Error)
**Domain:** CAREER
**Expert:** EXPERT_A

### Engine Output
- Lagna: Aries (Mesha)
- Moon Nakshatra: Jyeshta at 23°45'

### Expected
- Moon Nakshatra: Anuradha at 21°30'

### Classical Reference
- Drik Panchang 2024, Lahiri ayanamsa ephemeris

### Assessment
Expert disagreement — astronomical calculation appears incorrect.

### Suggested Fix
Verify Moon longitude calculation against Swiss Ephemeris data.
```

---

## 5. Evaluation Workflow

### Step 1: Select a Chart
```bash
curl -H "X-API-Key: jre-beta-key-alpha" http://localhost:8000/api/v1/fixtures
```

### Step 2: Evaluate the Chart
```bash
curl -X POST http://localhost:8000/api/v1/evaluate/fixture \
  -H "X-API-Key: jre-beta-key-alpha" \
  -H "Content-Type: application/json" \
  -d '{"fixture_id": "chart_001_pilot"}'
```

### Step 3: Review the Output
- Check `evaluation_id` — you'll need this for feedback
- Review each yoga's status, strength, and timing
- Compare against your domain expertise
- Identify which category (CE/RE/MC/DE/NE) applies

### Step 4: Classify Your Feedback
Select **exactly one** primary category:
- **CE** — Calculation Error (astronomical fact is wrong)
- **RE** — Reasoning Error (classical rule misapplied)
- **MC** — Missing Coverage (engine lacks the rule)
- **DE** — DDE/Token Error (threshold routing wrong)
- **NE** — Narrative/Token Error (text is problematic)

### Step 5: Submit Feedback
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "X-API-Key: jre-beta-key-alpha" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "[from step 2]",
    "expert_id": "EXPERT_A",
    "domain": "CAREER",
    "feedback_category": "CE",
    "expert_agreement": false,
    "expert_disagreement": true,
    "astronomical_issue": true,
    "chart_id": "chart_001_pilot",
    "free_text": "Moon Nakshatra computed incorrectly..."
  }'
```

---

## 6. What to Evaluate

### 6.1 Astronomical Accuracy (Category: CE)
- [ ] Lagna matches known value for birth time/place
- [ ] Planetary longitudes match ephemeris
- [ ] Nakshatra assignments are correct
- [ ] Retrograde status matches current astronomy
- [ ] Dasha periods align with Vimshottari calculation

### 6.2 Classical Reasoning (Category: RE)
- [ ] Yoga formations follow BPHS/Phaladeepika rules
- [ ] Modifier pipeline (combustion, debilitation) applied correctly
- [ ] Chain impact (dispositorship) is sound
- [ ] Varga confirmation (D9/D10) is appropriate
- [ ] Dynamic strength calculation is reasonable

### 6.3 Coverage Completeness (Category: MC)
- [ ] All known classical yogas for the chart are detected
- [ ] Missing yogas that should be present are flagged
- [ ] Divisional charts (D10, D12, D24) are utilized where appropriate

### 6.4 DDE Integrity (Category: DE)
- [ ] Esoteric tokens match the mathematical facts
- [ ] Gandanta boundaries detected correctly
- [ ] Shadbala thresholds applied consistently
- [ ] Token selection is deterministic across runs

### 6.5 Narrative Quality (Category: NE)
- [ ] No ambiguous or conditional language
- [ ] Classical citations are accurate
- [ ] Narrative matches the token's meaning
- [ ] Culturally sensitive and respectful

---

## 7. Golden Governance Rule

> **Your feedback populates the Evidence Dataset for v1.1.0-dev research proposals. No live rules will be changed based on individual requests.**

Every piece of structured feedback becomes a data point that may (or may not) justify a v1.1.0-dev change through the formal research proposal process. Individual feedback entries do not trigger immediate code changes.

This ensures:
1. **Scientific rigor** — Changes are data-driven, not request-driven
2. **Regression prevention** — No hasty modifications without full test validation
3. **Transparency** — All changes are documented through the proposal process
4. **Reproducibility** — Every change has a clear evidence trail

---

## 8. Priority Levels

| Priority | Description | Example |
|----------|-------------|---------|
| **P0 — Critical** | Astronomical facts are fundamentally wrong | Wrong Lagna, wrong Moon Nakshatra |
| **P1 — High** | Classical reasoning misapplied | False positive Raja Yoga, missed cancellation |
| **P2 — Medium** | Missing coverage or DDE routing issue | Undetected Saraswati Yoga, wrong Gandanta trigger |
| **P3 — Low** | Narrative quality or minor interpretation | Ambiguous text, cultural sensitivity |

---

## 9. Data Analysis Expectations

After collecting feedback from 3-5 experts across 70 charts, we expect to:

1. **Identify patterns** — e.g., "80% of P0 errors are Calculation Errors in Dasha calculation"
2. **Quantify accuracy** — e.g., "Engine achieves 77.5% F1 on HOLDOUT set"
3. **Prioritize v1.1.0-dev** — e.g., "Top 3 Missing Coverage items will be addressed in v1.1.0-dev"
4. **Validate DDE integrity** — e.g., "No DDE/Token Errors detected across 70 charts"

---

*This protocol is part of the JRE v1.0.0-beta beta testing program. The reasoning engine is frozen at v1.0.0-beta. All feedback is routed through the evidence dataset pipeline.*
