---
name: inhaler-checklist-pmdi-spacer
description: |
  Standardized step-by-step evaluation checklist for pressurized metered-dose inhaler (pMDI) used WITH a valved holding chamber / spacer, covering both mouthpiece-type (adult/older child) and face-mask-type (pediatric/infant) configurations, with Levels 0-3 proficiency rubric per step and CRITIKAL-informed critical-error mapping. Use when evaluating pMDI+spacer inhaler-use video, photo, or observation notes; or when an evaluator agent needs the criteria for scoring. Based on GINA 2024, German Airway League standardized checklist, CRITIKAL study classification, and pediatric spacer/face-mask technique literature.
---

# pMDI + Spacer Inhaler Technique Evaluation Checklist

## Scope

This checklist applies to **pressurized metered-dose inhalers (pMDI) used together with a spacer / valved holding chamber (VHC)** — e.g., AeroChamber, OptiChamber, Volumatic, Babyhaler. It covers **two device subtypes**:

- **Mouthpiece-type spacer**: patient's lips form a direct seal around a mouthpiece on the spacer. Typically used by older children/adults who can follow breathing instructions.
- **Face-mask-type spacer** (pediatric/infant configuration): a soft face mask attached to the spacer covers nose and mouth, relying on positional seal rather than a voluntary lip seal. Typically used for infants, toddlers, and young children who cannot reliably form a mouthpiece seal.

The evaluator must confirm which subtype is present (from `device-id` output, `spacer_subtype` field) before scoring S4, since seal-quality criteria differ materially between the two.

For a **bare pMDI without a spacer**, use `inhaler-checklist-pmdi` (separate skill). For **DPI-Turbuhaler**, use `inhaler-checklist-turbuhaler`.

## Why Spacer Technique Differs From Bare pMDI

A spacer/VHC acts as an aerosol reservoir with a one-way valve, which:
- **Removes the need for precise hand-breath coordination** — the single most error-prone step for bare pMDI (CRIT-pMDI-04/05/06) is largely mitigated, because the aerosol cloud is held in the chamber until the patient inhales.
- **Reduces oropharyngeal deposition** — large particles impact the spacer walls rather than the throat, lowering local/systemic ICS side effects and improving lung deposition.
- Introduces **new failure modes** specific to the device: multiple actuations per breath (each actuation should get its own full inhalation cycle), spacer valve not opening (poor mask/mouthpiece seal), static charge reducing aerosol availability (relevant for older non-antistatic plastic spacers), and — for face-mask subtype — inadequate mask seal against the face.

## Evaluation Framework

- **7 sequential steps** (S1–S7), each scored 0–3
- **1 conditional step** (S8) for ICS-containing inhalers; cap-replacement is folded into S7 rather than a separate S9 (spacer devices are typically left assembled between uses)
- **Maximum total score**: 21 (or 24 with conditional step)
- **Critical errors**: separately tracked; a single critical error = overall FAIL regardless of other scores
- **Subtype-dependent scoring**: S4 rubric branches by `spacer_subtype` (mouthpiece vs. face_mask)

## Step-by-Step Checklist

### S1 — Shake the inhaler and assemble with spacer

**Action**: Vigorously shake the pMDI canister 4–5 times, then firmly insert it into the spacer's rubber port so it is well seated and airtight.

**Why it matters**: Same propellant/drug mixing rationale as bare pMDI. A loosely seated canister leaks aerosol at the spacer port instead of delivering it into the chamber.

**Rubric**:
- **Level 3** — Shakes vigorously ≥4 times, canister firmly and fully seated in spacer port
- **Level 2** — Shakes 2–3 times, canister seated adequately
- **Level 1** — Minimal shake OR canister loosely seated (visible gap/wobble)
- **Level 0** — No shake AND/OR canister not properly connected

**Critical error mapping**: `CRIT-SPC-01` "No shaking" — inconsistent dose (same rationale as CRIT-pMDI-01).

**Observable in video**: Hand shake motion; insertion/click of canister into spacer port.

---

### S2 — Remove caps and inspect

**Action**: Remove the pMDI mouthpiece cap and, if present, the spacer's own mouthpiece/mask cap; inspect for obstruction.

**Rubric**:
- **Level 3** — Both caps removed, brief inspection
- **Level 2** — Caps removed, no inspection
- **Level 1** — Only one cap removed or removed with difficulty
- **Level 0** — Cap(s) left on

**Critical error mapping**: `CRIT-SPC-02` "Cap not removed" — total dose loss if the pMDI cap blocks the canister stem.

**Observable in video**: Cap removal motion(s).

---

### S3 — Position spacer and achieve seal (device-holding step)

**Action**: Bring the spacer to the face and establish the seal appropriate to the subtype (see S4 for the detailed seal rubric — S3 covers *positioning/holding*, not seal quality itself: correct grip, spacer held roughly horizontal, patient in upright or near-upright posture).

**Why it matters**: A tilted spacer or slumped posture can cause the pMDI valve to actuate at an angle, reduce priming reliability, and — for face-mask subtype — makes maintaining seal harder.

**Rubric**:
- **Level 3** — Spacer held horizontally, patient upright, stable grip throughout
- **Level 2** — Minor tilt or posture deviation, still functional
- **Level 1** — Notable tilt/instability, seal likely compromised
- **Level 0** — Spacer not properly positioned (e.g., aimed away from face, patient supine without justification)

**Critical error mapping**: None directly; compounds with S4.

**Observable in video**: Spacer angle, patient body position, caregiver hand position (pediatric cases).

---

### S4 — Achieve and maintain airtight seal (SUBTYPE-DEPENDENT)

**Action (mouthpiece-type)**: Place spacer mouthpiece between teeth, close lips to form an airtight seal, tongue flat and not obstructing.

**Action (face-mask-type)**: Press the mask firmly and evenly against the face, covering both nose and mouth, with no gaps at the cheeks or chin/nasal bridge. Hold in place for the full duration of the dose delivery (not just the actuation).

**Why it matters**: Any air leak — at the lips (mouthpiece) or at the mask-face junction (face-mask) — dilutes/vents the aerosol and reduces the effective dose. For infants/toddlers, mask seal is the single most common failure point in real-world spacer use and is analogous in clinical importance to the mouthpiece lip-seal step.

**Rubric — mouthpiece subtype**:
- **Level 3** — Tight, sustained lip seal, tongue not obstructing, maintained through full inhalation
- **Level 2** — Adequate seal with brief lapses OR tongue position unclear
- **Level 1** — Visible intermittent air leak at lips
- **Level 0** — Mouthpiece not in mouth OR major/continuous leak

**Rubric — face-mask subtype**:
- **Level 3** — Mask fully seals nose+mouth, no visible gap, maintained for the entire breathing sequence (through valve-click cycles or ~5-6 breaths), minimal patient resistance/distress disrupting seal
- **Level 2** — Seal adequate but with brief gaps (e.g., child briefly pulls away, quickly re-seated by caregiver)
- **Level 1** — Visible persistent gap at cheek/chin, or seal maintained for only part of the required breathing duration
- **Level 0** — Mask not making facial contact, held away from face, or child crying/fighting the mask with no effective seal for most of the sequence

**Critical error mapping**: `CRIT-SPC-03` "No effective seal (mouthpiece or mask)" — this is the spacer-specific analogue of dose loss via leak; treated as critical because, unlike bare pMDI's air-leak step, spacer efficacy depends almost entirely on chamber+seal integrity rather than coordination.

**Observable in video**: Lip closure or mask-to-face contact; cheek movement (mouthpiece leak indicator); visible gap or light passing under mask edge; caregiver hand pressure (pediatric).

---

### S5 — Actuate ONE puff into the spacer, then inhale

**Action**: With seal established, press the canister once to release a single actuation into the chamber. Then begin inhalation (this may follow immediately, since the spacer buffers the aerosol — precise coordination is not required, unlike bare pMDI).

**Why it matters**: Multiple actuations released into the chamber before inhaling causes aerosol particles to collide and coalesce ("rain-out"), reducing the respirable fraction reaching the lungs. Each actuation should be followed by inhalation before the next dose is released.

**Rubric**:
- **Level 3** — Single actuation per dose, inhalation begins promptly (within ~1-2 sec, or breathing is already in progress against the mask/mouthpiece)
- **Level 2** — Single actuation, brief delay before inhalation (~3-5 sec) — some aerosol settling likely but not severe
- **Level 1** — Single actuation with long delay (>5 sec) before inhalation begins
- **Level 0** — Multiple actuations pressed into the chamber before/without intervening inhalation ("double-puffing")

**Critical error mapping**: `CRIT-SPC-04` "Multiple actuations without intervening inhalation" — significantly reduces respirable dose via particle coalescence.

**Observable in video + audio**: Number of distinct actuation sounds/motions vs. number of separate inhalation cycles; time gap between actuation and inhalation onset.

---

### S6 — Inhale to effect (age/protocol-appropriate breathing pattern)

**Action**: Depending on age and ability —
- **Single-breath protocol** (older cooperative children/adults): one slow, deep inhalation to full lung capacity immediately following actuation.
- **Tidal-breathing protocol** (infants, toddlers, or anyone unable to perform a single deep breath — common with face-mask subtype): 5–6 slow, normal-depth tidal breaths through the spacer per actuation, observable via valve movement or chest rise.

**Why it matters**: Either protocol delivers the dose if performed correctly; the error is stopping too early (too few tidal breaths, or a truncated single breath) such that most of the chamber's aerosol is never inhaled.

**Rubric**:
- **Level 3** — Full single deep breath (mouthpiece protocol) OR ≥5 tidal breaths with visible valve/chest movement each cycle (tidal protocol)
- **Level 2** — Slightly shortened: breath somewhat shallow, or 3-4 tidal breaths
- **Level 1** — Clearly truncated: brief single breath, or 1-2 tidal breaths only
- **Level 0** — No effective inhalation observed after actuation

**Critical error mapping**: `CRIT-SPC-05` "Inhalation truncated / insufficient tidal breaths" — partial dose delivery, spacer-adapted analogue of CRIT-pMDI-07.

**Observable in video + audio**: Valve flutter/click sounds (visual proxy for airflow through chamber), chest rise count, duration of breathing sequence.

---

### S7 — Breath-hold (if single-breath protocol) or completion of tidal cycle, then remove spacer and recap

**Action**: For single-breath protocol: hold breath ~10 sec after inhalation, then exhale slowly. For tidal-breathing protocol: simply complete the prescribed number of tidal breaths (no discrete breath-hold expected). Then remove the spacer from the mouth/face and replace caps.

**Rubric**:
- **Level 3** — Breath-hold ≥10 sec (single-breath) OR full tidal sequence completed without early removal (tidal); spacer/caps handled appropriately afterward
- **Level 2** — Breath-hold 5–9 sec, or tidal sequence completed with minor early removal (within last breath)
- **Level 1** — Breath-hold 1–4 sec, or tidal sequence cut short by 1-2 breaths
- **Level 0** — No breath-hold at all (single-breath protocol) or mask/mouthpiece removed well before the sequence is complete

**Critical error mapping**: `CRIT-SPC-06` "No breath-hold" (single-breath protocol only) — substantial dose loss, analogous to CRIT-pMDI-08. Not scored as critical under tidal-breathing protocol, where the equivalent failure is already captured in S6.

**Observable in video**: Mouth/mask removal timing, chest position, breath count.

---

### S8 (conditional, ICS only) — Rinse mouth and gargle

**Action**: For ICS-containing inhalers used via mouthpiece-type spacer with a cooperative patient: rinse mouth with water, gargle, spit out. For infants/face-mask subtype: wipe the face/mouth area after dosing (rinsing/gargling generally not developmentally feasible) — evaluate against age-appropriate oral hygiene practice rather than the adult rinse-and-spit standard.

**Rubric**:
- **Level 3** — Age-appropriate oral hygiene performed (rinse+gargle+spit for verbal children/adults; face/mouth wipe for infants)
- **Level 2** — Partial oral hygiene (rinse without gargle, or incomplete wipe)
- **Level 1** — Minimal effort (e.g., drinks water without rinsing)
- **Level 0** — No oral care at all

**Critical error mapping**: Not dose-affecting; `CRIT-SPC-07` "No oral hygiene with ICS" flagged for long-term local side-effect risk, same clinical rationale as CRIT-pMDI-09.

**Observable in video**: Water/cup presence, rinsing or wiping motion.

## Critical Error Summary

A single critical error = **overall FAIL** regardless of total score.

| ID | Description | Step | Clinical Impact |
|---|---|---|---|
| CRIT-SPC-01 | No shaking | S1 | Inconsistent dose |
| CRIT-SPC-02 | Cap(s) not removed | S2 | Total/partial dose loss |
| CRIT-SPC-03 | No effective seal (mouthpiece or mask) | S4 | Major dose loss via leak |
| CRIT-SPC-04 | Multiple actuations without intervening inhalation | S5 | Reduced respirable fraction (particle coalescence) |
| CRIT-SPC-05 | Inhalation truncated / insufficient tidal breaths | S6 | Partial dose |
| CRIT-SPC-06 | No breath-hold (single-breath protocol only) | S7 | Exhaled dose loss |
| CRIT-SPC-07 | No oral hygiene (ICS) | S8 | Long-term oropharyngeal/facial side effects (not acute dose) |

**Note on coordination errors**: Unlike bare pMDI, actuation-before-inhalation and actuation-after-inhalation (CRIT-pMDI-04/05) are **not** critical errors for spacer use — the chamber buffers the aerosol, which is the core clinical benefit of adding a spacer. Do not penalize timing between actuation and inhalation onset as critical; only penalize excessive delay (S5, non-critical) or multiple actuations before any inhalation (CRIT-SPC-04, critical).

## Overall Verdict Logic

```
IF any critical error detected:
    verdict = FAIL
    reason = "Critical error(s) invalidate dose delivery"
ELSE IF total_score >= 18 (86%):
    verdict = PROFICIENT
ELSE IF total_score >= 14 (67%):
    verdict = ADEQUATE_WITH_EDUCATION
ELSE IF total_score >= 10 (48%):
    verdict = NEEDS_INTENSIVE_TRAINING
ELSE:
    verdict = FAIL
    reason = "Multiple severe deviations"
```

## VLM Observation Guidance

| Step | Visual reliability | Audio reliability | Subtype-specific notes |
|---|---|---|---|
| S1 (shake+assemble) | High (hand motion, insertion) | High (mixing/click sound) | Same both subtypes |
| S2 (caps) | High | Low | Same both subtypes |
| S3 (position/hold) | Moderate (angle, posture) | Low | Face-mask: watch caregiver hand position |
| S4 (seal) | High for mouthpiece (lip closure); **Moderate** for mask (gap visibility depends on camera angle) | Low | Face-mask seal quality is the hardest step to assess visually — flag low-confidence when camera angle obscures mask edge |
| S5 (single actuation timing) | Moderate (finger motion) | High (distinct actuation click count) | Count actuation sounds carefully — this is how double-puffing (CRIT-SPC-04) is detected |
| S6 (inhalation pattern) | High for tidal (visible valve flutter, repeated chest rise); Moderate for single-breath (chest expansion) | Moderate (valve click audible only if camera/mic close) | Determine single-breath vs. tidal protocol from apparent patient age before scoring |
| S7 (hold/completion) | High (chest position, removal timing) | High (silence duration for single-breath hold) | Tidal protocol: no breath-hold expected, do not penalize |
| S8 (oral hygiene) | High | Moderate | Infant: expect wipe, not rinse |

**Recommendation**: Combine visual + audio for S1, S5, S6 — actuation counting (S5) is the step most unique to spacer evaluation and most easily missed on visual-only analysis.

## References

- Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention*. GINA 2024.
- Worth H, Voshaar T, Hartl S, Wright D, Wallace D, Adamus J. German Airway League standardized checklist (spacer addendum).
- Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study: Type, frequency, and association with asthma outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J, Gich I, Pedersen S; ADMIT. *Systematic Review of Errors in Inhaler Use: Has Patient Technique Improved Over Time?* Chest 2016;150(2):394-406.
- Plaza V, Giner J, Rodrigo GJ, et al. *Errors in the use of inhalers by health care professionals: A systematic review.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
- Amirav I, Newhouse MT. *Aerosol therapy with valved holding chambers in young children: importance of the facemask seal.* Pediatrics 2001;108(2):389-394.
- Rubin BK. *Air and soul: the science and application of aerosol therapy.* Respir Care 2010;55(7):911-921.
