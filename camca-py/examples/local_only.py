"""On-premise / privacy-sensitive mode: all backends via local Ollama.

No data leaves the local network — suitable for Korean PIPA-compliant patient
data, hospital-only deployments, or research where cloud transmission is restricted.

Prerequisites:
    pip install camca
    ollama pull gemma3:4b
    ollama pull gemma3:27b
    # Optional: ollama pull qwen2.5vl:32b
"""
import sys
from pathlib import Path

from camca import create_backend, PersonaConfig, MultiModelPipeline


def main(video_path: str, case_id: str = "LOCAL-001"):
    pipeline = MultiModelPipeline(
        device_id_backend=create_backend("ollama:gemma3:4b"),     # fast, small
        segmenter_backend=create_backend("ollama:gemma3:12b"),    # mid
        evaluator_a=PersonaConfig(
            "evaluator-a", "GINA-strict",
            create_backend("ollama:gemma3:27b"),                  # best local quality
        ),
        evaluator_b=PersonaConfig(
            "evaluator-b", "real-world-pragmatic",
            create_backend("ollama:qwen2.5vl:32b"),               # different family for diversity
        ),
        tie_breaker=PersonaConfig(
            "tie-breaker", "clinical-pharmacy-educator",
            create_backend("ollama:gemma3:27b"),
        ),
        case_dir=Path(f"./camca_logs/{case_id}"),
    )

    result = pipeline.run_from_video(Path(video_path), case_id=case_id)
    print(f"\n✓ Local-only analysis complete: {result.final_score['final_verdict']}")
    print(f"  All data remained on this machine.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "patient.mp4")
