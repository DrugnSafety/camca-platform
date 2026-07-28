"""VLM ↔ Telemetry reconciliation policy (v0.2.1).

Handles the case where VLM evaluator and telemetry-derived measurements
disagree about the same clinical step. Provides confidence-weighted decisions
and explicit conflict flagging for clinician review.

Real-world example from CAMCA-KIM-001:
  - VLM (Evaluator A+B) estimated S7 breath-hold ≈ 3s → Level 1
  - Algorithm detected 11.3s (confidence 0.3, low) → falsely "adequate"
  - Reconciliation: telemetry_confidence < 0.5 → VLM wins → Level 1 retained
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReconciliationOutcome(Enum):
    AGREE = "agree"                          # Both within 1 level — average
    VLM_WINS = "vlm_wins"                    # Telemetry low confidence
    TELEMETRY_WINS = "telemetry_wins"        # VLM low confidence
    CONFLICT_FLAGGED = "conflict_flagged"    # Both high confidence but disagree ≥2 levels


@dataclass
class ReconciliationResult:
    final_level: int | None
    outcome: ReconciliationOutcome
    rationale: str
    vlm_level: int | None = None
    telemetry_level: int | None = None
    vlm_confidence: float = 0.0
    telemetry_confidence: float = 0.0
    requires_clinician_review: bool = False

    def to_dict(self) -> dict:
        return {
            "final_level": self.final_level,
            "outcome": self.outcome.value,
            "rationale": self.rationale,
            "vlm_level": self.vlm_level,
            "telemetry_level": self.telemetry_level,
            "vlm_confidence": round(self.vlm_confidence, 2),
            "telemetry_confidence": round(self.telemetry_confidence, 2),
            "requires_clinician_review": self.requires_clinician_review,
        }


def reconcile_step_score(
    vlm_level: int | None,
    vlm_confidence: float,
    telemetry_level: int | None,
    telemetry_confidence: float,
    confidence_threshold: float = 0.5,
    conflict_diff_threshold: int = 2,
) -> ReconciliationResult:
    """Reconcile VLM and telemetry-derived level scores for a single step.

    Decision policy:
      1. If telemetry confidence < threshold → trust VLM
      2. If VLM confidence < threshold → trust telemetry
      3. If both confident AND agree (diff ≤ 1) → average them
      4. If both confident AND disagree (diff ≥ conflict_diff_threshold)
         → flag for clinician review, return VLM as conservative default

    Args:
        vlm_level: VLM evaluator's level (0-3) or None if unobservable
        vlm_confidence: 0.0-1.0
        telemetry_level: Telemetry-derived level (0-3) or None if anchor failed
        telemetry_confidence: 0.0-1.0; if anchor failed, set to 0.0
        confidence_threshold: Minimum confidence to trust a source (default 0.5)
        conflict_diff_threshold: Level difference triggering clinician flag (default 2)
    """
    # Both missing → cannot reconcile
    if vlm_level is None and telemetry_level is None:
        return ReconciliationResult(
            final_level=None,
            outcome=ReconciliationOutcome.CONFLICT_FLAGGED,
            rationale="Neither VLM nor telemetry could evaluate this step",
            vlm_confidence=vlm_confidence,
            telemetry_confidence=telemetry_confidence,
            requires_clinician_review=True,
        )

    # Telemetry missing or low confidence → trust VLM
    if telemetry_level is None or telemetry_confidence < confidence_threshold:
        return ReconciliationResult(
            final_level=vlm_level,
            outcome=ReconciliationOutcome.VLM_WINS,
            rationale=(
                f"Telemetry confidence {telemetry_confidence:.2f} below threshold "
                f"{confidence_threshold} (or anchor unavailable). VLM evaluation used."
            ),
            vlm_level=vlm_level,
            telemetry_level=telemetry_level,
            vlm_confidence=vlm_confidence,
            telemetry_confidence=telemetry_confidence,
        )

    # VLM missing or low confidence → trust telemetry
    if vlm_level is None or vlm_confidence < confidence_threshold:
        return ReconciliationResult(
            final_level=telemetry_level,
            outcome=ReconciliationOutcome.TELEMETRY_WINS,
            rationale=(
                f"VLM confidence {vlm_confidence:.2f} below threshold "
                f"{confidence_threshold}. Telemetry-derived value used."
            ),
            vlm_level=vlm_level,
            telemetry_level=telemetry_level,
            vlm_confidence=vlm_confidence,
            telemetry_confidence=telemetry_confidence,
        )

    # Both confident → check agreement
    diff = abs(vlm_level - telemetry_level)
    if diff < conflict_diff_threshold:
        # Average
        final = round((vlm_level + telemetry_level) / 2)
        return ReconciliationResult(
            final_level=final,
            outcome=ReconciliationOutcome.AGREE,
            rationale=(
                f"Both sources confident (VLM {vlm_confidence:.2f}, "
                f"telemetry {telemetry_confidence:.2f}); agree within {diff} level."
            ),
            vlm_level=vlm_level,
            telemetry_level=telemetry_level,
            vlm_confidence=vlm_confidence,
            telemetry_confidence=telemetry_confidence,
        )

    # Both confident but disagree → flag
    return ReconciliationResult(
        final_level=min(vlm_level, telemetry_level),  # conservative: lower level
        outcome=ReconciliationOutcome.CONFLICT_FLAGGED,
        rationale=(
            f"Both sources high confidence but disagree by {diff} levels "
            f"(VLM={vlm_level}, telemetry={telemetry_level}). Conservative lower "
            f"value used; clinician review required."
        ),
        vlm_level=vlm_level,
        telemetry_level=telemetry_level,
        vlm_confidence=vlm_confidence,
        telemetry_confidence=telemetry_confidence,
        requires_clinician_review=True,
    )


# ---------- Telemetry → Level conversion helpers ----------

def breath_hold_to_level(duration_ms: int) -> tuple[int, float]:
    """Convert measured breath-hold duration to GINA Level 0-3 + confidence.

    Returns (level, confidence).
    """
    if duration_ms is None or duration_ms <= 0:
        return 0, 0.0
    if duration_ms >= 10000:
        return 3, 0.9
    if duration_ms >= 5000:
        return 2, 0.85
    if duration_ms >= 1000:
        return 1, 0.80
    return 0, 0.85


def lip_seal_to_level(distance_px: float | None) -> tuple[int, float]:
    """Convert measured lip distance to Level 0-3 + confidence."""
    if distance_px is None:
        return 0, 0.0
    if distance_px <= 5.0:
        return 3, 0.9
    if distance_px <= 10.0:
        return 2, 0.85
    if distance_px <= 20.0:
        return 1, 0.75
    return 0, 0.85


def chest_expansion_to_level(expansion_pct: float | None) -> tuple[int, float]:
    """Convert chest expansion percentage to Level 0-3 + confidence."""
    if expansion_pct is None:
        return 0, 0.0
    if expansion_pct >= 10.0:
        return 3, 0.85
    if expansion_pct >= 5.0:
        return 2, 0.80
    if expansion_pct >= 2.0:
        return 1, 0.75
    return 0, 0.75


def coordination_to_level(gap_ms: int | None) -> tuple[int, float]:
    """Convert actuation-inhalation gap to Level 0-3 + confidence."""
    if gap_ms is None:
        return 0, 0.0  # cannot determine
    abs_gap = abs(gap_ms)
    if abs_gap <= 300:
        return 3, 0.90
    if abs_gap <= 600:
        return 2, 0.85
    if abs_gap <= 1000:
        return 1, 0.80
    return 0, 0.90  # >1000ms = clearly bad
