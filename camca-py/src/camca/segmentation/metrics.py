"""검증 지표 — spec §5.4: MABE < 0.5s, 겹침 0건, 순서 위반 0건."""
from __future__ import annotations


def mean_absolute_boundary_error_sec(pred: list[dict], gold: list[dict]) -> float | None:
    """양쪽 모두 observable한 step의 start/end 경계 오차 평균(초).

    비교 가능한 경계가 하나도 없으면 None.
    """
    gold_by_id = {s["step_id"]: s for s in gold}
    errors_ms: list[float] = []
    for p in pred:
        g = gold_by_id.get(p["step_id"])
        if not g or not p.get("observable") or not g.get("observable"):
            continue
        errors_ms.append(abs(p["t_start_ms"] - g["t_start_ms"]))
        errors_ms.append(abs(p["t_end_ms"] - g["t_end_ms"]))
    if not errors_ms:
        return None
    return round(sum(errors_ms) / len(errors_ms) / 1000.0, 3)


def overlap_violations(segments: list[dict]) -> int:
    """observable 세그먼트 간 시간 겹침 쌍의 수 (구조 불변조건 — 0이어야 함)."""
    obs = sorted((s for s in segments if s.get("observable")),
                 key=lambda s: s["t_start_ms"])
    return sum(1 for a, b in zip(obs, obs[1:]) if a["t_end_ms"] > b["t_start_ms"])
