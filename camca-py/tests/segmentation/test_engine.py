"""Stage 2 refiner + engine 오케스트레이션 — mock VLM 백엔드, 실제 API 호출 없음."""
import json
from camca.segmentation.vlm_refiner import build_refiner_prompt, apply_vlm_refinement

from tests.conftest import make_telemetry
from camca.segmentation.engine import PhaseRecognitionEngine


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
