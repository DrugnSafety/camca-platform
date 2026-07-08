"""케이스 1건 처리 — 상태 머신을 구동하는 유일한 곳.

QUALITY_CHECK → (부적합) RETAKE_REQUESTED
             → 익명화 → ANALYZING(파이프라인) → 저장 → SCORED → 발행 → REPORT_ISSUED
예외는 잡 큐(jobs.py)가 받아 FAILED 처리하므로 여기서는 그대로 올린다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .db import Case, Evaluation, Score, Segmentation, write_audit
from .quality_gate import QualityResult
from .state import (ANALYZING, QUALITY_CHECK, REPORT_ISSUED, RETAKE_REQUESTED,
                    SCORED, needs_attention_reasons)


@dataclass
class RunnerDeps:
    """전 외부 의존 주입점 — CI는 전부 mock, 운영은 build_default_deps()."""
    telemetry_fn: Callable[[str], list[dict]]
    quality_fn: Callable[[list[dict]], QualityResult]
    anonymize_fn: Callable[[Path, Path], Any]
    pipeline_factory: Callable[[Path, bool], Any]   # (case_dir, use_phase_engine)
    issue_fn: Callable[..., Any]                     # (session, case, result_dict, settings)


def process_case(case_id: str, session_factory, settings: Settings,
                 deps: RunnerDeps) -> None:
    with session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise ValueError(f"unknown case: {case_id}")
        case.status = QUALITY_CHECK
        s.commit()
        video_path = case.video_path
        device_type = case.device_type

    # 1) Quality gate (spec §2 quality_gate — L6 차단)
    telemetry = deps.telemetry_fn(video_path)
    quality = deps.quality_fn(telemetry)
    with session_factory() as s:
        case = s.get(Case, case_id)
        case.view_angle = quality.view
        if not quality.passed:
            case.status = RETAKE_REQUESTED
            case.quality_flag = ",".join(quality.reasons)
            write_audit(s, "retake_requested", case_id=case_id,
                        detail={"reasons": quality.reasons})
            s.commit()
            return
        if quality.vlm_weight_up:
            case.quality_flag = "vlm_weight_up"
        s.commit()

    # 2) 익명화 — 클라우드로 나가는 유일한 산출물 (PIPA 경계)
    case_dir = Path(settings.storage_root) / "cases" / case_id
    anon_path = case_dir / "anonymized.mp4"
    deps.anonymize_fn(Path(video_path), anon_path)
    with session_factory() as s:
        case = s.get(Case, case_id)
        case.anonymized_path = str(anon_path)
        case.status = ANALYZING
        write_audit(s, "cloud_dispatch", case_id=case_id,
                    detail={"artifact": str(anon_path)})
        s.commit()

    # 3) camca-py 파이프라인 (익명화본만 전달)
    pipeline = deps.pipeline_factory(case_dir, True)
    result = pipeline.run_from_video(anon_path, case_id=case_id)

    # 4) 산출물 저장 + NEEDS_ATTENTION 판정 (spec §3, §4)
    segments = (result.segments or {}).get("segments", [])
    reasons = needs_attention_reasons(result.final_score, result.kappa_stats, segments)
    with session_factory() as s:
        case = s.get(Case, case_id)
        s.add(Segmentation(case_id=case_id, segments=segments,
                           events=(result.segments or {}).get("events", []),
                           engine=(result.segments or {}).get("engine", "vlm-prompt")))
        s.add(Evaluation(case_id=case_id, evaluator="A", raw=result.evaluator_a))
        s.add(Evaluation(case_id=case_id, evaluator="B", raw=result.evaluator_b))
        if result.tie_breaker:
            s.add(Evaluation(case_id=case_id, evaluator="TB", raw=result.tie_breaker))
        s.add(Score(case_id=case_id, final_score=result.final_score,
                    kappa=result.kappa_stats,
                    verdict=result.final_score.get("final_verdict", "UNKNOWN")))
        case.status = SCORED
        case.needs_attention = bool(reasons)
        case.attention_reasons = reasons
        s.commit()

    # 5) 자동 발행 — NEEDS_ATTENTION이어도 막지 않는다 (spec §4)
    with session_factory() as s:
        case = s.get(Case, case_id)
        deps.issue_fn(s, case, result, settings)
        case.status = REPORT_ISSUED
        write_audit(s, "report_issued", case_id=case_id,
                    detail={"needs_attention": case.needs_attention})
        s.commit()


def build_default_deps() -> RunnerDeps:
    """운영 배선 — VLM/MediaPipe 실의존. 테스트에서는 사용하지 않는다."""
    from camca.backends import create_backend
    from camca.pipeline import MultiModelPipeline, PersonaConfig
    from camca.telemetry import extract_telemetry
    from .anonymizer import anonymize_video
    from .quality_gate import evaluate_quality
    from .reports_web import issue_reports

    def pipeline_factory(case_dir: Path, use_phase_engine: bool):
        return MultiModelPipeline(
            device_id_backend=create_backend("claude:sonnet"),
            segmenter_backend=create_backend("claude:sonnet"),
            evaluator_a=PersonaConfig("evaluator-a", "GINA-strict",
                                      create_backend("claude:opus")),
            evaluator_b=PersonaConfig("evaluator-b", "real-world-pragmatic",
                                      create_backend("gemini:pro")),
            case_dir=case_dir,
            use_phase_engine=use_phase_engine,
        )

    return RunnerDeps(
        telemetry_fn=extract_telemetry,
        quality_fn=evaluate_quality,
        anonymize_fn=anonymize_video,
        pipeline_factory=pipeline_factory,
        issue_fn=issue_reports,
    )
