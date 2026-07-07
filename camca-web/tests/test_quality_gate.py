"""업로드 직후 사전검사 — 부적합 즉시 재촬영 안내 (spec §2 quality_gate)."""
from camca_web.quality_gate import evaluate_quality


def _stream(n, lip=20.0, face_detected=True):
    """합성 telemetry — lip_distance_px>0이면 얼굴 검출로 간주."""
    return [{"timestamp_ms": i * 100,
             "lip_distance_px": lip if face_detected else 0.0,
             "head_pitch_deg": 0.0} for i in range(n)]


def test_frontal_video_passes():
    r = evaluate_quality(_stream(100))
    assert r.passed is True
    assert r.reasons == []


def test_no_face_fails_with_reason():
    r = evaluate_quality(_stream(100, face_detected=False))
    assert r.passed is False
    assert "face_not_detected" in r.reasons


def test_empty_telemetry_fails():
    r = evaluate_quality([])
    assert r.passed is False
    assert "no_telemetry" in r.reasons


def test_partial_detection_passes_with_vlm_weight_up():
    """측면 등 검출률 낮음 → 차단하지 않되 Stage 2 VLM 가중 상향 (spec §5.3-2)."""
    stream = _stream(60) + _stream(40, face_detected=False)
    r = evaluate_quality(stream)
    assert r.passed is True
    assert r.vlm_weight_up is True
