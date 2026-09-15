---
name: adjudicator-comparison-template
description: |
  Output schema and template strings for the adjudicator agent's comparison report. Defines the exact JSON structure of per-step agreement, kappa interpretation phrases (Korean + English), clinician-review-flag rationales, and the consensus narrative. Use whenever the adjudicator emits its final adjudication output.
---

# Adjudicator Comparison Output Template

## Purpose

Standardize the structure and language used by the adjudicator agent when comparing Evaluator A and Evaluator B outputs. This skill is the source of truth for:

- Output JSON schema
- Interpretive phrases (κ ranges)
- Per-step agreement labels
- Consensus narrative templates

## Full Output JSON Schema

```json
{
  "schema_version": "1.0",
  "case_id": "CAMCA-XXX",
  "adjudicated_at": "2026-05-12T14:35:00Z",
  "device_type": "pMDI",
  "evaluator_a": {
    "model": "claude-opus",
    "persona": "GINA-strict",
    "total_score": 12,
    "critical_error_count": 1,
    "log_path": "logs/evaluator_a_CAMCA-XXX_20260512_143000.json"
  },
  "evaluator_b": {
    "model": "claude-sonnet",
    "persona": "real-world-pragmatic",
    "total_score": 16,
    "critical_error_count": 1,
    "log_path": "logs/evaluator_b_CAMCA-XXX_20260512_143005.json"
  },
  "inter_rater_reliability": {
    "kappa_unweighted": 0.22,
    "kappa_linear_weighted": 0.53,
    "kappa_quadratic_weighted": 0.77,
    "interpretation": "moderate",
    "interpretation_ko": "중등도 합의",
    "narrative_en": "Linear weighted κ = 0.53 (moderate agreement, Landis & Koch 1977). Tie-breaker invoked due to κ below threshold of 0.6.",
    "narrative_ko": "선형 가중 κ = 0.53 (중등도 합의). 임계값 0.6 이하로 tie-breaker 자동 호출."
  },
  "per_step_agreement": [
    {
      "step_id": "S1",
      "step_name": "Shake the inhaler",
      "evaluator_a_level": 2,
      "evaluator_b_level": 3,
      "level_diff": 1,
      "agreement_class": "disagree_minor",
      "agreement_label_en": "Minor disagreement — strict view sees protocol deviation; pragmatic view sees preserved effect",
      "agreement_label_ko": "경미한 불일치 — 엄격 평가는 프로토콜 일탈로 봄, 실용 평가는 효과 유지로 봄",
      "consensus_level": 3,
      "consensus_rationale": "Pragmatic interpretation aligns with HFA pMDI real-world practice; minor protocol deviation does not compromise dose delivery."
    }
  ],
  "critical_error_consensus": {
    "method": "union — any flag from either evaluator counts",
    "both_flagged": ["CRIT-pMDI-04"],
    "a_only_flagged": [],
    "b_only_flagged": [],
    "consensus_critical_errors": ["CRIT-pMDI-04"],
    "disagreement_resolved_by_tie_breaker": []
  },
  "tie_breaker": {
    "invoked": true,
    "reason": "kappa_below_threshold",
    "evaluator_c": {
      "model": "claude-opus",
      "persona": "clinical-pharmacy-educator",
      "log_path": "logs/tie_breaker_CAMCA-XXX.json"
    },
    "majority_vote_decisions": [
      {
        "step_id": "S1",
        "a_level": 2,
        "b_level": 3,
        "c_level": 3,
        "majority_level": 3
      }
    ]
  },
  "consensus_evaluation": {
    "per_step_consensus_levels": {
      "S1": 3, "S2": 3, "S3": 3, "S4": 3,
      "S5": 0, "S6": 1, "S7": 2
    },
    "total_score": 15,
    "max_possible": 21,
    "percent": 71.4,
    "critical_error_count": 1,
    "overall_verdict": "FAIL",
    "verdict_reason_en": "Critical error CRIT-pMDI-04 invalidates dose regardless of other scores",
    "verdict_reason_ko": "치명적 오류 CRIT-pMDI-04 발생으로 다른 점수와 무관하게 약물 전달 무효"
  },
  "clinician_review_flag": {
    "set": true,
    "reasons": [
      "Moderate kappa (0.53) — outside high-confidence zone",
      "Critical error present — patient requires re-training"
    ],
    "priority": "moderate"
  },
  "audit_trail": {
    "evaluator_a_log": "logs/evaluator_a_CAMCA-XXX_20260512_143000.json",
    "evaluator_b_log": "logs/evaluator_b_CAMCA-XXX_20260512_143005.json",
    "stats_log": "logs/adjudication_CAMCA-XXX.stats.json",
    "tie_breaker_log": "logs/tie_breaker_CAMCA-XXX.json"
  }
}
```

## Kappa Interpretation Phrases

Following Landis & Koch 1977.

| κ Range | English | Korean | Action |
|---|---|---|---|
| κ < 0 | Poor (worse than chance) | 매우 낮음 — 시스템 점검 필요 | Halt, flag for engineering review |
| 0.0–0.20 | Slight | 미약한 합의 | Investigate evaluator divergence; consider re-training |
| 0.21–0.40 | Fair | 약한 합의 | Tie-breaker mandatory; consider re-prompting |
| 0.41–0.60 | Moderate | 중등도 합의 | Tie-breaker recommended (per CAMCA threshold) |
| 0.61–0.80 | Substantial | 상당한 합의 | Proceed with averaged consensus + clinician review flag |
| 0.81–1.00 | Almost perfect | 거의 완벽한 합의 | Auto-approve; spot-check only |

## Per-Step Agreement Labels

| Class | English | Korean |
|---|---|---|
| agree (diff=0) | Full agreement at level {N} | 두 평가자 모두 레벨 {N}로 평가 일치 |
| disagree_minor (diff=1) | Minor disagreement — strict vs pragmatic interpretation | 경미한 불일치 — 엄격 vs 실용 관점 차이 |
| disagree_moderate (diff=2) | Moderate disagreement — substantive technique interpretation difference | 중등도 불일치 — 평가 해석의 실질적 차이 |
| disagree_major (diff=3) | Major disagreement — evaluators reach opposite conclusions | 큰 불일치 — 평가자 간 정반대 의견 |

## Clinician Review Flag — Priority Levels

| Priority | Trigger conditions | Recommended turnaround |
|---|---|---|
| `none` | κ ≥ 0.8 AND no critical errors AND no tie-breaker | No human review needed |
| `low` | κ ≥ 0.8 AND critical errors present | Within 1 week |
| `moderate` | 0.6 ≤ κ < 0.8 OR tie-breaker invoked | Within 48 hours |
| `high` | κ < 0.6 OR critical-error disagreement (after tie-breaker) | Within 24 hours |
| `urgent` | Major disagreement (diff=3) on any critical step | Same day |

## Consensus Decision Methods

### When tie-breaker NOT invoked (κ ≥ 0.6 AND no critical-error disagreement)
- Per-step consensus level = `round((A_level + B_level) / 2)`
- For ties (e.g., A=2, B=3 → round to 3, but with A persona note: prefer B's view since clinical effect preserved)
- Critical errors: union (any flag = flagged)

### When tie-breaker IS invoked
- Per-step consensus level = majority vote (2 of 3 wins)
- For 3-way split (rare, diff=2 case with C in the middle): use median
- Critical errors: majority vote (2 of 3 flagged = consensus flagged)

## Audit Trail Requirements

Every adjudication MUST produce:
1. The full output JSON (above)
2. References to both evaluator logs (read-only paths)
3. Reference to deterministic kappa stats JSON
4. Reference to tie-breaker log (if invoked)
5. Timestamp in ISO 8601 UTC

This enables full reproducibility for IRB review and publication.

## Output File Naming Convention

```
logs/adjudication_{case_id}_{ISO_timestamp}.json
```

Example: `logs/adjudication_CAMCA-001_20260512T143500Z.json`

## TODO

- [ ] Add visualization template (HTML / matplotlib) for kappa + agreement matrix
- [ ] Add CSV row template for research_log_exporter
- [ ] Add summary table generator for n=30 pilot study aggregation
