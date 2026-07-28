"""Use the deterministic scoring layer WITHOUT running VLM backends.

Useful when you already have evaluator JSON outputs from elsewhere (e.g., manual
review, GPT-4o, other research) and just want CAMCA's kappa + verdict layer.
"""
import json
from camca import compute_stats, compute_final_score

# Two pre-existing evaluator outputs
eval_a = {
    "case_id": "DEMO",
    "device_type": "pMDI",
    "per_step_evaluation": [
        {"step_id": "S1", "level": 2}, {"step_id": "S2", "level": 3},
        {"step_id": "S3", "level": 2}, {"step_id": "S4", "level": 3},
        {"step_id": "S5", "level": 0}, {"step_id": "S6", "level": 1},
        {"step_id": "S7", "level": 1},
    ],
    "critical_errors_detected": [{"critical_error_id": "CRIT-pMDI-04"}],
    "summary": {"total_score": 12, "max_possible": 21},
}

eval_b = {
    "case_id": "DEMO",
    "device_type": "pMDI",
    "per_step_evaluation": [
        {"step_id": "S1", "level": 3}, {"step_id": "S2", "level": 3},
        {"step_id": "S3", "level": 3}, {"step_id": "S4", "level": 3},
        {"step_id": "S5", "level": 0}, {"step_id": "S6", "level": 2},
        {"step_id": "S7", "level": 2},
    ],
    "critical_errors_detected": [{"critical_error_id": "CRIT-pMDI-04"}],
    "summary": {"total_score": 16, "max_possible": 21},
}

# Compute kappa + agreement statistics
stats = compute_stats(eval_a, eval_b)
print(json.dumps(stats["kappa"], indent=2))
print(f"\nTie-breaker needed: {stats['tie_breaker_recommendation']['needed']}")
print(f"Reason: {stats['tie_breaker_recommendation']['reason']}")

# Build a consensus and run final scoring
consensus = {p["step_id"]: round((p["evaluator_a_level"] + p["evaluator_b_level"]) / 2)
             for p in stats["per_step_agreement"]}
final = compute_final_score(
    per_step_levels=consensus,
    critical_errors=stats["critical_error_consensus"]["both_flagged"],
    device_type="pMDI",
    case_id="DEMO",
)
print(f"\nFinal verdict: {final['final_verdict']}")
print(f"Reason: {final['verdict_reason']}")
print(f"Deterministic signature: {final['deterministic_signature']}")
