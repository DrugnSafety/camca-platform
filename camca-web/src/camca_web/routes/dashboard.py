"""의사용 대시보드 — 사후 모니터링 + 타임라인 경계 수정 (flywheel 라벨 입구)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..db import Case, Segmentation, SegmentsCorrected, write_audit
from .staff import require_staff

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request):
    require_staff(request)
    with request.app.state.session_factory() as s:
        cases = s.query(Case).order_by(Case.uploaded_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        request, "dashboard.html", {"cases": cases})


@router.get("/cases/{case_id}")
def case_detail(request: Request, case_id: str):
    require_staff(request)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        seg = (s.query(Segmentation).filter_by(case_id=case_id)
               .order_by(Segmentation.created_at.desc()).first())
    segments = seg.segments if seg else []
    duration = max((x.get("t_end_ms") or 0) for x in segments) if segments else 1
    return request.app.state.templates.TemplateResponse(
        request, "case_detail.html",
        {"case": case, "segments": segments, "duration_ms": max(duration, 1)})


class CorrectionPayload(BaseModel):
    segments: list[dict]


def _diff_segments(before: list[dict], after: list[dict]) -> list[dict]:
    """step_id 기준으로 t_start_ms/t_end_ms/observable 변경만 추출."""
    by_id = {x["step_id"]: x for x in before}
    diffs = []
    for seg in after:
        old = by_id.get(seg["step_id"])
        if not old:
            continue
        for field in ("t_start_ms", "t_end_ms", "observable"):
            if field in seg and seg.get(field) != old.get(field):
                diffs.append({"step_id": seg["step_id"], "field": field,
                              "before": old.get(field), "after": seg.get(field)})
    return diffs


@router.post("/cases/{case_id}/segments")
def correct_segments(request: Request, case_id: str, payload: CorrectionPayload):
    user = require_staff(request)
    with request.app.state.session_factory() as s:
        seg = (s.query(Segmentation).filter_by(case_id=case_id)
               .order_by(Segmentation.created_at.desc()).first())
        if seg is None:
            raise HTTPException(404)
        diff = _diff_segments(seg.segments, payload.segments)
        s.add(SegmentsCorrected(case_id=case_id, corrected_by=user,
                                segments=payload.segments, diff=diff))
        write_audit(s, "segments_corrected", case_id=case_id,
                    detail={"by": user, "n_changes": len(diff)})
        s.commit()
    return {"ok": True, "n_changes": len(diff)}
