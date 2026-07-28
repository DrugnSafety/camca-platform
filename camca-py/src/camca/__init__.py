"""CAMCA — Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique.

Python package for video-based inhaler technique evaluation with multi-model
(Claude / Gemini / local Ollama) dual-agent comparison and Cohen's kappa
inter-rater reliability scoring.

Quick start:

    from camca import create_backend, PersonaConfig, MultiModelPipeline

    pipeline = MultiModelPipeline(
        device_id_backend=create_backend("claude:sonnet"),
        segmenter_backend=create_backend("claude:sonnet"),
        evaluator_a=PersonaConfig("A", "GINA-strict", create_backend("claude:opus")),
        evaluator_b=PersonaConfig("B", "real-world-pragmatic", create_backend("gemini:pro")),
    )
    result = pipeline.run_from_video("patient.mp4", case_id="DEMO-001")

For details: https://github.com/drugnsafety/camca
"""

__version__ = "0.3.0"

from .backends import (
    VLMBackend,
    ClaudeBackend,
    GeminiBackend,
    OllamaBackend,
    BackendError,
    create_backend,
)
from .pipeline import MultiModelPipeline, PersonaConfig, PipelineResult
from .scoring import (
    cohens_kappa,
    weighted_kappa,
    interpret_kappa,
    compute_stats,
    compute_final_score,
)
from .reports import (
    build_patient_pdf,
    build_clinician_pdf,
    build_bilingual_reports,
)
from .resources import (
    skill_text,
    font_path,
    static_guide_path,
    available_skills,
)
from .schemas import (
    VLMClinicalReport,
    StepEvaluation,
    CriticalErrorDetection,
    EvaluationSummary,
    DeviceIdReport,
    can_enforce_schema,
)

# Telemetry is optional — import lazily via camca.telemetry
__all__ = [
    # Backends
    "VLMBackend", "ClaudeBackend", "GeminiBackend", "OllamaBackend",
    "BackendError", "create_backend",
    # Pipeline
    "MultiModelPipeline", "PersonaConfig", "PipelineResult",
    # Scoring
    "cohens_kappa", "weighted_kappa", "interpret_kappa",
    "compute_stats", "compute_final_score",
    # Reports
    "build_patient_pdf", "build_clinician_pdf", "build_bilingual_reports",
    # Resources
    "skill_text", "font_path", "static_guide_path", "available_skills",
    # Schemas (P4)
    "VLMClinicalReport", "StepEvaluation", "CriticalErrorDetection",
    "EvaluationSummary", "DeviceIdReport", "can_enforce_schema",
]
