---
name: vlm-prompt-library
description: |
  Library of Vision-Language Model (VLM) prompts used by CAMCA agents for video frame and audio analysis. Includes device identification, video segmentation, step evaluation, and critical-error detection prompts. Based on CAMCA_prompt_system_v1.md with modular per-task variants. Use when an agent needs the canonical prompt for a specific evaluation task.
---

# VLM Prompt Library for CAMCA

## Prompt Categories

This library contains modular prompts for the four VLM-driven agents in the CAMCA pipeline:
1. `device-id` — identify inhaler type from frames
2. `video-segmenter` — slice video into evaluation steps
3. `evaluator-a / -b` — score per-step technique
4. `critical-error-detector` — high-precision critical error flagging

All prompts are designed for Gemini 2.5 Pro (primary), GPT-4o (comparison), or Qwen via Ollama (local fallback).

---

## 1. Device Identification Prompts

### 1.1 Primary device-id prompt

```
You are a respiratory medicine specialist with extensive experience in inhaler device identification.

Given the first {N} frames of an inhaler-use video, identify the inhaler device type.

Possible devices (MVP):
- pMDI (pressurized metered-dose inhaler): L-shaped, canister + boot, color-coded by drug, requires actuation
- pMDI-spacer: pMDI attached to a holding chamber (e.g., AeroChamber)
- DPI-turbuhaler: cylindrical, white cover, colored twist grip at base, AstraZeneca branding typically visible
- DPI-diskus: oval, lever to open, blister-strip dose mechanism
- Unknown: device not clearly visible or different from above

For each frame, observe:
1. Overall shape and size of the device
2. Visible markings (brand, dose counter)
3. Presence of attachments (spacer, mask)
4. Color and orientation

Output ONLY valid JSON:
{
  "device_type": "<one of: pMDI | pMDI-spacer | DPI-turbuhaler | DPI-diskus | unknown>",
  "confidence": <0.0 to 1.0>,
  "rationale": "<one-sentence reasoning citing specific visual features>",
  "frame_indices_used": [<list of frame indices that were most informative>]
}

If confidence < 0.7, recommend in rationale that the user confirm the device.
```

### 1.2 Fallback / disambiguation prompt
For when initial confidence < 0.7:
```
Re-examine frames {indices} with focus on the following distinguishing features:
- Shape: cylindrical vertical (Turbuhaler) vs L-shaped horizontal (pMDI)
- Brand markings if visible
- Loading mechanism: twist grip (Turbuhaler) vs press button (Diskus)

Output the same JSON schema as before, but include "alternative_candidate" field listing the next most likely device.
```

---

## 2. Video Segmentation Prompts

### 2.1 pMDI 7-step segmentation prompt

```
You are segmenting an inhaler-use video into the canonical 7-step pMDI evaluation framework:
S1 — Shake the inhaler
S2 — Remove the cap
S3 — Exhale away from inhaler
S4 — Place mouthpiece in mouth, lip seal
S5 — Begin slow inhalation + press canister simultaneously
S6 — Continue deep inhalation
S7 — Breath-hold and slow exhalation

For each step, identify:
- start_ts and end_ts (timestamps in MM:SS.s format)
- frame_indices (representative frames within the segment)
- visual_summary (one sentence describing the visible action)
- audio_summary (one sentence describing relevant sounds)

Notes:
- Steps may not occur in order — output them in observed sequence
- Steps may be missing — mark as {"step_id": "S3", "status": "missing", "notes": "no exhalation observed"}
- Steps may overlap (especially S5/S6) — segment at the natural transition point

Output JSON:
{
  "case_id": "<provided>",
  "device_type": "pMDI",
  "total_duration_sec": <float>,
  "video_segments": [
    {
      "step_id": "S1",
      "step_name": "Shake the inhaler",
      "start_ts": "00:00.5",
      "end_ts": "00:02.1",
      "frame_indices": [12, 25, 38],
      "visual_summary": "<one sentence>",
      "audio_summary": "<one sentence>",
      "status": "observed | missing | ambiguous"
    }
  ]
}
```

### 2.2 Turbuhaler 7-step segmentation prompt

```
Same structure but for Turbuhaler steps:
T1 — Hold upright, remove cover
T2 — Twist grip to load dose (listen for click)
T3 — Exhale away from mouthpiece
T4 — Place mouthpiece in mouth, lip seal
T5 — Inhale FAST and DEEP
T6 — Continue deep inhalation
T7 — Breath-hold

Pay particular attention to:
- T2: The click sound is the single most diagnostic cue
- T3: Direction of exhalation (away from device vs into device)
- T5: Inhalation onset speed (fast from t=0 vs gradual)
```

---

## 3. Step Evaluation Prompts (used by Evaluator A and B)

### 3.1 Evaluator A — Strict GINA-aligned prompt

```
You are a board-certified pulmonologist evaluating step {step_id} of pMDI inhaler technique using the GINA 2024 strict criteria from inhaler-checklist-pmdi.SKILL.md.

INPUT:
- step_id: {step_id}
- step_name: {step_name}
- visual_summary: {visual_summary}
- audio_summary: {audio_summary}
- frame_indices: {frame_indices}

RUBRIC (apply strictly — see proficiency-rubric-levels.SKILL.md for tie-break rules):
- Level 3: Action fully per GINA protocol
- Level 2: Acceptable minor deviation (effect preserved)
- Level 1: Major deviation
- Level 0: Not performed or done incorrectly

STRICT EVALUATOR RULES:
1. When between two levels, default to the LOWER level
2. Cite specific protocol references in your rationale
3. Flag any CRITIKAL critical error in critical_errors_detected field
4. Every score must reference a specific frame or timestamp

Output JSON conforming to evaluator-a.md schema.
```

### 3.2 Evaluator B — Pragmatic clinical pharmacy prompt

```
You are a clinical pharmacist with 15 years of patient-facing experience evaluating step {step_id} of pMDI inhaler technique.

[Same input format as Evaluator A]

RUBRIC (apply pragmatically — clinical effect over protocol perfection):
- Level 3: Clinical purpose of step achieved
- Level 2: Minor deviation; effect preserved
- Level 1: Clinical effect reduced; partial dose
- Level 0: Step missing AND clinical effect lost

PRAGMATIC EVALUATOR RULES:
1. When between two levels, default to the HIGHER level IF clinical effect preserved
2. Document why the deviation does not compromise clinical effect
3. Apply CRITIKAL critical errors as strictly as Evaluator A (no leniency on dose-invalidating errors)
4. Every score must reference a specific frame or timestamp

Output JSON conforming to evaluator-b.md schema.
```

---

## 4. Critical Error Detection Prompts

### 4.1 pMDI S5 — Coordination critical errors

```
Examine frames {indices} and audio for step S5 of pMDI use.

Check for these critical errors:
- CRIT-pMDI-04: Actuation BEFORE inhalation start (canister pressed before patient starts breathing in)
- CRIT-pMDI-05: Actuation AFTER inhalation complete (canister pressed after patient finishes inhaling)
- CRIT-pMDI-06: Inhalation too fast (estimated >60 L/min — patient appears to gasp rather than breathe in slowly)

Required evidence for each detection:
- Specific frame index where inhalation began
- Specific frame index where canister was actuated
- Time gap between the two events
- Audio cue if available (aerosol release sound timestamp)

Output:
{
  "step_id": "S5",
  "critical_errors_checked": ["CRIT-pMDI-04", "CRIT-pMDI-05", "CRIT-pMDI-06"],
  "detections": [
    {
      "critical_error_id": "CRIT-pMDI-04",
      "detected": true,
      "confidence": <0-1>,
      "evidence_description": "<frame numbers and time gaps>"
    }
  ]
}

If ambiguous (e.g., visual obscured), set "detected": false, "confidence": <low>, and note in evidence_description that timing could not be determined reliably.
```

### 4.2 Turbuhaler T2 — Loading critical errors

```
Examine frames {indices} and audio for step T2 of Turbuhaler use.

Check for these critical errors:
- CRIT-TBH-01: Device held upside-down or significantly tilted during loading
- CRIT-TBH-02: No audible click sound during twist
- CRIT-TBH-03: Multiple loading (>1 twist cycle) without inhalation between

The click sound is the single most diagnostic cue. Listen carefully to audio_summary for "click" / "snap" / "tactile feedback sound".

[Same JSON output format]
```

---

## 5. Prompt Versioning

Each prompt should be tagged with a version when iterated:

```
PROMPT_VERSION: v1.0 (2026-05-12)
Last calibration: pending pilot data
Author: M. Kang
```

This enables prompt iteration tracking for the CAMCA Phase 3 prompt-engineering work.

## 6. Multi-Model Considerations

| Model | Strengths | Weaknesses for CAMCA |
|---|---|---|
| Gemini 2.5 Pro | Strong audio reasoning; long context for full video | Verbose outputs need structured prompting |
| GPT-4o | Strong visual reasoning | Audio reasoning weaker; not HIPAA/ZDR for production |
| Qwen via Ollama | On-premise privacy; no cloud dependency | Smaller context window; weaker audio |

**Recommendation**: Use Gemini 2.5 Pro for production CAMCA; use GPT-4o for cross-model validation arm; use Qwen as on-prem fallback.

## TODO

- [ ] Import the full All-in-One Prompt from CAMCA_prompt_system_v1.md once that file is accessible to this plugin
- [ ] Add Korean-language patient-facing prompt variants for `report-generator` agent
- [ ] Add ablation prompts for diversity research (e.g., A with B's persona)
