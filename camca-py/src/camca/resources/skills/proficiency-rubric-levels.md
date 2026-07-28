---
name: proficiency-rubric-levels
description: |
  Levels 0-3 ordinal scoring rubric used across all device checklists in CAMCA. Defines what each level means in terms of observable behavior, estimated dose loss, and clinical impact. Includes persona-specific tie-break rules for strict (Evaluator A) vs pragmatic (Evaluator B) interpretations. Use whenever an evaluator agent assigns a level score to ensure rubric consistency.
---

# Levels 0-3 Proficiency Rubric

## Universal Definitions

| Level | Label | Observable behavior | Estimated dose impact |
|---|---|---|---|
| **3** | Correct | Action performed fully per protocol | 0% dose loss; full clinical effect expected |
| **2** | Acceptable minor deviation | Effect preserved despite imperfect technique | ≤15% dose loss; clinically equivalent |
| **1** | Major deviation | Technique substantially deviates from protocol | 15-50% dose loss; clinically suboptimal |
| **0** | Not performed or incorrect | Step missing OR done in a way that defeats its purpose | >50% dose loss or total loss |

## Persona-Specific Tie-Break Rules

Critical for ensuring inter-rater reliability **with intentional diversity**, not artificial agreement.

When observed behavior sits between two adjacent levels:

| Persona | Rule | Rationale |
|---|---|---|
| **Strict evaluator (A)** | Default to LOWER level | Captures protocol deviations even when effect preserved; provides upper bound of strictness |
| **Pragmatic evaluator (B)** | Default to HIGHER level **only if clinical effect preserved** | Reflects real-world clinical pharmacy practice; provides lower bound of strictness |
| **Tie-breaker** | Clinical-impact-weighted midpoint | Cast deciding vote when A and B disagree by ≥2 levels |

Both A and B MUST document the rationale for their tie-break choice in the `rationale` field of their output.

## Critical Error Override (Independent of Levels)

Regardless of Level score assigned:
- If a CRITIKAL critical error is detected in a step → the `is_critical_error` flag for that step is set to `true`
- The overall verdict becomes FAIL regardless of total score
- Level score is still recorded for IRR statistics
- **Both A and B apply this rule identically** (no persona-driven leniency on critical errors)

## Inter-Level Examples — Detailed Calibration

### pMDI Step S1 (Shaking)

| Observation | Strict (A) | Pragmatic (B) | Rationale |
|---|---|---|---|
| Vigorous shake ×5 | 3 | 3 | Per protocol |
| Vigorous shake ×3 | 2 | 3 | A: <protocol; B: HFA needs only 2-3 shakes in practice |
| Gentle shake ×2 | 2 | 2 | Both: under-shaken |
| Wave motion only | 1 | 1 | Both: ineffective mixing |
| No shake | 0+CRIT | 0+CRIT | Both: CRIT-pMDI-01 flagged |

### pMDI Step S5 (Coordination of inhalation start + actuation)

| Observation | Strict (A) | Pragmatic (B) | Rationale |
|---|---|---|---|
| Inhalation start + actuation within 0.3s | 3 | 3 | Perfect coordination |
| Gap 0.4-0.6s, both within inhalation | 2 | 3 | A: <ideal; B: still within useful flow window |
| Gap 0.7-1.0s | 1 | 2 | A: major timing error; B: partial dose preserved |
| Gap >1.0s OR pre-inhalation actuation | 0+CRIT | 0+CRIT | Both: CRIT-pMDI-04 |
| No actuation | 0+CRIT | 0+CRIT | Both: critical error |

### Turbuhaler Step T5 (Forceful inhalation)

| Observation (estimated PIF) | Strict (A) | Pragmatic (B) | Rationale |
|---|---|---|---|
| ≥60 L/min, sustained | 3 | 3 | Per protocol |
| 50-60 L/min, sustained | 2 | 3 | A: below ideal; B: adequate for most patients |
| 30-50 L/min | 1 | 2 | A: clear deviation; B: partial aerosolization |
| <30 L/min (pMDI-style slow) | 0+CRIT | 0+CRIT | Both: CRIT-TBH-05 |

### Turbuhaler Step T2 (Twist with click)

| Observation | Strict (A) | Pragmatic (B) | Rationale |
|---|---|---|---|
| Full twist + audible click | 3 | 3 | Per protocol |
| Twist + click, brief tilt | 2 | 3 | A: protocol deviation; B: click present = dose loaded |
| Twist motion, no click audible | 1 | 1 | Both: cannot confirm dose loaded |
| No twist OR loaded twice without inhalation | 0+CRIT | 0+CRIT | Both: CRIT-TBH-02 or -03 |

## How to Apply Persona Rules in Practice

**When you are Evaluator A (strict)**:
- Read the protocol-specified action (e.g., "shake 4-5 times")
- Observe the patient's action (e.g., "shook 2 times")
- Assess: is this exactly per protocol? If no, go to lower level
- Document rationale: cite the protocol source

**When you are Evaluator B (pragmatic)**:
- Read the clinical purpose of the action (e.g., "mix HFA propellant")
- Observe the patient's action (e.g., "shook 2 times")
- Assess: would a reasonable clinical pharmacist consider this functionally adequate? If yes, go to higher level
- Document rationale: explain why clinical effect is preserved despite protocol deviation

## Inter-Rater Reliability Targets

Per CAMCA design intent:

- **Critical error agreement**: ≥0.90 (Cohen's kappa) — no persona-driven divergence allowed
- **Level scoring agreement**: 0.4-0.7 (Cohen's kappa, linear weighted) — moderate; intentional divergence expected
- **Verdict-level agreement**: ≥0.7 — final classifications should mostly converge

If level scoring kappa is too high (>0.8), the personas are not differentiated enough — recalibrate prompts to maintain meaningful diversity.

## TODO (deferred to next iteration)

- Calibration video set for level boundaries (to refine VLM prompts based on observed disagreement patterns)
- Empirical comparison of A vs B level distribution in n=30 pilot study (Phase 4 of CAMCA roadmap)
