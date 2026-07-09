"""리포트 발행 — camca-py PDF 생성기 재사용. 수정본 재발행은 revision 증가.

revision 1은 reports/, revision ≥ 2는 reports/v{n}/ 에 저장해 원본 PDF를
덮어쓰지 않는다 (수정 전·후 비교가 연구 데이터 — spec §4).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from camca.cli import _build_clinician_content, _build_patient_content
from camca.reports import build_bilingual_reports
from sqlalchemy import func

from .auth import make_patient_token
from .config import Settings
from .db import Case, Evaluation, Report, Score, Segmentation


def issue_reports(session, case: Case, result, settings: Settings,
                  revision: int = 1) -> list[Report]:
    out_dir = Path(settings.storage_root) / "cases" / case.id / "reports"
    if revision > 1:
        out_dir = out_dir / f"v{revision}"
    out_dir.mkdir(parents=True, exist_ok=True)
    device = (result.device_id.get("device_type", "pmdi")
              .lower().replace("-", "_"))
    paths = build_bilingual_reports(
        patient_content=_build_patient_content(result),
        clinician_content=_build_clinician_content(result),
        output_dir=out_dir,
        case_id=case.id,
        device=device,
    )
    rows = []
    for kind, path in paths.items():
        row = Report(case_id=case.id, kind=kind, pdf_path=str(path),
                     revision=revision)
        session.add(row)
        rows.append(row)
    return rows


def next_revision(session, case_id: str) -> int:
    cur = (session.query(func.max(Report.revision))
           .filter(Report.case_id == case_id).scalar())
    return (cur or 0) + 1


def _result_from_db(session, case: Case, final_score: dict) -> SimpleNamespace:
    """저장된 산출물로 PipelineResult 동형 객체 재구성 — 재발행은 파이프라인을
    다시 돌리지 않고 DB의 원시 JSON에서 콘텐츠를 만든다."""
    score = (session.query(Score).filter_by(case_id=case.id)
             .order_by(Score.created_at.desc()).first())
    evals = {e.evaluator: e.raw
             for e in session.query(Evaluation).filter_by(case_id=case.id)}
    seg = (session.query(Segmentation).filter_by(case_id=case.id)
           .order_by(Segmentation.created_at.desc()).first())
    return SimpleNamespace(
        case_id=case.id,
        device_id={"device_type": case.device_type},
        segments={"segments": seg.segments if seg else [],
                  "events": seg.events if seg else []},
        evaluator_a=evals.get("A") or {},
        evaluator_b=evals.get("B") or {},
        tie_breaker=evals.get("TB"),
        kappa_stats=score.kappa if score else {"kappa": {}},
        final_score=final_score,
        metadata={"started_at": (case.uploaded_at.isoformat()
                                 if case.uploaded_at else ""),
                  "stages": []},
    )


def reissue_reports(session, case: Case, corrected_final_score: dict,
                    settings: Settings) -> int:
    """수정된 final_score로 다음 revision 발행. 발행된 revision 번호를 반환."""
    revision = next_revision(session, case.id)
    result = _result_from_db(session, case, corrected_final_score)
    issue_reports(session, case, result, settings, revision=revision)
    return revision


def patient_link(case_id: str, settings: Settings) -> str:
    return f"/r/{make_patient_token(case_id, settings.secret_key)}"
