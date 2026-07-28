"""Minimal example: Claude-only dual evaluation on a single video.

Prerequisites:
    pip install "camca[claude]"
    export ANTHROPIC_API_KEY="sk-ant-..."

Run:
    python basic_analysis.py /path/to/patient_video.mp4
"""
import sys
from pathlib import Path

from camca import create_backend, PersonaConfig, MultiModelPipeline


def main(video_path: str):
    case_dir = Path("./camca_logs/DEMO-001")

    pipeline = MultiModelPipeline(
        device_id_backend=create_backend("claude:sonnet"),
        segmenter_backend=create_backend("claude:sonnet"),
        evaluator_a=PersonaConfig(
            "evaluator-a", "GINA-strict",
            create_backend("claude:opus"),
        ),
        evaluator_b=PersonaConfig(
            "evaluator-b", "real-world-pragmatic",
            create_backend("claude:sonnet"),
        ),
        case_dir=case_dir,
    )

    result = pipeline.run_from_video(Path(video_path), case_id="DEMO-001")

    print("\n=== Result ===")
    print(f"Device:  {result.device_id['device_type']}")
    print(f"Verdict: {result.final_score['final_verdict']}")
    print(f"Score:   {result.final_score['score_components']['core_steps_total']}"
          f"/{result.final_score['score_components']['core_steps_max']} "
          f"({result.final_score['score_components']['core_steps_percent']}%)")
    print(f"Kappa:   {result.kappa_stats['kappa']['linear_weighted']} "
          f"({result.kappa_stats['kappa']['interpretation_linear']})")
    print(f"\nFiles saved to: {case_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
