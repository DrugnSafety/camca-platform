"""리포트 golden file 비교 (spec §8).

발행 경로의 콘텐츠 매핑(PipelineResult → patient/clinician content)을 golden
JSON과 바이트 단위로 비교해, 매핑 변경이 의도치 않게 리포트를 바꾸는 것을
잡는다. PDF 자체는 생성 시각 등으로 바이트가 변하므로 구조·핵심 문자열만
검증한다 (PDF 생성기 내부는 camca-py에서 검증됨).

golden 갱신: CAMCA_UPDATE_GOLDEN=1 pytest tests/test_reports_golden.py
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"


def _fixed_result():
    """고정 fixture — 실측 케이스(CAMCA-20260512-150557) 구조를 축약."""
    return SimpleNamespace(
        case_id="GOLD-001",
        device_id={"device_type": "pMDI"},
        segments={"segments": [
            {"step_id": "S4", "observable": True, "t_start_ms": 0,
             "t_end_ms": 1500, "boundary_source": "both"},
            {"step_id": "S5", "observable": True, "t_start_ms": 1500,
             "t_end_ms": 3000, "boundary_source": "telemetry"},
        ], "events": []},
        evaluator_a={"per_step_evaluation": []},
        evaluator_b={"per_step_evaluation": []},
        tie_breaker=None,
        kappa_stats={
            "kappa": {"unweighted": 0.55, "linear_weighted": 0.72,
                      "quadratic_weighted": 0.8,
                      "interpretation_linear": "substantial"},
            "per_step_agreement": [
                {"step_id": "S4", "evaluator_a_level": 2,
                 "evaluator_b_level": 2, "level_diff": 0, "agreement": "agree"},
                {"step_id": "S5", "evaluator_a_level": 2,
                 "evaluator_b_level": 3, "level_diff": 1,
                 "agreement": "disagree_minor"},
            ],
            "critical_error_consensus": {"both_flagged": []},
        },
        final_score={
            "final_verdict": "ADEQUATE_WITH_EDUCATION",
            "per_step_levels": {"S4": 2, "S5": 3},
            "score_components": {"core_steps_total": 5, "core_steps_max": 6,
                                 "core_steps_percent": 83.3},
            "critical_error_override": {"applied": False,
                                        "critical_errors": []},
        },
        metadata={"started_at": "2026-07-01T09:00:00+00:00",
                  "stages": [{"stage_name": "phase-engine",
                              "model_used": "claude:sonnet",
                              "duration_ms": 1200}]},
    )


def _canon(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _check_golden(name: str, content: dict):
    path = GOLDEN_DIR / name
    rendered = _canon(content)
    if os.environ.get("CAMCA_UPDATE_GOLDEN") == "1":
        GOLDEN_DIR.mkdir(exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    assert path.exists(), (
        f"golden 없음: {path} — CAMCA_UPDATE_GOLDEN=1 로 생성 후 커밋하세요")
    assert rendered == path.read_text(encoding="utf-8"), (
        f"{name} 이 golden과 다릅니다. 의도된 변경이면 CAMCA_UPDATE_GOLDEN=1 "
        f"pytest 로 갱신 후 diff를 리뷰해 커밋하세요")


def test_patient_content_matches_golden():
    from camca.cli import _build_patient_content
    _check_golden("patient_content.json", _build_patient_content(_fixed_result()))


def test_clinician_content_matches_golden():
    from camca.cli import _build_clinician_content
    _check_golden("clinician_content.json",
                  _build_clinician_content(_fixed_result()))


def test_issued_pdfs_have_expected_structure(client, settings):
    """PDF 4종: 매직 헤더 + 텍스트에 case_id 포함 + 실질 분량."""
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    from camca_web.db import Case, Participant
    from camca_web.reports_web import issue_reports

    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-G", dob="1980-01-01")
        s.add(p); s.flush()
        case = Case(id="GOLD-001", participant_id=p.id, video_path="v.mp4",
                    device_type="pMDI", source="clinic", status="SCORED")
        s.add(case); s.flush()
        rows = issue_reports(s, case, _fixed_result(), settings)
        s.commit()

    assert {r.kind for r in rows} == {"patient_ko", "patient_en",
                                      "clinician_ko", "clinician_en"}
    for r in rows:
        pdf = Path(r.pdf_path)
        raw = pdf.read_bytes()
        assert raw[:5] == b"%PDF-"
        reader = pypdf.PdfReader(pdf)
        assert len(reader.pages) >= 1
        text = "".join(page.extract_text() or "" for page in reader.pages)
        assert "GOLD-001" in text
        assert len(text) > 200                    # 빈 껍데기 방지


def test_reissued_pdf_reflects_corrected_verdict(client, settings):
    """수정본 재발행 경로도 동일 생성기 사용 — 수정 verdict가 PDF에 반영된다."""
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    from camca_web.db import Case, Participant, Score
    from camca_web.reports_web import issue_reports, reissue_reports

    result = _fixed_result()
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-G2", dob="1980-01-01")
        s.add(p); s.flush()
        case = Case(id="GOLD-002", participant_id=p.id, video_path="v.mp4",
                    device_type="pMDI", source="clinic", status="REPORT_ISSUED")
        s.add(case); s.flush()
        s.add(Score(case_id="GOLD-002", final_score=result.final_score,
                    kappa=result.kappa_stats, verdict="ADEQUATE_WITH_EDUCATION"))
        result.case_id = "GOLD-002"
        issue_reports(s, case, result, settings)
        corrected = dict(result.final_score)
        corrected["final_verdict"] = "PROFICIENT"
        revision = reissue_reports(s, case, corrected, settings)
        s.commit()

    assert revision == 2
    with client.app.state.session_factory() as s:
        from camca_web.db import Report
        v2 = s.query(Report).filter_by(case_id="GOLD-002", revision=2,
                                       kind="clinician_en").one()
    text = "".join(page.extract_text() or ""
                   for page in pypdf.PdfReader(v2.pdf_path).pages)
    assert "PROFICIENT" in text
