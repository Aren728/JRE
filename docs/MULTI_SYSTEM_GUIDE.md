# Multi-System Yoga Evaluation Guide

## Overview

This guide documents the complete multi-layered Yoga evaluation flow in JRS, from natal chart input through divisional chart confirmation. It covers the RI-010 engine's 5-layer pipeline and provides API example payloads for chart evaluations.

---

## Full Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE YOGA EVALUATION FLOW                            │
│                                                                             │
│  Input: Birth Data + Divisional Chart Facts                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                   │   │
│  │    "planets": {                                                      │   │
│  │      "JUPITER": {"house": 1, "rashi": "DHANUSHA", "rashi_num": 9,  │   │
│  │                  "combust": false, "debilitated": false, ...},      │   │
│  │      "MOON":    {"house": 1, "rashi": "KARKA", "rashi_num": 4, ...},│   │
│  │      ...                                                             │   │
│  │    },                                                                │   │
│  │    "house_lords": {4: "MOON", 5: "SUN", 9: "JUPITER", ...},        │   │
│  │    "lagna": "KARKA",                                                 │   │
│  │    "planet_d9_sign":  {"JUPITER": "DHANUSHA", "MOON": "KARKA"},    │   │
│  │    "planet_d9_house": {"JUPITER": 1, "MOON": 1},                   │   │
│  │    "planet_d10_sign": {"JUPITER": "MAKARA"},                        │   │
│  │    "planet_d7_sign":  {"JUPITER": "DHANUSHA"}                       │   │
│  │  }                                                                   │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Layer 1: STRUCTURAL DETECTION                                      │   │
│  │  RelationshipGraphService.extract_relationships(jre_facts)          │   │
│  │                                                                      │   │
│  │  Detects: Conjunctions, Aspects (Parashari), Exchanges,            │   │
│  │           Dispositorships (with combust chain truncation)            │   │
│  │                                                                      │   │
│  │  Output: list[PlanetRelationship]                                   │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Layer 2: YOGA FORMATION + DEEP MODIFIERS                           │   │
│  │  YogaEvaluatorService.evaluate_classical_yogas(jre_facts)           │   │
│  │                                                                      │   │
│  │  a) Detect classical yogas (Gajakesari, Raja, Dhana, etc.)         │   │
│  │  b) Run 5-tier ModifierEvaluationService on each FORMED yoga        │   │
│  │     Tier 1: Combustion → CANCELLED                                  │   │
│  │     Tier 2: Debilitation / Neecha Bhanga                            │   │
│  │     Tier 3: Graha Yuddha (1.0° threshold, victor/defeated)         │   │
│  │     Tier 4: Cheshta Bala (retrograde boost 1.2×)                   │   │
│  │     Tier 5: Node Taint (conjunction 0.7×, aspect 0.85×)           │   │
│  │                                                                      │   │
│  │  Output: list[YogaEvaluation] with modifier_report attached         │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Layer 3: VARGA CONFIRMATION (Divisional Charts)                    │   │
│  │  VargaConfirmationService.evaluate_d9_confirmation(planets, facts)  │   │
│  │                                                                      │   │
│  │  a) Check D9 debilitation → binary CANCELLED                       │   │
│  │  b) Count Kendra/Trikona in D9 → STRONG/MODERATE/WEAK              │   │
│  │  c) Detect Vargottama (D1 == D9 sign) → 2.0× multiplier           │   │
│  │  d) D10 career + D7 progeny specialized checks                      │   │
│  │                                                                      │   │
│  │  Applied in evaluate_classical_yogas after modifier pipeline:        │   │
│  │  if "planet_d9_house" in jre_facts:                                 │   │
│  │      for each FORMED/WEAKENED yoga:                                 │   │
│  │          confirmation = svc.evaluate_d9_confirmation(planets, facts) │   │
│  │          if confirmation.status == CANCELLED:                        │   │
│  │              yoga.status = CANCELLED                                 │   │
│  │                                                                      │   │
│  │  Output: VargaConfirmationResult (status, strength, multiplier)     │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Layer 4: TRANSIT ACTIVATION + TEMPORAL                             │   │
│  │  TransitActivationService.evaluate_activation(yogas, dasha, transits)│   │
│  │                                                                      │   │
│  │  • Dasha-first hierarchy (Dasha > Antardasha > Transit)             │   │
│  │  • Vedha obstruction masks (Phaladeepika Ch 26)                     │   │
│  │  • Tara Bala strength (Nakshatra-based)                              │   │
│  │                                                                      │   │
│  │  Output: ActivationResult per yoga                                  │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐   │
│  │  Layer 5: EVIDENCE CONVERGENCE + CROSS-DOMAIN                       │   │
│  │  ConvergenceService.assess_domain(outcome, evidence, windows)       │   │
│  │                                                                      │   │
│  │  • Aggregate evidence from all layers                               │   │
│  │  • Cross-system independence analysis (Vedic/Western/Nadi)          │   │
│  │  • Classify: STRONGLY_SUPPORTED → CONTRADICTED                      │   │
│  │  • Timing: CONVERGENT / DIVERGENT / INACTIVE                        │   │
│  │                                                                      │   │
│  │  Output: DomainAssessment                                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │\n└─────────────────────────────────────────────────────────────────────────────┘\n```\n\n---\n\n## Service Layer Reference\n\n| Layer | Service | Package | Input | Output |\n|-------|---------|---------|-------|--------|\n| 1 | `RelationshipGraphService` | `jrs.structural` | `jre_facts` | `list[PlanetRelationship]` |\n| 2 | `YogaEvaluatorService` | `jrs.yoga_evaluator` | `jre_facts` | `list[YogaEvaluation]` |\n| 2 | `ModifierEvaluationService` | `jrs.yoga_evaluator` | `planets, jre_facts` | `ModifierReport` |\n| 3 | `VargaConfirmationService` | `jrs.varga` | `planets, jre_facts` | `VargaConfirmationResult` |\n| 3 | `SaptavargajaBalaService` | `jrs.varga` | `planet, facts` | `SaptavargajaScore` |\n| 4 | `TransitActivationService` | `jrs.temporal` | `yogas, dasha, transits` | `ActivationResult` |\n| 4 | `VedhaService` | `jrs.temporal` | `transit, natal` | `list[VedhaRecord]` |\n| 4 | `TaraBalaService` | `jrs.temporal` | `transit_nak, moon_nak` | `TaraResult` |\n| 5 | `ConvergenceService` | `jrs.convergence` | `outcome, evidence, windows` | `DomainAssessment` |\n| 5 | `IndependenceAnalyzer` | `jrs.multisystem` | `provenances` | `(adjusted_convergence, independence)` |\n\n---\n\n## API Example: Complete Chart Evaluation\n\n### Example 1: Gajakesari Yoga with D9 Confirmation\n\n**Request:**\n\n```json\n{\n  \"planets\": {\n    \"JUPITER\": {\n      \"house\": 1,\n      \"rashi\": \"DHANUSHA\",\n      \"rashi_num\": 9,\n      \"combust\": false,\n      \"debilitated\": false,\n      \"retrograde\": false\n    },\n    \"MOON\": {\n      \"house\": 1,\n      \"rashi\": \"KARKA\",\n      \"rashi_num\": 4,\n      \"combust\": false,\n      \"debilitated\": false\n    }\n  },\n  \"house_lords\": {\n    \"1\": \"MOON\",\n    \"5\": \"SUN\",\n    \"9\": \"JUPITER\"\n  },\n  \"lagna\": \"KARKA\",\n  \"planet_d9_sign\": {\n    \"JUPITER\": \"DHANUSHA\",\n    \"MOON\": \"KARKA\"\n  },\n  \"planet_d9_house\": {\n    \"JUPITER\": 1,\n    \"MOON\": 1\n  }\n}\n```\n\n**Evaluation Flow:**\n\n```\n1. Structural Detection:\n   - Jupiter in Kendra from Moon (same house = conjunction)\n\n2. Yoga Formation:\n   - Gajakesari: Jupiter in Kendra from Moon → FORMED\n   - Modifier pipeline: No afflictions → FORMED (strength 1.0)\n\n3. Varga Confirmation (D9):\n   - Jupiter D9 house: 1 (Kendra) ✓\n   - Moon D9 house: 1 (Kendra) ✓\n   - kendra_trikona_count: 2/2 → STRONG (1.5×)\n   - Vargottama check: Jupiter D1=DHANUSHA, D9=DHANUSHA → Vargottama (2.0×)\n   - Moon D1=KARKA, D9=KARKA → Vargottama (2.0×)\n   - Net multiplier: 1.5 × 2.0 = 3.0×\n   - confirmation_status: FORMED\n```\n\n**Response:**\n\n```json\n{\n  \"yoga_name\": \"Gajakesari\",\n  \"status\": \"FORMED\",\n  \"modifier_report\": {\n    \"overall_status\": \"FORMED\",\n    \"overall_strength\": 1.0,\n    \"cancellation_reason\": null\n  },\n  \"varga_confirmation\": {\n    \"confirmation_status\": \"FORMED\",\n    \"strength\": \"STRONG\",\n    \"kendra_trikona_count\": 2,\n    \"total_planets\": 2,\n    \"vargottama_planets\": [\"JUPITER\", \"MOON\"],\n    \"vargottama_multiplier\": 2.0,\n    \"net_strength_multiplier\": 3.0\n  }\n}\n```\n\n---\n\n### Example 2: Raja Yoga with Combustion Cancellation\n\n**Request:**\n\n```json\n{\n  \"planets\": {\n    \"MARS\": {\n      \"house\": 10,\n      \"rashi\": \"VRISHCHIKA\",\n      \"rashi_num\": 8,\n      \"house_lord_of\": 4,\n      \"combust\": false,\n      \"debilitated\": false\n    },\n    \"JUPITER\": {\n      \"house\": 10,\n      \"rashi\": \"VRISHCHIKA\",\n      \"rashi_num\": 8,\n      \"house_lord_of\": 5,\n      \"combust\": true,\n      \"debilitated\": false\n    }\n  },\n  \"house_lords\": {\n    \"4\": \"MARS\",\n    \"5\": \"JUPITER\"\n  },\n  \"planet_d9_sign\": {\n    \"MARS\": \"MESHA\",\n    \"JUPITER\": \"KARKA\"\n  },\n  \"planet_d9_house\": {\n    \"MARS\": 1,\n    \"JUPITER\": 4\n  }\n}\n```\n\n**Evaluation Flow:**\n\n```\n1. Structural Detection:\n   - Mars (4th lord) + Jupiter (5th lord) conjunct in house 10\n   - Kendra lord + Trikona lord conjunction → Raja Yoga\n\n2. Yoga Formation:\n   - Raja Yoga: FORMED at detection\n   - Modifier pipeline:\n     - Mars: No afflictions (strength 1.0)\n     - Jupiter: COMBUSTION (Tier 1) → CANCELLED\n     - Overall: CANCELLED (any planet combust → binary)\n   - Status: CANCELLED, reason: \"JUPITER is combust\"\n\n3. Varga Confirmation:\n   - Skipped (yoga already CANCELLED by modifiers)\n```\n\n**Response:**\n\n```json\n{\n  \"yoga_name\": \"Raja\",\n  \"status\": \"CANCELLED\",\n  \"cancellation_reason\": \"JUPITER is combust\",\n  \"modifier_report\": {\n    \"overall_status\": \"CANCELLED\",\n    \"overall_strength\": 0.0,\n    \"cancellation_reason\": \"JUPITER is combust\",\n    \"planet_results\": [\n      {\"planet\": \"MARS\", \"status\": \"FORMED\", \"modifier_chain\": []},\n      {\"planet\": \"JUPITER\", \"status\": \"CANCELLED\",\n       \"modifier_chain\": [\"COMBUSTION\"]}\n    ]\n  }\n}\n```\n\n---\n\n### Example 3: Saptavargaja Bala Score\n\n**Request:**\n\n```json\n{\n  \"planets\": {\n    \"JUPITER\": {\n      \"rashi_num\": 9,\n      \"planet_d2_sign\": \"DHANUSHA\",\n      \"planet_d3_sign\": \"KARKA\",\n      \"planet_d7_sign\": \"DHANUSHA\",\n      \"planet_d9_sign\": \"DHANUSHA\",\n      \"planet_d12_sign\": \"KARKA\",\n      \"planet_d30_sign\": \"SIMHA\"\n    }\n  }\n}\n```\n\n**Evaluation:**\n\n```\nSaptavargajaBalaService.evaluate_planet(\"JUPITER\", facts)\n\nD1  (rashi_num=9):  DHANUSHA → Moolatrikona = 5.0\nD2  (sign=DHANUSHA): Moolatrikona = 5.0\nD3  (sign=KARKA):   Friend (Moon) = 3.0\nD7  (sign=DHANUSHA): Moolatrikona = 5.0\nD9  (sign=DHANUSHA): Moolatrikona = 5.0\nD12 (sign=KARKA):   Friend = 3.0\nD30 (sign=SIMHA):   Enemy (Sun) = 1.0\n─────────────────────────────\nTotal: 27.0  →  VERY_STRONG (≥ 25)\n```\n\n**Response:**\n\n```json\n{\n  \"planet\": \"JUPITER\",\n  \"total_score\": 27.0,\n  \"dignity_level\": \"VERY_STRONG\",\n  \"varga_scores\": {\n    \"D1\": 5.0, \"D2\": 5.0, \"D3\": 3.0, \"D7\": 5.0,\n    \"D9\": 5.0, \"D12\": 3.0, \"D30\": 1.0\n  },\n  \"moolatrikona_count\": 4,\n  \"own_sign_count\": 0,\n  \"friend_count\": 2,\n  \"enemy_count\": 1\n}\n```\n\n---\n\n## Integration Pattern\n\nThe recommended integration pattern for consuming the RI-010 engine:\n\n```python\nfrom jrs.yoga_evaluator.service import YogaEvaluatorService\nfrom jrs.varga import VargaConfirmationService, SaptavargajaBalaService\n\n# 1. Initialize services\nyoga_svc = YogaEvaluatorService()  # Injects VargaConfirmationService internally\nsaptavargaja_svc = SaptavargajaBalaService()\n\n# 2. Evaluate classical yogas (includes D9 confirmation if data available)\nyogas = yoga_svc.evaluate_classical_yogas(jre_facts, transit_planet=\"JUPITER\")\n\n# 3. Compute Saptavargaja Bala for each planet\nfor planet_name, planet_data in jre_facts.get(\"planets\", {}).items():\n    score = saptavargaja_svc.evaluate_planet(planet_name, planet_data)\n    print(f\"{planet_name}: {score.total_score} ({score.dignity_level})\")\n\n# 4. Check D9 confirmation for specific yoga\nconfirmation = yoga_svc.evaluate_d9_confirmation(\n    [\"JUPITER\", \"MOON\"], jre_facts\n)\nprint(f\"D9 confirmation: {confirmation.strength}, multiplier: {confirmation.net_strength_multiplier}\")\n\n# 5. Evaluate D10 career confirmation\ncareer = yoga_svc.evaluate_d10_career([\"JUPITER\"], jre_facts)\nprint(f\"Career strong: {career.is_d10_career_strong}\")\n```\n\n---\n\n## Classical Source Citations\n\n| Layer | Primary Sources |\n|-------|----------------|\n| Structural Detection | BPHS Ch 33 (Dispositorship), Ch 41 (Yoga Yoga) |\n| Modifier Pipeline | BPHS Ch 7 (Combustion), Ch 43 (Debilitation); Phaladeepika Ch 1; Saravali Ch 24 (Graha Yuddha) |\n| Node Taint | BPHS Ch 9 v. 12; RI-010C MY-025–030 |\n| Varga Confirmation | BPHS Ch 35 (Navamsha); Jataka Parijata Ch 2; Phaladeepika Ch 2 |\n| Saptavargaja | BPHS Ch 3 (Varga), Ch 45 (Saptavargaja); Jataka Parijata Ch 3 |\n| Transit Activation | BPHS Ch 44 (Gochara); Phaladeepika Ch 26 (Vedha) |\n| Multi-System | Independence analysis per RI-010F (provenance tracking) |\n"
