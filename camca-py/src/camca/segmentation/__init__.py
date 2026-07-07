"""Phase Recognition Engine — telemetry-anchored hybrid segmentation (v0.4.0)."""
from .events import PhaseEvent, detect_events
from .alignment import align_events_to_steps
from .templates import get_template, PMDI_TEMPLATE, TURBUHALER_TEMPLATE
from .engine import PhaseRecognitionEngine
from .metrics import mean_absolute_boundary_error_sec, overlap_violations

__all__ = [
    "PhaseEvent", "detect_events", "align_events_to_steps",
    "get_template", "PMDI_TEMPLATE", "TURBUHALER_TEMPLATE",
    "PhaseRecognitionEngine",
    "mean_absolute_boundary_error_sec", "overlap_violations",
]
