"""의사 점수(레벨) 수정 → scores_corrected + diff + 수정본 리포트 재발행 (spec §4).

수정 기록이 Step 2 human-vs-LLM 연구 데이터가 되도록 원본 레벨과 diff를
그대로 보존하고, 재발행 PDF는 revision 디렉토리로 분리해 원본을 덮어쓰지 않는다.
"""
import pytest

from camca_web.auth import hash_password
from camca_web.db import (AuditLog, Case, Evaluation, Participant, Report,
                          Score, ScoresCorrected, Segmentation)

FINAL_SCORE = {
    "case_id": "case-sc",
    "device_type": "pMDI",
    "per_step_levels": {"S1": None, "S2": None, "S3": None, "S4": 2, "S5": 3,
                        "S6": 3, "S7": 2, "S8": None, "S9": None},
    "score_components": {"core_steps_total": 10, "core_steps_max": 21,
                         "core_steps_percent": 47.6},
    "critical_error_override": {"applied": False, "critical_errors": [],
                                "verdict_override": None},
    "final_verdict": "FAIL",
}

KAPPA = {
    "kappa": {"linear_weighted": 0.09, "interpretation_linear": "slight"},
    "per_step_agreement": [
        {"step_id": "S4", "evaluator_a_level": 1, "evaluator_b_level": 3,
         "level_diff": 2, "agreement": "disagree_moderate"},
        {"step_id": "S5", "evaluator_a_level": 3, "evaluator_b_level": 3,
         "level_diff": 0, "agreement": "agree"},
    ],
    "critical_error_consensus": {"both_flagged": []},
}


@pytest.fixture
def staff(client):
    client.app.state.staff_accounts = {"dr-kang": hash_password("pw")}
    return client.post("/login", data={"username": "dr-kang", "password": "pw"},
                       follow_redirects=False).cookies


@pytest.fixture
def scored_case(client):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-SC", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-sc", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED"))
        s.add(Segmentation(case_id="case-sc", engine="telemetry-anchored-v1",
                           events=[],
                           segments=[{"step_id": "S5", "observable": True,
                                      "t_start_ms": 6000, "t_end_ms": 9000}]))
        s.add(Evaluation(case_id="case-sc", evaluator="A", raw={"src": "a"}))
        s.add(Evaluation(case_id="case-sc", evaluator="B", raw={"src": "b"}))
        s.add(Score(case_id="case-sc", final_score=FINAL_SCORE, kappa=KAPPA,
                    verdict="FAIL"))
        s.add(Report(case_id="case-sc", kind="patient_ko",
                     pdf_path="r1.pdf", revision=1))
        s.commit()
    return "case-sc"


def _corrected(**overrides):
    levels = dict(FINAL_SCORE["per_step_levels"])
    levels.update(overrides)
    return {"per_step_levels": levels}


def test_score_edit_requires_login(client, scored_case):
    r = client.post(f"/cases/{scored_case}/scores", json=_corrected(S4=3),
                    follow_redirects=False)
    assert r.status_code in (302, 303)


def test_correction_saves_diff_and_recomputes_deterministic(client, staff,
                                                            scored_case):
    pytest.importorskip("reportlab")
    r = client.post(f"/cases/{scored_case}/scores", cookies=staff,
                    json=_corrected(S4=3))
    assert r.status_code == 200
    body = r.json()
    assert body["n_changes"] == 1
    with client.app.state.session_factory() as s:
        row = s.query(ScoresCorrected).one()
        assert row.corrected_by == "dr-kang"
        assert row.diff == [{"step_id": "S4", "before": 2, "after": 3}]
        # 원본 레벨 맵은 Score 행에 그대로 보존 (연구 데이터)
        original = s.query(Score).one()
        assert original.final_score["per_step_levels"]["S4"] == 2
        # 수정 레벨로 결정론 엔진 재계산: 11/21 = 52.4% → NEEDS_INTENSIVE_TRAINING
        fs = row.final_score
        assert fs["score_components"]["core_steps_total"] == 11
        assert fs["final_verdict"] == "NEEDS_INTENSIVE_TRAINING"
        assert fs["deterministic_signature"].startswith("sha256:")
        events = [a.event for a in s.query(AuditLog).all()]
        assert "scores_corrected" in events


def test_correction_reissues_reports_as_next_revision(client, staff,
                                                      scored_case):
    pytest.importorskip("reportlab")
    r = client.post(f"/cases/{scored_case}/scores", cookies=staff,
                    json=_corrected(S4=3))
    assert r.status_code == 200
    assert r.json()["revision"] == 2
    with client.app.state.session_factory() as s:
        v2 = s.query(Report).filter_by(case_id="case-sc", revision=2).all()
        assert {x.kind for x in v2} == {"patient_ko", "patient_en",
                                        "clinician_ko", "clinician_en"}
        from pathlib import Path
        for x in v2:
            assert Path(x.pdf_path).exists()
            assert "/v2/" in x.pdf_path      # v1 PDF를 덮어쓰지 않는다
        # 재발행 audit에 diff가 남는다 (원본 대비 기록 — spec §4)
        reissued = [a for a in s.query(AuditLog).all()
                    if a.event == "report_reissued"]
        assert len(reissued) == 1
        assert reissued[0].detail["revision"] == 2
        assert reissued[0].detail["diff"] == [
            {"step_id": "S4", "before": 2, "after": 3}]


def test_correction_can_mark_step_unobservable(client, staff, scored_case):
    pytest.importorskip("reportlab")
    r = client.post(f"/cases/{scored_case}/scores", cookies=staff,
                    json=_corrected(S7=None))
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        row = s.query(ScoresCorrected).one()
        assert row.diff == [{"step_id": "S7", "before": 2, "after": None}]
        assert row.final_score["score_components"]["core_steps_total"] == 8


def test_noop_correction_creates_nothing(client, staff, scored_case):
    r = client.post(f"/cases/{scored_case}/scores", cookies=staff,
                    json=_corrected())
    assert r.status_code == 200
    assert r.json() == {"ok": True, "n_changes": 0, "revision": None}
    with client.app.state.session_factory() as s:
        assert s.query(ScoresCorrected).count() == 0
        assert s.query(Report).filter_by(revision=2).count() == 0


def test_invalid_level_rejected(client, staff, scored_case):
    r = client.post(f"/cases/{scored_case}/scores", cookies=staff,
                    json=_corrected(S4=5))
    assert r.status_code == 422
    with client.app.state.session_factory() as s:
        assert s.query(ScoresCorrected).count() == 0


def test_correction_without_score_404(client, staff):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-NS", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-ns", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="ANALYZING"))
        s.commit()
    r = client.post("/cases/case-ns/scores", cookies=staff,
                    json=_corrected(S4=3))
    assert r.status_code == 404


def test_case_detail_shows_score_editor(client, staff, scored_case):
    r = client.get(f"/cases/{scored_case}", cookies=staff)
    assert r.status_code == 200
    assert "scoreTable" in r.text
    assert "FAIL" in r.text              # 현재 verdict 표시
    # A/B 레벨 컨텍스트 제공 (per_step_agreement)
    assert 'data-score-step="S4"' in r.text


def test_case_detail_shows_latest_corrected_levels(client, staff, scored_case):
    pytest.importorskip("reportlab")
    client.post(f"/cases/{scored_case}/scores", cookies=staff,
                json=_corrected(S4=3))
    r = client.get(f"/cases/{scored_case}", cookies=staff)
    assert r.status_code == 200
    assert "수정본 v2" in r.text          # 최신 수정 배지
