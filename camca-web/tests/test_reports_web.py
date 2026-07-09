"""자동 발행(PDF 4종 + reports 행) + 서명 링크 열람 (생년월일 확인, 열람 로그)."""
from types import SimpleNamespace

import pytest

from camca_web.auth import make_patient_token
from camca_web.db import AuditLog, Case, Participant, Report


def _result():
    return SimpleNamespace(
        case_id="case-pt",
        device_id={"device_type": "pMDI"},
        segments={"segments": [], "events": []},
        evaluator_a={}, evaluator_b={}, tie_breaker=None,
        kappa_stats={"kappa": {"linear_weighted": 0.8,
                               "interpretation_linear": "substantial"},
                     "critical_error_consensus": {"both_flagged": []},
                     "per_step_agreement": []},
        final_score={"final_verdict": "PASS",
                     "per_step_levels": {},
                     "score_components": {"core_steps_total": 8, "core_steps_max": 10,
                                          "core_steps_percent": 80.0},
                     "critical_error_override": {"critical_errors": []}},
        metadata={"started_at": "2026-07-07T00:00:00", "stages": []},
    )


@pytest.fixture
def seeded_case(client, settings):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-PT", dob="1980-01-01")
        s.add(p); s.flush()
        c = Case(id="case-pt", participant_id=p.id, video_path="v.mp4",
                 device_type="pMDI", source="clinic", status="SCORED")
        s.add(c); s.commit()
    return "case-pt"


def test_issue_reports_creates_pdfs_and_rows(client, settings, seeded_case):
    pytest.importorskip("reportlab")
    from camca_web.reports_web import issue_reports
    with client.app.state.session_factory() as s:
        case = s.get(Case, seeded_case)
        rows = issue_reports(s, case, _result(), settings)
        s.commit()
    assert {r.kind for r in rows} == {"patient_ko", "patient_en",
                                      "clinician_ko", "clinician_en"}
    with client.app.state.session_factory() as s:
        for r in s.query(Report).all():
            from pathlib import Path
            assert Path(r.pdf_path).exists()


def test_patient_link_flow(client, settings, seeded_case):
    token = make_patient_token(seeded_case, settings.secret_key)
    r = client.get(f"/r/{token}")
    assert r.status_code == 200
    assert "생년월일" in r.text                      # 확인 폼
    r = client.post(f"/r/{token}", data={"dob": "1980-01-01"})
    assert r.status_code == 200
    with client.app.state.session_factory() as s:   # 열람 로그
        events = [a.event for a in s.query(AuditLog).all()]
        assert "report_viewed" in events


def test_patient_link_wrong_dob_rejected(client, settings, seeded_case):
    token = make_patient_token(seeded_case, settings.secret_key)
    r = client.post(f"/r/{token}", data={"dob": "1999-12-31"})
    assert r.status_code == 403


def test_patient_link_tampered_token_404(client, settings, seeded_case):
    r = client.get("/r/not-a-real-token")
    assert r.status_code == 404
