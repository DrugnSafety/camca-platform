"""spec §5.3-2 — quality gate가 낮은 telemetry 검출률을 보고하면 Stage 2 VLM 가중 상향.

vlm_weight_up=True 의미: telemetry가 열화된 영상(측면 등)에서는 VLM이 경계
disagreement의 우선권을 가진다. 단 conflict 플래그(NEEDS_ATTENTION 경로)와
no-overlap 불변조건은 유지된다.
"""
import pytest

from camca.segmentation.vlm_refiner import apply_vlm_refinement


def _seg(step_id, start, end, conf=0.8, **kw):
    return {"step_id": step_id, "label": step_id, "observable": True,
            "needs_vlm": False, "t_start_ms": start, "t_end_ms": end,
            "boundary_source": "telemetry", "boundary_confidence": conf, **kw}


def _vlm(step_id, start, end, conf=0.9):
    return {"segments": [{"step_id": step_id, "observed": True,
                          "t_start_ms": start, "t_end_ms": end,
                          "visual_summary": "vlm view", "confidence": conf}]}


# ---- 기본 모드: 기존 동작 불변 (regression guard) ----

def test_default_conflict_keeps_telemetry_boundary():
    out = apply_vlm_refinement([_seg("S4", 5000, 8000)], _vlm("S4", 9500, 12000))
    seg = out[0]
    assert seg["t_start_ms"] == 5000                 # ms 정밀도 우위 원칙
    assert seg["conflict_flagged"] is True
    assert seg["vlm_proposed_t_start_ms"] == 9500


def test_default_mid_gap_keeps_boundary_without_flag():
    out = apply_vlm_refinement([_seg("S4", 5000, 8000)], _vlm("S4", 6000, 9000))
    seg = out[0]
    assert seg["t_start_ms"] == 5000
    assert "conflict_flagged" not in seg


# ---- vlm_weight_up 모드 ----

def test_weight_up_conflict_adopts_vlm_boundary_but_keeps_flag():
    out = apply_vlm_refinement([_seg("S4", 5000, 8000)], _vlm("S4", 9500, 12000),
                               vlm_weight_up=True)
    seg = out[0]
    assert seg["t_start_ms"] == 9500                 # VLM 경계 채택
    assert seg["t_end_ms"] == 12000
    assert seg["boundary_source"] == "vlm"
    assert seg["telemetry_proposed_t_start_ms"] == 5000   # 연구용 추적 보존
    assert seg["conflict_flagged"] is True           # 배지 경로는 그대로
    assert seg["boundary_confidence"] <= 0.85        # VLM 검출자 cap과 동일


def test_weight_up_mid_gap_adopts_vlm_without_flag():
    out = apply_vlm_refinement([_seg("S4", 5000, 8000)], _vlm("S4", 6000, 9000),
                               vlm_weight_up=True)
    seg = out[0]
    assert seg["t_start_ms"] == 6000
    assert seg["boundary_source"] == "vlm"
    assert "conflict_flagged" not in seg


def test_weight_up_agreement_unchanged_from_default():
    out = apply_vlm_refinement([_seg("S4", 5000, 8000, conf=0.8)],
                               _vlm("S4", 5200, 8100), vlm_weight_up=True)
    seg = out[0]
    assert seg["t_start_ms"] == 5000                 # 일치 시 telemetry 유지
    assert seg["boundary_source"] == "both"
    assert seg["boundary_confidence"] == pytest.approx(0.9)


def test_weight_up_clamps_adopted_boundary_to_no_overlap():
    """VLM 채택이 이전 세그먼트와 겹치면 이전 끝으로 클램프 (구조 불변조건)."""
    segs = [_seg("S4", 5000, 8000), _seg("S5", 8000, 11000)]
    out = apply_vlm_refinement(segs, _vlm("S5", 6500, 10000), vlm_weight_up=True)
    s4, s5 = out
    assert s4["t_end_ms"] == 8000
    assert s5["t_start_ms"] == 8000                  # 6500 → 8000 클램프
    assert s5["t_end_ms"] == 10000


# ---- 엔진 → refiner 전파 ----

def test_engine_passes_weight_flag_to_refinement(monkeypatch, tmp_path):
    from camca.segmentation import engine as engine_mod
    from camca.segmentation.engine import PhaseRecognitionEngine

    seen = []

    def spy_apply(segments, vlm_result, vlm_weight_up=False):
        seen.append(vlm_weight_up)
        return segments

    class FakeBackend:
        def model_id(self):
            return "fake:v0"

        def analyze_frames(self, prompt, frames, **kw):
            return {"step_id": "S4", "observed": True,
                    "t_start_ms": 5000, "t_end_ms": 8000,
                    "visual_summary": "x", "confidence": 0.9}

    monkeypatch.setattr(engine_mod, "apply_vlm_refinement", spy_apply)
    monkeypatch.setattr(engine_mod, "extract_boundary_frames",
                        lambda *a, **kw: [tmp_path / "f.png"])
    eng = PhaseRecognitionEngine(vlm_backend=FakeBackend(), vlm_weight_up=True)
    eng._refine_with_vlm([_seg("S4", 5000, 8000)], tmp_path / "v.mp4", "pMDI")
    assert seen and all(v is True for v in seen)


def test_engine_default_weight_is_off(monkeypatch, tmp_path):
    from camca.segmentation import engine as engine_mod
    from camca.segmentation.engine import PhaseRecognitionEngine

    seen = []
    monkeypatch.setattr(engine_mod, "apply_vlm_refinement",
                        lambda s, v, vlm_weight_up=False:
                        seen.append(vlm_weight_up) or s)
    monkeypatch.setattr(engine_mod, "extract_boundary_frames",
                        lambda *a, **kw: [tmp_path / "f.png"])

    class FakeBackend:
        def model_id(self):
            return "fake:v0"

        def analyze_frames(self, prompt, frames, **kw):
            return {"step_id": "S4", "observed": True, "t_start_ms": 5000,
                    "t_end_ms": 8000, "visual_summary": "x", "confidence": 0.9}

    eng = PhaseRecognitionEngine(vlm_backend=FakeBackend())
    eng._refine_with_vlm([_seg("S4", 5000, 8000)], tmp_path / "v.mp4", "pMDI")
    assert seen and all(v is False for v in seen)


# ---- 파이프라인 → 엔진 전파 ----

def _telemetry():
    return [{
        "timestamp_ms": ts, "audio_energy_db": 36.0, "lip_distance_px": 20.0,
        "head_pitch_deg": 0.0, "index_finger_acceleration": 0.0,
        "wrist_zero_crossing_rate": 0, "chest_expansion_ratio": 1.0,
        "hand_mouth_distance_px": 300.0,
    } for ts in range(0, 3000, 100)]


def test_pipeline_propagates_weight_flag_to_engine(monkeypatch):
    import camca.segmentation as seg_pkg
    from camca.pipeline import MultiModelPipeline, PersonaConfig

    class DummyBackend:
        def model_id(self):
            return "dummy:v0"

        def analyze_frames(self, prompt, frames, **kw):
            return {}

    captured = {}

    class SpyEngine:
        def __init__(self, vlm_backend=None, vlm_weight_up=False):
            captured["vlm_weight_up"] = vlm_weight_up

        def segment_from_telemetry(self, telemetry, device_type, case_id,
                                   video_path=None):
            return {"engine": "telemetry-anchored-v1", "case_id": case_id,
                    "segments": [], "events": []}

    monkeypatch.setattr(seg_pkg, "PhaseRecognitionEngine", SpyEngine)
    p = MultiModelPipeline(
        device_id_backend=DummyBackend(), segmenter_backend=DummyBackend(),
        evaluator_a=PersonaConfig("A", "strict", DummyBackend()),
        evaluator_b=PersonaConfig("B", "pragmatic", DummyBackend()),
        use_phase_engine=True,
    )
    p.set_phase_vlm_weight_up(True)
    p._stage_segment(frames=[], device_type="pMDI", telemetry=_telemetry(),
                     case_id="X-001")
    assert captured["vlm_weight_up"] is True


def test_pipeline_weight_flag_defaults_off(monkeypatch):
    import camca.segmentation as seg_pkg
    from camca.pipeline import MultiModelPipeline, PersonaConfig

    class DummyBackend:
        def model_id(self):
            return "dummy:v0"

        def analyze_frames(self, prompt, frames, **kw):
            return {}

    captured = {}

    class SpyEngine:
        def __init__(self, vlm_backend=None, vlm_weight_up=False):
            captured["vlm_weight_up"] = vlm_weight_up

        def segment_from_telemetry(self, telemetry, device_type, case_id,
                                   video_path=None):
            return {"engine": "telemetry-anchored-v1", "case_id": case_id,
                    "segments": [], "events": []}

    monkeypatch.setattr(seg_pkg, "PhaseRecognitionEngine", SpyEngine)
    p = MultiModelPipeline(
        device_id_backend=DummyBackend(), segmenter_backend=DummyBackend(),
        evaluator_a=PersonaConfig("A", "strict", DummyBackend()),
        evaluator_b=PersonaConfig("B", "pragmatic", DummyBackend()),
        use_phase_engine=True,
    )
    p._stage_segment(frames=[], device_type="pMDI", telemetry=_telemetry(),
                     case_id="X-001")
    assert captured["vlm_weight_up"] is False
