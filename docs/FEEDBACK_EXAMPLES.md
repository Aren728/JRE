# JRE Feedback Examples

**Reference document for beta testers** — Concrete examples of structured feedback submissions.

---

## Example 1: Correct Prediction (Agreement)

**Scenario:** The engine correctly identifies Raja Yoga activation during Virat Kohli's 2018 peak ranking.

```json
{
  "evaluation_id": "adbb13a87c9f7c61",
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
  "free_text": "Engine correctly identified Raja Yoga activation during Kohli's 2018 peak. Dasha alignment with Jupiter MD is classically sound. The Kendra-Trikona connection between Saturn (10th lord) and Jupiter (9th lord) is a textbook Raja Yoga formation for career prominence."
}
```

**What this tells us:** The engine's Raja Yoga detection and Dasha activation are working correctly for this chart configuration.

---

## Example 2: Missing Yoga (False Negative)

**Scenario:** The engine missed a Saraswati Yoga for a writer's breakthrough.

```json
{
  "evaluation_id": "def4567890123456",
  "expert_id": "EXPERT_B",
  "domain": "ARTISTIC",
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": true,
  "false_positive": false,
  "false_negative": true,
  "timing_issue": false,
  "interpretation_issue": false,
  "astronomical_issue": false,
  "other": false,
  "free_text": "Chart should show Saraswati Yoga for writing success. Jupiter in 2nd house from Moon with Mercury in Kendra from Lagna. Engine missed this classical formation. The Saraswati Yoga conditions (Jupiter, Venus, Mercury in Kendra or Trikona) appear to be met but not detected."
}
```

**What this tells us:** There may be a gap in the Saraswati Yoga detection logic, or the formation conditions are stricter than classical texts specify.

---

## Example 3: Astronomical Error

**Scenario:** The engine calculates the wrong Nakshatra for the Moon.

```json
{
  "evaluation_id": "ghi78901234567890",
  "expert_id": "EXPERT_A",
  "domain": "CAREER",
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": false,
  "false_positive": false,
  "false_negative": false,
  "timing_issue": false,
  "interpretation_issue": false,
  "astronomical_issue": true,
  "other": false,
  "free_text": "Moon Nakshatra calculated as Jyeshta, but should be Anuradha based on exact longitude (15° Scorpio). This affects all downstream Dasha calculations and could explain why the timing appears off for several events."
}
```

**What this tells us:** There may be an ephemeris precision issue or ayanamsa discrepancy affecting Nakshatra boundaries. This is a high-priority fix since it cascades to all temporal calculations.

---

## Example 4: Timing Issue with Partial Agreement

**Scenario:** The engine detects the right yoga but at the wrong time.

```json
{
  "evaluation_id": "jkl0123456789012",
  "expert_id": "EXPERT_C",
  "domain": "WEALTH",
  "expert_agreement": false,
  "expert_disagreement": true,
  "missing_yoga": false,
  "false_positive": false,
  "false_negative": false,
  "timing_issue": true,
  "interpretation_issue": false,
  "astronomical_issue": false,
  "other": false,
  "free_text": "Dhana Yoga is correctly formed and detected, but the Dasha activation shows Jupiter MD when the wealth event actually occurred during Saturn MD. The yoga formation is accurate but the temporal mapping seems off. Saturn is the 10th lord, not directly involved in the Dhana Yoga, so the activation multiplier should be lower."
}
```

**What this tells us:** The Dasha matching logic may need refinement — the engine is matching planets that are involved in the yoga but not the Dasha lords. This helps us understand the boundary between direct and indirect Dasha influence.

---

## How to Use These Examples

1. **Match your situation** to the closest example above
2. **Copy the JSON structure** and replace with your specific findings
3. **Be specific in `free_text`** — the more detail, the better
4. **Include the exact `evaluation_id`** from your API response
5. **Set only the relevant flags** — multiple flags can be true if applicable

### Quick Flag Reference

| Flag | When to Use |
|------|-------------|
| `expert_agreement` | Engine got it right |
| `expert_disagreement` | Engine got it wrong |
| `missing_yoga` | Classical yoga not detected |
| `false_positive` | Yoga detected that shouldn't exist |
| `false_negative` | Yoga missed that should have been detected |
| `timing_issue` | Dasha activation timing is wrong |
| `interpretation_issue` | Classical interpretation is incorrect |
| `astronomical_issue` | Underlying calculation is wrong |
| `other` | Something else entirely |

---

*These examples are part of the JRE v1.0.0-beta beta testing program.*
