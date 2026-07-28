"""VLM prompts for the CAMCA pipeline.

Prompts are derived from the original plugin's skills/vlm-prompt-library and
embedded here for self-containedness. Skill text (full checklists, rubrics)
is loaded at runtime from camca.resources.
"""
from __future__ import annotations

from .resources import skill_text


DEVICE_ID_PROMPT = """You are a respiratory medicine specialist identifying inhaler devices.

Examine the provided frames (extracted from an inhaler-use video).

Possible devices (MVP scope):
- pMDI (pressurized metered-dose inhaler): L-shaped, canister + boot, color-coded
- pMDI-spacer: pMDI with attached holding chamber
- DPI-turbuhaler: cylindrical, white cover, colored twist grip at base
- unknown

Output strict JSON only:
{
  "device_type": "<pMDI | pMDI-spacer | DPI-turbuhaler | unknown>",
  "confidence": <0.0-1.0>,
  "rationale": "<one sentence citing specific visual features>",
  "frame_indices_used": [<list of frame numbers>]
}

If confidence < 0.7, recommend user confirmation in the rationale.
"""


SEGMENTATION_PROMPT_TEMPLATE = """You are segmenting an inhaler-use video into canonical evaluation steps.

Device: {device_type}
Step template: {step_template}

For each canonical step, examine the frames and produce:
- start_ts / end_ts (MM:SS.s format)
- frame_indices_representative
- visual_summary (one sentence)
- audio_summary (one sentence; "N/A" if no audio analysis)
- status: "observed" | "missing" | "unobservable" | "ambiguous"

Steps may be missing if the video begins mid-demonstration; use status="unobservable" for those.

Output strict JSON:
{{
  "device_type": "{device_type}",
  "total_duration_sec": <float>,
  "video_segments": [
    {{
      "step_id": "<step_id>",
      "step_name": "<step_name>",
      "status": "<observed|unobservable|ambiguous>",
      "start_ts": "<MM:SS.s>",
      "end_ts": "<MM:SS.s>",
      "frame_indices_representative": [<int>],
      "visual_summary": "<sentence>",
      "audio_summary": "<sentence>",
      "ambiguity_notes": "<sentence or null>"
    }}
  ]
}}
"""


PERSONA_INSTRUCTIONS = {
    "GINA-strict": (
        "You are a board-certified pulmonologist applying GINA 2024 strictly. "
        "When between two levels, choose the LOWER level. Document the specific "
        "protocol deviation. Apply CRITIKAL critical-error definitions exactly. "
        "Do NOT extend leniency to elderly/pediatric patients."
    ),
    "real-world-pragmatic": (
        "You are a clinical pharmacist with 15+ years of patient-facing experience. "
        "When between two levels, choose the HIGHER level IF clinical effect is preserved. "
        "Document why deviation does not compromise effect. "
        "Apply CRITIKAL critical errors as strictly as the other evaluator."
    ),
    "clinical-pharmacy-educator": (
        "You are a clinical pharmacy educator with 25+ years of training-patient experience. "
        "You sit between strict and pragmatic — weighting clinical effect over protocol perfection "
        "but demanding solid evidence. You are the deciding vote when other evaluators disagree."
    ),
}


EVALUATOR_PROMPT_TEMPLATE = """You are evaluating inhaler technique using the CAMCA dual-agent framework.

PERSONA: {persona_label}
{persona_instructions}

DEVICE: {device_type}
CASE ID: {case_id}

CHECKLIST RUBRIC (Levels 0-3, full text follows):
{checklist_summary}

CRITICAL ERROR DEFINITIONS (CRITIKAL-based):
{critical_errors_list}

SEGMENT METADATA (per-step summaries from segmenter):
{segments_json}

QUANTITATIVE TELEMETRY (deterministic measurements from MediaPipe + Audio DSP):
{telemetry_summary}

[CLINICAL INTERPRETATION GUIDANCE]
- Telemetry data above provides ground-truth measurements (timing, dB, distances).
  Use these as anchors for your evaluation — do NOT estimate quantities the
  telemetry already measured.
- For S5 (coordination): see clinical_anchors.S5_coordination_check for the
  exact actuation-to-inhalation gap; classify CRIT-pMDI-04 based on this.
- For S7 (breath-hold): see clinical_anchors.S7_breath_hold_check; the audio
  dB drop is more reliable than visual chest motion.
- If telemetry is empty, fall back to frame-based estimation and lower confidence.

For each step in the device's checklist, evaluate using the provided frames and segments.
Apply the rubric strictly to your persona.

Output strict JSON conforming to this schema:
{{
  "evaluator": "<A or B>",
  "evaluator_persona": "{persona_label}",
  "model": "{model_id}",
  "case_id": "{case_id}",
  "device_type": "{device_type}",
  "evaluated_at": "<ISO timestamp>",
  "per_step_evaluation": [
    {{
      "step_id": "<id>",
      "step_name": "<name>",
      "level": <0-3 or null>,
      "status": "observed | unobservable",
      "rationale": "<sentence with frame/timestamp evidence>",
      "evidence_frames": [<int>],
      "is_critical_error": <bool>,
      "matched_critical_error_id": <string or null>
    }}
  ],
  "critical_errors_detected": [
    {{"critical_error_id": "<id>", "description": "<text>", "evidence": "<text>"}}
  ],
  "summary": {{
    "observable_steps": <int>,
    "observable_max": <int>,
    "observable_total_score": <int>,
    "observable_percent": <float>,
    "unobservable_steps": [<step_ids>],
    "critical_error_count": <int>,
    "overall_verdict_provisional": "<verdict>"
  }}
}}
"""


STEP_TEMPLATES = {
    "pMDI": [
        "S1 Shake", "S2 Cap", "S3 Exhale away", "S4 Lip seal",
        "S5 Inhalation+actuation coord", "S6 Deep inhalation", "S7 Breath-hold",
        "S8 (ICS) Rinse", "S9 Replace cap",
    ],
    "pMDI-spacer": [
        "S0 Attach spacer", "S1 Shake", "S2 Cap", "S3 Exhale away", "S4 Lip seal",
        "S5 Actuate then breathe", "S6 Deep inhalation", "S7 Breath-hold",
        "S8 (ICS) Rinse", "S9 Replace cap",
    ],
    "DPI-turbuhaler": [
        "T1 Upright+cover", "T2 Twist+click", "T3 Exhale away",
        "T4 Lip seal", "T5 Forceful inhalation", "T6 Deep inhalation",
        "T7 Breath-hold", "T8 (ICS) Rinse", "T9 Replace cover",
    ],
}


def build_evaluator_prompt(
    persona_label: str,
    device_type: str,
    case_id: str,
    model_id: str,
    segments: dict,
    telemetry_summary: dict | None = None,
) -> str:
    """Construct the full evaluator prompt with checklist + critical errors + telemetry.

    Args:
        telemetry_summary: Output of camca.telemetry.compute_telemetry_summary().
                          If None or empty, prompt notes "no telemetry available".
    """
    import json

    device_to_skill = {
        "pMDI": "inhaler-checklist-pmdi",
        "pMDI-spacer": "inhaler-checklist-pmdi",
        "DPI-turbuhaler": "inhaler-checklist-turbuhaler",
    }
    skill_name = device_to_skill.get(device_type, "inhaler-checklist-pmdi")

    try:
        checklist = skill_text(skill_name)
    except FileNotFoundError:
        checklist = f"(Checklist skill '{skill_name}' not bundled.)"

    try:
        critical = skill_text("critical-errors-critikal")
    except FileNotFoundError:
        critical = "(Critical errors skill not bundled.)"

    if telemetry_summary and not telemetry_summary.get("empty"):
        telemetry_str = json.dumps(telemetry_summary, indent=2, ensure_ascii=False)[:3000]
    else:
        telemetry_str = (
            "(No quantitative telemetry available — extract conclusions from "
            "frames and segment metadata only. Lower confidence appropriately.)"
        )

    return EVALUATOR_PROMPT_TEMPLATE.format(
        persona_label=persona_label,
        persona_instructions=PERSONA_INSTRUCTIONS.get(persona_label, ""),
        device_type=device_type,
        case_id=case_id,
        model_id=model_id,
        checklist_summary=checklist[:3500],
        critical_errors_list=critical[:1500],
        segments_json=json.dumps(segments, indent=2, ensure_ascii=False)[:3000],
        telemetry_summary=telemetry_str,
    )


def build_segmentation_prompt(device_type: str) -> str:
    """Construct the segmentation prompt for a given device."""
    steps = STEP_TEMPLATES.get(device_type, [])
    return SEGMENTATION_PROMPT_TEMPLATE.format(
        device_type=device_type,
        step_template=", ".join(steps),
    )
