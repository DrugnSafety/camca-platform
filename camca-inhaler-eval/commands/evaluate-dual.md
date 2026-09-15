---
description: Run full dual-agent inhaler technique evaluation on an .mp4 video — produces consensus score, kappa statistics, and Korean patient PDF
argument-hint: <video.mp4> [case_id]
allowed-tools: Read, Write, Bash, Task
---

# /evaluate-dual — Main CAMCA Use Case (v0.4.0 + telemetry)

This is the primary command for the CAMCA dual-agent inhaler evaluation pipeline. Use when the user provides an inhaler-use video and wants the full automated assessment with inter-rater reliability validation.

## What's new in v0.4.0

The pipeline now includes **Layer 0 — quantitative telemetry extraction** BEFORE VLM evaluators. MediaPipe (vision landmarks) + librosa (audio energy) produce 0.1s-resolution measurements that turn VLM "estimation" into "measurement interpretation". This dramatically improves S5 (coordination) and S7 (breath-hold) accuracy.

## Workflow

Given user input `$ARGUMENTS`, parse out:
1. Video file path (.mp4) — required
2. case_id — optional; auto-generate as `CAMCA-{timestamp}` if not provided

Execute the following steps in order:

### 1. Validate input

- Check that the video file exists and is `.mp4`
- If not, halt with a clear error message

### 2. Invoke `device-id` agent

Pass the video file. Receive `device_type`. If `unknown`, ask the user to confirm or abort.

### 3. Load device-specific checklist skill

- For `pMDI` → load `${CLAUDE_PLUGIN_ROOT}/skills/inhaler-checklist-pmdi/SKILL.md`
- For `DPI-turbuhaler` → load `${CLAUDE_PLUGIN_ROOT}/skills/inhaler-checklist-turbuhaler/SKILL.md`

### 3.5. **(NEW v0.4.0) Extract quantitative telemetry — Layer 0**

Run the telemetry extractor BEFORE evaluators:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/run_telemetry.py \
  --video {video_path} \
  --output-dir ${CLAUDE_PLUGIN_ROOT}/logs/{case_id}/
```

This produces:
- `01b_telemetry_stream.json`: per-0.1s measurements (6 indicators)
- `01c_telemetry_summary.json`: clinical anchors (S5 coordination ms gap, S7 breath-hold duration, etc.)

**Fallback policy**:
- If telemetry script fails → log warning, continue without telemetry (VLM-only fallback)
- If MediaPipe not installed → use `--skip-vision` (audio-only mode still extracts breath-hold)
- If both fail → proceed with VLM-only evaluation; clinician review flag set to "high"

### 4. Invoke `video-segmenter` agent

Pass video + device_type. Receive segmented video JSON.

### 5. **Parallel dual evaluation (with telemetry injection)**

Dispatch `evaluator-a` and `evaluator-b` agents in **a single message with two Agent tool calls** so they run concurrently. Each receives the same segmented input + the telemetry summary from step 3.5 + their device checklist skill reference.

**Critical**: Do not let either evaluator see the other's output. Pass each only the segmented input + telemetry summary + their device checklist skill reference.

**Telemetry guidance for evaluators** (added to their prompts):
> "Quantitative telemetry has been provided. Use `clinical_anchors.S5_coordination_check.gap_ms` for S5 evaluation directly; do NOT estimate from frames. Use `clinical_anchors.S7_breath_hold_check.duration_ms` for S7."

### 6. Invoke `adjudicator` agent

Pass both evaluator outputs. The adjudicator will:
- Invoke `scripts/kappa_calculator.py` (deterministic)
- Decide if tie-breaker needed
- If yes, invoke `tie-breaker` agent
- Produce consensus evaluation

### 7. Invoke `scoring-engine`

Run `scripts/scoring_engine.py` for deterministic final score.

### 8. Invoke `report-generator`

Produce Korean patient PDF + clinician summary PDF.

### 9. Export research logs

Save:
- `logs/evaluator_a_{case_id}.json`
- `logs/evaluator_b_{case_id}.json`
- `logs/adjudication_{case_id}.json`
- `logs/adjudication_{case_id}.stats.json` (kappa stats)
- `logs/final_score_{case_id}.json`
- `logs/research_export_{case_id}.csv` (one-row research log)

### 10. Present to user

Display a concise summary to the user:
- Overall verdict (PROFICIENT / ADEQUATE / NEEDS TRAINING / FAIL)
- Kappa value + interpretation
- Clinician review flag status
- Critical errors found (if any)
- Computer:// links to PDF reports and JSON logs

## Error Handling

- If any agent fails, do NOT proceed to the next stage. Surface the error.
- If the video is unreadable, halt immediately.
- If `device-id` confidence is below 0.7, ask the user for confirmation before proceeding.
- If kappa cannot be computed (e.g., only 1 step), report this as a data-quality issue rather than producing a misleading kappa value.

## Privacy Note

If patient faces are visible, recommend pre-processing with MediaPipe Face Mesh before this command (per CAMCA privacy-by-design principle). Add this as a warning to the user before running the pipeline.
