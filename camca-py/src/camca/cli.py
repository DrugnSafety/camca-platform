"""CLI entrypoint for the camca package — installed as `camca` command via pyproject.toml."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backends import create_backend, BackendError
from .pipeline import MultiModelPipeline, PersonaConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="camca",
        description="CAMCA — Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Main analyze command
    ana = sub.add_parser("analyze", help="Analyze an inhaler-use video.")
    ana.add_argument("--video", type=Path, required=True, help="Input .mp4 video")
    ana.add_argument("--case-id", required=True, help="Case identifier")
    ana.add_argument("--output-dir", type=Path, default=None,
                     help="Output directory (default: ./camca_logs/<case-id>)")
    ana.add_argument("--fps", type=float, default=1.0, help="Frame extraction rate")

    ana.add_argument("--device-id-backend", default="claude:sonnet")
    ana.add_argument("--segmenter-backend", default="claude:sonnet")
    ana.add_argument("--evaluator-a", default="claude:opus")
    ana.add_argument("--evaluator-a-persona", default="GINA-strict")
    ana.add_argument("--evaluator-b", default="gemini:pro")
    ana.add_argument("--evaluator-b-persona", default="real-world-pragmatic")
    ana.add_argument("--tie-breaker", default=None,
                     help="Optional tie-breaker backend (e.g. claude:opus)")
    ana.add_argument("--tie-breaker-persona", default="clinical-pharmacy-educator")
    ana.add_argument("--tie-breaker-threshold", type=float, default=0.6)
    ana.add_argument("--no-pdf", action="store_true",
                     help="Skip PDF report generation")

    # Phase recognition only (v0.4.0)
    seg = sub.add_parser("segment", help="Run phase recognition only (no evaluation)")
    seg.add_argument("--video", required=True)
    seg.add_argument("--device", default="pMDI",
                     help="pMDI | pMDI-AIM-simulator | pMDI-spacer | DPI-turbuhaler")
    seg.add_argument("--case-id", required=True)
    seg.add_argument("--out", default=None, help="Output JSON path (default: stdout)")
    seg.add_argument("--vlm", default=None,
                     help="VLM backend for Stage 2, e.g. claude:sonnet (omit = telemetry-only)")
    seg.add_argument("--no-vlm", action="store_true", help="Force telemetry-only mode")

    # Info command
    info = sub.add_parser("info", help="Show package info + bundled resources.")

    # Version
    sub.add_parser("version", help="Show camca version.")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "version":
        from . import __version__
        print(f"camca {__version__}")
        return 0

    if args.cmd == "info":
        return _show_info()

    if args.cmd == "analyze":
        return _run_analyze(args)

    if args.cmd == "segment":
        return _run_segment(args)

    return 1


def _run_segment(args) -> int:
    import json
    from .segmentation import PhaseRecognitionEngine

    backend = None
    if args.vlm and not args.no_vlm:
        backend = create_backend(args.vlm)
    engine = PhaseRecognitionEngine(vlm_backend=backend)
    result = engine.segment(args.video, device_type=args.device, case_id=args.case_id)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"Segmentation written to {args.out}")
    else:
        print(payload)
    return 0


def _show_info() -> int:
    from . import __version__
    from .resources import available_skills, font_path, static_guide_path

    print(f"camca version: {__version__}")
    print(f"\nBundled skills ({len(available_skills())}):")
    for s in available_skills():
        print(f"  - {s}")

    print("\nBundled fonts:")
    try:
        print(f"  - NanumGothic Regular: {font_path('NanumGothic', 'Regular')}")
        print(f"  - NanumGothic Bold:    {font_path('NanumGothic', 'Bold')}")
    except FileNotFoundError as e:
        print(f"  WARNING: {e}")

    print("\nBundled static patient guides:")
    for lang in ("ko", "en"):
        try:
            p = static_guide_path("pmdi", lang)
            print(f"  - pMDI ({lang}): {p}")
        except FileNotFoundError:
            print(f"  - pMDI ({lang}): NOT BUNDLED")

    print("\nBackend availability:")
    for spec in ("claude:sonnet", "gemini:flash", "ollama:gemma3:12b"):
        try:
            be = create_backend(spec)
            print(f"  ✓ {spec} — ready ({be.model_id()})")
        except (BackendError, ImportError) as e:
            print(f"  ✗ {spec} — {e}")

    return 0


def _run_analyze(args) -> int:
    if not args.video.exists():
        print(f"ERROR: video not found: {args.video}", file=sys.stderr)
        return 2

    case_dir = args.output_dir or Path("./camca_logs") / args.case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    try:
        device_id_backend = create_backend(args.device_id_backend)
        segmenter_backend = create_backend(args.segmenter_backend)
        eval_a = PersonaConfig("evaluator-a", args.evaluator_a_persona,
                               create_backend(args.evaluator_a))
        eval_b = PersonaConfig("evaluator-b", args.evaluator_b_persona,
                               create_backend(args.evaluator_b))
        tb = None
        if args.tie_breaker:
            tb = PersonaConfig("tie-breaker", args.tie_breaker_persona,
                               create_backend(args.tie_breaker))
    except BackendError as e:
        print(f"ERROR: backend setup failed: {e}", file=sys.stderr)
        return 3

    pipeline = MultiModelPipeline(
        device_id_backend=device_id_backend,
        segmenter_backend=segmenter_backend,
        evaluator_a=eval_a,
        evaluator_b=eval_b,
        tie_breaker=tb,
        case_dir=case_dir,
    )

    try:
        result = pipeline.run_from_video(
            args.video, case_id=args.case_id, fps=args.fps,
            invoke_tie_breaker_threshold=args.tie_breaker_threshold,
        )
    except Exception as e:
        print(f"ERROR: pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 4

    # Optional: build PDFs
    if not args.no_pdf:
        try:
            from .reports import build_bilingual_reports
            patient_content = _build_patient_content(result)
            clinician_content = _build_clinician_content(result)
            paths = build_bilingual_reports(
                patient_content=patient_content,
                clinician_content=clinician_content,
                output_dir=case_dir,
                case_id=args.case_id,
                device=result.device_id.get("device_type", "pmdi").lower().replace("-", "_"),
            )
            for k, p in paths.items():
                print(f"  PDF ({k}): {p}")
        except Exception as e:
            print(f"WARNING: PDF generation failed: {e}", file=sys.stderr)

    print(f"\n✓ Analysis complete. Outputs in: {case_dir}")
    return 0


def _build_patient_content(result) -> dict:
    """Map PipelineResult to patient PDF content schema."""
    final = result.final_score
    fa = result.final_score
    return {
        "case_id": result.case_id,
        "evaluation_date": result.metadata.get("started_at", "")[:10],
        "device_type": result.device_id.get("device_type", "unknown"),
        "final_verdict": final["final_verdict"],
        "core_score": final["score_components"]["core_steps_total"],
        "core_max": final["score_components"]["core_steps_max"],
        "core_percent": final["score_components"]["core_steps_percent"],
        "kappa": result.kappa_stats["kappa"]["linear_weighted"],
        "kappa_interpretation_ko": result.kappa_stats["kappa"]["interpretation_linear"],
        "kappa_interpretation_en": result.kappa_stats["kappa"]["interpretation_linear"],
        "critical_errors_patient_friendly": [],
        "strengths_ko": [],  # User should populate via separate call to LLM for narrative
        "strengths_en": [],
        "improvements_ko": [],
        "improvements_en": [],
        "followup_recommendation_ko": "다음 진료 시 의료진과 함께 결과를 확인해 주세요.",
        "followup_recommendation_en": "Please review the results with your healthcare team at your next visit.",
    }


def _build_clinician_content(result) -> dict:
    """Map PipelineResult to clinician PDF content schema."""
    final = result.final_score
    ka = result.kappa_stats
    md = result.metadata
    return {
        "case_id": result.case_id,
        "evaluation_date": md.get("started_at", ""),
        "device_type": result.device_id.get("device_type", "unknown"),
        "final_verdict": final["final_verdict"],
        "core_score": final["score_components"]["core_steps_total"],
        "core_max": final["score_components"]["core_steps_max"],
        "core_percent": final["score_components"]["core_steps_percent"],
        "critical_errors": final["critical_error_override"]["critical_errors"],
        "kappa": ka["kappa"]["linear_weighted"],
        "kappa_interpretation_ko": ka["kappa"]["interpretation_linear"],
        "kappa_interpretation_en": ka["kappa"]["interpretation_linear"],
        "tie_breaker_invoked": result.tie_breaker is not None,
        "clinician_review_priority": (
            "high" if ka["kappa"]["linear_weighted"] < 0.6
            else "moderate" if ka["kappa"]["linear_weighted"] < 0.8
            else "low"
        ),
        "per_step_breakdown": [
            {
                "step_id": p["step_id"],
                "a_level": p["evaluator_a_level"],
                "b_level": p["evaluator_b_level"],
                "tb_level": "-",
                "consensus_level": final["per_step_levels"].get(p["step_id"], "-"),
                "agreement_label": p["agreement"],
            }
            for p in ka["per_step_agreement"]
        ],
        "metadata": {
            "models_used": {s["stage_name"]: s.get("model_used", "?")
                            for s in md.get("stages", []) if s.get("model_used")},
            "stage_durations_ms": {s["stage_name"]: s["duration_ms"]
                                    for s in md.get("stages", []) if s["duration_ms"] > 0},
            "started_at": md.get("started_at", ""),
            "completed_at": md.get("completed_at", ""),
            "total_duration_sec": round(md.get("total_duration_ms", 0) / 1000, 1),
        },
    }


if __name__ == "__main__":
    sys.exit(main())
