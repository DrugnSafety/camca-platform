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
