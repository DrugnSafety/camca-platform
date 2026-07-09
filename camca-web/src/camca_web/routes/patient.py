"""환자용 — 서명 링크 + 생년월일 확인 후 리포트 열람 (회원가입 없음)."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse

from ..auth import dob_matches, read_patient_token
from ..db import Case, Participant, Report, write_audit

router = APIRouter()


def _resolve_case(request: Request, token: str):
    settings = request.app.state.settings
    case_id = read_patient_token(token, settings.secret_key,
                                 settings.patient_link_max_age_sec)
    if case_id is None:
        raise HTTPException(404)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        participant = s.get(Participant, case.participant_id)
        reports = s.query(Report).filter_by(case_id=case_id).all()
    return case, participant, reports


@router.get("/r/{token}")
def verify_form(request: Request, token: str):
    _resolve_case(request, token)   # 토큰 유효성만 먼저 확인
    return request.app.state.templates.TemplateResponse(
        request, "patient_verify.html", {"token": token, "error": None})


@router.post("/r/{token}")
def view_report(request: Request, token: str, dob: str = Form()):
    case, participant, reports = _resolve_case(request, token)
    if not dob_matches(dob, participant.dob):
        raise HTTPException(403, detail="생년월일이 일치하지 않습니다.")
    with request.app.state.session_factory() as s:
        write_audit(s, "report_viewed", case_id=case.id, detail={"channel": "link"})
        s.commit()
    return request.app.state.templates.TemplateResponse(
        request, "patient_report.html",
        {"token": token, "case": case, "reports": reports})


@router.get("/r/{token}/pdf/{kind}")
def download_pdf(request: Request, token: str, kind: str):
    case, _, reports = _resolve_case(request, token)
    match = [r for r in reports if r.kind == kind and r.kind.startswith("patient")]
    if not match:
        raise HTTPException(404)
    return FileResponse(match[-1].pdf_path, media_type="application/pdf")
