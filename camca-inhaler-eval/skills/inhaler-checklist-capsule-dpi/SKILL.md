---
name: inhaler-checklist-capsule-dpi
description: |
  Standardized step-by-step evaluation checklist for capsule-based dry powder inhalers (single-capsule-load DPIs) — Boehringer Ingelheim HandiHaler (tiotropium), Novartis Breezhaler (Onbrez / Seebri / Ultibro / Enerzair), Neohaler (US Breezhaler equivalent), and similar devices requiring the patient to load and pierce one capsule per dose. Provides 7 core steps (C1–C7) scored on a Levels 0–3 proficiency rubric, conditional steps for ICS rinse / capsule disposal / storage, and CRITIKAL-informed critical-error mapping (CRIT-CAP-01 onward). Use when evaluating capsule DPI technique from video, photo, or observation notes; when an evaluator or VLM agent needs the scoring criteria for these devices; or when routing a case that involves capsule handling, capsule piercing, capsule whirring/rattling sound, or a swallowed capsule. Based on GINA 2024, CRITIKAL, Sanchis 2016, Plaza 2018, ERS/ISAM 2011, and Boehringer Ingelheim / Novartis product information.
---

# Capsule-Based DPI Inhaler Technique Evaluation Checklist

## Scope

This checklist applies to **single-capsule-load dry powder inhalers**, in which the patient inserts one capsule into the device for each dose, pierces it, inhales the contents, and then discards the empty capsule.

Covered devices and representative products:

| Device | Manufacturer | Representative products | Drug class |
|---|---|---|---|
| **HandiHaler** | Boehringer Ingelheim | Spiriva HandiHaler (tiotropium 18 µg) | LAMA |
| **Breezhaler** | Novartis | Onbrez (indacaterol), Seebri (glycopyrronium), Ultibro (indacaterol/glycopyrronium), Enerzair (indacaterol/glycopyrronium/**mometasone**) | LABA / LAMA / LABA-LAMA / **ICS-LABA-LAMA** |
| **Neohaler** | Novartis (US) | Arcapta Neohaler, Seebri Neohaler, Utibron Neohaler | US trade equivalent of Breezhaler |
| Other single-capsule devices | various | Aerolizer, Rotahaler, Cyclohaler / Podhaler-type capsule devices | varies |

**Not covered — route to the sibling skill instead:**

| If the device is… | Use skill |
|---|---|
| Pressurized metered-dose inhaler, no spacer | `inhaler-checklist-pmdi` |
| pMDI with valved holding chamber / spacer or face mask | `inhaler-checklist-pmdi-spacer` |
| Turbuhaler (twist-and-click reservoir DPI) | `inhaler-checklist-turbuhaler` |
| Diskus / Accuhaler (blister-strip DPI with lever) | `inhaler-checklist-diskus` |
| Ellipta (blister-strip DPI, cover-open actuation) | `inhaler-checklist-ellipta` |
| Genuair / Pressair (feedback-window DPI) | `inhaler-checklist-genuair` |
| Respimat (soft mist inhaler) | `inhaler-checklist-respimat` |

If the video shows a capsule being removed from a blister card and inserted into the device, this is the correct skill regardless of trade name.

## Critical Conceptual Differences From Every Other Inhaler

Capsule DPIs are the **only** inhalers in routine use that require the patient to physically **handle and load a separate capsule for every single dose**. This introduces an entire class of failure modes that do not exist for any reservoir DPI, blister DPI, pMDI, or soft mist inhaler:

1. **The capsule can be swallowed orally instead of inhaled.** This is a well-documented, clinically serious real-world error — patients (especially those also taking oral tablets, older patients, and patients with low health literacy) place the capsule in their mouth and swallow it. The result is **total dose loss**: tiotropium, indacaterol and glycopyrronium have negligible oral bioavailability from a swallowed capsule, so the patient receives essentially no treatment while believing they are adherent. Repeated over weeks this presents as unexplained treatment failure.
2. **The capsule may not be pierced at all.** A closed capsule delivers nothing. Unlike a reservoir DPI, there is no dose counter to reveal the omission.
3. **The piercing button may be pressed repeatedly**, fragmenting the gelatin/HPMC shell. Fragments can be carried into the mouth or lower airway on inhalation.
4. **The capsule may not be emptied.** Powder frequently remains after one inhalation, and a second inhalation is required by design (this is explicitly instructed in both HandiHaler and Breezhaler product information).

Uniquely, these devices also provide **two forms of direct, objective feedback that no other inhaler offers**:

- **Audible whirring / rattling**: during a correct, forceful inhalation the pierced capsule spins rapidly in its chamber and produces a distinctive whirring or rattling sound. This sound is direct real-time confirmation that inspiratory flow was sufficient to aerosolize the powder. **No sound = inadequate inspiratory flow (or unpierced/misplaced capsule).**
- **Post-dose visual inspection**: the capsule is transparent and can be opened and examined after inhalation. An empty capsule confirms the dose was taken; residual powder mandates a repeat inhalation.

These two feedback channels make capsule DPIs **unusually verifiable** in an automated evaluation setting — provided the recording includes audio.

Like all DPIs, capsule devices are breath-actuated and require **fast, deep, forceful** inhalation — the opposite of the slow inhalation taught for pMDI. Patients switching from pMDI reliably under-perform here.

## Evaluation Framework

- **7 sequential core steps** (C1–C7), each scored 0–3
- **3 conditional steps** (C8 ICS rinse — usually N/A, C9 capsule disposal, C10 cleaning/storage)
- **Maximum core score**: 21 (up to 30 with all conditional steps applicable)
- Critical errors override the score-based verdict to FAIL

## Step-by-Step Checklist

### C1 — Remove capsule from blister immediately before use

**Action**: Immediately before dosing, peel back the blister foil and remove **one** capsule. Do not push the capsule through the foil. Do not remove capsules in advance, and do not store loose capsules in the device or a pill organizer.

**Why it matters**: The powder is **highly moisture sensitive**. A capsule exposed to ambient humidity absorbs water, the powder clumps, and it will no longer aerosolize even with a perfect inhalation. Both Boehringer Ingelheim (HandiHaler) and Novartis (Breezhaler) product information state explicitly that the capsule must be removed from the blister only immediately before use. Pre-loading the device "so it is ready in the morning" is a common and consequential patient shortcut.

**Rubric**:
- **Level 3** — Blister peeled open, exactly one capsule removed immediately before use, capsule handled minimally and kept dry
- **Level 2** — Capsule removed correctly but with a delay of tens of seconds, or excessive handling of the capsule body
- **Level 1** — Capsule pushed through the foil (risk of cracking), or capsule taken from a partly opened/pre-peeled blister of uncertain age
- **Level 0** — Capsule was pre-loaded/pre-removed well in advance, stored loose, or is visibly cracked/damaged and used anyway

**Critical error mapping**: `CRIT-CAP-01` "Capsule pre-removed from blister / stored loose before use"

**Observable in video**: Blister card in frame, peeling motion, time between removal and loading, capsule integrity.

---

### C2 — Open the device and place the capsule in the CAPSULE CHAMBER (never the mouthpiece)

**Action**: Open the dust cap, then open the mouthpiece (HandiHaler: lift the mouthpiece upward; Breezhaler/Neohaler: tilt the mouthpiece open). Drop the capsule into the **capsule chamber in the base of the device**. Close the mouthpiece until it **clicks**.

**Why it matters**: Placing the capsule directly into the mouthpiece is a recurrent real-world error. In that position the piercing pins cannot engage it, the capsule cannot spin, and — most dangerously — the capsule sits directly in the inhalation path where it may be drawn toward the mouth. The **click** on closing confirms the mouthpiece is properly seated so that the piercing mechanism will align with the capsule.

**Rubric**:
- **Level 3** — Device opened correctly, capsule dropped into the base chamber, mouthpiece closed with an audible click
- **Level 2** — Capsule correctly placed in the chamber, but mouthpiece closure hesitant / click not clearly audible
- **Level 1** — Capsule placed in the chamber only after fumbling or a failed attempt; or mouthpiece not fully closed
- **Level 0** — Capsule placed **in the mouthpiece** instead of the chamber, or device closed with no capsule inside

**Critical error mapping**:
- `CRIT-CAP-02` "Capsule placed in the mouthpiece instead of the capsule chamber"
- `CRIT-CAP-03` "Device closed without a capsule loaded"

**Observable in video**: Device opening motion, destination of the capsule (base chamber vs. mouthpiece bore), mouthpiece closing; click in audio.

---

### C3 — Press the piercing button(s) ONCE, firmly, and release

**Action**: Hold the device upright with the mouthpiece pointing up. Press the side piercing button(s) **fully in one time** and release. HandiHaler has a single green piercing button; Breezhaler/Neohaler has two side buttons pressed simultaneously.

**Why it matters**: This is the step that makes the dose available at all. An unpierced capsule delivers **zero drug** — and, because there is no dose counter, nothing alerts the patient. Conversely, pressing the buttons repeatedly ("to be sure") **fragments the capsule shell**; both manufacturers warn against multiple piercing because shell fragments may be carried into the mouth or airway on inhalation. Device orientation should be upright/vertical at this moment so that powder is not spilled before the pins withdraw.

**Rubric**:
- **Level 3** — Device upright, button(s) pressed fully **once**, released cleanly; a soft piercing sound may be audible
- **Level 2** — Pressed once but incompletely at first with a single immediate correction, or device tilted during piercing
- **Level 1** — Piercing performed but hesitant/partial, uncertain whether the shell was pierced
- **Level 0** — Capsule not pierced at all, **or** button(s) pressed repeatedly (≥3 presses) with visible/likely capsule fragmentation

**Critical error mapping**:
- `CRIT-CAP-04` "Capsule not pierced"
- `CRIT-CAP-05` "Piercing button pressed multiple times — capsule fragmentation"

**Observable in video**: Thumb/finger on the piercing button, **number of presses (count them explicitly)**, device orientation, visible capsule state through the transparent chamber.

---

### C4 — Hold the device horizontally and exhale fully AWAY from the mouthpiece

**Action**: Bring the device to a **horizontal** orientation with the mouthpiece level. Turn the head away from the device and exhale completely (to functional residual capacity). Never exhale into the mouthpiece.

**Why it matters**: Two distinct requirements are combined here.
- **Orientation**: the capsule must be able to spin freely in a horizontal chamber. Inhaling with the device pointed sharply up or down impedes capsule rotation and powder release.
- **Exhaling away**: exhaled breath is warm and saturated with water vapour. Blowing into the device wets the pierced capsule and clumps the powder, destroying the dose that has just been made available — a fully preventable total-dose loss. Exhaling fully first also maximises the subsequent inspiratory volume and flow.

**Rubric**:
- **Level 3** — Device held horizontally, head clearly turned away, complete audible exhalation before inhaling
- **Level 2** — Exhalation performed away from the device but incomplete/shallow, or device orientation only approximately horizontal
- **Level 1** — Minimal or absent exhalation, but the patient did not exhale into the device; or device markedly tilted
- **Level 0** — **Exhalation into the mouthpiece** (any duration)

**Critical error mapping**:
- `CRIT-CAP-06` "Exhalation into the device"
- `CRIT-CAP-07` "Device not held horizontally during dosing"

**Observable in video + audio**: Device angle relative to the floor, head/device separation, exhalation sound and its direction.

---

### C5 — Seal lips around the mouthpiece and inhale RAPIDLY, FORCEFULLY and DEEPLY — listen for the capsule whirring

**Action**: Place the mouthpiece in the mouth and close the lips tightly around it (do not cover the air vents on the sides of the device). Inhale **as fast, as forcefully and as deeply as possible**, from the very first instant, until the lungs are full. **A whirring or rattling sound should be heard** as the capsule spins.

**Why it matters**: This is **the** decisive step. There is no propellant — the powder is de-agglomerated and aerosolized entirely by turbulent energy from the patient's own inspiratory flow spinning the capsule against the chamber walls. Insufficient flow means the capsule does not spin, the powder is not dispersed, and the drug is deposited in the oropharynx rather than the lung. CRITIKAL identified insufficient inspiratory effort as the dominant critical error among DPI users, and Sanchis et al. found that inhaler technique has not improved over 40 years, with inspiratory-manoeuvre errors among the most persistent.

The **whirring sound is unique to this device class and is a direct, real-time, patient-usable biofeedback signal**: if the patient hears it, flow was adequate; if not, something is wrong (capsule unpierced, capsule misplaced, lips not sealed, vents occluded, or inspiratory effort too weak). Patients should be explicitly taught to listen for it.

**Common patient error**: patients trained on pMDI ("breathe in slowly and gently") apply that manoeuvre here and deliver essentially nothing to the lungs.

**Rubric**:
- **Level 3** — Tight lip seal, vents unobstructed, inhalation visibly and audibly fast/forceful from t=0 and continued to full inflation; **capsule whirring clearly audible**
- **Level 2** — Adequate seal, inhalation moderately fast and reasonably deep; whirring audible but brief or faint
- **Level 1** — Inhalation slow-to-moderate or truncated; **no whirring audible** despite a pierced capsule; or visible air leak / cheek puffing / vents covered
- **Level 0** — Inhalation clearly slow (pMDI-style), very shallow, absent, or through the nose; no capsule movement

**Critical error mapping**:
- `CRIT-CAP-08` "Inhalation too weak to spin the capsule (no whirring)"
- `CRIT-CAP-09` "Capsule swallowed orally instead of inhaled" — the capsule is placed in the mouth and swallowed; total dose loss

> `CRIT-CAP-09` is scored here because it is at this point in the sequence that the error becomes visible. If the video shows the patient putting the capsule itself into the mouth at any stage, score C5 = Level 0 and flag `CRIT-CAP-09` immediately — the entire remaining sequence is moot.

**Observable in audio**: **Capsule whirring/rattling — the single most diagnostic cue for this device class.** Inhalation sound intensity and onset speed.
**Observable in video**: Lip seal, hand position relative to the side air vents, speed and magnitude of chest expansion, inhalation duration.

---

### C6 — Hold breath ~10 seconds, then remove the device and exhale slowly away

**Action**: Remove the mouthpiece from the mouth while continuing to hold the breath. Hold for approximately **10 seconds**, or as long as is comfortable. Then exhale slowly, away from the device.

**Why it matters**: The breath-hold allows fine powder particles suspended in the airways to deposit by sedimentation and diffusion onto the airway wall rather than being exhaled. Omitting the breath-hold is one of the most frequent errors across all inhaler types (Sanchis 2016) and was a critical error in CRITIKAL. Exhaling away from the device also protects the (possibly still-in-use) capsule and mouthpiece from moisture.

**Rubric**:
- **Level 3** — Breath-hold ≥10 sec, device removed from the mouth, slow controlled exhalation directed away from the device
- **Level 2** — Breath-hold 5–9 sec, exhalation away from device
- **Level 1** — Breath-hold 1–4 sec
- **Level 0** — No breath-hold (immediate exhalation), or exhalation into the device

**Critical error mapping**: `CRIT-CAP-10` "No breath-hold"

**Observable in video**: Mouth closure, elapsed time to first exhalation, device position at exhalation.

---

### C7 — Open the device and CHECK the capsule is empty; repeat the inhalation if powder remains

**Action**: Open the mouthpiece and look at the capsule through its transparent shell. If **any powder remains**, close the device and **repeat steps C4–C6** (a second inhalation) — do not pierce again. Only when the capsule is empty is the dose complete.

**Why it matters**: This is a design feature, not an optional refinement: both HandiHaler and Breezhaler product information instruct a second inhalation from the same pierced capsule, because a single manoeuvre commonly fails to empty it. Patients who take one inhalation and stop are chronically under-dosed while appearing fully adherent. The transparent capsule makes this the only inhaler class where the patient can **objectively verify at the point of care that the dose was actually delivered** — a verification opportunity that should always be taught and always be assessed.

**Rubric**:
- **Level 3** — Device opened, capsule visually inspected, and either confirmed empty **or** a correct second inhalation performed and re-checked
- **Level 2** — Capsule inspected but only cursorily; or a second inhalation performed routinely without inspection
- **Level 1** — Device opened but no meaningful inspection; residual powder not noticed
- **Level 0** — Capsule never inspected **and** no second inhalation, with powder remaining (partial or lost dose)

**Critical error mapping**: `CRIT-CAP-11` "Capsule not emptied and second inhalation not performed"

**Observable in video**: Device reopened, capsule brought into view/held up to the light, presence of a second inhalation cycle.

---

### C8 (conditional — ICS-containing products ONLY) — Rinse mouth, gargle, and spit

**Applicability — read carefully**: **Most capsule DPI products are LAMA, LABA, or LAMA/LABA and contain NO inhaled corticosteroid.** For Spiriva HandiHaler (tiotropium), Onbrez (indacaterol), Seebri (glycopyrronium), Ultibro / Utibron (indacaterol/glycopyrronium) and Arcapta, this step is **N/A — do not penalise the patient for not rinsing, and do not include it in the denominator.**

**The important exception**: **Enerzair Breezhaler (indacaterol / glycopyrronium / mometasone furoate) DOES contain an inhaled corticosteroid** and the rinse step **is required**. If the product is Enerzair — or any other capsule DPI whose label lists an ICS — score this step normally.

**Action (when applicable)**: Rinse the mouth with water, gargle, and spit the water out. Do not swallow.

**Why it matters**: ICS deposited in the oropharynx causes oropharyngeal candidiasis and dysphonia. Oropharyngeal deposition from DPIs is typically higher than from HFA pMDIs, making rinsing correspondingly more important.

**Rubric**:
- **Level 3** — Rinses, gargles, and spits out
- **Level 2** — Rinses and spits without gargling
- **Level 1** — Rinses but swallows the water
- **Level 0** — No rinse at all with an ICS-containing product
- **N/A** — Non-ICS product (the usual case): exclude from scoring

**Critical error mapping**: `CRIT-CAP-12` "No mouth rinse with an ICS-containing capsule DPI (e.g. Enerzair)"

**Evaluator note**: If the product identity cannot be determined from the video, report this step as *indeterminate* rather than scoring it, and state the assumption explicitly in the output.

---

### C9 (conditional) — Remove and discard the used capsule

**Action**: Tip the used capsule out of the chamber and **discard it in household waste**. Never re-use a capsule, never leave a used capsule in the device between doses, and never swallow it.

**Why it matters**: A capsule left in the chamber may be mistaken for a fresh dose, blocks correct loading of the next dose, and accumulates moisture inside the device. It is also a source of the swallowed-capsule error, since patients emptying the device may reflexively put the capsule in the mouth.

**Rubric**:
- **Level 3** — Used capsule removed and discarded appropriately
- **Level 2** — Capsule removed but left on a surface / handled untidily
- **Level 1** — Capsule left in the device with the intent to remove it later
- **Level 0** — Used capsule left in the device, re-used, or placed in the mouth

**Critical error mapping**: `CRIT-CAP-13` "Used capsule retained in the device or re-used"

---

### C10 (conditional) — Close the device, clean and store dry

**Action**: Close the mouthpiece and the dust cap. Keep the device **dry — never wash it with water or any liquid**; if needed, wipe the mouthpiece inside and out with a dry cloth or tissue. Store at room temperature away from humidity (not in a bathroom or beside a sink). Keep unused capsules sealed in their blister card. Replace the device according to the product information (HandiHaler: replace yearly / with each new prescription pack; Breezhaler/Neohaler: use only the inhaler supplied with that pack and discard both together).

**Rubric**:
- **Level 3** — Mouthpiece and cap closed, device stored dry and correctly, cleaning method correct if performed
- **Level 2** — Device closed and stored, minor deviations (e.g. left out on a damp surface)
- **Level 1** — Cap left open or device stored in a humid location
- **Level 0** — Device rinsed/washed with water, or a capsule left loaded in an open device

**Critical error mapping**: `CRIT-CAP-14` "Device washed with water or stored in a humid environment"

---

## Critical Error Summary — Capsule-Based DPI

| ID | Description | Step | Clinical Impact |
|---|---|---|---|
| CRIT-CAP-01 | Capsule pre-removed from blister / stored loose before use | C1 | Moisture uptake; powder clumps and will not aerosolize |
| CRIT-CAP-02 | Capsule placed in the mouthpiece instead of the capsule chamber | C2 | Not pierced, cannot spin, no dose; capsule may be drawn toward mouth |
| CRIT-CAP-03 | Device closed and actuated with no capsule loaded | C2 | No dose; patient believes treatment was taken |
| CRIT-CAP-04 | Capsule not pierced | C3 | Zero drug delivered; no dose counter to reveal the omission |
| CRIT-CAP-05 | Piercing button pressed multiple times — capsule fragmentation | C3 | Risk of inhaling gelatin/HPMC shell fragments; erratic dose |
| CRIT-CAP-06 | Exhalation into the device | C4 | Moisture clumps the pierced-capsule powder; dose lost |
| CRIT-CAP-07 | Device not held horizontally during dosing | C4, C5 | Capsule cannot spin freely; incomplete powder release |
| CRIT-CAP-08 | Inhalation too weak to spin the capsule (no whirring heard) | C5 | Powder not de-agglomerated; drug deposits in oropharynx, not lung |
| CRIT-CAP-09 | **Capsule swallowed orally instead of inhaled** | C5 | **Total dose loss** — negligible oral bioavailability; silent treatment failure while patient appears adherent |
| CRIT-CAP-10 | No breath-hold | C6 | Fine particles exhaled before deposition |
| CRIT-CAP-11 | Capsule not emptied and second inhalation not performed | C7 | Chronic partial dosing despite apparent adherence |
| CRIT-CAP-12 | No mouth rinse with an ICS-containing capsule DPI (e.g. Enerzair) | C8 | Oropharyngeal candidiasis, dysphonia |
| CRIT-CAP-13 | Used capsule retained in the device or re-used | C9 | Next dose blocked/confounded; moisture in device; swallowing risk |
| CRIT-CAP-14 | Device washed with water or stored in a humid environment | C10 | Device fouling; subsequent doses clump |

**Population context**: CRITIKAL (Price DB et al., n≈3,660 with 1,663 video-recorded technique assessments) found insufficient inspiratory effort in DPI users to be the critical error most strongly associated with uncontrolled asthma and increased exacerbation rate; no breath-hold and exhalation into the device were the next most prevalent. Sanchis et al. (Chest 2016, 144 studies over 40 years) found only ~31% of patients demonstrated correct technique overall, with **no improvement over four decades**. Plaza et al. (2018) further showed that errors are frequently missed by clinicians themselves, reinforcing the value of objective, device-specific checklists such as this one. The capsule-handling errors above (`CRIT-CAP-01` to `CRIT-CAP-05`, `CRIT-CAP-09`, `CRIT-CAP-11`) are **device-class-specific and are not captured by generic DPI checklists**.

## Overall Verdict Logic

```
core_max = 21   # C1..C7, 3 points each

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

Conditional steps C8–C10 are scored and reported separately; when applicable they are added to both the numerator and the denominator before the percentage thresholds are applied. C8 is **N/A for non-ICS products** (the majority of capsule DPIs) and must then be excluded from the denominator entirely.

## VLM Observation Guidance

| Step | Visual reliability | Audio reliability | Notes |
|---|---|---|---|
| C1 (capsule from blister) | High | Low | Look for blister card in frame; pre-loading is often only inferable — report as such |
| C2 (capsule into chamber) | **VERY HIGH** | Moderate | Track the capsule's destination frame-by-frame: base chamber vs. mouthpiece bore. Closing click audible |
| C3 (pierce once) | High | Moderate | **Count button presses explicitly.** Faint piercing crunch may be audible |
| C4 (horizontal + exhale away) | High | High | Device angle is directly measurable; exhalation direction visible and audible |
| C5 (forceful inhalation) | Moderate | **VERY HIGH** | **Capsule whirring/rattling is high-reliability audio evidence of adequate inspiratory flow** — near-definitive when present |
| C5 (capsule swallowed) | **VERY HIGH** | Low | Capsule entering the mouth is unambiguous on video; flag `CRIT-CAP-09` immediately |
| C6 (breath-hold) | High | High | Silence duration between end of inspiration and first exhalation |
| C7 (capsule empty check) | **HIGH** | Low | **Post-inhalation inspection of the transparent capsule is high-reliability visual evidence that the dose was actually delivered** |
| C8 (ICS rinse) | High | Moderate | Only assess after confirming the product contains an ICS (Enerzair); otherwise N/A |
| C9 (discard capsule) | High | Low | Watch the used capsule's fate |
| C10 (close/store) | High | Low | Cap closure and storage location |

**Critical recommendations for VLM agents:**

1. **Audio is decisive for C5.** The capsule whirring/rattling sound is the highest-value single cue available on any inhaler in this library — it directly and physically confirms that inspiratory flow was sufficient to spin the capsule. When clean audio is present, these devices are **unusually verifiable** compared with all other inhaler classes.
2. **Without audio, C5 must be reported as LOW CONFIDENCE.** Chest-expansion speed alone is a weak proxy for peak inspiratory flow. Do not assign Level 3 at C5 from silent video; cap the score at Level 2 and state the confidence limitation explicitly in the output rather than inferring a critical error that cannot be substantiated.
3. **C7 is the strongest visual verification point.** Empty-capsule inspection is high-reliability visual evidence; if the patient never reopens the device, record that the dose could not be verified.
4. **Count the piercing button presses.** This is the only way to detect `CRIT-CAP-05`, and it requires deliberate frame-level attention rather than a holistic impression.
5. **Identify the product before scoring C8.** Read the blister card or device labelling if visible. Defaulting to "ICS rinse required" is wrong for most capsule DPI products and produces false critical errors.

## Switching Patient Notes (Clinical Context)

When evaluating a patient who has switched to a capsule DPI:

- **From pMDI**: expect under-performance at C5 (slow, pMDI-style inhalation). Coordination errors disappear, but the entire capsule-handling sequence (C1–C3, C7, C9) is completely new and is the highest-yield teaching target.
- **From another DPI (Turbuhaler, Diskus, Ellipta)**: the inspiratory manoeuvre transfers well; the capsule handling does not. Patients accustomed to a self-contained device frequently omit C3 (piercing) or C7 (empty check) entirely.
- **Patients on multiple oral medications**: explicitly probe for the swallowed-capsule error (`CRIT-CAP-09`). Ask directly, "what do you do with the capsule?" — a patient who answers "I swallow it" has been receiving no treatment.
- **Low-inspiratory-flow patients** (severe COPD, frail elderly, acute exacerbation): if no whirring can be produced, the device class may be inappropriate; consider referral for a device change (e.g. soft mist inhaler or pMDI with spacer) rather than repeated retraining.

## References

- Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention, 2024 update.*
- Price DB, Román-Rodríguez M, McQueen RB, et al. *Inhaler Errors in the CRITIKAL Study: Type, Frequency and Association with Asthma Outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J, Gich I, Pedersen S; ADMIT. *Systematic Review of Errors in Inhaler Use: Has Patient Technique Improved Over Time?* Chest 2016;150(2):394-406.
- Plaza V, Giner J, Rodrigo GJ, Dolovich MB, Sanchis J. *Errors in the Use of Inhalers by Health Care Professionals: A Systematic Review.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
- Laube BL, Janssens HM, de Jongh FH, et al. *What the pulmonary specialist should know about the new inhalation therapies.* Eur Respir J 2011;37(6):1308-1331. (ERS/ISAM Task Force consensus statement)
- Boehringer Ingelheim. *Spiriva HandiHaler (tiotropium bromide inhalation powder) — Prescribing Information / Instructions for Use.*
- Novartis. *Breezhaler (Onbrez / Seebri / Ultibro / Enerzair Breezhaler) — Summary of Product Characteristics and Instructions for Use.*
- Novartis. *Neohaler (Arcapta / Seebri / Utibron Neohaler) — US Prescribing Information and Instructions for Use.*
