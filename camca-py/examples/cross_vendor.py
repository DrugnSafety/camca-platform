"""Cross-vendor dual evaluation: Claude Opus (strict) vs Gemini Pro (pragmatic)
with local Gemma3 as tie-breaker.

Strongest research-grade configuration for IRB/publication.

Prerequisites:
    pip install "camca[all]"
    export ANTHROPIC_API_KEY="sk-ant-..."
    export GOOGLE_API_KEY="AIza..."
    ollama pull gemma3:27b
"""
import sys
from pathlib import Path

from camca import create_backend, PersonaConfig, MultiModelPipeline


def main(video_path: str, case_id: str = "CROSS-001"):
    pipeline = MultiModelPipeline(
        device_id_backend=create_backend("claude:sonnet"),
        segmenter_backend=create_backend("gemini:flash"),
        evaluator_a=PersonaConfig(
            "evaluator-a", "GINA-strict",
            create_backend("claude:opus"),
        ),
        evaluator_b=PersonaConfig(
            "evaluator-b", "real-world-pragmatic",
            create_backend("gemini:pro"),
        ),
        tie_breaker=PersonaConfig(
            "tie-breaker", "clinical-pharmacy-educator",
            create_backend("ollama:gemma3:27b"),
        ),
        case_dir=Path(f"./camca_logs/{case_id}"),
    )

    result = pipeline.run_from_video(
        Path(video_path),
        case_id=case_id,
        invoke_tie_breaker_threshold=0.6,
    )

    # Quick summary
    a_total = result.evaluator_a.get("summary", {}).get("observable_total_score", "?")
    b_total = result.evaluator_b.get("summary", {}).get("observable_total_score", "?")
    print(f"\nA (Opus+strict): {a_total}, B (Gemini+pragmatic): {b_total}")
    print(f"Tie-breaker invoked: {result.tie_breaker is not None}")
    print(f"Consensus: {result.final_score['final_verdict']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "patient.mp4")
