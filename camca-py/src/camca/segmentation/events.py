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


def detect_shake(telemetry: list[dict]) -> list[PhaseEvent]:
    """E1 — wrist ZCR ≥ WRIST_SHAKE_ZCR_MIN이 500ms 이상 지속되는 구간."""
    flags = [s["wrist_zero_crossing_rate"] >= WRIST_SHAKE_ZCR_MIN for s in telemetry]
    events = []
    for i0, i1 in _contiguous_runs(flags, EVENT_MIN_SUSTAIN_SAMPLES):
        zcrs = [telemetry[i]["wrist_zero_crossing_rate"] for i in range(i0, i1)]
        events.append(PhaseEvent(
            type="shake",
            t_start_ms=telemetry[i0]["timestamp_ms"],
            t_end_ms=telemetry[i1 - 1]["timestamp_ms"],
            confidence=min(1.0, 0.6 + 0.1 * max(zcrs)),
            detail={"max_zcr": max(zcrs), "n_samples": i1 - i0},
        ))
    return events


def detect_hand_to_mouth(telemetry: list[dict]) -> list[PhaseEvent]:
    """E2/E7 — 히스테리시스: NEAR_PX 미만 진입 = hand_to_mouth, FAR_PX 초과 복귀 = mouth_removal.

    hand_mouth_distance_px == 0.0 은 미검출(unknown)이므로 상태를 바꾸지 않는다.
    """
    events: list[PhaseEvent] = []
    near = False
    valid_count = sum(1 for s in telemetry if s.get("hand_mouth_distance_px", 0.0) > 0.0)
    coverage = valid_count / len(telemetry) if telemetry else 0.0
    base_conf = 0.5 + 0.4 * min(coverage, 1.0)

    for s in telemetry:
        d = s.get("hand_mouth_distance_px", 0.0)
        if d <= 0.0:
            continue  # unknown — 상태 유지
        if not near and d < HAND_MOUTH_NEAR_PX:
            near = True
            events.append(PhaseEvent(
                type="hand_to_mouth", t_start_ms=s["timestamp_ms"],
                t_end_ms=s["timestamp_ms"], confidence=base_conf,
                detail={"distance_px": d, "coverage": round(coverage, 2)},
            ))
        elif near and d > HAND_MOUTH_FAR_PX:
            near = False
            events.append(PhaseEvent(
                type="mouth_removal", t_start_ms=s["timestamp_ms"],
                t_end_ms=s["timestamp_ms"], confidence=base_conf,
                detail={"distance_px": d, "coverage": round(coverage, 2)},
            ))
    return events


def detect_lip_seal(telemetry: list[dict]) -> list[PhaseEvent]:
    """E3 — lip_distance_px < LIP_SEAL_MAX_DISTANCE_PX 지속 구간 (0.0 = 미검출 제외)."""
    flags = [0.0 < s["lip_distance_px"] < LIP_SEAL_MAX_DISTANCE_PX for s in telemetry]
    events = []
    for i0, i1 in _contiguous_runs(flags, EVENT_MIN_SUSTAIN_SAMPLES):
        events.append(PhaseEvent(
            type="lip_seal",
            t_start_ms=telemetry[i0]["timestamp_ms"],
            t_end_ms=telemetry[i1 - 1]["timestamp_ms"],
            confidence=0.9,
            detail={"n_samples": i1 - i0},
        ))
    return events


def detect_inhalation_onset_event(telemetry: list[dict], device_type: str = "pMDI") -> list[PhaseEvent]:
    """E4 — audio onset (device profile) 우선, 실패 시 chest expansion fallback (L8 완화)."""
    profile = get_audio_profile(device_type)
    onset_ms = detect_inhalation_onset(telemetry, onset_threshold_db=profile["inhalation_min_db"])
    if onset_ms is not None:
        return [PhaseEvent(
            type="inhalation_onset", t_start_ms=onset_ms, t_end_ms=onset_ms,
            confidence=0.9, detail={"signal": "audio",
                                    "threshold_db": profile["inhalation_min_db"]},
        )]
    # Fallback: chest expansion ≥ 기준비율 지속
    flags = [s["chest_expansion_ratio"] >= CHEST_EXPANSION_INHALATION_RATIO for s in telemetry]
    runs = _contiguous_runs(flags, EVENT_MIN_SUSTAIN_SAMPLES)
    if runs:
        i0, _ = runs[0]
        return [PhaseEvent(
            type="inhalation_onset", t_start_ms=telemetry[i0]["timestamp_ms"],
            t_end_ms=telemetry[i0]["timestamp_ms"],
            confidence=0.6, detail={"signal": "chest"},
        )]
    return []


def detect_actuation(telemetry: list[dict]) -> list[PhaseEvent]:
    """E5 — |finger accel| ≥ threshold. 10Hz에서 1샘플=100ms ≥ 최소지속 50ms."""
    flags = [abs(s["index_finger_acceleration"]) >= INDEX_FINGER_ACTUATION_ACCEL_THRESHOLD
             for s in telemetry]
    events = []
    for i0, i1 in _contiguous_runs(flags, min_run=1):
        peak = max(abs(telemetry[i]["index_finger_acceleration"]) for i in range(i0, i1))
        events.append(PhaseEvent(
            type="actuation",
            t_start_ms=telemetry[i0]["timestamp_ms"],
            t_end_ms=telemetry[i1 - 1]["timestamp_ms"],
            confidence=min(1.0, 0.7 + peak / 1000.0),
            detail={"peak_accel": peak},
        ))
    return events


def detect_breath_hold_event(telemetry: list[dict], device_type: str = "pMDI") -> list[PhaseEvent]:
    """E6 — 기존 audio 기반 detect_breath_hold 우선, 실패 시 정지(stillness) fallback.

    Stillness = 흡입 이벤트 이후 (chest plateau: 롤링 std ≤ STILLNESS_CHEST_STD_MAX)
    AND (audio ≤ baseline+5dB) 가 3초 이상.
    """
    profile = get_audio_profile(device_type)
    bh = detect_breath_hold(
        telemetry,
        min_peak_db_for_detection=profile["min_peak_db_for_detection"],
    )
    if bh is not None:
        return [PhaseEvent(
            type="breath_hold", t_start_ms=bh.onset_ms,
            t_end_ms=bh.offset_ms or telemetry[-1]["timestamp_ms"],
            confidence=bh.confidence, detail={"signal": "audio", **bh.to_dict()},
        )]

    # Stillness fallback — 흡입 시작점 이후부터 탐색
    onset_events = detect_inhalation_onset_event(telemetry, device_type)
    search_from_ms = onset_events[0].t_end_ms if onset_events else 0
    silence_db = profile["baseline_db"] + 5.0
    window = EVENT_MIN_SUSTAIN_SAMPLES

    flags = []
    for i, s in enumerate(telemetry):
        if s["timestamp_ms"] <= search_from_ms or i < window:
            flags.append(False)
            continue
        chest_win = [telemetry[j]["chest_expansion_ratio"] for j in range(i - window, i + 1)]
        mean = sum(chest_win) / len(chest_win)
        std = (sum((c - mean) ** 2 for c in chest_win) / len(chest_win)) ** 0.5
        flags.append(std <= STILLNESS_CHEST_STD_MAX
                     and s["audio_energy_db"] <= silence_db
                     and s["chest_expansion_ratio"] >= CHEST_EXPANSION_INHALATION_RATIO - 0.02)

    runs = _contiguous_runs(flags, min_run=30)  # 3초 = 30샘플
    if not runs:
        return []
    i0, i1 = runs[0]
    return [PhaseEvent(
        type="breath_hold",
        t_start_ms=telemetry[i0]["timestamp_ms"],
        t_end_ms=telemetry[i1 - 1]["timestamp_ms"],
        confidence=0.55,  # fallback은 낮은 confidence
        detail={"signal": "stillness",
                "duration_ms": telemetry[i1 - 1]["timestamp_ms"] - telemetry[i0]["timestamp_ms"]},
    )]


def detect_events(telemetry: list[dict], device_type: str = "pMDI") -> list[PhaseEvent]:
    """모든 검출기를 실행하고 시간순 정렬된 이벤트 목록 반환 (Stage 1 진입점)."""
    if not telemetry:
        return []
    events: list[PhaseEvent] = []
    events += detect_shake(telemetry)
    events += detect_hand_to_mouth(telemetry)
    events += detect_lip_seal(telemetry)
    events += detect_inhalation_onset_event(telemetry, device_type)
    events += detect_actuation(telemetry)
    events += detect_breath_hold_event(telemetry, device_type)
    return sorted(events, key=lambda e: (e.t_start_ms, e.type))
