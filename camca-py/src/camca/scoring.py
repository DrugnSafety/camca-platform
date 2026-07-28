"""Deterministic scoring: Cohen's kappa + final verdict.

Pure Python — no external dependencies. Same input → same output (verified by
deterministic_signature).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


# ---------- Cohen's kappa ----------

def cohens_kappa(
    rater_a: list[int],
    rater_b: list[int],
    categories: list[int] | None = None,
) -> float:
    """Unweighted Cohen's kappa."""
    if len(rater_a) != len(rater_b):
        raise ValueError("Rater lists must have equal length")
    if not rater_a:
        return 0.0

    n = len(rater_a)
    if categories is None:
        categories = sorted(set(rater_a) | set(rater_b))

    p_o = sum(1 for a, b in zip(rater_a, rater_b) if a == b) / n
    p_e = sum(
        (sum(1 for x in rater_a if x == c) / n)
        * (sum(1 for x in rater_b if x == c) / n)
        for c in categories
    )

    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1 - p_e)


def weighted_kappa(
    rater_a: list[int],
    rater_b: list[int],
    weight: str = "linear",
    max_diff: int = 3,
) -> float:
    """Weighted Cohen's kappa with linear or quadratic weights."""
    if len(rater_a) != len(rater_b):
        raise ValueError("Rater lists must have equal length")
    if not rater_a:
        return 0.0

    n = len(rater_a)
    categories = sorted(set(rater_a) | set(rater_b))
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}

    matrix = [[0] * k for _ in range(k)]
    for a, b in zip(rater_a, rater_b):
        matrix[idx[a]][idx[b]] += 1

    weights = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            d = abs(categories[i] - categories[j])
            if weight == "linear":
                weights[i][j] = 1 - (d / max_diff)
            elif weight == "quadratic":
                weights[i][j] = 1 - ((d / max_diff) ** 2)
            else:
                weights[i][j] = 1.0 if d == 0 else 0.0

    p_o = sum(weights[i][j] * matrix[i][j] for i in range(k) for j in range(k)) / n
    row = [sum(matrix[i]) / n for i in range(k)]
    col = [sum(matrix[i][j] for i in range(k)) / n for j in range(k)]
    p_e = sum(weights[i][j] * row[i] * col[j] for i in range(k) for j in range(k))

    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1 - p_e)


def interpret_kappa(kappa: float) -> str:
    """Landis & Koch 1977 interpretation."""
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa < 0.21:
        return "slight"
    if kappa < 0.41:
        return "fair"
    if kappa < 0.61:
        return "moderate"
    if kappa < 0.81:
        return "substantial"
    return "almost perfect"


# ---------- Statistics aggregator ----------

def compute_stats(eval_a: dict[str, Any], eval_b: dict[str, Any]) -> dict[str, Any]:
    """Compute the full statistics dict for two evaluator outputs.

    Both inputs must conform to the CAMCA evaluator schema:
      {
        "case_id": str, "device_type": str,
        "per_step_evaluation": [{"step_id": str, "level": int, ...}, ...],
        "critical_errors_detected": [{"critical_error_id": str}, ...],
        "summary": {"total_score": int, "max_possible": int}
      }
    """
    if eval_a.get("case_id") != eval_b.get("case_id"):
        raise ValueError(f"case_id mismatch: {eval_a.get('case_id')} vs {eval_b.get('case_id')}")
    if eval_a.get("device_type") != eval_b.get("device_type"):
        raise ValueError(f"device_type mismatch")

    # Filter to observable (level not None)
    obs_a = [s for s in eval_a["per_step_evaluation"] if s.get("level") is not None]
    obs_b = [s for s in eval_b["per_step_evaluation"] if s.get("level") is not None]
    if [s["step_id"] for s in obs_a] != [s["step_id"] for s in obs_b]:
        raise ValueError("step structure mismatch on observable steps")

    levels_a = [s["level"] for s in obs_a]
    levels_b = [s["level"] for s in obs_b]

    kw_un = cohens_kappa(levels_a, levels_b, categories=[0, 1, 2, 3])
    kw_lin = weighted_kappa(levels_a, levels_b, weight="linear", max_diff=3)
    kw_quad = weighted_kappa(levels_a, levels_b, weight="quadratic", max_diff=3)

    per_step = []
    for sa, sb in zip(obs_a, obs_b):
        diff = abs(sa["level"] - sb["level"])
        agreement = ("agree" if diff == 0 else "disagree_minor" if diff == 1
                     else "disagree_moderate" if diff == 2 else "disagree_major")
        per_step.append({
            "step_id": sa["step_id"],
            "step_name": sa.get("step_name", ""),
            "evaluator_a_level": sa["level"],
            "evaluator_b_level": sb["level"],
            "level_diff": diff,
            "agreement": agreement,
        })

    crit_a = {ce["critical_error_id"] for ce in eval_a.get("critical_errors_detected", [])}
    crit_b = {ce["critical_error_id"] for ce in eval_b.get("critical_errors_detected", [])}

    score_a = eval_a.get("summary", {}).get("total_score", sum(levels_a))
    score_b = eval_b.get("summary", {}).get("total_score", sum(levels_b))
    max_score = eval_a.get("summary", {}).get("max_possible", len(levels_a) * 3)

    n = len(per_step) or 1
    return {
        "case_id": eval_a["case_id"],
        "device_type": eval_a["device_type"],
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "kappa": {
            "unweighted": round(kw_un, 4),
            "linear_weighted": round(kw_lin, 4),
            "quadratic_weighted": round(kw_quad, 4),
            "interpretation_linear": interpret_kappa(kw_lin),
        },
        "per_step_agreement": per_step,
        "summary_agreement": {
            "exact_match_rate": sum(1 for p in per_step if p["agreement"] == "agree") / n,
            "minor_disagree_rate": sum(1 for p in per_step if p["agreement"] == "disagree_minor") / n,
            "moderate_disagree_rate": sum(1 for p in per_step if p["agreement"] == "disagree_moderate") / n,
            "major_disagree_rate": sum(1 for p in per_step if p["agreement"] == "disagree_major") / n,
        },
        "critical_error_consensus": {
            "both_flagged": sorted(crit_a & crit_b),
            "a_only_flagged": sorted(crit_a - crit_b),
            "b_only_flagged": sorted(crit_b - crit_a),
            "disagreement_present": bool(crit_a ^ crit_b),
        },
        "score_divergence": {
            "evaluator_a_score": score_a,
            "evaluator_b_score": score_b,
            "absolute_diff": abs(score_a - score_b),
            "percent_diff": abs(score_a - score_b) / max_score * 100 if max_score else 0,
            "max_possible": max_score,
        },
        "tie_breaker_recommendation": {
            "needed": (kw_lin < 0.6) or bool(crit_a ^ crit_b),
            "reason": ("kappa below 0.6" if kw_lin < 0.6
                       else "critical error disagreement" if (crit_a ^ crit_b)
                       else "not needed"),
        },
        "clinician_review_flag": {
            "set": 0.6 <= kw_lin < 0.8,
            "reason": "moderate agreement zone" if 0.6 <= kw_lin < 0.8 else None,
        },
    }


# ---------- Final scoring ----------

DEVICE_MAX_SCORES = {
    "pMDI": {"core_max": 21, "core_steps": 7},
    "pMDI-spacer": {"core_max": 24, "core_steps": 8},
    "DPI-turbuhaler": {"core_max": 21, "core_steps": 7},
}

VERDICT_THRESHOLDS = [
    (86, "PROFICIENT"),
    (67, "ADEQUATE_WITH_EDUCATION"),
    (48, "NEEDS_INTENSIVE_TRAINING"),
    (0, "FAIL"),
]


def compute_final_score(
    per_step_levels: dict[str, int],
    critical_errors: list[str],
    device_type: str,
    case_id: str = "",
) -> dict[str, Any]:
    """Compute deterministic final verdict from per-step consensus levels.

    Args:
        per_step_levels: {"S1": 3, "S2": 3, ..., "S7": 2}
        critical_errors: list of critical error IDs detected
        device_type: pMDI | pMDI-spacer | DPI-turbuhaler
        case_id: optional case identifier
    """
    if device_type not in DEVICE_MAX_SCORES:
        raise ValueError(f"Unsupported device_type: {device_type}")
    spec = DEVICE_MAX_SCORES[device_type]

    core_keys = [k for k in per_step_levels if not k.endswith("8") and not k.endswith("9")]
    core_total = sum(per_step_levels[k] for k in core_keys)
    core_percent = round((core_total / spec["core_max"]) * 100, 1)

    verdict_without_override = "FAIL"
    for threshold, label in VERDICT_THRESHOLDS:
        if core_percent >= threshold:
            verdict_without_override = label
            break

    critical_override = bool(critical_errors)
    final_verdict = "FAIL" if critical_override else verdict_without_override
    verdict_reason = (
        f"Critical error(s) {critical_errors} invalidate dose regardless of score "
        f"(otherwise would be {verdict_without_override} at {core_percent}%)"
        if critical_override
        else f"Score-based: {core_percent}% in {final_verdict} band"
    )

    # Deterministic signature
    sig_input = {
        "case_id": case_id, "device_type": device_type,
        "per_step": per_step_levels, "critical_errors": sorted(critical_errors),
    }
    sig = "sha256:" + hashlib.sha256(
        json.dumps(sig_input, sort_keys=True).encode()
    ).hexdigest()[:16]

    return {
        "case_id": case_id,
        "device_type": device_type,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "per_step_levels": per_step_levels,
        "score_components": {
            "core_steps_total": core_total,
            "core_steps_max": spec["core_max"],
            "core_steps_percent": core_percent,
        },
        "critical_error_override": {
            "applied": critical_override,
            "critical_errors": critical_errors,
            "verdict_override": "FAIL" if critical_override else None,
        },
        "final_verdict": final_verdict,
        "verdict_reason": verdict_reason,
        "score_band_without_override": f"{verdict_without_override} ({core_percent}%)",
        "deterministic_signature": sig,
    }
