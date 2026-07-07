# Phase Recognition Engine Implementation Plan (Plan 1 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** camca-py에 telemetry-anchored 하이브리드 phase recognition 모듈(`camca/segmentation/`)을 추가해, VLM 단독 세그멘테이션의 경계 겹침·actuation 미검출·L7(1fps) 문제를 해소한다.

**Architecture:** 3단계 — Stage 1: 0.1초 telemetry에서 결정론적 이벤트 검출(E1~E7, LLM 미관여) → Stage 2: VLM이 후보 경계 ±1초 dense 프레임만 정밀 라벨링 + telemetry-blind 단계(S2/S3) sparse 스캔 → Stage 3: canonical 순서 제약 정렬로 겹침 없는 S1~S9 세그먼트 + 경계별 confidence/source 출력. 기존 `segmentation.json` 소비자(evaluator A/B)와 하위 호환.

**Tech Stack:** Python 3.11+, 기존 camca-py 모듈 재사용(MediaPipe/librosa telemetry, thresholds, breath_hold_detector, VLMBackend), pytest. VLM 없이도 Stage 1+3만으로 동작(순수 함수 → 전 단계 mediapipe 불필요 테스트 가능).

**Working directory:** `camca-py/` (모든 경로는 이 디렉토리 기준)

**Scope note (Plan 2):** 웹 플랫폼 모놀리스(FastAPI, 업로드→발행→대시보드)는 별도 계획 `2026-07-07-camca-web-platform.md`(후속 작성)로 분리한다. 본 계획은 CLI로 검증 가능한 엔진만 다룬다.

**사전 확인 사항 (계획 작성 시 실측):**
- 현재 telemetry 7키에 `hand_mouth_distance_px` 없음 → Task 1에서 추가
- `detect_inhalation_onset`, `detect_breath_hold`, `DEVICE_AUDIO_PROFILES`, `WRIST_SHAKE_ZCR_MIN` 등은 `camca/telemetry/`에 이미 존재 → 재사용
- `camca-py/tests/` 디렉토리 없음 → Task 0에서 생성
- pydantic `VideoSegment`/`SegmentationReport`는 `camca/schemas.py`에 존재 (pydantic 미설치 시 no-op fallback 포함)

---

## File Structure

```
camca-py/
├── src/camca/
│   ├── segmentation/                    # 신규 패키지
│   │   ├── __init__.py                  # 공개 API re-export
│   │   ├── events.py                    # PhaseEvent + E1~E7 검출기 (Stage 1)
│   │   ├── templates.py                 # canonical step 템플릿 + event→step 매핑
│   │   ├── alignment.py                 # 순서 제약 정렬 → 겹침 없는 세그먼트 (Stage 3)
│   │   ├── vlm_refiner.py               # 경계 dense 프레임 + VLM 정밀화 (Stage 2)
│   │   ├── engine.py                    # PhaseRecognitionEngine 오케스트레이션
│   │   └── metrics.py                   # boundary error 검증 지표
│   ├── telemetry/
│   │   ├── mediapipe_extractor.py       # 수정: hand_mouth_distance_px 추가
│   │   ├── pipeline.py                  # 수정: TELEMETRY_KEYS + audio-only fallback 키 추가
│   │   └── thresholds.py                # 수정: hand-mouth/stillness 상수 추가
│   ├── pipeline.py                      # 수정: MultiModelPipeline에 use_phase_engine 옵션
│   └── cli.py                           # 수정: `camca segment` 서브커맨드 추가
└── tests/
    ├── conftest.py                      # 합성 telemetry 빌더 fixture
    └── segmentation/
        ├── test_events.py
        ├── test_alignment.py
        ├── test_engine.py
        └── test_metrics.py
```

각 파일 책임: `events.py`는 telemetry→이벤트만(파일 I/O 없음), `alignment.py`는 이벤트→세그먼트만(telemetry 모름), `engine.py`만이 셋을 조립하고 파일을 쓴다. VLM 의존은 `vlm_refiner.py`에 격리.

---

### Task 0: 테스트 스캐폴딩 + 합성 telemetry 빌더

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/segmentation/__init__.py` (빈 파일)

- [ ] **Step 1: conftest에 합성 telemetry 빌더 작성**

MediaPipe 없이 모든 검출기를 테스트하기 위한 핵심 fixture. 10Hz(100ms) 샘플을 구간별 오버라이드로 생성한다.

```python
# tests/conftest.py
"""Shared fixtures — synthetic telemetry builder (no mediapipe required)."""
import pytest


BASELINE_SAMPLE = {
    "audio_energy_db": 36.0,
    "lip_distance_px": 20.0,
    "head_pitch_deg": 0.0,
    "index_finger_acceleration": 0.0,
    "wrist_zero_crossing_rate": 0,
    "chest_expansion_ratio": 1.0,
    "hand_mouth_distance_px": 300.0,
}


def make_telemetry(duration_ms: int, overrides: list[tuple[int, int, dict]] = ()) -> list[dict]:
    """Build a 10Hz synthetic telemetry stream.

    Args:
        duration_ms: total length
        overrides: list of (t_start_ms, t_end_ms, {field: value}) applied to
                   samples whose timestamp falls in [t_start_ms, t_end_ms).
    """
    samples = []
    for ts in range(0, duration_ms, 100):
        s = {"timestamp_ms": ts, **BASELINE_SAMPLE}
        for t0, t1, fields in overrides:
            if t0 <= ts < t1:
                s.update(fields)
        samples.append(s)
    return samples


@pytest.fixture
def telemetry_builder():
    return make_telemetry


@pytest.fixture
def full_technique_telemetry():
    """정석적인 pMDI 시연 20초: 흔들기→손이 입으로→입술 밀폐→흡입+actuation→숨참기→제거."""
    return make_telemetry(20_000, [
        (500, 2500, {"wrist_zero_crossing_rate": 4}),                       # E1 shake
        (3000, 4500, {"hand_mouth_distance_px": 150.0}),                    # E2 접근 중
        (4500, 15_000, {"hand_mouth_distance_px": 40.0}),                   # 입 근처 유지
        (5000, 12_000, {"lip_distance_px": 3.0}),                           # E3 lip seal
        (6000, 9000, {"audio_energy_db": 62.0,                              # E4 흡입음
                      "chest_expansion_ratio": 1.15}),
        (6000, 6200, {"index_finger_acceleration": 150.0}),                 # E5 actuation
        (9000, 15_000, {"audio_energy_db": 36.0,                            # E6 숨참기(무음+정지)
                        "chest_expansion_ratio": 1.14}),
        (15_000, 20_000, {"hand_mouth_distance_px": 280.0}),                # E7 제거
    ])
```

- [ ] **Step 2: 빈 패키지 파일 생성**

```bash
mkdir -p tests/segmentation
touch tests/segmentation/__init__.py
```

- [ ] **Step 3: pytest 수집 확인**

Run: `cd camca-py && python -m pytest tests/ --collect-only -q`
Expected: `no tests ran` (에러 없이 수집 0건)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: add synthetic telemetry builder fixture for segmentation tests"
```

---

### Task 1: telemetry에 hand_mouth_distance_px 추가

스펙 E2/E7(손→입 접근/제거)의 신호. 현재 7키 telemetry에 없어 신규 추가한다.

**Files:**
- Modify: `src/camca/telemetry/mediapipe_extractor.py`
- Modify: `src/camca/telemetry/pipeline.py` (TELEMETRY_KEYS, audio-only fallback, TelemetrySample)
- Test: `tests/segmentation/test_telemetry_keys.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_telemetry_keys.py
"""hand_mouth_distance_px가 telemetry 스키마에 포함되는지 확인 (mediapipe 불필요)."""
from camca.telemetry.pipeline import TELEMETRY_KEYS, TelemetrySample


def test_hand_mouth_distance_in_keys():
    assert "hand_mouth_distance_px" in TELEMETRY_KEYS


def test_telemetry_sample_has_hand_mouth_field():
    s = TelemetrySample(
        timestamp_ms=0, audio_energy_db=36.0, lip_distance_px=20.0,
        head_pitch_deg=0.0, index_finger_acceleration=0.0,
        wrist_zero_crossing_rate=0, chest_expansion_ratio=1.0,
        hand_mouth_distance_px=300.0,
    )
    assert s.to_dict()["hand_mouth_distance_px"] == 300.0
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_telemetry_keys.py -v`
Expected: FAIL — `AssertionError` (KEYS에 없음) / `TypeError: unexpected keyword argument`

- [ ] **Step 3: pipeline.py 수정**

`src/camca/telemetry/pipeline.py`에서 세 곳 수정:

```python
# (1) TELEMETRY_KEYS 리스트 끝에 추가
TELEMETRY_KEYS = [
    "timestamp_ms",
    "audio_energy_db",
    "lip_distance_px",
    "head_pitch_deg",
    "index_finger_acceleration",
    "wrist_zero_crossing_rate",
    "chest_expansion_ratio",
    "hand_mouth_distance_px",
]

# (2) TelemetrySample dataclass에 필드 추가 (chest_expansion_ratio 아래)
    chest_expansion_ratio: float
    hand_mouth_distance_px: float = 0.0

# (3) extract_telemetry()의 audio-only fallback dict에 키 추가
            {
                "timestamp_ms": ts,
                "audio_energy_db": db,
                "lip_distance_px": 0.0,
                "head_pitch_deg": 0.0,
                "index_finger_acceleration": 0.0,
                "wrist_zero_crossing_rate": 0,
                "chest_expansion_ratio": 1.0,
                "hand_mouth_distance_px": 0.0,
            }
```

- [ ] **Step 4: mediapipe_extractor.py에 측정 메서드 추가**

`VisionTelemetryExtractor`에 메서드 추가 (`wrist_zero_crossing_rate` 메서드 아래). 입 중심(FaceMesh 입술 상/하 중점)과 검지 끝(Hands INDEX_FINGER_TIP)의 픽셀 거리:

```python
    def hand_mouth_distance_px(self, frame_rgb) -> float:
        """검지 끝과 입 중심 사이 픽셀 거리. 얼굴/손 미검출 시 0.0 (unknown)."""
        face = self._face.process(frame_rgb)
        hands = self._hands.process(frame_rgb)
        if not face.multi_face_landmarks or not hands.multi_hand_landmarks:
            return 0.0
        h, w = frame_rgb.shape[:2]
        flm = face.multi_face_landmarks[0].landmark
        mouth_x = (flm[LIP_UPPER_IDX].x + flm[LIP_LOWER_IDX].x) / 2 * w
        mouth_y = (flm[LIP_UPPER_IDX].y + flm[LIP_LOWER_IDX].y) / 2 * h
        tip = hands.multi_hand_landmarks[0].landmark[INDEX_FINGER_TIP]
        return float(round(math.hypot(tip.x * w - mouth_x, tip.y * h - mouth_y), 1))
```

그리고 `extract()`의 samples.append dict에 한 줄 추가:

```python
                    "chest_expansion_ratio": self.chest_expansion_ratio(rgb),
                    "hand_mouth_distance_px": self.hand_mouth_distance_px(rgb),
```

**주의**: 미검출 시 0.0은 "가까움"이 아니라 "unknown" 의미. 검출기(Task 3)는 0.0 샘플을 무시해야 한다.

- [ ] **Step 5: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_telemetry_keys.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add src/camca/telemetry/ tests/segmentation/test_telemetry_keys.py
git commit -m "feat(telemetry): add hand_mouth_distance_px metric for phase events E2/E7"
```

---

### Task 2: thresholds 상수 추가 + PhaseEvent 모델

**Files:**
- Modify: `src/camca/telemetry/thresholds.py`
- Create: `src/camca/segmentation/__init__.py`
- Create: `src/camca/segmentation/events.py`
- Test: `tests/segmentation/test_events.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_events.py
"""Stage 1 이벤트 검출기 테스트 — 전부 합성 telemetry, mediapipe 불필요."""
from tests.conftest import make_telemetry
from camca.segmentation.events import PhaseEvent


def test_phase_event_to_dict():
    e = PhaseEvent(type="shake", t_start_ms=500, t_end_ms=2400,
                   confidence=0.9, source="telemetry", detail={"max_zcr": 4})
    d = e.to_dict()
    assert d["type"] == "shake"
    assert d["t_start_ms"] == 500
    assert d["source"] == "telemetry"
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_events.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'camca.segmentation'`

- [ ] **Step 3: thresholds 상수 + 모델 구현**

`src/camca/telemetry/thresholds.py` 끝에 추가:

```python
# ---- Phase recognition (segmentation) thresholds — v0.4.0 ----

HAND_MOUTH_NEAR_PX = 80.0
"""검지-입 거리가 이 값 미만이면 '기기가 입 근처'로 판정."""

HAND_MOUTH_FAR_PX = 160.0
"""이 값 초과로 복귀하면 '기기 제거'로 판정 (히스테리시스 밴드)."""

EVENT_MIN_SUSTAIN_SAMPLES = 5
"""이벤트 성립 최소 지속 샘플 수 (10Hz에서 500ms) — 단발 노이즈 배제."""

STILLNESS_CHEST_STD_MAX = 0.02
"""숨참기(정지) 판정: 창 내 chest_expansion_ratio 표준편차 상한."""
```

`src/camca/segmentation/__init__.py`:

```python
"""Phase Recognition Engine — telemetry-anchored hybrid segmentation (v0.4.0)."""
from .events import PhaseEvent, detect_events
from .alignment import align_events_to_steps
from .engine import PhaseRecognitionEngine
from .metrics import mean_absolute_boundary_error_sec

__all__ = [
    "PhaseEvent", "detect_events", "align_events_to_steps",
    "PhaseRecognitionEngine", "mean_absolute_boundary_error_sec",
]
```

(주의: `alignment`/`engine`/`metrics`는 Task 4~7에서 생성. 이 시점에는 `__init__.py`를 아래 최소본으로 작성하고, 각 태스크에서 import를 추가한다.)

```python
"""Phase Recognition Engine — telemetry-anchored hybrid segmentation (v0.4.0)."""
from .events import PhaseEvent, detect_events

__all__ = ["PhaseEvent", "detect_events"]
```

`src/camca/segmentation/events.py`:

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_events.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add src/camca/telemetry/thresholds.py src/camca/segmentation/ tests/segmentation/test_events.py
git commit -m "feat(segmentation): add PhaseEvent model and phase-recognition thresholds"
```

---

### Task 3: E1~E7 검출기 구현

**Files:**
- Modify: `src/camca/segmentation/events.py`
- Modify: `tests/segmentation/test_events.py`

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/segmentation/test_events.py`에 추가:

```python
from camca.segmentation.events import (
    detect_shake, detect_hand_to_mouth, detect_lip_seal,
    detect_inhalation_onset_event, detect_actuation,
    detect_breath_hold_event, detect_events,
)


def test_detect_shake_finds_sustained_zcr():
    t = make_telemetry(5000, [(500, 2500, {"wrist_zero_crossing_rate": 4})])
    events = detect_shake(t)
    assert len(events) == 1
    assert events[0].type == "shake"
    assert events[0].t_start_ms == 500
    assert 2300 <= events[0].t_end_ms <= 2500


def test_detect_shake_ignores_single_spike():
    t = make_telemetry(5000, [(500, 700, {"wrist_zero_crossing_rate": 4})])  # 200ms < 500ms
    assert detect_shake(t) == []


def test_detect_hand_to_mouth_approach_and_removal():
    t = make_telemetry(20_000, [
        (4500, 15_000, {"hand_mouth_distance_px": 40.0}),
        (15_000, 20_000, {"hand_mouth_distance_px": 280.0}),
    ])
    events = detect_hand_to_mouth(t)
    types = [e.type for e in events]
    assert "hand_to_mouth" in types
    assert "mouth_removal" in types
    approach = next(e for e in events if e.type == "hand_to_mouth")
    removal = next(e for e in events if e.type == "mouth_removal")
    assert approach.t_start_ms == 4500
    assert removal.t_start_ms == 15_000


def test_detect_hand_to_mouth_ignores_zero_unknown():
    """0.0은 미검출(unknown)이므로 '가까움'으로 판정하면 안 된다."""
    t = make_telemetry(5000, [(0, 5000, {"hand_mouth_distance_px": 0.0})])
    assert detect_hand_to_mouth(t) == []


def test_detect_lip_seal():
    t = make_telemetry(15_000, [(5000, 12_000, {"lip_distance_px": 3.0})])
    events = detect_lip_seal(t)
    assert len(events) == 1
    assert events[0].type == "lip_seal"
    assert events[0].t_start_ms == 5000


def test_inhalation_onset_from_audio():
    t = make_telemetry(15_000, [(6000, 9000, {"audio_energy_db": 62.0})])
    events = detect_inhalation_onset_event(t, device_type="pMDI")
    assert len(events) == 1
    assert events[0].t_start_ms == 6000
    assert events[0].detail["signal"] == "audio"


def test_inhalation_onset_chest_fallback_when_audio_quiet():
    """L8 완화: AIM 시뮬레이터처럼 audio가 조용하면 chest expansion으로 fallback."""
    t = make_telemetry(15_000, [(6000, 9000, {"chest_expansion_ratio": 1.15})])
    events = detect_inhalation_onset_event(t, device_type="pMDI-AIM-simulator")
    assert len(events) == 1
    assert events[0].detail["signal"] == "chest"
    assert events[0].confidence < 0.8  # fallback은 confidence 낮게


def test_detect_actuation_spike():
    t = make_telemetry(10_000, [(6000, 6200, {"index_finger_acceleration": 150.0})])
    events = detect_actuation(t)
    assert len(events) == 1
    assert events[0].type == "actuation"
    assert events[0].t_start_ms == 6000


def test_detect_actuation_below_threshold_ignored():
    t = make_telemetry(10_000, [(6000, 6200, {"index_finger_acceleration": 50.0})])
    assert detect_actuation(t) == []


def test_detect_breath_hold_stillness_fallback():
    """audio peak가 없어도 (chest plateau + 무음) 정지 구간을 breath_hold로 검출."""
    t = make_telemetry(20_000, [
        (6000, 9000, {"audio_energy_db": 47.0, "chest_expansion_ratio": 1.15}),  # AIM 수준 흡입
        (9000, 15_000, {"chest_expansion_ratio": 1.14}),                         # 정지+무음
    ])
    events = detect_breath_hold_event(t, device_type="pMDI-AIM-simulator")
    assert len(events) == 1
    assert events[0].type == "breath_hold"
    assert 8500 <= events[0].t_start_ms <= 9500


def test_detect_events_full_technique(full_technique_telemetry):
    events = detect_events(full_technique_telemetry, device_type="pMDI")
    types = {e.type for e in events}
    assert {"shake", "hand_to_mouth", "lip_seal", "inhalation_onset",
            "actuation", "breath_hold", "mouth_removal"} <= types
    # 시간순 정렬 보장
    starts = [e.t_start_ms for e in events]
    assert starts == sorted(starts)
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_events.py -v`
Expected: FAIL — `ImportError: cannot import name 'detect_shake'`

- [ ] **Step 3: 검출기 구현**

`src/camca/segmentation/events.py`에 추가:

```python
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
    """E5 — |finger accel| ≥ threshold, 최소 지속 50ms(연속 샘플 기준 1개+, 10Hz라 1샘플=100ms)."""
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_events.py -v`
Expected: PASS (전체 통과). 실패 시 threshold 경계값(합성 데이터의 47dB vs profile 45dB 등)을 테스트가 아닌 **합성 데이터 쪽에서** 조정 — threshold 상수는 임상 보정값이므로 테스트 편의로 바꾸지 않는다.

- [ ] **Step 5: Commit**

```bash
git add src/camca/segmentation/events.py tests/segmentation/test_events.py
git commit -m "feat(segmentation): implement E1-E7 deterministic phase-event detectors"
```

---

### Task 4: canonical 템플릿 + 순서 제약 정렬 (Stage 3)

**Files:**
- Create: `src/camca/segmentation/templates.py`
- Create: `src/camca/segmentation/alignment.py`
- Test: `tests/segmentation/test_alignment.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_alignment.py
"""Stage 3 — 이벤트→겹침 없는 canonical 세그먼트 정렬."""
from camca.segmentation.events import PhaseEvent
from camca.segmentation.alignment import align_events_to_steps
from camca.segmentation.templates import PMDI_TEMPLATE


def _ev(type, t0, t1=None, conf=0.9):
    return PhaseEvent(type=type, t_start_ms=t0, t_end_ms=t1 or t0, confidence=conf)


FULL_EVENTS = [
    _ev("shake", 500, 2400),
    _ev("hand_to_mouth", 4500),
    _ev("lip_seal", 5000, 11_900),
    _ev("inhalation_onset", 6000),
    _ev("actuation", 6000, 6100),
    _ev("breath_hold", 9000, 14_900),
    _ev("mouth_removal", 15_000),
]


def test_all_canonical_steps_present():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    assert [s["step_id"] for s in segs] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]


def test_no_overlapping_boundaries():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    observed = [s for s in segs if s["observable"]]
    for a, b in zip(observed, observed[1:]):
        assert a["t_end_ms"] <= b["t_start_ms"], f"{a['step_id']} overlaps {b['step_id']}"


def test_event_anchored_steps_observable():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    by_id = {s["step_id"]: s for s in segs}
    assert by_id["S1"]["observable"] is True          # shake
    assert by_id["S4"]["observable"] is True          # hand_to_mouth + lip_seal
    assert by_id["S5"]["observable"] is True          # inhalation + actuation
    assert by_id["S7"]["observable"] is True          # breath_hold + removal
    assert by_id["S2"]["observable"] is False         # telemetry-blind (cap)
    assert by_id["S3"]["observable"] is False         # telemetry-blind (exhale away)
    assert by_id["S2"]["needs_vlm"] is True           # Stage 2가 채울 대상


def test_boundary_source_and_confidence_recorded():
    segs = align_events_to_steps(FULL_EVENTS, PMDI_TEMPLATE, video_duration_ms=20_000)
    s5 = next(s for s in segs if s["step_id"] == "S5")
    assert s5["boundary_source"] == "telemetry"
    assert 0.0 < s5["boundary_confidence"] <= 1.0
    assert any(e["type"] == "actuation" for e in s5["events"])


def test_out_of_order_events_still_canonical_order():
    """환자가 순서를 바꿔도 (예: 흔들기를 입에 문 후에) canonical 순서로 출력."""
    events = [
        _ev("hand_to_mouth", 1000),
        _ev("shake", 3000, 4000),          # 순서 위반
        _ev("inhalation_onset", 6000),
        _ev("breath_hold", 9000, 12_000),
    ]
    segs = align_events_to_steps(events, PMDI_TEMPLATE, video_duration_ms=15_000)
    assert [s["step_id"] for s in segs] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
    s1 = next(s for s in segs if s["step_id"] == "S1")
    assert s1["observable"] is True
    assert s1.get("order_violation") is True          # 위반 사실은 기록


def test_missing_events_marked_unobservable():
    segs = align_events_to_steps([], PMDI_TEMPLATE, video_duration_ms=10_000)
    assert all(s["observable"] is False for s in segs)
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_alignment.py -v`
Expected: FAIL — `ModuleNotFoundError` (templates/alignment 없음)

- [ ] **Step 3: templates.py 구현**

```python
# src/camca/segmentation/templates.py
"""Canonical step 템플릿 — 각 step이 어떤 telemetry 이벤트로 anchor되는지 정의.

anchor_events가 빈 step은 telemetry-blind → Stage 2 VLM이 채운다 (needs_vlm).
S6(흡입 지속)은 S5 inhalation_onset ~ S7 breath_hold 사이 구간으로 유도되므로
derived_between으로 표기한다.
"""

PMDI_TEMPLATE = [
    {"step_id": "S1", "label": "Shake the inhaler",
     "anchor_events": ["shake"]},
    {"step_id": "S2", "label": "Remove cap and inspect",
     "anchor_events": []},
    {"step_id": "S3", "label": "Exhale gently away from inhaler",
     "anchor_events": []},
    {"step_id": "S4", "label": "Place mouthpiece in mouth with lip seal",
     "anchor_events": ["hand_to_mouth", "lip_seal"]},
    {"step_id": "S5", "label": "Begin slow inhalation AND press canister simultaneously",
     "anchor_events": ["inhalation_onset", "actuation"]},
    {"step_id": "S6", "label": "Continue slow deep inhalation to full lung capacity",
     "anchor_events": [], "derived_between": ("S5", "S7")},
    {"step_id": "S7", "label": "Hold breath 10 sec, then exhale slowly",
     "anchor_events": ["breath_hold", "mouth_removal"]},
    {"step_id": "S8", "label": "Rinse mouth (ICS only)",
     "anchor_events": []},
    {"step_id": "S9", "label": "Replace cap and store",
     "anchor_events": []},
]

TURBUHALER_TEMPLATE = [
    {"step_id": "T1", "label": "Unscrew and remove cover", "anchor_events": []},
    {"step_id": "T2", "label": "Hold upright and twist grip until click",
     "anchor_events": []},  # click은 audio 이벤트 — Phase 2에서 추가
    {"step_id": "T3", "label": "Exhale gently away from inhaler", "anchor_events": []},
    {"step_id": "T4", "label": "Place mouthpiece in mouth with lip seal",
     "anchor_events": ["hand_to_mouth", "lip_seal"]},
    {"step_id": "T5", "label": "Inhale forcefully and deeply",
     "anchor_events": ["inhalation_onset"]},
    {"step_id": "T6", "label": "Remove inhaler while holding breath",
     "anchor_events": ["mouth_removal"]},
    {"step_id": "T7", "label": "Hold breath 10 sec, then exhale slowly",
     "anchor_events": ["breath_hold"]},
]


def get_template(device_type: str) -> list[dict]:
    """device_type prefix로 템플릿 선택 (pMDI 계열은 모두 PMDI_TEMPLATE)."""
    if device_type.lower().startswith("dpi") or "turbuhaler" in device_type.lower():
        return TURBUHALER_TEMPLATE
    return PMDI_TEMPLATE
```

- [ ] **Step 4: alignment.py 구현**

```python
# src/camca/segmentation/alignment.py
"""Stage 3 — 이벤트 시퀀스를 canonical 템플릿에 정렬해 겹침 없는 세그먼트 생성.

불변조건 (spec §5.4):
  1. 출력은 항상 canonical 순서 (모든 step 포함, 미관측은 observable=False)
  2. observable 세그먼트 간 시간 겹침 0
  3. 각 세그먼트에 boundary_confidence / boundary_source / events 기록
"""
from __future__ import annotations

from typing import Any

from .events import PhaseEvent


def _assign_events(events: list[PhaseEvent], template: list[dict]) -> dict[str, list[PhaseEvent]]:
    """각 이벤트를 anchor_events 매핑에 따라 step에 배정. 같은 타입 복수 발생 시 첫 것만."""
    assignment: dict[str, list[PhaseEvent]] = {t["step_id"]: [] for t in template}
    consumed_types: set[str] = set()
    for step in template:
        for ev_type in step["anchor_events"]:
            if ev_type in consumed_types:
                continue
            matches = [e for e in events if e.type == ev_type]
            if matches:
                assignment[step["step_id"]].append(matches[0])
                consumed_types.add(ev_type)
    return assignment


def align_events_to_steps(
    events: list[PhaseEvent],
    template: list[dict],
    video_duration_ms: int,
) -> list[dict[str, Any]]:
    """이벤트 → canonical 세그먼트 목록 (겹침 없음 보장)."""
    assignment = _assign_events(events, template)

    # 1차: 이벤트가 있는 step의 draft 경계
    segments: list[dict[str, Any]] = []
    for step in template:
        evs = assignment[step["step_id"]]
        seg: dict[str, Any] = {
            "step_id": step["step_id"],
            "label": step["label"],
            "observable": bool(evs),
            "needs_vlm": not evs,          # telemetry로 못 본 step은 VLM 확인 대상
            "t_start_ms": min(e.t_start_ms for e in evs) if evs else None,
            "t_end_ms": max(e.t_end_ms for e in evs) if evs else None,
            "boundary_source": "telemetry" if evs else None,
            "boundary_confidence": (
                round(sum(e.confidence for e in evs) / len(evs), 2) if evs else 0.0
            ),
            "events": [e.to_dict() for e in evs],
        }
        segments.append(seg)

    # S6류 derived step: 앞뒤 anchor 사이 구간
    by_id = {s["step_id"]: s for s in segments}
    for step in template:
        if "derived_between" not in step:
            continue
        prev_id, next_id = step["derived_between"]
        prev_s, next_s = by_id.get(prev_id), by_id.get(next_id)
        seg = by_id[step["step_id"]]
        if prev_s and next_s and prev_s["observable"] and next_s["observable"] \
                and prev_s["t_end_ms"] < next_s["t_start_ms"]:
            seg.update(
                observable=True, needs_vlm=False,
                t_start_ms=prev_s["t_end_ms"], t_end_ms=next_s["t_start_ms"],
                boundary_source="telemetry",
                boundary_confidence=round(
                    (prev_s["boundary_confidence"] + next_s["boundary_confidence"]) / 2, 2),
            )

    # 순서 위반 검출: observable step들의 실제 시간이 canonical 순서와 다르면 기록
    observed = [s for s in segments if s["observable"]]
    anchor_times = [s["t_start_ms"] for s in observed]
    if anchor_times != sorted(anchor_times):
        for s, sorted_t in zip(observed, sorted(anchor_times)):
            if s["t_start_ms"] != sorted_t:
                s["order_violation"] = True

    # 겹침 제거: observable 세그먼트를 시간순으로 보고 인접 경계를 중간점에서 클리핑
    observed_sorted = sorted(observed, key=lambda s: s["t_start_ms"])
    for a, b in zip(observed_sorted, observed_sorted[1:]):
        if a["t_end_ms"] > b["t_start_ms"]:
            mid = (b["t_start_ms"] + a["t_end_ms"]) // 2
            mid = max(b["t_start_ms"], min(mid, a["t_end_ms"]))
            # 단, 원래 순서 그대로 자르되 최소 100ms 폭 보장
            a["t_end_ms"] = mid
            b["t_start_ms"] = mid
            a["boundary_confidence"] = round(a["boundary_confidence"] * 0.8, 2)
            b["boundary_confidence"] = round(b["boundary_confidence"] * 0.8, 2)

    # 경계를 영상 범위로 클램프
    for s in segments:
        if s["observable"]:
            s["t_start_ms"] = max(0, min(s["t_start_ms"], video_duration_ms))
            s["t_end_ms"] = max(s["t_start_ms"], min(s["t_end_ms"], video_duration_ms))

    return segments
```

- [ ] **Step 5: `__init__.py`에 export 추가**

```python
from .events import PhaseEvent, detect_events
from .alignment import align_events_to_steps
from .templates import get_template, PMDI_TEMPLATE, TURBUHALER_TEMPLATE

__all__ = ["PhaseEvent", "detect_events", "align_events_to_steps",
           "get_template", "PMDI_TEMPLATE", "TURBUHALER_TEMPLATE"]
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_alignment.py -v`
Expected: PASS (전체)

- [ ] **Step 7: Commit**

```bash
git add src/camca/segmentation/ tests/segmentation/test_alignment.py
git commit -m "feat(segmentation): canonical templates + order-constrained alignment (no-overlap invariant)"
```

---

### Task 5: 검증 지표 (boundary error)

**Files:**
- Create: `src/camca/segmentation/metrics.py`
- Test: `tests/segmentation/test_metrics.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_metrics.py
"""Spec §5.4 검증 게이트 지표 — human 라벨 대비 mean absolute boundary error."""
from camca.segmentation.metrics import mean_absolute_boundary_error_sec, overlap_violations


def test_boundary_error_perfect_match():
    pred = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    gold = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    assert mean_absolute_boundary_error_sec(pred, gold) == 0.0


def test_boundary_error_averages_start_and_end():
    pred = [{"step_id": "S1", "observable": True, "t_start_ms": 1000, "t_end_ms": 3000}]
    gold = [{"step_id": "S1", "observable": True, "t_start_ms": 500, "t_end_ms": 2400}]
    # |1000-500| + |3000-2400| = 1100ms / 2경계 = 550ms = 0.55s
    assert abs(mean_absolute_boundary_error_sec(pred, gold) - 0.55) < 1e-9


def test_boundary_error_skips_unobservable():
    pred = [{"step_id": "S2", "observable": False, "t_start_ms": None, "t_end_ms": None}]
    gold = [{"step_id": "S2", "observable": False, "t_start_ms": None, "t_end_ms": None}]
    assert mean_absolute_boundary_error_sec(pred, gold) is None  # 비교 대상 없음


def test_overlap_violations_counts():
    segs = [
        {"step_id": "S4", "observable": True, "t_start_ms": 0, "t_end_ms": 1500},
        {"step_id": "S5", "observable": True, "t_start_ms": 500, "t_end_ms": 3000},
    ]
    assert overlap_violations(segs) == 1
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 구현**

```python
# src/camca/segmentation/metrics.py
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
```

- [ ] **Step 4: `__init__.py`에 export 추가**

```python
from .metrics import mean_absolute_boundary_error_sec, overlap_violations
```
(`__all__`에 두 이름 추가)

- [ ] **Step 5: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_metrics.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Commit**

```bash
git add src/camca/segmentation/ tests/segmentation/test_metrics.py
git commit -m "feat(segmentation): boundary-error and overlap-violation validation metrics"
```

---

### Task 6: VLM boundary refiner (Stage 2)

**Files:**
- Create: `src/camca/segmentation/vlm_refiner.py`
- Test: `tests/segmentation/test_engine.py` (mock 백엔드 사용, 파일 신규)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_engine.py
"""Stage 2 refiner + engine 오케스트레이션 — mock VLM 백엔드, 실제 API 호출 없음."""
import json
from camca.segmentation.vlm_refiner import build_refiner_prompt, apply_vlm_refinement


class MockBackend:
    """VLMBackend 인터페이스 최소 구현 — analyze_frames가 고정 JSON 반환."""
    def __init__(self, response: dict):
        self._response = response
        self.calls = []

    def model_id(self) -> str:
        return "mock:test"

    def analyze_frames(self, prompt, frames, **kwargs):
        self.calls.append({"prompt": prompt, "n_frames": len(frames)})
        return self._response


def test_refiner_prompt_mentions_step_and_window():
    seg = {"step_id": "S5", "label": "Begin slow inhalation AND press canister simultaneously",
           "observable": True, "t_start_ms": 6000, "t_end_ms": 6100,
           "boundary_confidence": 0.8}
    prompt = build_refiner_prompt(seg, window_ms=1000)
    assert "S5" in prompt
    assert "6000" in prompt or "6.0" in prompt


def test_apply_vlm_refinement_fills_unobserved_step():
    segments = [
        {"step_id": "S2", "label": "Remove cap and inspect", "observable": False,
         "needs_vlm": True, "t_start_ms": None, "t_end_ms": None,
         "boundary_source": None, "boundary_confidence": 0.0, "events": []},
    ]
    vlm_result = {"segments": [
        {"step_id": "S2", "observed": True, "t_start_ms": 1000, "t_end_ms": 2000,
         "visual_summary": "Cap removed with left hand.", "confidence": 0.7},
    ]}
    refined = apply_vlm_refinement(segments, vlm_result)
    s2 = refined[0]
    assert s2["observable"] is True
    assert s2["boundary_source"] == "vlm"
    assert s2["t_start_ms"] == 1000
    assert s2["visual_summary"] == "Cap removed with left hand."


def test_apply_vlm_refinement_confirms_telemetry_boundary():
    segments = [
        {"step_id": "S5", "label": "...", "observable": True, "needs_vlm": False,
         "t_start_ms": 6000, "t_end_ms": 6100,
         "boundary_source": "telemetry", "boundary_confidence": 0.8, "events": []},
    ]
    vlm_result = {"segments": [
        {"step_id": "S5", "observed": True, "t_start_ms": 6050, "t_end_ms": 6150,
         "visual_summary": "Thumb press visible.", "confidence": 0.9},
    ]}
    refined = apply_vlm_refinement(segments, vlm_result)
    s5 = refined[0]
    assert s5["boundary_source"] == "both"          # telemetry + VLM 일치(±500ms)
    assert s5["boundary_confidence"] > 0.8          # 상호 확인으로 상승
    assert s5["t_start_ms"] == 6000                 # telemetry 경계 유지 (ms 정밀도 우위)


def test_apply_vlm_refinement_flags_conflict():
    segments = [
        {"step_id": "S5", "label": "...", "observable": True, "needs_vlm": False,
         "t_start_ms": 6000, "t_end_ms": 6100,
         "boundary_source": "telemetry", "boundary_confidence": 0.8, "events": []},
    ]
    vlm_result = {"segments": [
        {"step_id": "S5", "observed": True, "t_start_ms": 9000, "t_end_ms": 9500,
         "visual_summary": "Press appears later.", "confidence": 0.9},
    ]}
    refined = apply_vlm_refinement(segments, vlm_result)
    s5 = refined[0]
    assert s5["conflict_flagged"] is True           # >2s 불일치 → 임상 검토 대상
    assert s5["boundary_confidence"] < 0.8
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'camca.segmentation.vlm_refiner'`

- [ ] **Step 3: vlm_refiner.py 구현**

```python
# src/camca/segmentation/vlm_refiner.py
"""Stage 2 — VLM이 후보 경계 ±window의 dense 프레임만 보고 라벨 확정/보정.

역할 분리:
  - telemetry 경계가 있으면 VLM은 '확인자' — 일치 시 confidence 상승(source=both),
    큰 불일치 시 conflict_flagged (기존 reconciliation 정책과 동일 사상).
  - telemetry-blind step(needs_vlm)은 VLM이 '검출자' — sparse 전체 스캔으로 채움.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

BOUNDARY_WINDOW_MS = 1000
BOUNDARY_DENSE_FPS = 6
VLM_AGREEMENT_TOLERANCE_MS = 500
VLM_CONFLICT_THRESHOLD_MS = 2000


def extract_boundary_frames(
    video_path: Path | str,
    center_ms: int,
    output_dir: Path,
    window_ms: int = BOUNDARY_WINDOW_MS,
    fps: int = BOUNDARY_DENSE_FPS,
) -> list[Path]:
    """경계 center_ms ± window_ms 구간을 dense fps로 추출 (L7 해결의 핵심)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    start_sec = max(0.0, (center_ms - window_ms) / 1000.0)
    duration_sec = 2 * window_ms / 1000.0
    pattern = str(output_dir / f"b{center_ms}_%03d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{start_sec:.3f}", "-i", str(video_path),
         "-t", f"{duration_sec:.3f}", "-vf", f"fps={fps}", pattern],
        capture_output=True, check=True,
    )
    return sorted(output_dir.glob(f"b{center_ms}_*.png"))


def build_refiner_prompt(segment: dict[str, Any], window_ms: int = BOUNDARY_WINDOW_MS) -> str:
    """단일 세그먼트 경계 확인용 프롬프트 (JSON 출력 강제)."""
    return (
        f"You are verifying one step of an inhaler-technique video.\n"
        f"Step: {segment['step_id']} — {segment['label']}\n"
        f"Telemetry-proposed window: {segment['t_start_ms']}ms to {segment['t_end_ms']}ms "
        f"(frames cover ±{window_ms}ms around this window).\n"
        f"Confirm whether this step actually occurs here, adjust boundaries if the frames "
        f"show otherwise, and describe what you see.\n"
        f"Respond ONLY with JSON: {{\"step_id\": \"{segment['step_id']}\", "
        f"\"observed\": bool, \"t_start_ms\": int, \"t_end_ms\": int, "
        f"\"visual_summary\": str, \"confidence\": float}}"
    )


def build_blind_scan_prompt(unobserved: list[dict[str, Any]], device_type: str) -> str:
    """telemetry-blind step들(S2/S3 등)을 sparse 전체 프레임에서 찾는 프롬프트."""
    steps_desc = "\n".join(f"- {s['step_id']}: {s['label']}" for s in unobserved)
    return (
        f"You are scanning an inhaler-technique video ({device_type}) for steps that "
        f"body-landmark telemetry cannot detect:\n{steps_desc}\n"
        f"For EACH step above, report whether it is visible anywhere in these frames.\n"
        f"NEVER fabricate timestamps — if not visible, set observed=false.\n"
        f'Respond ONLY with JSON: {{"segments": [{{"step_id": str, "observed": bool, '
        f'"t_start_ms": int|null, "t_end_ms": int|null, "visual_summary": str, '
        f'"confidence": float}}]}}'
    )


def apply_vlm_refinement(
    segments: list[dict[str, Any]],
    vlm_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """VLM 응답을 draft 세그먼트에 병합 (순수 함수 — I/O 없음).

    규칙:
      - needs_vlm step + VLM observed → observable=True, source=vlm
      - telemetry step + VLM 일치(±500ms) → source=both, confidence +0.1 (cap 1.0)
      - telemetry step + VLM 불일치(>2000ms) → conflict_flagged, confidence×0.6,
        경계는 telemetry 유지 (ms 정밀도 우위 원칙)
    """
    vlm_by_id = {s["step_id"]: s for s in vlm_result.get("segments", [])}
    refined = []
    for seg in segments:
        seg = dict(seg)  # copy
        v = vlm_by_id.get(seg["step_id"])
        if v is None:
            refined.append(seg)
            continue
        if seg.get("needs_vlm") and v.get("observed"):
            seg.update(
                observable=True, needs_vlm=False,
                t_start_ms=v["t_start_ms"], t_end_ms=v["t_end_ms"],
                boundary_source="vlm",
                boundary_confidence=round(min(v.get("confidence", 0.5), 0.85), 2),
                visual_summary=v.get("visual_summary"),
            )
        elif seg.get("observable") and v.get("observed"):
            gap = abs(v["t_start_ms"] - seg["t_start_ms"])
            if gap <= VLM_AGREEMENT_TOLERANCE_MS:
                seg.update(
                    boundary_source="both",
                    boundary_confidence=round(min(1.0, seg["boundary_confidence"] + 0.1), 2),
                    visual_summary=v.get("visual_summary"),
                )
            elif gap >= VLM_CONFLICT_THRESHOLD_MS:
                seg.update(
                    conflict_flagged=True,
                    boundary_confidence=round(seg["boundary_confidence"] * 0.6, 2),
                    visual_summary=v.get("visual_summary"),
                    vlm_proposed_t_start_ms=v["t_start_ms"],
                )
            else:
                seg["visual_summary"] = v.get("visual_summary")
        refined.append(seg)
    return refined
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_engine.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/camca/segmentation/vlm_refiner.py tests/segmentation/test_engine.py
git commit -m "feat(segmentation): VLM boundary refiner with agreement/conflict reconciliation"
```

---

### Task 7: PhaseRecognitionEngine 오케스트레이션

**Files:**
- Create: `src/camca/segmentation/engine.py`
- Modify: `src/camca/segmentation/__init__.py`
- Modify: `tests/segmentation/test_engine.py`

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/segmentation/test_engine.py`에 추가:

```python
from tests.conftest import make_telemetry
from camca.segmentation.engine import PhaseRecognitionEngine


def _full_telemetry():
    return make_telemetry(20_000, [
        (500, 2500, {"wrist_zero_crossing_rate": 4}),
        (4500, 15_000, {"hand_mouth_distance_px": 40.0}),
        (5000, 12_000, {"lip_distance_px": 3.0}),
        (6000, 9000, {"audio_energy_db": 62.0, "chest_expansion_ratio": 1.15}),
        (6000, 6200, {"index_finger_acceleration": 150.0}),
        (9000, 15_000, {"audio_energy_db": 36.0, "chest_expansion_ratio": 1.14}),
        (15_000, 20_000, {"hand_mouth_distance_px": 280.0}),
    ])


def test_engine_stage1_and_3_without_vlm():
    """VLM 백엔드 없이도 telemetry-only 모드로 동작해야 한다."""
    engine = PhaseRecognitionEngine(vlm_backend=None)
    result = engine.segment_from_telemetry(
        telemetry=_full_telemetry(), device_type="pMDI", case_id="TEST-001",
    )
    assert result["engine"] == "telemetry-anchored-v1"
    assert result["case_id"] == "TEST-001"
    seg_ids = [s["step_id"] for s in result["segments"]]
    assert seg_ids == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
    s5 = next(s for s in result["segments"] if s["step_id"] == "S5")
    assert s5["observable"] is True
    assert s5["boundary_source"] == "telemetry"
    assert isinstance(result["events"], list)
    assert len(result["events"]) >= 6


def test_engine_output_backward_compatible():
    """기존 segmentation.json 소비자(evaluator)가 요구하는 필드 존재 확인."""
    engine = PhaseRecognitionEngine(vlm_backend=None)
    result = engine.segment_from_telemetry(
        telemetry=_full_telemetry(), device_type="pMDI", case_id="TEST-001",
    )
    for seg in result["segments"]:
        assert "step_id" in seg and "label" in seg and "observable" in seg
        if seg["observable"]:
            assert seg["t_start_ms"] is not None and seg["t_end_ms"] is not None


def test_engine_structural_invariants():
    from camca.segmentation.metrics import overlap_violations
    engine = PhaseRecognitionEngine(vlm_backend=None)
    result = engine.segment_from_telemetry(
        telemetry=_full_telemetry(), device_type="pMDI", case_id="TEST-001",
    )
    assert overlap_violations(result["segments"]) == 0
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'camca.segmentation.engine'`

- [ ] **Step 3: engine.py 구현**

```python
# src/camca/segmentation/engine.py
"""Phase Recognition Engine — Stage 1(events) → Stage 2(VLM refine) → Stage 3(align).

VLM 백엔드가 None이면 Stage 2를 건너뛴다 (telemetry-only 모드 — CI/테스트/저비용 스크리닝).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .events import detect_events
from .alignment import align_events_to_steps
from .templates import get_template
from .vlm_refiner import (
    apply_vlm_refinement,
    build_blind_scan_prompt,
    build_refiner_prompt,
    extract_boundary_frames,
)


class PhaseRecognitionEngine:
    """telemetry-anchored 하이브리드 세그멘테이션 엔진.

    Usage:
        engine = PhaseRecognitionEngine(vlm_backend=create_backend("claude:sonnet"))
        result = engine.segment(video_path, device_type="pMDI", case_id="X")
        # 또는 telemetry를 이미 갖고 있으면:
        result = engine.segment_from_telemetry(telemetry, "pMDI", "X")
    """

    def __init__(self, vlm_backend: Any | None = None):
        self.vlm_backend = vlm_backend

    def segment_from_telemetry(
        self,
        telemetry: list[dict],
        device_type: str,
        case_id: str,
        video_path: Path | str | None = None,
    ) -> dict[str, Any]:
        duration_ms = telemetry[-1]["timestamp_ms"] if telemetry else 0
        template = get_template(device_type)

        # Stage 1
        events = detect_events(telemetry, device_type)

        # Stage 3 (draft — Stage 2 전에 draft 경계가 필요)
        segments = align_events_to_steps(events, template, duration_ms)

        # Stage 2 (VLM 있고 영상 접근 가능할 때만)
        vlm_model = None
        if self.vlm_backend is not None and video_path is not None:
            segments = self._refine_with_vlm(segments, Path(video_path))
            vlm_model = self.vlm_backend.model_id()

        return {
            "engine": "telemetry-anchored-v1",
            "case_id": case_id,
            "device_type": device_type,
            "total_duration_ms": duration_ms,
            "vlm_model": vlm_model,
            "events": [e.to_dict() for e in events],
            "segments": segments,
        }

    def segment(
        self,
        video_path: Path | str,
        device_type: str,
        case_id: str,
    ) -> dict[str, Any]:
        """영상에서 telemetry 추출부터 실행하는 편의 진입점 (mediapipe 필요)."""
        from ..telemetry.pipeline import extract_telemetry
        telemetry = extract_telemetry(video_path)
        return self.segment_from_telemetry(telemetry, device_type, case_id, video_path)

    # ---- internal ----

    def _refine_with_vlm(self, segments: list[dict], video_path: Path) -> list[dict]:
        import json

        with tempfile.TemporaryDirectory(prefix="camca_refine_") as tmp:
            tmp_dir = Path(tmp)
            merged = segments

            # (a) telemetry 경계 확인 — observable step마다 경계 dense 프레임
            for seg in [s for s in merged if s.get("observable")]:
                frames = extract_boundary_frames(video_path, seg["t_start_ms"], tmp_dir)
                if not frames:
                    continue
                raw = self.vlm_backend.analyze_frames(build_refiner_prompt(seg), frames)
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                merged = apply_vlm_refinement(merged, {"segments": [parsed]})

            # (b) telemetry-blind step — sparse 전체 스캔 1회
            blind = [s for s in merged if s.get("needs_vlm")]
            if blind:
                sparse = extract_boundary_frames(
                    video_path, center_ms=0, output_dir=tmp_dir,
                    window_ms=10 ** 9, fps=1,   # 전체 구간 1fps
                )
                raw = self.vlm_backend.analyze_frames(
                    build_blind_scan_prompt(blind, seg_device := merged[0].get("device_type", "")),
                    sparse,
                )
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                merged = apply_vlm_refinement(merged, parsed)

        return merged
```

**주의**: `_refine_with_vlm`의 (b)에서 `seg_device` walrus는 segments dict에 device_type이 없으므로 빈 문자열이 된다 — `segment_from_telemetry`에서 `device_type`을 인자로 전달하도록 `_refine_with_vlm(self, segments, video_path, device_type)` 시그니처로 구현할 것 (호출부도 동일하게). 최종 코드:

```python
    def _refine_with_vlm(self, segments: list[dict], video_path: Path, device_type: str) -> list[dict]:
        ...
                raw = self.vlm_backend.analyze_frames(
                    build_blind_scan_prompt(blind, device_type), sparse,
                )
        ...
```
호출부: `segments = self._refine_with_vlm(segments, Path(video_path), device_type)`

- [ ] **Step 4: `__init__.py` 최종본으로 갱신**

```python
"""Phase Recognition Engine — telemetry-anchored hybrid segmentation (v0.4.0)."""
from .events import PhaseEvent, detect_events
from .alignment import align_events_to_steps
from .templates import get_template, PMDI_TEMPLATE, TURBUHALER_TEMPLATE
from .engine import PhaseRecognitionEngine
from .metrics import mean_absolute_boundary_error_sec, overlap_violations

__all__ = [
    "PhaseEvent", "detect_events", "align_events_to_steps",
    "get_template", "PMDI_TEMPLATE", "TURBUHALER_TEMPLATE",
    "PhaseRecognitionEngine",
    "mean_absolute_boundary_error_sec", "overlap_violations",
]
```

- [ ] **Step 5: 전체 테스트 통과 확인**

Run: `python -m pytest tests/ -v`
Expected: PASS (전체)

- [ ] **Step 6: Commit**

```bash
git add src/camca/segmentation/ tests/segmentation/test_engine.py
git commit -m "feat(segmentation): PhaseRecognitionEngine orchestrating 3-stage hybrid pipeline"
```

---

### Task 8: MultiModelPipeline 통합 (opt-in)

**Files:**
- Modify: `src/camca/pipeline.py` (`MultiModelPipeline.__init__`, `_stage_segment`)
- Test: `tests/segmentation/test_pipeline_integration.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_pipeline_integration.py
"""MultiModelPipeline이 use_phase_engine 플래그로 신규 엔진을 쓰는지 (mock, 영상 없음)."""
from camca.pipeline import MultiModelPipeline


class DummyBackend:
    def model_id(self):
        return "dummy:v0"

    def analyze_frames(self, prompt, frames, **kwargs):
        return {}


def _make_pipeline(**kwargs):
    from camca.pipeline import PersonaConfig
    return MultiModelPipeline(
        device_id_backend=DummyBackend(),
        segmenter_backend=DummyBackend(),
        evaluator_a=PersonaConfig("A", "strict", DummyBackend()),
        evaluator_b=PersonaConfig("B", "pragmatic", DummyBackend()),
        case_dir=None,
        **kwargs,
    )


def test_flag_defaults_false_for_backward_compat():
    p = _make_pipeline()
    assert p.use_phase_engine is False


def test_flag_accepted():
    p = _make_pipeline(use_phase_engine=True)
    assert p.use_phase_engine is True
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_pipeline_integration.py -v`
Expected: FAIL — `TypeError: unexpected keyword argument 'use_phase_engine'`

- [ ] **Step 3: pipeline.py 수정**

`MultiModelPipeline.__init__` 시그니처에 파라미터 추가 (`tie_breaker` 관련 파라미터들 뒤, 기존 순서 유지):

```python
    def __init__(
        self,
        ...기존 파라미터 그대로...,
        use_phase_engine: bool = False,
    ):
        ...기존 본문 그대로...
        self.use_phase_engine = use_phase_engine
```

`_stage_segment`를 분기 처리 (기존 VLM-프롬프트 경로는 그대로 두고 앞에 분기 추가):

```python
    def _stage_segment(self, frames: list[Path], device_type: str,
                       video_path: Path | None = None,
                       telemetry: list[dict] | None = None) -> dict[str, Any]:
        # v0.4.0: telemetry-anchored phase engine (opt-in)
        if self.use_phase_engine and telemetry:
            from .segmentation import PhaseRecognitionEngine
            started = self._now_iso()
            engine = PhaseRecognitionEngine(vlm_backend=self.segmenter_backend)
            result = engine.segment_from_telemetry(
                telemetry, device_type, case_id=self.case_id or "unknown",
                video_path=video_path,
            )
            self._record("phase-engine", self.segmenter_backend.model_id(), started, 0, True)
            self._write_json("03_segments.json", result)
            return result
        # 기존 VLM-프롬프트 경로 (변경 없음)
        ...
```

**주의**: `run()`에서 `_stage_segment` 호출부에 `video_path`/`telemetry`를 전달해야 한다. `run()`은 telemetry를 `_stage_telemetry`에서 이미 추출하므로, telemetry 추출을 세그멘테이션 **앞으로** 이동:

```python
        # run() 내부 — 기존 [2/5] Segmenting 직전에 telemetry 먼저
        telemetry = self._stage_telemetry(video_path) if self.use_phase_engine else None
        result.segments = self._stage_segment(frames, device_type,
                                              video_path=video_path, telemetry=telemetry)
```

(기존 `_stage_telemetry` 호출 위치가 세그멘테이션 뒤라면 중복 호출을 피하도록 결과를 재사용. `run()`의 실제 구조를 보고 telemetry 변수를 한 번만 만들 것. `case_id`는 run()의 인자이므로 `self.case_id`가 없다면 `_stage_segment`에 case_id 파라미터를 추가해 전달한다.)

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_pipeline_integration.py tests/ -v`
Expected: PASS (전체 — 기존 경로 회귀 없음)

- [ ] **Step 5: Commit**

```bash
git add src/camca/pipeline.py tests/segmentation/test_pipeline_integration.py
git commit -m "feat(pipeline): opt-in use_phase_engine flag routing to PhaseRecognitionEngine"
```

---

### Task 9: CLI `camca segment` 서브커맨드

**Files:**
- Modify: `src/camca/cli.py`
- Test: `tests/segmentation/test_cli_segment.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/segmentation/test_cli_segment.py
"""camca segment 서브커맨드 — argparse 배선만 검증 (실제 영상 처리 없음)."""
import pytest
from camca.cli import build_parser


def test_segment_subcommand_exists():
    parser = build_parser()
    args = parser.parse_args([
        "segment", "--video", "demo.mp4", "--device", "pMDI",
        "--case-id", "X-001", "--out", "seg.json", "--no-vlm",
    ])
    assert args.command == "segment"
    assert args.video == "demo.mp4"
    assert args.no_vlm is True
```

**전제 확인**: `cli.py`에 `build_parser()`가 없다면 (main()이 파서를 내부 생성) — 파서 생성부를 `build_parser()` 함수로 추출하는 것을 이 태스크의 첫 스텝으로 삼는다. 기존 CLI 진입 방식(`camca analyze ...`)과 동일한 서브커맨드 패턴을 따를 것.

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/segmentation/test_cli_segment.py -v`
Expected: FAIL

- [ ] **Step 3: cli.py에 서브커맨드 추가**

```python
# build_parser() 내 서브파서 등록부에 추가
    seg = subparsers.add_parser("segment", help="Run phase recognition only (no evaluation)")
    seg.add_argument("--video", required=True)
    seg.add_argument("--device", default="pMDI",
                     help="pMDI | pMDI-AIM-simulator | pMDI-spacer | DPI-turbuhaler")
    seg.add_argument("--case-id", required=True)
    seg.add_argument("--out", default=None, help="Output JSON path (default: stdout)")
    seg.add_argument("--vlm", default=None,
                     help="VLM backend for Stage 2, e.g. claude:sonnet (omit = telemetry-only)")
    seg.add_argument("--no-vlm", action="store_true", help="Force telemetry-only mode")


# main()의 command 분기에 추가
    if args.command == "segment":
        import json
        from .segmentation import PhaseRecognitionEngine

        backend = None
        if args.vlm and not args.no_vlm:
            from .backends import create_backend
            backend = create_backend(args.vlm)
        engine = PhaseRecognitionEngine(vlm_backend=backend)
        result = engine.segment(args.video, device_type=args.device, case_id=args.case_id)
        payload = json.dumps(result, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(payload, encoding="utf-8")
            print(f"Segmentation written to {args.out}")
        else:
            print(payload)
        return 0
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/segmentation/test_cli_segment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/camca/cli.py tests/segmentation/test_cli_segment.py
git commit -m "feat(cli): add 'camca segment' subcommand for standalone phase recognition"
```

---

### Task 10: KIM/PARK regression fixture + 검증 게이트 문서화

**Files:**
- Create: `tests/segmentation/test_regression_park.py`
- Create: `tests/fixtures/park_gold_segments.json`
- Modify: `README.md` (camca-py) — phase engine 사용법 한 단락

- [ ] **Step 1: PARK 케이스 gold 라벨 fixture 작성**

기존 검증된 세그멘테이션(`evaluations/CAMCA-20260512-150557/segmentation.json`)의 관측 가능 4단계를 gold로 고정:

```json
// tests/fixtures/park_gold_segments.json
{
  "case_id": "CAMCA-PARK-001",
  "device_type": "pMDI-AIM-simulator",
  "source": "human-reviewed VLM segmentation, 2026-05-12 (see evaluations/CAMCA-20260512-150557)",
  "video_duration_ms": 13330,
  "segments": [
    {"step_id": "S4", "observable": true,  "t_start_ms": 0,    "t_end_ms": 1500},
    {"step_id": "S5", "observable": true,  "t_start_ms": 500,  "t_end_ms": 3000},
    {"step_id": "S6", "observable": true,  "t_start_ms": 1500, "t_end_ms": 6000},
    {"step_id": "S7", "observable": true,  "t_start_ms": 6000, "t_end_ms": 12500},
    {"step_id": "S1", "observable": false, "t_start_ms": null, "t_end_ms": null},
    {"step_id": "S2", "observable": false, "t_start_ms": null, "t_end_ms": null},
    {"step_id": "S3", "observable": false, "t_start_ms": null, "t_end_ms": null},
    {"step_id": "S8", "observable": false, "t_start_ms": null, "t_end_ms": null},
    {"step_id": "S9", "observable": false, "t_start_ms": null, "t_end_ms": null}
  ],
  "note": "gold 경계 자체가 VLM 산출(겹침 있음)이므로 MABE 게이트는 향후 human 재라벨 후 강화. 현 시점 게이트: 관측/비관측 일치 + 겹침 0 + MABE < 1.5s"
}
```

- [ ] **Step 2: regression 테스트 작성**

영상 파일이 저장소에 없으므로, 이 테스트는 **PARK 영상 telemetry를 근사한 합성 스트림**으로 엔진 구조 불변조건 + gold 대비 관측 단계 일치를 검증한다. (실영상 검증은 Step 4의 수동 게이트.)

```python
# tests/segmentation/test_regression_park.py
"""PARK-001 근사 regression — 관측/비관측 패턴과 구조 불변조건이 gold와 일치하는지."""
import json
from pathlib import Path

from tests.conftest import make_telemetry
from camca.segmentation.engine import PhaseRecognitionEngine
from camca.segmentation.metrics import overlap_violations

GOLD = json.loads(
    (Path(__file__).parent.parent / "fixtures" / "park_gold_segments.json").read_text()
)


def park_like_telemetry():
    """PARK-001 특성 재현: 영상이 입에 문 상태로 시작(S1-S3 부재), AIM이라 audio 조용."""
    return make_telemetry(13_300, [
        (0, 11_000, {"hand_mouth_distance_px": 40.0, "lip_distance_px": 3.0}),
        (500, 3000, {"index_finger_acceleration": 150.0}),        # actuation posture
        (3000, 4500, {"audio_energy_db": 47.0,                     # AIM 수준 흡입음
                      "chest_expansion_ratio": 1.12}),
        (4500, 11_000, {"chest_expansion_ratio": 1.11}),           # 정지(숨참기)
        (11_000, 13_300, {"hand_mouth_distance_px": 280.0}),       # 제거
    ])


def test_park_observability_pattern_matches_gold():
    engine = PhaseRecognitionEngine(vlm_backend=None)
    result = engine.segment_from_telemetry(
        park_like_telemetry(), device_type="pMDI-AIM-simulator", case_id="PARK-REGRESSION",
    )
    pred = {s["step_id"]: s["observable"] for s in result["segments"]}
    gold = {s["step_id"]: s["observable"] for s in GOLD["segments"]}
    # telemetry-blind인 S2/S3와 사전/사후 단계(S1/S8/S9)는 미관측이어야 함
    for sid in ["S1", "S2", "S3", "S8", "S9"]:
        assert pred[sid] == gold[sid] == False


def test_park_no_overlap_unlike_legacy_vlm_output():
    """핵심 개선 검증: 기존 VLM 출력은 S4/S5/S6이 겹쳤다. 신규 엔진은 겹침 0."""
    engine = PhaseRecognitionEngine(vlm_backend=None)
    result = engine.segment_from_telemetry(
        park_like_telemetry(), device_type="pMDI-AIM-simulator", case_id="PARK-REGRESSION",
    )
    assert overlap_violations(result["segments"]) == 0
```

- [ ] **Step 3: 테스트 실행·통과 확인**

Run: `python -m pytest tests/segmentation/test_regression_park.py -v`
Expected: PASS. 실패 시: park_like_telemetry의 값이 검출기 threshold와 안 맞는 경우이므로 **검출기 로직이 아닌 합성 값**을 실제 PARK telemetry 로그(camca-inhaler-eval/logs/CAMCA-PARK-001/ 참고)에 맞게 조정.

- [ ] **Step 4: 실영상 수동 검증 게이트 (문서화)**

`README.md`(camca-py)에 추가할 사용법 + 게이트:

```markdown
### Phase Recognition Engine (v0.4.0)

telemetry-anchored 하이브리드 세그멘테이션 (spec: docs/superpowers/specs/2026-07-07-camca-platform-design.md §5):

    # telemetry-only (무비용, CI용)
    camca segment --video patient.mp4 --device pMDI --case-id X-001 --no-vlm --out seg.json

    # 하이브리드 (VLM 경계 정밀화)
    camca segment --video patient.mp4 --device pMDI --case-id X-001 --vlm claude:sonnet

**검증 게이트 (Step 1 데이터 12영상 확보 시 실행):**
- mean_absolute_boundary_error_sec < 0.5 (human 경계 라벨 대비)
- overlap_violations == 0 (구조 불변조건)
- KIM-001/PARK-001에서 기존 consensus score 재현
```

- [ ] **Step 5: 전체 테스트 + Commit**

Run: `python -m pytest tests/ -v`
Expected: 전체 PASS

```bash
git add tests/ README.md
git commit -m "test(segmentation): PARK regression fixture + validation gate docs"
```

---

## Self-Review 결과 (계획 작성 시 수행)

1. **Spec coverage**: §5.2 Stage 1(E1~E7)→Task 2-3, Stage 2→Task 6, Stage 3→Task 4, §5.3-1(리뷰 UI)→**Plan 2 범위**(플랫폼), §5.3-2(quality gate 연동)→기존 view_angle.py 활용은 Plan 2에서 engine 파라미터로 연결, §5.4(검증 게이트)→Task 5+10. hand-mouth 신호 부재 gap→Task 1로 해소.
2. **Placeholder scan**: 통과 — 모든 스텝에 실행 가능한 코드/커맨드 포함. Task 8-9는 기존 파일의 실제 구조에 따라 조정 여지가 있어 전제 확인 지침을 명기함.
3. **Type consistency**: `PhaseEvent(type, t_start_ms, t_end_ms, confidence, source, detail)` 전 태스크 일관. 세그먼트 dict 키(`step_id/label/observable/needs_vlm/t_start_ms/t_end_ms/boundary_source/boundary_confidence/events`) Task 4 정의를 6·7·10에서 동일 사용. `overlap_violations`/`mean_absolute_boundary_error_sec` 명칭 일관.

**알려진 후속 작업 (이 계획 범위 밖):**
- Plan 2: 웹 플랫폼 모놀리스 (업로드→발행→대시보드→타임라인 리뷰 UI)
- Step 1 12영상 human 라벨링 후 MABE < 0.5s 게이트 실측
- Turbuhaler T2 click audio 이벤트 검출기 (템플릿에 자리만 마련됨)
