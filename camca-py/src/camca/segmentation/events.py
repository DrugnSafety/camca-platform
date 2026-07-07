"""Stage 1 — deterministic phase-event detection from 0.1s telemetry.

각 검출기는 telemetry(list[dict])만 입력받는 순수 함수이며 LLM에 의존하지 않는다.
출력 이벤트 타입 (스펙 §5.2 E1~E7):
    shake, hand_to_mouth, lip_seal, inhalation_onset, actuation,
    breath_hold, mouth_removal
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from ..telemetry.thresholds import (
    EVENT_MIN_SUSTAIN_SAMPLES,
    HAND_MOUTH_FAR_PX,
    HAND_MOUTH_NEAR_PX,
    INDEX_FINGER_ACTUATION_ACCEL_THRESHOLD,
    LIP_SEAL_MAX_DISTANCE_PX,
    WRIST_SHAKE_ZCR_MIN,
    CHEST_EXPANSION_INHALATION_RATIO,
    STILLNESS_CHEST_STD_MAX,
    get_audio_profile,
)
from ..telemetry.breath_hold_detector import detect_breath_hold, detect_inhalation_onset


@dataclass
class PhaseEvent:
    """Telemetry에서 검출된 단일 phase 이벤트."""
    type: str
    t_start_ms: int
    t_end_ms: int
    confidence: float
    source: str = "telemetry"
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _contiguous_runs(flags: list[bool], min_run: int) -> list[tuple[int, int]]:
    """True 연속 구간의 (start_idx, end_idx_exclusive) 목록. min_run 미만은 버림."""
    runs, start = [], None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_run:
                runs.append((start, i))
            start = None
    if start is not None and len(flags) - start >= min_run:
        runs.append((start, len(flags)))
    return runs


def detect_events(telemetry: list[dict], device_type: str = "pMDI") -> list[PhaseEvent]:
    """모든 검출기를 실행하고 시간순 정렬된 이벤트 목록 반환 (Stage 1 진입점).

    Task 2 단계의 임시 placeholder — Task 3에서 E1~E7 검출기 구현으로 대체된다.
    """
    return []
