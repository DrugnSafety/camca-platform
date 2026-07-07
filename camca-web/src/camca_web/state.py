"""spec §4 — 케이스 상태 머신과 NEEDS_ATTENTION 규칙. DB 미의존 순수 로직."""
from __future__ import annotations

UPLOADED = "UPLOADED"
QUALITY_CHECK = "QUALITY_CHECK"
RETAKE_REQUESTED = "RETAKE_REQUESTED"
ANALYZING = "ANALYZING"
SCORED = "SCORED"
REPORT_ISSUED = "REPORT_ISSUED"
FAILED = "FAILED"

_TRANSITIONS: dict[str, set[str]] = {
    UPLOADED: {QUALITY_CHECK},
    QUALITY_CHECK: {ANALYZING, RETAKE_REQUESTED},
    ANALYZING: {SCORED, FAILED},
    SCORED: {REPORT_ISSUED},
    FAILED: {ANALYZING},            # 스태프 원클릭 재실행
    RETAKE_REQUESTED: set(),        # 재촬영은 새 케이스로 업로드
    REPORT_ISSUED: set(),
}

KAPPA_ATTENTION_THRESHOLD = 0.6
PARTIAL_DATA_MIN_UNOBSERVED = 5     # 9단계 중 미관측 ≥ 5 → PARTIAL_DATA


def can_transition(cur: str, new: str) -> bool:
    return new in _TRANSITIONS.get(cur, set())


def needs_attention_reasons(final_score: dict, kappa_stats: dict,
                            segments: list[dict]) -> list[str]:
    """spec §4의 4조건 검사. 발행은 막지 않고 배지 사유만 반환."""
    reasons: list[str] = []
    crit = (final_score.get("critical_error_override") or {}).get("critical_errors") or []
    if len(crit) >= 1:
        reasons.append("critical_error")
    if any(s.get("conflict_flagged") for s in segments):
        reasons.append("conflict_flagged")
    unobserved = sum(1 for s in segments if not s.get("observable"))
    if unobserved >= PARTIAL_DATA_MIN_UNOBSERVED:
        reasons.append("partial_data")
    kappa = (kappa_stats.get("kappa") or {}).get("linear_weighted")
    if kappa is not None and kappa < KAPPA_ATTENTION_THRESHOLD:
        reasons.append("low_kappa")
    return reasons
