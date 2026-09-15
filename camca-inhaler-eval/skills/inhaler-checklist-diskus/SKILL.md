---
name: inhaler-checklist-diskus
description: |
  Standardized step-by-step evaluation checklist for the GlaxoSmithKline Diskus / Accuhaler dry powder inhaler (DPI) and its Diskus-equivalent generic Wixela Inhub, with Levels 0-3 proficiency rubric per step and CRITIKAL-informed critical-error mapping. Use when evaluating Diskus/Accuhaler/Wixela Inhub technique from video, photo, or observation notes; or when an evaluator agent needs the scoring criteria for this device. Covers the 7 core steps (D1-D7, max 21 points) plus conditional ICS mouth-rinse and closing/storage steps, the DPI-universal critical errors (no dose loading, exhaling into the device, weak inspiratory effort, device tilted after loading, no breath-hold, no ICS rinse), and VLM observation guidance for the audible lever click and dose-counter reading. Based on GINA 2024, the GSK Diskus/Accuhaler patient instruction leaflet, CRITIKAL (Price DB et al. 2017), and DPI inspiratory-flow literature.
---

# Diskus / Accuhaler Inhaler Technique Evaluation Checklist

## Scope

This checklist applies to the **multi-dose reservoir-free blister-strip DPI** family built on the GSK Diskus mechanism:

- **Diskus** (US naming) / **Accuhaler** (EU/UK/AU naming) — the same device. Products include fluticasone propionate (Flovent/Flixotide Diskus), salmeterol (Serevent Diskus/Accuhaler), fluticasone-salmeterol (Advair Diskus / Seretide Accuhaler).
- **Wixela Inhub** — a Diskus-equivalent generic fluticasone-salmeterol DPI. The dose-loading mechanism is a slide/lever action rather than GSK's thumbgrip-plus-lever geometry, but the clinical technique requirements (horizontal hold, load-until-click, do-not-tilt, forceful inhalation, breath-hold) are identical, so it is scored with this checklist. Note the mechanical difference only in the free-text observation, not in the score.

**Use a sibling skill instead for other devices:**

| Device | Skill |
|---|---|
| Bare pMDI, no spacer | `inhaler-checklist-pmdi` |
| pMDI with spacer / valved holding chamber (mouthpiece or face-mask) | `inhaler-checklist-pmdi-spacer` |
| AstraZeneca Turbuhaler (twist-grip DPI) | `inhaler-checklist-turbuhaler` |

Confirm the device from the `device-id` output before scoring. Diskus/Accuhaler is distinguishable from Turbuhaler on video by its flat, round, clam-shell body with a side-facing dose counter window, versus Turbuhaler's tall cylindrical body with a colored base grip.

## Critical Conceptual Differences

**Versus pMDI**: Diskus is **breath-actuated**. There is no propellant and no hand-breath coordination requirement; instead the patient's own inspiratory flow must strip and aerosolize the powder from the opened blister. Inhalation must be **fast, forceful and deep** — the exact opposite of the slow inhalation taught for pMDI. Patients switching from pMDI reliably under-perform here.

**Versus Turbuhaler**: Two device-specific reversals that evaluators must not confuse:
1. **Orientation** — Diskus is held and loaded **horizontally** (mouthpiece facing the patient, dose-counter window facing up or toward the patient). Turbuhaler must be held **vertically/upright** for loading. Scoring a Diskus down for "not upright" is an evaluator error.
2. **Loading mechanism** — Diskus loads by a **slide/lever action** (open thumbgrip until it clicks, then push the lever fully back until it clicks), not by a twist.

**Shared with all DPIs**: Once the dose is loaded, the powder sits loose in an opened blister in the inhalation channel. Tilting, shaking, inverting, or dropping the device after loading spills the dose. Exhaling into the mouthpiece introduces humidity that clumps powder — for a Diskus this can degrade the loaded dose *and* the remaining blisters in the strip.

**Inspiratory flow requirement**: The Diskus is a low-to-medium internal-resistance DPI. Adequate dose emission requires roughly **≥30 L/min peak inspiratory flow (PIF)**, with optimal fine-particle delivery around **60 L/min** and above. Patients with severe airflow limitation, acute exacerbation, advanced age, or significant frailty may be unable to generate suboptimal-threshold PIF; if inspiratory effort scores Level 0-1 repeatedly, flag for possible **device-mismatch** and recommend clinician review of device suitability rather than education alone.

## Evaluation Framework

- **7 sequential core steps** (D1–D7), each scored 0–3
- **2 conditional steps** (D8 ICS mouth rinse, D9 closing/storage), each scored 0–3
- **Maximum core score**: **21** (27 with both conditional steps)
- Verdict thresholds are computed on the **core 21-point** score; conditional steps are reported separately and can raise a critical-error flag (D8) but do not change the denominator
- Critical errors override the score-based verdict to FAIL

## Step-by-Step Checklist

### D1 — Hold the Diskus horizontally and open the thumbgrip until it clicks

**Action**: Hold the Diskus flat/horizontal in one hand, with the mouthpiece facing the patient. Place the thumb of the other hand in the thumbgrip and push it **away** from the body, rotating the outer case open, until it **clicks** into the fully open position. The mouthpiece and the lever are now exposed. Briefly inspect the mouthpiece for obstruction, debris, or visible moisture.

**Why it matters**: The Diskus must be opened fully — a partially opened case does not expose the mouthpiece and does not engage the dose-loading lever. The horizontal hold established here must be maintained through D2 and D3; unlike Turbuhaler, a vertical hold is *not* required and, once the dose is loaded, a vertical or tilted hold actively risks losing the powder.

**Rubric**:
- **Level 3** — Device held clearly horizontal; thumbgrip pushed to full open with an audible/visible click; brief mouthpiece inspection
- **Level 2** — Held horizontal, opened fully and clicked, no inspection
- **Level 1** — Case opened only partially (mouthpiece not fully exposed) OR device held at a marked tilt while opening
- **Level 0** — Case not opened, or opened so incompletely that the mouthpiece/lever remain inaccessible

**Critical error mapping**: `CRIT-DSK-01` "Device not opened / mouthpiece not exposed" — no dose can be delivered.

**Observable in video**: Thumb-in-groove motion, rotation of the outer shell, mouthpiece becoming visible, hand plane relative to horizontal.
**Observable in audio**: Opening click (moderate diagnostic value; quieter than the lever click).

---

### D2 — Slide the lever fully back until it clicks (load the dose); confirm the dose counter

**Action**: Keeping the Diskus **horizontal**, slide/push the small lever away from the mouthpiece as far as it will go, until it **clicks**. This pierces and positions one blister of the strip in the inhalation channel. Confirm the **dose counter has decremented by exactly one** (numbers 5 and below are shown in red on GSK devices, indicating the strip is nearly exhausted).

**Why it matters**: This is the dose-metering step and the single most diagnostic mechanical criterion for the device. Without a full lever throw and its click, no blister is opened and inhalation delivers nothing. Conversely, sliding the lever repeatedly before inhaling opens and **wastes** additional blisters — each lever click discards one dose and the counter falls accordingly, which is both dose-wasting and, for combination ICS/LABA products, a source of premature strip exhaustion.

**Rubric**:
- **Level 3** — Lever pushed through its full travel with an audible click, device held horizontal throughout; patient/caregiver checks the dose counter
- **Level 2** — Full lever throw with click, device horizontal, counter not checked
- **Level 1** — Lever motion observed but incomplete/no audible click, OR device visibly tilted during the lever action
- **Level 0** — Lever never operated (patient inhales through an unloaded device) OR lever operated ≥2 times before inhaling (extra blisters wasted)

**Critical error mapping**:
- `CRIT-DSK-02` "Dose not loaded — lever not pushed or no click" — no drug available to inhale
- `CRIT-DSK-03` "Lever operated multiple times before inhalation" — wasted doses, counter over-decrement; patient may run out of medication earlier than expected

**Observable in video**: Lever displacement, thumb/finger travel, dose-counter digits before vs. after (a legible counter change is the strongest visual proof of loading).
**Observable in audio**: Lever click — **very high** diagnostic value, distinctly sharper than the case-opening click.

---

### D3 — Keep the device level: do NOT tilt, shake, or invert after loading

**Action**: After the click, hold the Diskus steady and level while bringing it toward the mouth. Do **not** shake it (unlike a pMDI), do not turn it over, and do not point the mouthpiece downward.

**Why it matters**: The loaded blister is open and the powder is loose in the channel. Tilting, inverting, or shaking the device spills powder out of the mouthpiece before it can be inhaled — a silent failure the patient will never notice, because there is no taste or sensation feedback with a Diskus. Patients transitioning from pMDI frequently shake out of habit; this is a device-inappropriate carry-over error and should be called out explicitly in feedback.

**Rubric**:
- **Level 3** — Device kept level and steady from loading to mouth, no shake, no tilt
- **Level 2** — Minor, brief tilt (<~30°) while raising the device to the mouth; dose loss likely negligible
- **Level 1** — Marked tilt (≥~45°) or mouthpiece pointed downward briefly after loading
- **Level 0** — Device shaken, inverted, or mouthpiece pointed down for a sustained period after loading

**Critical error mapping**: `CRIT-DSK-04` "Device tilted, shaken, or inverted after dose loading" — powder spills from the open blister, partial or total dose loss.

**Observable in video**: Device plane during the hand-to-mouth transit; any oscillating shake motion; mouthpiece direction.

---

### D4 — Exhale fully and gently AWAY from the mouthpiece

**Action**: Turn the head or move the Diskus to the side, exhale gently and completely (to comfortable functional residual capacity / near-empty lungs), and do **not** exhale into or across the mouthpiece.

**Why it matters**: Two distinct benefits and one distinct hazard.
- *Benefit*: exhaling first empties the lungs so the subsequent inhalation can be a single, long, forceful breath to total lung capacity — the deeper the starting deficit, the better the powder is carried to the small airways.
- *Hazard*: exhaled air is warm and ~100% humidified. Blown into a Diskus mouthpiece it wets the open blister and the inhalation channel, clumping the powder so it will not aerosolize. **For DPIs this is more severe than for pMDIs**: with a pMDI, exhaling into the mouthpiece merely disturbs the current puff, whereas with a Diskus moisture can degrade the currently loaded dose and contaminate the channel for subsequent doses from the same strip. Repeated exhalation into the device is a recognized cause of persistent "the inhaler stopped working" complaints.

**Rubric**:
- **Level 3** — Clear, complete exhalation with the device unambiguously away from the mouth (head turned or device moved aside)
- **Level 2** — Exhalation performed, device held to the side but close to the airstream; no direct blowing into the mouthpiece
- **Level 1** — Minimal or absent exhalation before inhaling (starting from near-full lungs limits the achievable inhaled volume), but nothing blown into the device
- **Level 0** — Exhalation directed **into** the mouthpiece (any duration)

**Critical error mapping**:
- `CRIT-DSK-05` "Exhalation into the mouthpiece" — humidity clumps the powder; current dose lost and remaining blisters/channel at risk. Higher severity than the pMDI analogue.
- `CRIT-DSK-06` "No exhalation before inhalation" — flagged as critical only when combined with a clearly truncated inhalation at D6 (i.e., inspired volume is grossly inadequate); otherwise scored as a non-critical Level 1 deviation at D4.

**Observable in video**: Head turn / device displacement, chest and shoulder fall, timing relative to mouthpiece placement.
**Observable in audio**: Exhalation sound and whether it is coloured by passing through the device.

---

### D5 — Place the mouthpiece in the mouth and seal the lips

**Action**: Place the mouthpiece between the teeth and close the lips firmly and evenly around it. Tongue flat on the floor of the mouth, not blocking the mouthpiece opening. Do not bite the mouthpiece shut. Do not cover the small air vents on the device body with fingers or lips.

**Why it matters**: A DPI is a flow-driven device — the entire aerosolization energy comes from the pressure drop the patient generates across the device. Any leak at the lips, or obstruction of the mouthpiece by the tongue, bleeds off that pressure drop and reduces the effective flow through the powder channel, so the dose emitted and the fine-particle fraction both fall. This step is functionally more consequential for a DPI than for a pMDI, where the propellant does the aerosolization work regardless of a modest leak.

**Rubric**:
- **Level 3** — Mouthpiece placed between teeth with a firm, complete lip seal; tongue clearly not obstructing; air vents unobstructed
- **Level 2** — Lip seal present and functional; tongue position or vent obstruction not verifiable from the recording
- **Level 1** — Visible gap, loose seal, cheek movement suggesting leak, or fingers partially over the vents
- **Level 0** — Mouthpiece not properly in the mouth (held in front of the lips, against the teeth only, or under the nose)

**Critical error mapping**: `CRIT-DSK-07` "No effective lip seal / mouthpiece not in mouth" — the inspiratory flow bypasses the powder channel and little or no drug is emitted.

**Observable in video**: Lip closure around the mouthpiece, cheek puffing (leak indicator), mouthpiece insertion depth, finger placement on the device body.

---

### D6 — Inhale FORCEFULLY and DEEPLY (most critical step)

**Action**: Breathe in through the mouthpiece **fast, hard, and deep from the very first instant**, and continue until the lungs are completely full — typically 2–3 seconds in adults, longer in a slow deep breath. The inhalation must be forceful at onset, not ramped up gradually.

**Why it matters**: This is **the** decisive step for Diskus. The dose is entrained and de-agglomerated purely by turbulent airflow through the opened blister and the device channel; if the patient inhales gently, the powder is not stripped from the blister and the little that emerges consists of large agglomerates that deposit in the mouth and oropharynx rather than the lungs. The critical band is:
- **<30 L/min** — sub-threshold; effectively no meaningful lung delivery
- **30–60 L/min** — dose emitted but fine-particle fraction reduced; sub-optimal
- **≥60 L/min** — target range for full dose emission and fine-particle delivery

Because the powder is stripped in the first fraction of a second of flow, a slow start followed by a strong finish is **not** equivalent to a forceful start — score onset, not just peak.

Insufficient inspiratory effort is the most prevalent critical DPI error identified in CRITIKAL and is associated with worse asthma control and higher exacerbation rates.

**Common patient errors**: (a) pMDI-trained patients deliberately inhaling *slowly and gently*, as they were correctly taught for their previous device; (b) genuinely unable to generate adequate PIF because of severe obstruction, exacerbation, frailty, or age — a device-selection problem, not a technique problem.

**Rubric**:
- **Level 3** — Inhalation visibly and audibly forceful from the very start, sustained to apparent full inflation; estimated PIF ≥60 L/min
- **Level 2** — Inhalation moderately forceful or forceful but ramped up rather than immediate; estimated PIF ~40–60 L/min — functional but sub-optimal
- **Level 1** — Inhalation weak-to-moderate, estimated PIF ~30–40 L/min, and/or clearly truncated before full inflation — major deviation, partial aerosolization at best
- **Level 0** — Slow, gentle, pMDI-style inhalation (estimated <30 L/min), or nasal inhalation, or no inhalation through the device at all — dose effectively not delivered

**Critical error mapping**:
- `CRIT-DSK-08` "Insufficient / weak inhalation (estimated PIF <30 L/min)" — powder not aerosolized; the dominant critical DPI error per CRITIKAL
- `CRIT-DSK-09` "Inhalation not forceful from onset" — first-instant flow is what strips the blister; a slow ramp loses the dose even if peak flow is later adequate
- `CRIT-DSK-10` "Inhalation truncated before full inflation" — partial dose, poor peripheral deposition

**If CRIT-DSK-08 is scored, always add the note**: "Confirm whether the patient is *choosing* to inhale gently (educable) or is *unable* to generate adequate inspiratory flow (device mismatch — refer for reassessment and consider a pMDI+spacer or a lower-resistance alternative)."

**Observable in audio**: Inhalation sound onset, sharpness, intensity and duration — **the single most diagnostic signal for this step**.
**Observable in video**: Speed and magnitude of chest/shoulder expansion, nostril and neck-accessory-muscle recruitment, total inspiratory duration.

---

### D7 — Remove the Diskus, hold the breath ~10 seconds, then exhale slowly AWAY from the device

**Action**: Take the Diskus out of the mouth, keeping the lips closed. Hold the breath for about **10 seconds**, or as long as is comfortable. Then exhale slowly through pursed lips, **directed away from the mouthpiece**.

**Why it matters**: Breath-holding lets the fine powder particles that are still suspended in the airways settle onto the airway walls by sedimentation and diffusion. Without a breath-hold a substantial fraction of the respirable dose is simply exhaled back out. Exhaling away from the device remains important even at this stage, because the mouthpiece is still open until D9 and humidity remains harmful to the strip.

**Rubric**:
- **Level 3** — Device removed from mouth, breath held ≥10 sec, then slow controlled exhalation clearly directed away from the device
- **Level 2** — Breath held 5–9 sec, exhalation away from the device
- **Level 1** — Breath held 1–4 sec, and/or exhalation direction not controlled (but not into the mouthpiece)
- **Level 0** — No breath-hold (immediate exhalation) OR exhalation directed into the mouthpiece

**Critical error mapping**:
- `CRIT-DSK-11` "No breath-hold" — the deposited fraction is substantially reduced by immediate exhalation
- `CRIT-DSK-12` "Post-inhalation exhalation into the mouthpiece" — same humidity mechanism as CRIT-DSK-05, affecting remaining doses in the strip

**Observable in video**: Timing of device removal, lip closure, chest held in inspiratory position, direction of the eventual exhalation.
**Observable in audio**: Duration of silence between the end of inhalation and the exhalation sound (a reliable proxy for breath-hold length).

---

### D8 (conditional — ICS-containing products only) — Rinse the mouth, gargle, and spit out

**Applies to**: fluticasone propionate (Flovent/Flixotide Diskus), fluticasone-salmeterol (Advair Diskus, Seretide Accuhaler, Wixela Inhub). **Does not apply to** salmeterol-only (Serevent) — do not penalize a missing rinse for a non-ICS product; mark this step "not applicable".

**Action**: After the breath-hold and exhalation, rinse the mouth thoroughly with water, gargle, and **spit the water out** (do not swallow — swallowing returns the deposited steroid to the GI tract and does not reduce systemic exposure as effectively).

**Why it matters**: Corticosteroid deposited in the oropharynx causes oral candidiasis, dysphonia/hoarseness, and sore throat. Oropharyngeal deposition from a lactose-carrier DPI such as the Diskus is typically **higher** than from a modern HFA pMDI, so rinsing matters more, not less, for this device — and higher still if the patient's inspiratory effort was weak (D6 Level 0-1), because the large agglomerates that fail to aerosolize land directly in the throat.

**Rubric**:
- **Level 3** — Rinses with water, gargles, and spits out
- **Level 2** — Rinses and spits without gargling
- **Level 1** — Rinses and swallows, or drinks water without rinsing
- **Level 0** — No oral care at all after an ICS dose

**Critical error mapping**: `CRIT-DSK-13` "No mouth rinse with ICS-containing product" — not dose-affecting, but flagged critical for cumulative local side-effect risk (candidiasis, dysphonia) and for adherence-threatening symptom burden.

**Observable in video**: Presence of a glass/cup, rinsing and gargling motion, spitting into a sink.
**Observable in audio**: Gargling sound (distinctive and reliable when captured).

---

### D9 (conditional) — Close the Diskus and store it dry

**Action**: Slide the thumbgrip **back toward you** until it **clicks** shut. Closing the device automatically resets the lever, so that the next dose can be loaded. Store the Diskus **closed, flat, and dry** at room temperature — never in a bathroom, never in a damp bag, and never rinsed or washed with water. Discard when the dose counter reaches **0**, or by the labelled in-use expiry after the foil overwrap is opened (commonly ~1 month for Advair Diskus; check the product label), whichever comes first.

**Why it matters**: Leaving the case open exposes the mouthpiece and the powder channel to ambient humidity and to pocket/bag debris, degrading the remaining blisters. Failing to close also means the lever is not reset, so the next dose may not load. The device cannot be washed — moisture is the principal enemy of every step of DPI function.

**Rubric**:
- **Level 3** — Thumbgrip slid fully closed with a click; device set down flat and dry; dose counter noted
- **Level 2** — Device closed properly, counter not checked, storage not observable
- **Level 1** — Case only partially closed, or device put away open into a pocket/bag
- **Level 0** — Case left open, or device exposed to water (rinsed/washed) or a humid environment (bathroom shelf, next to a sink)

**Critical error mapping**: `CRIT-DSK-14` "Device left open / stored damp" — humidity progressively degrades all remaining doses in the strip; a delayed-onset failure the patient will attribute to the medication rather than the technique.

**Observable in video**: Closing motion and click, where the device is placed afterward, dose-counter reading at the end of the sequence.

## Critical Error Summary — Diskus / Accuhaler / Wixela Inhub

A single critical error = **overall FAIL** regardless of total score.

| ID | Description | Step | Clinical Impact |
|---|---|---|---|
| CRIT-DSK-01 | Device not opened / mouthpiece not exposed | D1 | No dose delivery possible |
| CRIT-DSK-02 | Dose not loaded — lever not pushed fully / no click | D2 | No dose loaded; patient inhales through an empty channel |
| CRIT-DSK-03 | Lever operated multiple times before inhalation | D2 | Blisters wasted, counter over-decrements, early strip exhaustion |
| CRIT-DSK-04 | Device tilted, shaken, or inverted after loading | D3 | Powder spills from the open blister — partial/total dose loss, no patient-perceptible cue |
| CRIT-DSK-05 | Exhalation into the mouthpiece (pre-inhalation) | D4 | Humidity clumps powder — current dose lost and remaining strip degraded; **more severe for DPI than pMDI** |
| CRIT-DSK-06 | No exhalation before inhalation (critical only if combined with truncated inhalation at D6) | D4 | Inadequate inspired volume, poor peripheral deposition |
| CRIT-DSK-07 | No effective lip seal / mouthpiece not in mouth | D5 | Inspiratory flow bypasses the powder channel; little drug emitted |
| CRIT-DSK-08 | Insufficient / weak inhalation (estimated PIF <30 L/min) | D6 | Powder not aerosolized — **the dominant critical DPI error per CRITIKAL**; may indicate device mismatch |
| CRIT-DSK-09 | Inhalation not forceful from onset (slow ramp-up) | D6 | First-instant flow strips the blister; dose lost despite adequate peak flow |
| CRIT-DSK-10 | Inhalation truncated before full inflation | D6 | Partial dose, poor small-airway deposition |
| CRIT-DSK-11 | No breath-hold | D7 | Suspended respirable fraction exhaled straight back out |
| CRIT-DSK-12 | Post-inhalation exhalation into the mouthpiece | D7 | Humidity damage to remaining doses in the strip |
| CRIT-DSK-13 | No mouth rinse with ICS-containing product | D8 | Oral candidiasis, dysphonia (cumulative, not acute dose loss) |
| CRIT-DSK-14 | Device left open / stored damp / washed with water | D9 | Progressive degradation of all remaining blisters |

**CRITIKAL context (DPI subgroup)**: insufficient inspiratory effort was the DPI critical error most strongly and consistently associated with worse asthma control and increased exacerbation rate; failure to exhale away from the device and absent breath-hold were also highly prevalent. Sanchis et al. (Chest 2016) found DPI technique error rates essentially unimproved across four decades, with inadequate inspiratory force and absent breath-hold among the most frequent, and Plaza et al. (2018) showed the same errors are common among the **health-care professionals** doing the teaching — so do not assume prior instruction was correct.

## Overall Verdict Logic

Thresholds are identical to the pMDI, pMDI+spacer, and Turbuhaler checklists, computed over the **core 21-point** score (D1–D7):

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

Conditional steps D8 and D9 are reported alongside the core score and may independently raise `CRIT-DSK-13` / `CRIT-DSK-14`, which do trigger the critical-error FAIL branch, but their points are not added to the 21-point denominator.

## VLM Observation Guidance

| Step | Visual reliability | Audio reliability | Notes |
|---|---|---|---|
| D1 (horizontal hold + open thumbgrip) | **High** | Moderate | Hand plane and shell rotation are clearly visible; opening click is softer than the lever click. Do **not** penalize a horizontal hold here — that is correct for Diskus, unlike Turbuhaler |
| D2 (lever slide + click + counter) | **High** | **VERY HIGH** | The lever click is the single most diagnostic mechanical cue. If the dose-counter window is legible, a digit change before vs. after is near-definitive proof of loading — zoom/frame-sample the counter when resolution allows |
| D3 (no tilt/shake after loading) | **High** | Low | Track the device plane frame-by-frame from click to mouth. A shake motion is unmistakable and is a common pMDI carry-over |
| D4 (exhale away) | High | High | Head turn / device displacement is visually evident; the timbre of the exhalation reveals whether it passed through the device |
| D5 (lip seal) | High | Low | Cheek puffing indicates leak; insertion depth and finger position over vents are visible with a frontal angle |
| D6 (FORCEFUL deep inhalation) | **Low–Moderate** | **VERY HIGH** | Inspiratory force is **very hard to assess visually** — chest expansion speed is a weak, body-habitus- and clothing-dependent proxy. The inhalation sound's onset sharpness, intensity, and duration are far more informative. **If audio is unavailable or unusable, flag D6 with low confidence and state explicitly that PIF adequacy could not be assessed** rather than inferring a score from video alone |
| D7 (breath-hold) | High | High | Duration of silence between inhalation end and exhalation onset is a reliable timer; device-removal timing is visible |
| D8 (ICS rinse) | High | Moderate | Cup/sink presence; gargling sound is distinctive when captured. Verify product is ICS-containing before scoring |
| D9 (close + store) | High | Moderate | Closing click plus where the device is set down; end-of-video counter reading |

**Recommendations for VLM agents evaluating a Diskus:**
1. **Audio is co-equal with — and at D6 superior to — video.** Request or require an audio track. Two of the three highest-value signals for this device (the lever click at D2, the inspiratory sound at D6) are auditory.
2. **Read the dose counter.** It is the only objective, machine-readable state indicator on the device. Capture it at the start and end of the clip; a decrement of exactly 1 corroborates D2 Level 3, a decrement of ≥2 confirms `CRIT-DSK-03`, and no decrement supports `CRIT-DSK-02`.
3. **Never silently guess at D6.** Report an explicit confidence level for the inspiratory-force judgement, and downgrade confidence when audio is absent, the microphone is distant, or ambient noise masks the breath.
4. **Do not import Turbuhaler orientation rules.** Horizontal is correct for Diskus. A vertical hold during loading is at best neutral and, after loading, is itself a `CRIT-DSK-04` risk.

## Switching-Patient Notes (Clinical Context)

**From pMDI to Diskus** — expect and specifically probe for:
- Slow, gentle inhalation (D6) — the most common and most damaging carry-over; the patient is applying correct pMDI technique to the wrong device
- Shaking the device before use (D3) — correct for pMDI, harmful once a Diskus dose is loaded
- Waiting for a taste, spray sensation, or "puff" feedback and re-dosing when none arrives (D2, `CRIT-DSK-03`) — Diskus delivery is largely imperceptible apart from a faint lactose sweetness; counsel explicitly that absence of sensation does not mean absence of dose

**From Turbuhaler to Diskus** — expect:
- Vertical/upright holding and a twisting motion attempted on a device that requires horizontal holding and a slide (D1, D2)
- Generally *better* D6 performance, since forceful inhalation was already required

**Patients using both a Diskus and a pMDI concurrently** (common: ICS/LABA Diskus maintenance plus SABA pMDI reliever) are at elevated risk of applying the wrong inhalation pattern to each. Evaluate and educate on both devices in the same session, and make the "slow for the pMDI, fast and hard for the Diskus" contrast explicit — this contrast is the single highest-yield teaching point for these patients.

## References

- Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention*. GINA 2024.
- GlaxoSmithKline. *Diskus / Accuhaler patient instructions for use* (Advair Diskus, Seretide Accuhaler, Flovent Diskus, Serevent Diskus prescribing information and patient leaflets).
- Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study: Type, frequency, and association with asthma outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J, Gich I, Pedersen S; ADMIT. *Systematic Review of Errors in Inhaler Use: Has Patient Technique Improved Over Time?* Chest 2016;150(2):394-406.
- Plaza V, Giner J, Rodrigo GJ, Dolovich MB, Sanchis J. *Errors in the use of inhalers by health care professionals: A systematic review.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
- Laube BL, Janssens HM, de Jongh FH, et al. *What the pulmonary specialist should know about the new inhalation therapies.* Eur Respir J 2011;37(6):1308-1331. (ERS/ISAM task force: DPI inspiratory flow requirements, minimum vs. optimal PIF.)
- Ghosh S, Ohar JA, Drummond MB. *Peak Inspiratory Flow Rate in Chronic Obstructive Pulmonary Disease: Implications for Dry Powder Inhalers.* J Aerosol Med Pulm Drug Deliv 2017;30(6):381-387. (Suboptimal PIF thresholds and device mismatch.)
- Chrystyn H. *The Diskus: a review of its position among dry powder inhaler devices.* Int J Clin Pract 2007;61(6):1022-1036. (Diskus-specific device resistance and flow-dependence data.)
