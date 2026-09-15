---
description: Run single-evaluator (Evaluator A only) inhaler technique evaluation — faster path for screening; NOT IRR-validated
argument-hint: <video.mp4> [case_id]
allowed-tools: Read, Write, Bash, Task
---

# /evaluate-inhaler — Single-Evaluator Screening Mode

Single-pass evaluation using only Evaluator A (Opus + GINA strict). Use this command for:
- Quick screening before deciding whether full dual evaluation is needed
- Patient self-monitoring (when IRR is not the goal)
- Throughput-limited contexts (e.g., batch pre-screening of hundreds of videos)

**Do NOT use this command for clinical or research-grade assessment** — for that, use `/evaluate-dual`.

## Workflow

Given user input `$ARGUMENTS`, parse:
1. Video file path (.mp4) — required
2. case_id — optional; auto-generate as `CAMCA-SCREEN-{timestamp}` if not provided

### 1. Validate input

Same as `/evaluate-dual` stage 1.

### 2. Invoke device-id agent

Identify device. If confidence < 0.7, ask user to confirm.

### 3. Load device-specific checklist skill

Same as `/evaluate-dual` stage 3.

### 4. Invoke video-segmenter agent

Same as `/evaluate-dual` stage 4.

### 5. Invoke evaluator-a ONLY (skip evaluator-b)

Dispatch only evaluator-a. Receive single evaluation output.

### 6. SKIP adjudicator + tie-breaker

These stages are dual-evaluator-specific and not applicable.

### 7. Invoke scoring-engine

Use evaluator-a's output directly as the "consensus" input to `scoring_engine.py`. Note in the output that this is a single-evaluator result.

### 8. Invoke report-generator (simplified)

Produce a simplified Korean PDF that:
- Includes the same patient-facing content (verdict, strengths, improvements)
- **Replaces the kappa footer** with a prominent disclaimer:

```
⚠️ 본 평가는 단일 AI 평가자 결과로, 이중 평가(IRR 검증) 단계가 생략되었습니다.
정확한 평가를 위해 /evaluate-dual 또는 임상의 직접 평가를 권장합니다.
```

### 9. Export simplified log

JSON only, no CSV (single-evaluator data isn't suitable for IRR statistics).

### 10. Present to user with upgrade prompt

```markdown
## Screening Complete — {case_id}

**Device**: {device_type}
**Screening verdict**: {verdict} ({percent}%)
**Critical errors detected (by Evaluator A only)**: {list}

⚠️ This is a single-evaluator screening, NOT a dual-evaluator validated assessment.

To run the full IRR-validated evaluation:
`/evaluate-dual {video_path} {case_id}`
```

## When This Mode IS Appropriate

- Pre-pilot rapid prototyping (e.g., testing whether your video corpus is segmentable at all)
- Patient-facing app where simplicity matters more than rigor
- High-throughput screening where flagged cases will be re-run with `/evaluate-dual`

## When This Mode IS NOT Appropriate

- **Clinical decision-making** — always use dual
- **Research arm of CAMCA** — always use dual (IRB will reject single-evaluator data)
- **Publication-ready data** — kappa must be reported, requires dual
- **Patient with critical error history** — dual catches more

## Critical Rules — Do NOT Violate

- **NEVER** present this output as IRR-validated. Disclaimer must be visible.
- **NEVER** include kappa value (none exists — single evaluator).
- **NEVER** skip the upgrade prompt in the final user-facing summary.
- The PDF must explicitly disclose single-evaluator status.
