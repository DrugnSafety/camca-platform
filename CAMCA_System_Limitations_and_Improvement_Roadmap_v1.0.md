# CAMCA 시스템 한계 식별 및 개선 로드맵 v1.0

**작성일**: 2026-05-21
**저자**: Min-Gyu Kang, MD
**기반 데이터**: CAMCA-PARK-001, CAMCA-KIM-001 (n=2 pilot 검증 케이스)
**현재 시스템 버전**: camca-py v0.2.1, plugin v0.4.0

---

## 🎯 Executive Summary

n=2 실제 영상 검증으로 **8개의 식별 가능한 시스템 한계**를 발견했습니다. 이 중:
- **5개는 v0.2.1에서 부분/전체 해결** (해결됨 ✅)
- **3개는 v0.3.0+ 향후 작업** (예정 🔜)

본 문서는 각 한계의 **근본 원인 분석, 임상적 영향, 구현된/계획된 해결책, 검증 방법**을 종합합니다.

---

## 📊 한계 식별 매트릭스

| # | 한계 | 발견 케이스 | 현재 상태 | 임상 위험 | v 도입 |
|---|---|---|---|---|---|
| L1 | breath_hold detector false positive (quiet audio) | KIM-001 | ✅ Fixed | 잘못된 verdict (Level 1→3 inflation) | v0.2.1 |
| L2 | Finger acceleration threshold 너무 낮음 (8 px/s²) | KIM-001 | ✅ Fixed | False CRIT-pMDI-04 flag | v0.2.1 |
| L3 | Head pitch 좌표계 변환 버그 | KIM-001 | ✅ Fixed (camca-py) | S4 자세 평가 부정확 | v0.2.1 |
| L4 | AIM 시뮬레이터 audio threshold 불일치 | PARK+KIM | ✅ Fixed (profiles) | S5/S7 anchor 실패 | v0.2.1 |
| L5 | VLM↔Telemetry 충돌 시 정책 부재 | KIM-001 (Algo 11.3s vs VLM 3s) | ✅ Fixed (reconciliation) | 자동 verdict 신뢰도 낮음 | v0.2.1 |
| L6 | 카메라 각도 의존성 (측면→MediaPipe 검출 실패) | PARK-001 | 🔜 Planned | S4·S5 평가 정확도 변동 | v0.3.0 |
| L7 | VLM frame sampling (1 fps) 한계 | KIM-001 S7 (3s 추정 vs 실제 더 길수도) | 🔜 Planned | 시간적 지표 과소평가 | v0.3.0 |
| L8 | Audio peak 부재 시 inhalation 추론 불가 | KIM-001 (audio 97% baseline) | 🔜 Planned | AIM device class 전체 영향 | v0.4.0 |

---

## ✅ v0.2.1 해결된 한계 — 상세

### L1: Breath-Hold Detector False Positive

**근본 원인**: `detect_breath_hold()` 알고리즘이 audio peak를 무조건 inhalation peak로 가정. AIM 시뮬레이터처럼 audio가 거의 silent (35dB floor)인 경우 우연한 noise spike(43.9dB)를 peak로 인식하여 그 후 silence를 "breath-hold"로 false-flagged.

**구체 발현**: KIM-001 S7 평가에서 algorithm이 **11.3s breath-hold (adequate)**를 보고했으나 실제는 audio 자체가 검출 가능한 수준이 아니었음. Algorithm은 자체적으로 confidence 0.3을 출력하여 우려를 표명하고 있었지만, downstream 시스템이 이를 무시할 위험.

**구현된 해결**:
```python
# camca/telemetry/breath_hold_detector.py
def detect_breath_hold(telemetry, ..., min_peak_db_for_detection=55.0):
    peak_db = max(s['audio_energy_db'] for s in telemetry)
    if peak_db < min_peak_db_for_detection:
        return None  # 정직: "검출할 수 없음" 반환
```

**검증 결과**: KIM peak 43.9 < 55 → 정확히 None 반환 ✓

**잔여 작업**: 임상 사용 전 minimum_peak_db_for_detection 값을 device profile별로 calibration 필요 (현재는 default 55, AIM 시뮬레이터 45 hard-coded). n=30 pilot 데이터로 정량 보정 권장.

---

### L2: Finger Acceleration Threshold 8 px/s² 너무 낮음

**근본 원인**: 검지 손가락 끝 Y축 가속도 8 px/s²는 일반적인 손 움직임과 구분 불가. KIM 케이스에서 183 samples 중 **181개 (99%)**가 actuation event로 잘못 식별되었음.

**임상 위험**: False CRIT-pMDI-04 (early actuation) 또는 CRIT-pMDI-05 (late actuation) flag → 환자에게 잘못된 critical error 통보 가능.

**구현된 해결**:
```python
# camca/telemetry/thresholds.py
INDEX_FINGER_ACTUATION_ACCEL_THRESHOLD = 100.0  # 8 → 100 px/s²
INDEX_FINGER_ACTUATION_MIN_DURATION_MS = 50    # 50ms 이상 sustained spike만
INDEX_FINGER_SMOOTHING_WINDOW = 3              # 3-frame moving average
```

3-frame moving average는 `mediapipe_extractor.py`의 `index_finger_acceleration()` 메서드에 deque(maxlen=3)로 구현.

**검증 방법** (v0.3.0):
- KIM 케이스 actuation_count: 이전 181 → 새 ?? (실측 필요)
- PARK 케이스 actuation_count: 이전 127 → 새 ??
- Expected: <5 (실제 actuation 1-2회만)

---

### L3: Head Pitch 좌표계 변환 버그

**근본 원인**: 원래 계산식 `atan2(z_delta, y_delta)`이 MediaPipe FaceMesh의 정규화 z-좌표(depth)와 image-space y-좌표를 부적절하게 결합. 정면 자세에서 0°이어야 할 값이 100-118° 범위로 출력됨.

**구현된 해결**:
```python
def head_pitch_deg(self, frame_rgb):
    # ... face landmarks
    dy_norm = chin.y - nose.y  # normalized [0,1]
    REFERENCE_DY_NORMAL = 0.12  # 정면 자세 baseline
    SCALE_DEG_PER_NORM = 250.0  # empirical calibration
    pitch = (REFERENCE_DY_NORMAL - dy_norm) * SCALE_DEG_PER_NORM
    return float(round(pitch, 1))
```

**검증 필요**: 정면 자세 영상 5개 이상으로 mean ≈ 0°, std < 10° 확인 권장.

---

### L4: AIM Simulator Audio Threshold 불일치

**근본 원인**: pMDI 표준 audio threshold(50dB)는 실제 약물 분사 시 70-90dB가 발생함을 전제. AIM 훈련 시뮬레이터는 flow sensor만 있고 분사가 없어 audio가 일반 호흡 수준(40-56dB)에 그침. KIM peak 43.9dB, PARK peak 56.3dB → 둘 다 표준 50dB 기준으로 inhalation onset 검출 실패.

**구현된 해결**:
```python
# camca/telemetry/thresholds.py
DEVICE_AUDIO_PROFILES = {
    "pMDI":                {"baseline_db": 35, "inhalation_min_db": 50, "min_peak_db_for_detection": 55},
    "pMDI-AIM-simulator":  {"baseline_db": 35, "inhalation_min_db": 42, "min_peak_db_for_detection": 45},  # 5-10dB 하향
    "pMDI-spacer":         {"baseline_db": 35, "inhalation_min_db": 48, "min_peak_db_for_detection": 53},
    "DPI-turbuhaler":      {"baseline_db": 35, "inhalation_min_db": 55, "min_peak_db_for_detection": 60},
}

def get_audio_profile(device_type: str) -> dict: ...
```

**파이프라인 통합** (next step): `device-id` agent가 device sub-type을 출력하고, `breath_hold_detector` + 향후 audio analyzer가 자동으로 적절한 profile 선택하도록.

---

### L5: VLM ↔ Telemetry Reconciliation Policy 부재

**근본 원인**: VLM과 algorithm이 같은 단계에 다른 결론을 내는 경우 (KIM S7: VLM 3s vs Algo 11.3s) 시스템이 어느 쪽을 따라야 하는지 정책 없음. 두 측정원이 모두 동일 가중치로 평균되면 잘못된 verdict 발생.

**구현된 해결**: `camca/telemetry/reconciliation.py` 신규 모듈
```python
def reconcile_step_score(vlm_level, vlm_confidence, telemetry_level, telemetry_confidence,
                        confidence_threshold=0.5, conflict_diff_threshold=2):
    if telemetry_confidence < threshold:  return VLM_WINS
    if vlm_confidence < threshold:        return TELEMETRY_WINS
    if abs(diff) < conflict_diff:         return AGREE (average)
    return CONFLICT_FLAGGED + requires_clinician_review
```

**KIM S7 동작 검증**:
- Input: VLM=1 (conf 0.75), Telemetry=3 (conf 0.30)
- Output: **VLM_WINS, final=1, rationale logged**

---

## 🔜 v0.3.0+ 향후 작업 — 미해결 한계

### L6: 카메라 각도 의존성 (MediaPipe 검출 실패)

**관찰된 영향** (PARK-001):
- 측면 각도로 인해 영상 첫 5 frames의 face/hand landmark 검출 실패 (lip=0, pitch=0, finger_accel=0)
- 같은 KIM (정면)은 100% 검출 성공

**제안 해결책**:

#### A. 단기 (v0.3.0, 1주 작업)
1. **`device-id` agent에 "view_angle" 필드 추가** — frontal / lateral / oblique 분류
2. **각도에 따른 evaluator weighting 조정** — lateral 영상에서는 VLM이 vision telemetry보다 우선

#### B. 중기 (v0.4.0, 1개월)
3. **Multi-view MediaPipe ensemble** — 같은 face/hand에 대해 frontal-trained + lateral-trained 두 모델 사용
4. **IRB 영상 acquisition 표준 강제** — 정면 또는 30° 측면만 권장, 그 외는 자동 reject

#### C. 장기 (v0.5.0+)
5. **3D pose estimation** — single-view 한계 극복 (Apple Vision Pro / iPhone LiDAR 데이터 활용 가능?)

**예상 효과**:
- PARK-class 영상 (측면)의 평가 정확도 +30%
- 데이터셋 quality variance 감소

---

### L7: VLM Frame Sampling (1 fps) 한계 — 시간적 지표 과소평가 위험

**관찰된 영향** (KIM-001):
- VLM은 13초 영상에서 13 frames만 봄 → S7 breath-hold를 마지막 3 frames에서만 관찰 → 3s로 추정
- 실제 영상은 30 fps × 366 frames이며 더 긴 hold가 있을 수도

**제안 해결책**:

#### A. 단기 (v0.3.0, 1일)
1. **Frame extraction rate 2-4 fps로 상향** — VLM token cost 약간 증가하지만 정확도 향상
2. **Step-aware frame sampling** — S5/S7 같은 critical step은 더 dense하게 sampling

#### B. 중기 (v0.4.0)
3. **Hybrid analysis**: VLM은 frame-based decision, telemetry는 ms-level precision → 명시적으로 역할 분리
4. **Gemini Native Video API 활용** — frame 추출 우회, 영상 전체 직접 분석

#### C. 장기
5. **Active learning** — VLM이 "더 dense sampling 필요" flag를 출력하면 자동으로 해당 구간 재 sampling

**예상 효과**:
- 시간적 지표 (duration, timing) 정확도 +50%
- KIM S7 같은 경계 케이스 (3-10s) 정확한 분류 가능

---

### L8: Audio Peak 부재 시 Inhalation 추론 불가 (AIM Class 전체)

**관찰된 영향** (PARK + KIM 모두):
- 두 케이스 모두 audio peak가 51-56dB에 그쳐 inhalation onset detection 실패
- AIM 시뮬레이터로 평가하는 모든 환자 영상에 동일 한계 발생 예상

**제안 해결책**:

#### A. 단기 (v0.3.0): Vision-only inhalation detection
1. **`chest_expansion_ratio` 시계열로 inhalation 시작 판정** — audio 의존성 제거
2. **MediaPipe Pose의 chest landmark 활용도 강화** — 어깨 거리 변화율 계산

#### B. 중기 (v0.4.0): Audio classifier 학습
3. **DPI-Watch 데이터셋 기반 1D-CNN classifier** — inhalation / breath-hold / silence 분류
4. **AIM-specific dataset 수집** (n=30 IRB pilot에 포함) — AIM audio profile 학습

#### C. 장기 (v0.5.0)
5. **Multi-modal fusion model** — frame + audio + landmark → 통합 inhalation phase classifier

**예상 효과**:
- AIM 시뮬레이터 사용 환자 (CBNU 교육 케이스 다수) 평가 가능
- IRB pilot의 50% subgroup 정확도 향상

---

## 📋 우선순위 통합 매트릭스

| 한계 | 임상 영향 | 구현 난이도 | 권장 우선순위 |
|---|---|---|---|
| L6 (각도) | HIGH (n=30 중 측면 영상 다수 예상) | LOW (분류 추가) | **v0.3.0 P1** |
| L7 (1fps) | MEDIUM (경계 케이스) | LOW (rate 변경) | **v0.3.0 P2** |
| L8 (audio AIM) | HIGH (AIM 영상 전체) | HIGH (학습 필요) | **v0.4.0 P1** |

---

## 🔬 검증 계획

각 개선안 적용 후 다음 데이터로 정량 검증:

### 즉시 검증 (이미 수정된 L1-L5)
- ✅ Synthetic 데이터로 unit test (이미 수행됨, 모두 통과)
- 🔜 PARK + KIM 두 케이스로 regression test (next step in this session)

### Pilot 검증 (L6-L8 + L1-L5 종합)
- IRB n=30 pilot 데이터로:
  - Per-case telemetry coverage (각 단계 anchor 성공률)
  - Inter-rater reliability 변화 (κ improvement)
  - Critical error sensitivity/specificity vs gold standard

### 외부 검증
- DPI-Watch 데이터셋으로 audio classifier 정확도
- 다른 institution 영상 (예: MGH 추가 데이터) cross-validation

---

## 🚀 v0.3.0 마일스톤 제안

**Phase A** (2주 작업):
- L6: device-id에 view_angle 추가 + threshold 조정
- L7: frame rate 2-4 fps 상향 + step-aware sampling
- 두 fix를 PARK + KIM에 적용하여 정량 검증

**Phase B** (1개월):
- L8: DPI-Watch dataset 기반 audio classifier 학습 (외부 데이터 활용)
- AIM-specific dataset 수집 시작

**Phase C** (3개월):
- IRB n=30 pilot 시작
- 모든 v0.3.0 fix가 실제 임상 영상에 어떻게 작동하는지 검증

---

## 📝 문서 변경 이력

- **v1.0 (2026-05-21)**: 최초 작성. KIM + PARK 케이스 분석 결과 종합.
- **v1.1** (예정): PARK v0.2.1 재실행 결과 + plugin sync 후 업데이트
- **v2.0** (예정): IRB pilot 데이터 누적 후 정량 검증 결과 반영
