---
description: Compare two previously-saved evaluation JSON files using the adjudicator pipeline — kappa, agreement matrix, consensus (no re-evaluation of video)
argument-hint: <eval_a.json> <eval_b.json>
allowed-tools: Read, Write, Bash, Task
---

# /compare-evaluations — Offline Adjudication

Compare any two pre-existing evaluation JSONs without re-running the full pipeline. Useful for:

- **Comparing human expert vs AI**: Manually-scored evaluation vs evaluator-a/b output
- **Cross-model validation**: Gemini 2.5 Pro evaluation vs Claude Opus evaluation
- **Re-adjudication**: After fixing a bug in one evaluator, re-run kappa without re-running video analysis
- **Inter-VLM comparison arm** of CAMCA research (Gemini vs GPT-4o vs Qwen)

## Workflow

Given user input `$ARGUMENTS`, parse two file paths:
1. `eval_a.json` — first evaluation in evaluator-a/b output schema
2. `eval_b.json` — second evaluation in the same schema

### 1. Validate inputs

- Both files exist and parse as JSON
- Both conform to evaluator output schema (presence of: case_id, device_type, per_step_evaluation, critical_errors_detected, summary)
- Both reference the same case_id
- Both reference the same device_type
- Both reference the same set of step_ids

If validation fails → halt with clear error.

### 2. Skip the live pipeline (no video, no device-id, no segmenter)

These stages are not needed — both evaluations already contain the necessary structure.

### 3. Invoke adjudicator agent directly

Pass:
- `evaluator_a_output: <contents of eval_a.json>`
- `evaluator_b_output: <contents of eval_b.json>`

The adjudicator will:
- Invoke `scripts/kappa_calculator.py`
- Decide tie-breaker (skipped in offline mode since video is unavailable for re-evaluation)
- If tie-breaker needed: emit a warning but produce consensus via fallback method (majority vote on critical errors; average levels otherwise)

### 4. SKIP scoring-engine and report-generator (default)

By default, this command is comparison-only. The output is the adjudication JSON + kappa stats.

Optional flag `--with-final-score` invokes scoring-engine if desired.
Optional flag `--with-pdf` invokes report-generator if desired.

### 5. Present to user

```markdown
## Comparison Complete — {case_id}

**Evaluator A**: {model_a} ({persona_a})
**Evaluator B**: {model_b} ({persona_b})

**Inter-rater κ (linear weighted)**: {kappa} ({interpretation})

### Per-step agreement
| Step | A | B | Agreement |
|---|---|---|---|

### Critical error consensus
- Both flagged: {list}
- A only: {list}
- B only: {list}

### Tie-breaker
{if needed: "Recommended but cannot be auto-invoked in offline mode — video required"}

### Files produced
- [Kappa stats JSON](computer://...)
- [Adjudication JSON](computer://...)
```

## Use Cases

### Use Case 1: Human Expert Validation
```
/compare-evaluations \
  logs/CAMCA-001/04_evaluator_a.json \
  manual_review/CAMCA-001_human_expert.json
```
Measures how well AI matches human expert.

### Use Case 2: Cross-Model Validation (Research Arm)
```
/compare-evaluations \
  logs/CAMCA-001/eval_claude_opus.json \
  logs/CAMCA-001/eval_gemini_pro.json
```
Quantifies model-to-model agreement for publication.

### Use Case 3: Prompt Iteration A/B
```
/compare-evaluations \
  logs/CAMCA-001/eval_promptv1.json \
  logs/CAMCA-001/eval_promptv2.json
```
Measures whether a prompt change altered scoring (should be small κ change if prompt is just clarification).

## Critical Rules — Do NOT Violate

- **NEVER** invoke video segmentation or device-id in this command. It is offline by design.
- **NEVER** silently invoke tie-breaker — it requires video and cannot be run offline.
- **ALWAYS** preserve both input files as-is. Do not modify them.
- **ALWAYS** include a note in the output indicating which two evaluators were compared (model + persona for each).

## Limitations

- Cannot resolve disagreements via tie-breaker (no video access)
- Critical-error agreement depends on detector consistency in both inputs (different detector versions = artificial disagreement)
- κ interpretation requires same evaluation rubric in both inputs — if rubrics differ (e.g., Levels 0-3 vs Levels 1-5), output is meaningless
