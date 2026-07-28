---
name: critical-errors-critikal
description: |
  CRITIKAL study (Price DB et al. 2017) classification of critical vs non-critical inhaler errors. A critical error is defined as one that "is likely to result in significantly reduced drug delivery to the lungs OR associated with increased rate of severe exacerbations and uncontrolled asthma." Use whenever evaluating inhaler technique to ensure consistent critical-error flagging across all evaluators.
---

# CRITIKAL Critical-Error Classification System

## Definition

A **critical error** is one with documented association to clinical outcomes (uncontrolled asthma, severe exacerbations) per:

> Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study: Type, frequency, and association with asthma outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.e9.

CRITIKAL analyzed 3,660 patients across 7 European countries using video-recorded inhaler technique assessment. Errors were classified as **critical** or **non-critical** based on their independent association with worse asthma outcomes after adjustment for confounders.

## Why This Classification Matters

- A single critical error = clinically meaningful dose reduction → AI evaluation must flag with high sensitivity
- A non-critical error = protocol deviation without measurable clinical impact → may be acceptable in real-world practice
- The **dual-agent system uses critical-error agreement as the floor of inter-rater reliability** — both evaluators must agree on critical errors regardless of persona differences

## Universal Critical Errors (Apply to All Devices)

| Universal ID | Description | Devices |
|---|---|---|
| CRIT-UNIV-01 | Not exhaling before inhalation | pMDI, DPI, SMI |
| CRIT-UNIV-02 | Inhalation through nose instead of mouth | All |
| CRIT-UNIV-03 | No breath-hold after inhalation | All |
| CRIT-UNIV-04 | Exhalation into mouthpiece before inhalation | pMDI (dose loss), DPI (moisture damage) |
| CRIT-UNIV-05 | Inhalation occurs without dose loaded/aerosolized | DPI (no click), pMDI (no actuation) |

## Device-Specific Critical Errors

### pMDI (see `inhaler-checklist-pmdi` skill for full detail)
- CRIT-pMDI-01: No shaking (suspension formulations)
- CRIT-pMDI-02: Cap not removed
- CRIT-pMDI-03: Exhalation into inhaler
- CRIT-pMDI-04: Actuation before inhalation start (coordination)
- CRIT-pMDI-05: Actuation after inhalation complete (coordination)
- CRIT-pMDI-06: Inhalation too fast (>60 L/min — opposite problem from DPI)
- CRIT-pMDI-07: Inhalation truncated
- CRIT-pMDI-08: No breath-hold
- CRIT-pMDI-09: No mouth rinse with ICS

### Turbuhaler / DPI (see `inhaler-checklist-turbuhaler` skill for full detail)
- CRIT-TBH-01: Holding upside-down during loading
- CRIT-TBH-02: Loading without click
- CRIT-TBH-03: Multiple loading without inhalation between (overdose)
- CRIT-TBH-04: Exhalation into mouthpiece (moisture damage)
- CRIT-TBH-05: Inhalation too slow (<30 L/min)
- CRIT-TBH-06: Inhalation not started forcefully from t=0
- CRIT-TBH-07: Inhalation truncated
- CRIT-TBH-08: No breath-hold
- CRIT-TBH-09: No mouth rinse with ICS

## CRITIKAL Frequency Data

Per Price et al. 2017, the most prevalent **critical** errors:

| Device | Top Critical Error | Prevalence | Adjusted OR (uncontrolled asthma) |
|---|---|---|---|
| pMDI | Coordination failure (CRIT-pMDI-04/05) | 45% | 1.45 (95% CI 1.16-1.81) |
| pMDI | Inadequate inhalation (CRIT-pMDI-06/07) | 24% | 1.36 (95% CI 1.06-1.74) |
| pMDI | No breath-hold (CRIT-pMDI-08) | 38% | 1.30 (95% CI 1.05-1.61) |
| DPI | Insufficient inspiratory effort (CRIT-TBH-05/06) | 38% | 1.30 (95% CI 1.08-1.57) |
| DPI | No exhalation before inhalation (CRIT-UNIV-01) | 14% | 1.23 (95% CI 1.00-1.51) |

**Implication for evaluator agents**: These high-prevalence critical errors should receive higher detection sensitivity. Missing them has greater clinical cost than over-flagging.

## Non-Critical Errors (Documented in CRITIKAL but NOT Outcome-Associated)

These should NOT be flagged as critical by either Evaluator A or B:

- Forgetting to remove dust cap (oddly, not outcome-associated when caught before inhalation)
- Holding inhaler at wrong angle within ±30° of optimal
- Looking at the device during inhalation
- Slightly delayed breath-hold (5-9 seconds vs ideal 10)

The strict evaluator (A) may dock points for these but should NOT mark them as critical.

## Detection Sensitivity Targets (per CAMCA design)

For the dual-agent system:
- Critical error sensitivity target: **≥0.90** (false negatives are clinically costly)
- Critical error specificity target: **≥0.85** (false positives undermine trust)
- Both evaluators should achieve these independently — disagreement on critical errors triggers tie-breaker

## Output Format (for critical-error-detector agent)

```json
{
  "device_type": "pMDI",
  "step_id": "S5",
  "critical_errors_checked": ["CRIT-pMDI-04", "CRIT-pMDI-05", "CRIT-pMDI-06"],
  "detections": [
    {
      "critical_error_id": "CRIT-pMDI-04",
      "detected": true,
      "confidence": 0.91,
      "evidence_frame_indices": [98, 110],
      "evidence_description": "Inhalation onset at frame 98 (0.42s); canister actuation at frame 110 (0.84s); delay = 0.42s exceeds 0.3s tolerance"
    }
  ]
}
```

## References

- Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study: Type, frequency, and association with asthma outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.e9. **PRIMARY SOURCE**
- Sanchis J, Gich I, Pedersen S; ADMIT Group. *Systematic Review of Errors in Inhaler Use.* Chest 2016;150(2):394-406.
- Plaza V, Giner J, Rodrigo GJ, et al. *Errors in the use of inhalers by health care professionals.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
- Global Initiative for Asthma. *GINA 2024 Box 3-6: Common inhaler errors.*
