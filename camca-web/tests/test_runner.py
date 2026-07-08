"""process_case — 상태 전이·산출물 저장·NEEDS_ATTENTION·클라우드 경계를 mock으로 검증."""
from types import SimpleNamespace
import pytest

from camca_web.config import Settings
from camca_web.db import (make_engine, make_session_factory, init_db, AuditLog,
                          Participant, Case, Segmentation, Evaluation, Score)
from camca_web.quality_gate import QualityResult
from camca_web.runner import RunnerDeps, process_case


@pytest.fixture
def env(tmp_path):
    engine = make_engine("sqlite://")
    init_db(engine)
    sf = make_session_factory(engine)
    video = tmp_path / "original.mp4"
    video.write_bytes(b"fake")
    with sf() as s:
        p = Participant(research_code="RC-P", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-p", participant_id=p.id, video_path=str(video),
                   device_type="pMDI", source="clinic", status="UPLOADED"))
        s.commit()
    return sf, Settings(db_url="sqlite://", storage_root=tmp_path, secret_key="t")


def _fake_result(critical=(), kappa=0.8, conflict=False):
    segs = [{"step_id": f"S{i}", "observable": True,
             **({"conflict_flagged": True} if conflict and i == 5 else {})}
            for i in range(1, 10)]
    return SimpleNamespace(
        device_id={"device_type": "pMDI"},
        segments={"segments": segs, "events": [], "engine": "telemetry-anchored-v1"},
        evaluator_a={"per_step": ["a"]}, evaluator_b={"per_step": ["b"]},
        tie_breaker=None,
        kappa_stats={"kappa": {"linear_weighted": kappa}},
        final_score={"final_verdict": "PASS",
                     "critical_error_override": {"critical_errors": list(critical)}},
        metadata={},
    )


def _deps(result, quality=None, issued=None, anonymized_calls=None):
    def pipeline_factory(case_dir, use_phase_engine):
        return SimpleNamespace(run_from_video=lambda video_path, case_id: result)
    return RunnerDeps(
        telemetry_fn=lambda video_path: [{"timestamp_ms": 0, "lip_distance_px": 20.0}],
        quality_fn=lambda stream: quality or QualityResult(
            passed=True, view="frontal", face_detection_rate=0.95),
        anonymize_fn=lambda src, dst: (anonymized_calls is not None
                                        and anonymized_calls.append((src, dst))) or
                                       SimpleNamespace(output_path=dst,
                                                       total_frames=1, blurred_frames=1),
        pipeline_factory=pipeline_factory,
        issue_fn=lambda session, case, result_dict, settings: (issued is not None
                                                               and issued.append(case.id)),
    )


def test_happy_path_reaches_report_issued(env):
    sf, settings = env
    issued = []
    process_case("case-p", sf, settings, _deps(_fake_result(), issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "REPORT_ISSUED"
        assert case.needs_attention is False
        assert s.query(Segmentation).filter_by(case_id="case-p").count() == 1
        assert s.query(Evaluation).filter_by(case_id="case-p").count() == 2  # A, B
        assert s.query(Score).filter_by(case_id="case-p").count() == 1
    assert issued == ["case-p"]


def test_pipeline_receives_anonymized_video_not_original(env):
    """PIPA 경계: 파이프라인 입력은 익명화 산출물이어야 한다."""
    sf, settings = env
    calls = []
    seen_paths = []
    deps = _deps(_fake_result(), anonymized_calls=calls)
    orig_factory = deps.pipeline_factory
    def spy_factory(case_dir, use_phase_engine):
        p = orig_factory(case_dir, use_phase_engine)
        inner = p.run_from_video
        p.run_from_video = lambda video_path, case_id: (
            seen_paths.append(str(video_path)) or inner(video_path, case_id))
        return p
    deps.pipeline_factory = spy_factory
    process_case("case-p", sf, settings, deps)
    assert len(calls) == 1                       # 익명화 1회 수행
    assert "anonymized" in seen_paths[0]         # 원본이 아닌 익명화본 전달
    with sf() as s:                              # 클라우드 전송 audit 기록
        events = [a.event for a in s.query(AuditLog).all()]
        assert "cloud_dispatch" in events


def test_quality_fail_stops_at_retake(env):
    sf, settings = env
    bad = QualityResult(passed=False, view="back_or_unknown",
                        face_detection_rate=0.1, reasons=["face_not_detected"])
    issued = []
    process_case("case-p", sf, settings, _deps(_fake_result(), quality=bad, issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "RETAKE_REQUESTED"
        assert case.quality_flag == "face_not_detected"
    assert issued == []                          # 발행 안 함


def test_pipeline_receives_injected_telemetry_when_supported(env):
    """finding 1: pipeline_factory가 inject_telemetry를 지원하면 익명화 전 원본에서
    추출한 telemetry를 그대로 주입해, 오디오 없는 익명화본에서 재추출하지 않는다."""
    sf, settings = env
    injected = []

    class FakePipeline:
        def inject_telemetry(self, stream):
            injected.append(stream)

        def run_from_video(self, video_path, case_id):
            return _fake_result()

    deps = _deps(_fake_result())
    deps.pipeline_factory = lambda case_dir, use_phase_engine: FakePipeline()
    process_case("case-p", sf, settings, deps)
    assert len(injected) == 1
    assert injected[0] == [{"timestamp_ms": 0, "lip_distance_px": 20.0}]


def test_segments_key_falls_back_to_video_segments(env):
    """finding 1: legacy VLM segmenter는 'video_segments' 키를 쓰므로 runner가 대응해야 한다."""
    sf, settings = env
    result = _fake_result()
    result.segments = {"video_segments": result.segments["segments"], "engine": "vlm-prompt"}
    process_case("case-p", sf, settings, _deps(result))
    with sf() as s:
        seg = s.query(Segmentation).filter_by(case_id="case-p").one()
        assert len(seg.segments) == 9


def test_cloud_dispatch_audit_records_blur_coverage(env):
    """finding 2: 익명화 커버리지 감사 — anonymize_fn 반환값이 audit detail에 남아야 한다."""
    sf, settings = env
    process_case("case-p", sf, settings, _deps(_fake_result()))
    with sf() as s:
        dispatch = next(a for a in s.query(AuditLog).all() if a.event == "cloud_dispatch")
        assert "blur_coverage" in dispatch.detail
        assert dispatch.detail["blur_coverage"] == pytest.approx(1.0)  # 1 blurred / 1 total


def test_process_case_retry_replaces_not_duplicates(env):
    """finding 3: 재실행 시 기존 Segmentation/Evaluation/Score를 지우고 새로 채운다."""
    sf, settings = env
    process_case("case-p", sf, settings, _deps(_fake_result()))
    with sf() as s:
        case = s.get(Case, "case-p")
        case.status = "FAILED"
        s.commit()
    process_case("case-p", sf, settings, _deps(_fake_result()))
    with sf() as s:
        assert s.query(Segmentation).filter_by(case_id="case-p").count() == 1
        assert s.query(Evaluation).filter_by(case_id="case-p").count() == 2
        assert s.query(Score).filter_by(case_id="case-p").count() == 1


def test_needs_attention_badge_does_not_block_issue(env):
    """spec §4: critical error가 있어도 발행은 진행 + 배지."""
    sf, settings = env
    issued = []
    process_case("case-p", sf, settings,
                 _deps(_fake_result(critical=["no_breath_hold"], kappa=0.4),
                       issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "REPORT_ISSUED"
        assert case.needs_attention is True
        assert set(case.attention_reasons) >= {"critical_error", "low_kappa"}
    assert issued == ["case-p"]
