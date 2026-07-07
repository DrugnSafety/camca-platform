"""스태프용 라우트 — 로그인, 업로드 (원본은 로컬 스토리지에만 저장)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from ..auth import make_session_cookie, read_session_cookie, verify_password
from ..db import Case, Job, Participant, write_audit

router = APIRouter()


def require_staff(request: Request) -> str:
    user = read_session_cookie(request.cookies.get("camca_session", ""),
                               request.app.state.settings.secret_key)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


@router.get("/login")
def login_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        request, "login.html", {})


@router.post("/login")
def login(request: Request, username: str = Form(), password: str = Form()):
    accounts = getattr(request.app.state, "staff_accounts", {})
    hashed = accounts.get(username)
    if not hashed or not verify_password(password, hashed):
        raise HTTPException(status_code=401, detail="invalid credentials")
    resp = RedirectResponse("/upload", status_code=303)
    resp.set_cookie("camca_session",
                    make_session_cookie(username, request.app.state.settings.secret_key),
                    httponly=True)
    return resp


@router.get("/upload")
def upload_form(request: Request):
    require_staff(request)
    return request.app.state.templates.TemplateResponse(
        request, "upload.html", {"case_id": None})


@router.post("/upload")
async def upload(request: Request, video: UploadFile,
                 research_code: str = Form(), dob: str = Form(),
                 device_type: str = Form("pMDI"), source: str = Form("clinic")):
    user = require_staff(request)
    settings = request.app.state.settings
    with request.app.state.session_factory() as s:
        participant = s.query(Participant).filter_by(research_code=research_code).first()
        if participant is None:
            participant = Participant(research_code=research_code, dob=dob)
            s.add(participant)
            s.flush()
        case = Case(participant_id=participant.id, video_path="",
                    device_type=device_type, source=source, status="UPLOADED")
        s.add(case)
        s.flush()
        case_dir = Path(settings.storage_root) / "cases" / case.id
        case_dir.mkdir(parents=True, exist_ok=True)
        dest = case_dir / "original.mp4"
        try:
            dest.write_bytes(await video.read())
            case.video_path = str(dest)
            s.add(Job(case_id=case.id, status="pending"))
            write_audit(s, "case_uploaded", case_id=case.id,
                        detail={"by": user, "source": source})
            s.commit()
        except Exception:
            # Clean up the video file if write succeeded but commit failed
            if dest.exists():
                dest.unlink(missing_ok=True)
            # Remove case directory if now empty
            try:
                if not any(case_dir.iterdir()):
                    case_dir.rmdir()
            except (OSError, StopIteration):
                pass
            raise
        case_id = case.id
    return request.app.state.templates.TemplateResponse(
        request, "upload.html", {"case_id": case_id})


@router.post("/cases/{case_id}/rerun")
def rerun(request: Request, case_id: str):
    user = require_staff(request)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        job = (s.query(Job).filter_by(case_id=case_id)
               .order_by(Job.created_at.desc()).first())
        if job is None:
            job = Job(case_id=case_id)
            s.add(job)
        job.status = "pending"
        job.error = None
        case.status = "ANALYZING" if case.status == "FAILED" else case.status
        write_audit(s, "case_rerun", case_id=case_id, detail={"by": user})
        s.commit()
    return {"ok": True, "case_id": case_id}
