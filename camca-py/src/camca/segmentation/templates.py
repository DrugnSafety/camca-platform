"""Canonical step 템플릿 — 각 step이 어떤 telemetry 이벤트로 anchor되는지 정의.

anchor_events가 빈 step은 telemetry-blind → Stage 2 VLM이 채운다 (needs_vlm).
S6(흡입 지속)은 S5 inhalation_onset ~ S7 breath_hold 사이 구간으로 유도되므로
derived_between으로 표기한다.
"""

PMDI_TEMPLATE = [
    {"step_id": "S1", "label": "Shake the inhaler",
     "anchor_events": ["shake"]},
    {"step_id": "S2", "label": "Remove cap and inspect",
     "anchor_events": []},
    {"step_id": "S3", "label": "Exhale gently away from inhaler",
     "anchor_events": []},
    {"step_id": "S4", "label": "Place mouthpiece in mouth with lip seal",
     "anchor_events": ["hand_to_mouth", "lip_seal"]},
    {"step_id": "S5", "label": "Begin slow inhalation AND press canister simultaneously",
     "anchor_events": ["inhalation_onset", "actuation"]},
    {"step_id": "S6", "label": "Continue slow deep inhalation to full lung capacity",
     "anchor_events": [], "derived_between": ("S5", "S7")},
    {"step_id": "S7", "label": "Hold breath 10 sec, then exhale slowly",
     "anchor_events": ["breath_hold", "mouth_removal"]},
    {"step_id": "S8", "label": "Rinse mouth (ICS only)",
     "anchor_events": []},
    {"step_id": "S9", "label": "Replace cap and store",
     "anchor_events": []},
]

TURBUHALER_TEMPLATE = [
    {"step_id": "T1", "label": "Unscrew and remove cover", "anchor_events": []},
    {"step_id": "T2", "label": "Hold upright and twist grip until click",
     "anchor_events": []},  # click은 audio 이벤트 — Phase 2에서 추가
    {"step_id": "T3", "label": "Exhale gently away from inhaler", "anchor_events": []},
    {"step_id": "T4", "label": "Place mouthpiece in mouth with lip seal",
     "anchor_events": ["hand_to_mouth", "lip_seal"]},
    {"step_id": "T5", "label": "Inhale forcefully and deeply",
     "anchor_events": ["inhalation_onset"]},
    {"step_id": "T6", "label": "Remove inhaler while holding breath",
     "anchor_events": ["mouth_removal"]},
    {"step_id": "T7", "label": "Hold breath 10 sec, then exhale slowly",
     "anchor_events": ["breath_hold"]},
]


def get_template(device_type: str) -> list[dict]:
    """device_type prefix로 템플릿 선택 (pMDI 계열은 모두 PMDI_TEMPLATE)."""
    if device_type.lower().startswith("dpi") or "turbuhaler" in device_type.lower():
        return TURBUHALER_TEMPLATE
    return PMDI_TEMPLATE
