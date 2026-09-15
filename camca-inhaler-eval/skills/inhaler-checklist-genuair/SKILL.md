---
name: inhaler-checklist-genuair
description: |
  Standardized step-by-step evaluation checklist for the Genuair dry powder inhaler (DPI) — marketed as Eklira Genuair / Tudorza Pressair (aclidinium), Duaklir Genuair / Duaklir Pressair (aclidinium/formoterol) and Brimica Genuair (aclidinium/formoterol); "Pressair" is the United States trade name for the identical device — with a Levels 0-3 proficiency rubric per step and CRITIKAL-informed critical-error mapping. Use when evaluating Genuair/Pressair technique from video, photo, or observation notes; or when an evaluator agent needs the scoring criteria for this device. Covers the 7 core steps (G1-G7, max 21 points) plus conditional mouth-rinse (usually N/A — Genuair products are LAMA or LAMA/LABA and do NOT contain an inhaled corticosteroid) and cap-replacement/storage steps, the Genuair-specific critical errors (green button not pressed so the control window stays RED and no dose is loaded, holding the green button down during inhalation which blocks dose release, exhaling into the mouthpiece, inspiratory effort too weak to trigger the audible CLICK, control window still GREEN after inhalation meaning the dose was never taken, no breath-hold), and VLM observation guidance built around this device's unique built-in feedback: a RED-to-GREEN-to-RED control-window colour change plus an audible click. Based on GINA 2024, the AstraZeneca/Covis Genuair-Pressair product information and instructions for use, CRITIKAL (Price DB et al. 2017), and DPI inspiratory-flow literature.
---

# Genuair / Pressair Inhaler Technique Evaluation Checklist

## Scope

This checklist applies to the **Genuair** multi-dose reservoir dry powder inhaler, sold in the United States under the name **Pressair**. The device body, the green dose-loading button, the coloured control window and the audible click are identical across all products, so one checklist covers all of them:

- **Eklira Genuair** (EU) / **Tudorza Pressair** (US) — aclidinium bromide (LAMA) — *not ICS-containing*
- **Duaklir Genuair** (EU) / **Duaklir Pressair** (US) — aclidinium + formoterol (LAMA/LABA) — *not ICS-containing*
- **Brimica Genuair** (EU) — aclidinium + formoterol (LAMA/LABA) — *not ICS-containing*

All currently marketed Genuair/Pressair products are **COPD maintenance bronchodilators (LAMA or LAMA/LABA)**. **None contains an inhaled corticosteroid.** The mouth-rinse step is therefore normally scored **N/A** and excluded from the denominator — see G8 below, and do not penalise a patient for omitting it.

**Use a sibling skill instead for other devices:**

| Device | Skill |
|---|---|
| Bare pMDI, no spacer | `inhaler-checklist-pmdi` |
| pMDI with spacer / valved holding chamber (mouthpiece or face-mask) | `inhaler-checklist-pmdi-spacer` |
| AstraZeneca Turbuhaler (twist-grip DPI) | `inhaler-checklist-turbuhaler` |
| GSK Diskus / Accuhaler, Wixela Inhub (thumbgrip + lever DPI) | `inhaler-checklist-diskus` |
| GSK Ellipta (sliding-cover DPI) | `inhaler-checklist-ellipta` |

Confirm the device from the `device-id` output before scoring. On video the Genuair/Pressair is unmistakable: a rounded, chunky white body with a **large green button on the top**, a **coloured control window** on the same face as the button, a **dose indicator scale** on the back, and a **cap removed by squeezing two arrow marks on the sides** (not unscrewed, not slid, not hinged). If a twist grip, a lever, a thumbgrip or a sliding cover is visible, the wrong checklist has been selected.

## Critical Conceptual Differences

**Versus pMDI**: Genuair is **breath-actuated**. There is no propellant, no shaking, and no hand-breath coordination requirement; the patient's own inspiratory flow must aerosolize the powder. Inhalation must be **strong, deep and sustained** — the opposite of the slow inhalation taught for pMDI. Patients switching from a pMDI reliably under-perform on this step.

**Versus Turbuhaler, Diskus and Ellipta — the defining Genuair feature**: Genuair is the only widely used DPI with a **closed-loop, two-way feedback system that tells the patient (and the evaluator) whether each half of the manoeuvre actually worked**:

1. **Loading feedback (visual).** Pressing the green button fully down turns the control window from **RED to GREEN**. Green = a dose is metered and ready.
2. **Inhalation feedback (audio + visual).** A sufficiently forceful inhalation triggers an audible **CLICK** from the device, and the control window turns back from **GREEN to RED**. Red again = the dose was genuinely inhaled.

This means the two most common and most consequential DPI failures — *dose never loaded* and *inspiratory flow too weak to deliver the dose* — are **directly observable** rather than inferred. Treat the window colour sequence **RED → GREEN → RED** as the spine of the entire evaluation.

**The Genuair-unique handling error**: the green button must be **pressed all the way down and then RELEASED completely before inhaling**. Many patients press and *keep holding* the button down while they inhale (a habit imported from pMDI actuation, where you press and hold during inhalation). On Genuair, **holding the button down blocks the dose-release mechanism**: the powder is not released, the click does not sound, and the window does not return to red. This is a classic, device-specific, high-frequency error and must be scored explicitly.

## Evaluation Framework

- **7 sequential steps** (G1–G7), each scored 0–3
- **2 conditional steps** (G8 mouth rinse — *usually N/A for Genuair*, G9 cap replacement / storage / dose indicator)
- **Maximum core score**: 21 (27 if both conditional steps are applicable and scored)
- Critical errors override the score-based verdict to FAIL

## Step-by-Step Checklist

### G1 — Check the dose indicator, remove the cap by squeezing the side arrows

**Action**: Check the dose indicator on the back of the device for remaining doses. Remove the protective cap by **squeezing the two arrows marked on the sides of the cap** and pulling it straight off. Inspect the mouthpiece for foreign objects or powder residue.

**Why it matters**: The cap is released by lateral pressure on the arrow marks — it is not unscrewed and not levered off. Patients who try to twist or pry it may fail to open the device, or may damage the mouthpiece. Checking the indicator prevents attempting a dose from an exhausted device, which will produce no click and no colour change and will be misread by the patient as their own technique failure.

**Rubric**:
- **Level 3** — Glances at dose indicator, squeezes the side arrows, cap comes off cleanly, brief mouthpiece inspection
- **Level 2** — Cap removed correctly by squeezing the arrows, no indicator check and no inspection
- **Level 1** — Cap removed only after fumbling / twisting / prying, or removed with excessive force
- **Level 0** — Cap not removed, or attempts to use the device with the cap still on

**Critical error mapping**: `CRIT-GEN-08` "Attempting to use with cap on / device exhausted (striped band or indicator at 0)"

**Observable in video**: Grip on the sides of the cap, squeezing motion of thumb and forefinger, cap detaching straight off, eyes directed to the indicator scale.

---

### G2 — Hold horizontally: mouthpiece toward you, GREEN BUTTON UP

**Action**: Hold the inhaler **horizontally**, with the **mouthpiece facing towards you** and the **green button facing upwards**. Do not tilt, invert or point the button downwards.

**Why it matters**: The metering mechanism loads correctly only when the button is uppermost and the device is level. If the device is tilted or held with the button sideways/downwards while loading, the metered powder can be displaced from the dosing chamber and the dose may be partly or wholly lost even though the window turns green. This orientation also keeps the control window in the patient's line of sight, which is essential for them to use the built-in feedback at all.

**Rubric**:
- **Level 3** — Device held level and steady, mouthpiece towards the mouth, green button clearly uppermost, control window visible to the patient
- **Level 2** — Correct orientation but not perfectly level, or held so the window is not in the patient's view
- **Level 1** — Noticeably tilted (>45°) or button held sideways during loading
- **Level 0** — Device inverted / button pointing down, or mouthpiece pointing away from the patient during loading

**Critical error mapping**: `CRIT-GEN-07` "Device tilted or inverted during loading" — metered powder displaced

**Observable in video**: Wrist and forearm angle, position of the green button relative to the device body, direction the mouthpiece points.

---

### G3 — Press the green button ALL THE WAY DOWN, then RELEASE it fully (window RED → GREEN)

**Action**: Press the green button **fully down** in one firm movement, then **let go of it completely**. Confirm that the **control window has changed from RED to GREEN**. Do **not** keep the button pressed.

**Why it matters**: This is the dose-metering step and the first half of the device's feedback loop. A partial press does not meter a dose and the window stays red. Critically, **the button must be released before inhaling** — if it is held down, the internal mechanism stays locked and the dose cannot be released to the airstream no matter how well the patient inhales. The green window is the objective proof that a dose is ready; a patient who inhales with a red window inhales nothing but air.

**Common patient error**: pressing and **holding** the button throughout inhalation, carried over from pMDI actuation technique. This is the single most characteristic Genuair-specific error.

**Rubric**:
- **Level 3** — Button pressed fully down in one firm action, released completely, patient visibly checks the window and it is GREEN
- **Level 2** — Button pressed fully and released, window turns green, but the patient does not look at the window
- **Level 1** — Hesitant / partial press requiring a second attempt, or the button is released only just before inhalation begins; window eventually green
- **Level 0** — Button not pressed at all, or window remains RED, or the button is still held down when inhalation starts

**Critical error mapping**:
- `CRIT-GEN-01` "Green button not pressed / control window still RED — dose not loaded"
- `CRIT-GEN-02` "Green button held down during inhalation — dose release blocked"

**Observable in video**: Thumb travel on the green button (full depression vs. partial), the thumb **lifting off** the button, and the **control window colour change from red to green** — a direct, unambiguous visual event.

---

### G4 — Exhale fully AWAY from the device

**Action**: Move the inhaler away from the mouth and breathe out as fully and comfortably as possible. **Never exhale into the mouthpiece.**

**Why it matters**: Two reasons. First, exhaling to near residual volume maximises the subsequent inspiratory volume and flow, which is what aerosolizes the powder. Second, exhaled breath is warm and humid: moisture blown into a reservoir DPI clumps the powder in the dosing chamber, degrading the current dose and potentially subsequent doses. Because the dose is **already metered and sitting in the chamber** at this point (the window is green), exhaling into a loaded Genuair is particularly damaging.

**Rubric**:
- **Level 3** — Full, unhurried exhalation with the device held clearly away from the face
- **Level 2** — Exhalation performed but shallow, or the device held close to but not at the mouth
- **Level 1** — Minimal or no exhalation before inhaling, but not into the device
- **Level 0** — Exhaled INTO the mouthpiece (any duration)

**Critical error mapping**: `CRIT-GEN-03` "Exhalation into the mouthpiece" — moisture clumps the metered powder

**Observable in video + audio**: Device position relative to the mouth during exhalation, chest deflation, direction and sound of the exhaled breath, mouthpiece fogging.

---

### G5 — Lips sealed firmly around the mouthpiece

**Action**: Put the mouthpiece between the lips and **close the lips tightly** around it. Keep the tongue flat and out of the mouthpiece opening. Keep the device horizontal and do not obstruct the air inlets with the fingers or lips.

**Why it matters**: The device generates the turbulence needed to de-agglomerate the powder from the patient's own inspiratory flow. Any leak around the lips bleeds off that flow, and a weak flow means no click, no colour change and no dose. A poor seal is one of the commonest reasons a technically willing patient fails to trigger the click.

**Rubric**:
- **Level 3** — Tight, complete lip seal; tongue clear of the mouthpiece; air inlets unobstructed; device still horizontal
- **Level 2** — Adequate seal, tongue position not verifiable from the recording
- **Level 1** — Visible gap, loose lips, cheeks puffing during inhalation, or fingers partly over an air inlet
- **Level 0** — Mouthpiece not properly in the mouth, or teeth/lips blocking the opening

**Critical error mapping**: None assigned directly — a failed seal manifests as `CRIT-GEN-04` at G6 (no click).

**Observable in video**: Lip closure around the mouthpiece, cheek movement (puffing = leak), finger placement on the device body, mouthpiece insertion depth.

---

### G6 — Inhale STRONGLY and DEEPLY until you hear the CLICK — then keep inhaling

**Action**: Breathe in **strongly and deeply** through the mouthpiece. Continue until an audible **CLICK** is heard — the click is the device confirming that the dose has been released and correctly inhaled — and then **keep inhaling for as long as comfortable after the click**. Do not stop at the click.

**Why it matters**: This is **the** critical step and the second half of the feedback loop. The click sounds only when inspiratory flow is sufficient to trigger the release mechanism (i.e. a genuinely adequate PIF). No click means the flow was inadequate and the dose has **not** been delivered. Equally important, patients who stop inhaling the instant they hear the click truncate the manoeuvre and leave drug in the mouth and throat rather than the lungs — the click occurs *during*, not at the end of, a correct inhalation. Slow/weak inhalation is the most prevalent critical DPI error identified in CRITIKAL.

**Common patient errors**: (a) pMDI-style slow gentle inhalation — no click, no dose; (b) stopping the moment the click sounds; (c) inhaling with the green button still held down, in which case the click will never sound however hard the patient inhales (see `CRIT-GEN-02`).

**Rubric**:
- **Level 3** — Forceful, deep inhalation from the outset; **click clearly audible**; inhalation continues for several seconds after the click to apparent full lung capacity
- **Level 2** — Click audible, but inhalation is only moderately forceful or stops shortly after the click
- **Level 1** — Inhalation weak / slow; click delayed, faint or occurs only on a second attempt; or clearly truncated inhalation
- **Level 0** — **No click at any point** (inhalation too weak, seal failed, or button held down) — dose not delivered

**Critical error mapping**:
- `CRIT-GEN-04` "Inhalation too weak to trigger the click" — dose not released
- `CRIT-GEN-06` "Inhalation stopped at the click / truncated" — partial lung deposition

**Observable in audio**: The **click** (very high diagnostic value — a discrete mechanical sound) and the intensity/onset of the inhalation sound.
**Observable in video**: Speed and magnitude of chest and shoulder expansion, inhalation duration, whether the thumb is off the green button.

---

### G7 — Hold breath ~10 seconds, remove the inhaler, exhale away — then VERIFY the window is RED again

**Action**: Remove the inhaler from the mouth, **hold the breath for about 10 seconds** (or as long as comfortable), then breathe out slowly through the nose or pursed lips, **away from the device**. Then **look at the control window: it must have changed from GREEN back to RED**, confirming the dose was actually taken. If it is still green, the dose was not inhaled and the manoeuvre must be repeated.

**Why it matters**: The breath-hold lets the fine particles sediment onto the airway walls instead of being exhaled straight back out; omitting it is one of the most frequent critical errors across all inhaler classes. The **green → red window check** is the device's final confirmation and is unique among common DPIs: it gives an objective, retrospective answer to "did the drug actually go in?" Patients should be explicitly taught to perform this check every time, and evaluators should score whether they do.

**Rubric**:
- **Level 3** — Breath-hold ≥10 s, inhaler removed, slow controlled exhalation away from the device, **and the patient checks the control window, which is RED**
- **Level 2** — Breath-hold 5–9 s, exhalation away from the device; window is red but the patient does not check it
- **Level 1** — Breath-hold 1–4 s, or exhalation directed towards the device
- **Level 0** — No breath-hold (immediate exhalation), **or the control window is still GREEN after the attempt** (dose not taken)

**Critical error mapping**:
- `CRIT-GEN-05` "Control window still GREEN after inhalation" — dose was never actually inhaled
- `CRIT-GEN-09` "No breath-hold"

**Observable in video**: Mouth closed and still, elapsed silent time before exhalation, direction of exhalation, the patient's gaze returning to the window, and **the window colour itself (green vs. red) after the attempt** — a direct read-out of success or failure.

---

### G8 (conditional — ICS-containing products only; **normally N/A for Genuair**) — Rinse mouth, gargle and spit

**Action**: For ICS-containing inhalers — rinse the mouth with water, gargle and **spit out, do not swallow**.

**Applicability**: **All currently marketed Genuair/Pressair products (Eklira/Tudorza, Duaklir, Brimica) are LAMA or LAMA/LABA and contain NO inhaled corticosteroid.** For these products this step is **N/A**: score it as `N/A`, exclude it from the denominator, and **do not** record `CRIT-GEN-10` or deduct any points when the patient does not rinse.

Score this step only if the evaluated device is genuinely an ICS-containing product — for example if the patient's regimen includes a *separate* ICS inhaler used in the same session, or if a future ICS-containing Genuair presentation is being assessed. In a mixed-device session, apply the rinse requirement to the ICS device's own checklist, not to the Genuair.

**Rubric** (only when applicable):
- **Level 3** — Rinses, gargles and spits out
- **Level 2** — Rinses and spits without gargling
- **Level 1** — Rinses and swallows the water
- **Level 0** — No rinse
- **N/A** — Non-ICS product (the default for Genuair/Pressair)

**Clinical note (still worth teaching)**: aclidinium is an antimuscarinic and commonly causes **dry mouth**; a plain water rinse is a reasonable comfort measure and may reduce local irritation, but it is **not** a scored technique requirement and its omission is not an error.

**Critical error mapping**: `CRIT-GEN-10` "No mouth rinse with an ICS-containing product" — **not applicable to standard Genuair products**.

---

### G9 (conditional) — Replace the cap, check the dose indicator, store dry

**Action**: Put the protective cap back on the mouthpiece and press it into place. Check the dose indicator on the back: it moves in steps of 10, and when the **red striped band** appears in the indicator the device is **near empty** and a replacement should be obtained. When the last dose has been taken the device **locks** and cannot be re-loaded — it must be discarded. Store the inhaler in a dry place, away from bathrooms and other humid environments, and keep it in its pouch until first use.

**Why it matters**: The cap protects the mouthpiece from moisture and contamination between doses; a reservoir DPI left open in a humid room will clump. The striped band is the patient's advance warning to obtain a refill before running out — missing it is a common cause of unintentional treatment gaps in COPD. The end-of-life lock-out is a safety feature, not a fault, and patients should be told about it so they do not interpret a locked device as broken.

**Rubric**:
- **Level 3** — Cap replaced firmly, indicator checked, device stored in a dry place
- **Level 2** — Cap replaced, no indicator check
- **Level 1** — Cap replaced loosely / not fully seated
- **Level 0** — Cap not replaced, device left open and exposed to moisture

**Critical error mapping**: `CRIT-GEN-08` (device exhausted / striped band ignored / cap not replaced) — see summary table.

## Critical Error Summary — Genuair / Pressair

| ID | Description | Step | Clinical Impact |
|---|---|---|---|
| CRIT-GEN-01 | Green button not pressed (or only partially) — control window still RED | G3 | No dose metered; patient inhales air only |
| CRIT-GEN-02 | Green button held DOWN during inhalation instead of released | G3, G6 | Dose-release mechanism blocked; no click, no dose delivered |
| CRIT-GEN-03 | Exhalation into the mouthpiece | G4 | Moisture clumps the already-metered powder; current and later doses degraded |
| CRIT-GEN-04 | Inhalation too weak/slow to trigger the CLICK | G6 | Powder not released or not aerosolized — most prevalent critical DPI error per CRITIKAL |
| CRIT-GEN-05 | Control window still GREEN after the attempt | G7 | Objective proof the dose was never inhaled — full dose lost |
| CRIT-GEN-06 | Inhalation stopped at the click / truncated | G6 | Partial dose; drug deposits in the oropharynx rather than the lungs |
| CRIT-GEN-07 | Device tilted or inverted while loading | G2 | Metered powder displaced from the dosing chamber |
| CRIT-GEN-08 | Cap left on / device exhausted (striped band or locked) / cap not replaced | G1, G9 | No dose available; moisture ingress; unintentional treatment gap |
| CRIT-GEN-09 | No breath-hold | G7 | Fine particles exhaled before deposition |
| CRIT-GEN-10 | No mouth rinse with an ICS-containing product — **N/A for standard Genuair (LAMA / LAMA-LABA)** | G8 | Oropharyngeal candidiasis, dysphonia (only if an ICS is actually involved) |

**CRITIKAL context**: in the DPI subgroup, insufficient inspiratory effort was the dominant critical error, followed by failure to breath-hold and exhalation into the device. Genuair's design does not remove these errors, but — uniquely — it **exposes** the first and third of them in real time via the click and the window colour, which is why patient self-checking of the window should itself be taught and scored.

## Overall Verdict Logic

Same thresholds as the sibling device checklists (core steps G1–G7, maximum 21):

```
IF any critical error detected:
    verdict = FAIL
ELSE IF total_score >= 18 (86%):
    verdict = PROFICIENT
ELSE IF total_score >= 14 (67%):
    verdict = ADEQUATE_WITH_EDUCATION
ELSE IF total_score >= 10 (48%):
    verdict = NEEDS_INTENSIVE_TRAINING
ELSE:
    verdict = FAIL
```

Conditional steps G8 (when applicable) and G9 are scored and reported separately; when G8 is `N/A` — the normal case for Genuair — it is excluded from both numerator and denominator and never contributes a critical error.

## VLM Observation Guidance

| Step | Visual reliability | Audio reliability | Notes |
|---|---|---|---|
| G1 (cap off via side arrows, indicator) | High | Low | Squeeze-and-pull motion is distinctive; indicator digits may need a zoomed frame |
| G2 (horizontal, button UP) | High | Low | Wrist angle and button position are easy to read from a single frame |
| G3 (press fully, RELEASE; RED → GREEN) | **VERY HIGH** | Low | The window **colour change is a direct, frame-level visual event**. Also verify the thumb **lifts off** the button — a held-down thumb is `CRIT-GEN-02` |
| G4 (exhale away) | High | High | Device position relative to the face plus exhalation sound direction |
| G5 (lip seal) | High | Low | Cheek puffing indicates a leak |
| G6 (strong inhale until CLICK) | Moderate | **VERY HIGH** | The **click** is a discrete mechanical sound and the single best audio cue; also check inhalation continues past it |
| G7 (breath-hold; GREEN → RED) | **VERY HIGH** | High | Silence duration for the hold; the **post-attempt window colour is a definitive visual verdict** on dose delivery |
| G8 (rinse) | High | Moderate | Normally N/A — do not flag its absence |
| G9 (cap back, indicator/striped band) | High | Low | Striped band may require a zoomed or paused frame |

**Why this device is unusually well suited to VLM assessment**: most inhalers force the evaluator to *infer* whether a dose was loaded and whether inspiratory flow was adequate, and on Turbuhaler, Diskus and Ellipta the decisive confirmatory cues are largely **audio** (a click on loading, inhalation sound intensity). Genuair is the exception: the **RED → GREEN → RED control-window sequence is an exceptionally high-reliability *visual* signal** that reports both dose loading and dose delivery directly, in colour, on the device itself — no inference from breathing sounds required. Combined with the **high-reliability audible click** at G6, this gives two independent, objective confirmations of the two hardest-to-judge events in DPI technique.

**Practical guidance for VLM agents**:
- Prioritise obtaining clear frames of the **control window** immediately after the button press and immediately after the inhalation. These two frames alone resolve `CRIT-GEN-01`, `CRIT-GEN-02`, `CRIT-GEN-04` and `CRIT-GEN-05`.
- If the window is not visible in the recording (obscured by the hand, out of frame, poor lighting), **do not infer** the colour — mark G3/G7 window confirmation as `UNVERIFIABLE`, cap the step at Level 2, and recommend a re-recording with the button face towards the camera.
- Watch the thumb through the whole inhalation: continued contact with a depressed green button is `CRIT-GEN-02` even if everything else looks correct.
- Reason about consistency: green window + no click + window still green is a coherent picture of a failed inhalation (or a held button); red window from the start means the dose was never loaded.

## Switching-Patient Notes (Clinical Context)

When evaluating a patient who has switched to Genuair/Pressair from another device:

- **From a pMDI**: expect two carry-over errors — slow gentle inhalation (fails to trigger the click, `CRIT-GEN-04`) and press-and-hold actuation habit (`CRIT-GEN-02`). Teach explicitly: "press, let go, then breathe in hard."
- **From Turbuhaler or Diskus**: loading is a button press, not a twist or a lever; patients may hunt for a grip. Orientation also differs — Turbuhaler must be upright, Genuair must be horizontal with the button up.
- **From Ellipta**: patients accustomed to "open the cover = dose loaded" may remove the Genuair cap and inhale without ever pressing the green button (`CRIT-GEN-01`). The red window is the teaching anchor.
- **In all cases**, use the window as the education tool: ask the patient to narrate the colours ("red, now green, now red again"). Patients who can do this reliably self-correct most of the errors above without further coaching.

## References

- Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention*. GINA 2024.
- AstraZeneca / Covis Pharma. *Genuair / Pressair instructions for use and product information* (Eklira Genuair and Tudorza Pressair aclidinium bromide; Duaklir Genuair / Duaklir Pressair and Brimica Genuair aclidinium bromide + formoterol fumarate — summary of product characteristics, US prescribing information and patient information leaflets).
- Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study: Type, frequency, and association with asthma outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J, Gich I, Pedersen S; ADMIT. *Systematic Review of Errors in Inhaler Use: Has Patient Technique Improved Over Time?* Chest 2016;150(2):394-406.
- Plaza V, Giner J, Rodrigo GJ, Dolovich MB, Sanchis J. *Errors in the use of inhalers by health care professionals: A systematic review.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
- Laube BL, Janssens HM, de Jongh FH, et al. *What the pulmonary specialist should know about the new inhalation therapies.* Eur Respir J 2011;37(6):1308-1331. (ERS/ISAM task force: DPI inspiratory flow requirements, minimum vs. optimal PIF.)
