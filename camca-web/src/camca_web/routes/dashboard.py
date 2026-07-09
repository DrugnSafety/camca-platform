"""의사용 대시보드 — 사후 모니터링 + 타임라인 경계·점수 수정 (flywheel 라벨 입구)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from camca.scoring import compute_final_score

from ..db import (Case, Score, ScoresCorrected, Segmentation,
                  SegmentsCorrected, write_audit)
from ..reports_web import next_revision, reissue_reports
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
        score = (s.query(Score).filter_by(case_id=case_id)
                 .order_by(Score.created_at.desc()).first())
        corrected = (s.query(ScoresCorrected).filter_by(case_id=case_id)
                     .order_by(ScoresCorrected.created_at.desc()).first())
        issued_revision = next_revision(s, case_id) - 1
    segments = seg.segments if seg else []
    duration = max((x.get("t_end_ms") or 0) for x in segments) if segments else 1

    # 점수 편집 컨텍스트 — 최신 수정본이 있으면 그 레벨을 현재값으로 보여준다.
    score_ctx = None
    if score is not None:
        effective = (corrected.final_score if corrected is not None
                     else score.final_score)
        levels = ((corrected.per_step_levels if corrected is not None
                   else score.final_score.get("per_step_levels")) or {})
        ab = {p["step_id"]: p
              for p in (score.kappa or {}).get("per_step_agreement", [])}
        score_ctx = {
            "steps": [{"step_id": k, "level": levels[k],
                       "a": ab.get(k, {}).get("evaluator_a_level"),
                       "b": ab.get(k, {}).get("evaluator_b_level")}
                      for k in sorted(levels)],
            "verdict": effective.get("final_verdict", "?"),
            "percent": (effective.get("score_components") or {})
                       .get("core_steps_percent"),
            "corrected": corrected,
            "revision": issued_revision,
        }
    return request.app.state.templates.TemplateResponse(
        request, "case_detail.html",
        {"case": case, "segments": segments, "duration_ms": max(duration, 1),
         "score_ctx": score_ctx})


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


class ScoreCorrectionPayload(BaseModel):
    per_step_levels: dict[str, int | None]

    @field_validator("per_step_levels")
    @classmethod
    def _levels_in_rubric_range(cls, v: dict) -> dict:
        for step, level in v.items():
            if level is not None and not 0 <= level <= 3:
                raise ValueError(f"{step}: level must be 0-3 or null")
        return v


def _diff_levels(before: dict, after: dict) -> list[dict]:
    """수정 요청에 포함된 단계만 비교 — 빠진 키는 '변경 없음'으로 간주."""
    return [{"step_id": k, "before": before.get(k), "after": v}
            for k, v in sorted(after.items()) if before.get(k) != v]


@router.post("/cases/{case_id}/scores")
def correct_scores(request: Request, case_id: str,
                   payload: ScoreCorrectionPayload):
    """의사 점수 수정 → 결정론 엔진 재계산 + diff 기록 + 수정본 재발행 (spec §4)."""
    user = require_staff(request)
    settings = request.app.state.settings
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        score = (s.query(Score).filter_by(case_id=case_id)
                 .order_by(Score.created_at.desc()).first())
        if case is None or score is None:
            raise HTTPException(404, detail="no score to correct")
        latest = (s.query(ScoresCorrected).filter_by(case_id=case_id)
                  .order_by(ScoresCorrected.created_at.desc()).first())
        before = ((latest.per_step_levels if latest is not None
                   else score.final_score.get("per_step_levels")) or {})
        diff = _diff_levels(before, payload.per_step_levels)
        if not diff:
            return {"ok": True, "n_changes": 0, "revision": None}

        merged = {**before, **payload.per_step_levels}
        observed = {k: v for k, v in merged.items() if v is not None}
        crit = ((score.final_score.get("critical_error_override") or {})
                .get("critical_errors") or [])
        corrected_final = compute_final_score(
            observed, crit, case.device_type, case_id=case.id)
        s.add(ScoresCorrected(case_id=case_id, corrected_by=user,
                              per_step_levels=merged,
                              final_score=corrected_final, diff=diff))
        write_audit(s, "scores_corrected", case_id=case_id,
                    detail={"by": user, "n_changes": len(diff)})
        revision = reissue_reports(s, case, corrected_final, settings)
        write_audit(s, "report_reissued", case_id=case_id,
                    detail={"by": user, "revision": revision, "diff": diff})
        s.commit()
    return {"ok": True, "n_changes": len(diff), "revision": revision}
