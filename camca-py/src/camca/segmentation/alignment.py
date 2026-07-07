"""Stage 3 — 이벤트 시퀀스를 canonical 템플릿에 정렬해 겹침 없는 세그먼트 생성.

불변조건 (spec §5.4):
  1. 출력은 항상 canonical 순서 (모든 step 포함, 미관측은 observable=False)
  2. observable 세그먼트 간 시간 겹침 0
  3. 각 세그먼트에 boundary_confidence / boundary_source / events 기록

겹침 해소 알고리즘 노트:
  최초 설계는 시간순 인접 쌍의 겹침을 중간점에서 잘라 양쪽 다 줄이는 방식이었다.
  그러나 한 이벤트 구간이 다른 이벤트 구간에 완전히 포함되는 경우(예: lip_seal이
  inhalation_onset+actuation의 짧은 구간을 통째로 감싸는 경우) 중간점 클리핑은
  뒤 세그먼트의 시작을 그 세그먼트의 끝보다 뒤로 밀어버려 구간이 뒤집히는
  버그를 낳는다(반복 루프를 돌려도 해결되지 않음). 대신, 시간순으로 정렬한 뒤
  앞 세그먼트의 끝만 다음 세그먼트의 시작으로 잘라내는 단방향(directional)
  클리핑을 사용한다. 시작 시각은 절대 변경하지 않으므로 단 한 번의 좌→우
  패스만으로 모든 인접 쌍의 "겹침 없음" 불변조건이 항상 성립한다.
"""
from __future__ import annotations

from typing import Any

from .events import PhaseEvent


def _assign_events(events: list[PhaseEvent], template: list[dict]) -> dict[str, list[PhaseEvent]]:
    """각 이벤트를 anchor_events 매핑에 따라 step에 배정. 같은 타입 복수 발생 시 첫 것만."""
    assignment: dict[str, list[PhaseEvent]] = {t["step_id"]: [] for t in template}
    consumed_types: set[str] = set()
    for step in template:
        for ev_type in step["anchor_events"]:
            if ev_type in consumed_types:
                continue
            matches = [e for e in events if e.type == ev_type]
            if matches:
                assignment[step["step_id"]].append(matches[0])
                consumed_types.add(ev_type)
    return assignment


def align_events_to_steps(
    events: list[PhaseEvent],
    template: list[dict],
    video_duration_ms: int,
) -> list[dict[str, Any]]:
    """이벤트 → canonical 세그먼트 목록 (겹침 없음 보장)."""
    assignment = _assign_events(events, template)

    # 1차: 이벤트가 있는 step의 draft 경계
    segments: list[dict[str, Any]] = []
    for step in template:
        evs = assignment[step["step_id"]]
        seg: dict[str, Any] = {
            "step_id": step["step_id"],
            "label": step["label"],
            "observable": bool(evs),
            "needs_vlm": not evs,          # telemetry로 못 본 step은 VLM 확인 대상
            "t_start_ms": min(e.t_start_ms for e in evs) if evs else None,
            "t_end_ms": max(e.t_end_ms for e in evs) if evs else None,
            "boundary_source": "telemetry" if evs else None,
            "boundary_confidence": (
                round(sum(e.confidence for e in evs) / len(evs), 2) if evs else 0.0
            ),
            "events": [e.to_dict() for e in evs],
        }
        segments.append(seg)

    # S6류 derived step: 앞뒤 anchor 사이 구간
    by_id = {s["step_id"]: s for s in segments}
    for step in template:
        if "derived_between" not in step:
            continue
        prev_id, next_id = step["derived_between"]
        prev_s, next_s = by_id.get(prev_id), by_id.get(next_id)
        seg = by_id[step["step_id"]]
        if prev_s and next_s and prev_s["observable"] and next_s["observable"] \
                and prev_s["t_end_ms"] < next_s["t_start_ms"]:
            seg.update(
                observable=True, needs_vlm=False,
                t_start_ms=prev_s["t_end_ms"], t_end_ms=next_s["t_start_ms"],
                boundary_source="telemetry",
                boundary_confidence=round(
                    (prev_s["boundary_confidence"] + next_s["boundary_confidence"]) / 2, 2),
            )

    # 순서 위반 검출: observable step들의 실제 시간이 canonical 순서와 다르면 기록
    observed = [s for s in segments if s["observable"]]
    anchor_times = [s["t_start_ms"] for s in observed]
    if anchor_times != sorted(anchor_times):
        for s, sorted_t in zip(observed, sorted(anchor_times)):
            if s["t_start_ms"] != sorted_t:
                s["order_violation"] = True

    # 겹침 제거: observable 세그먼트를 시간순으로 보고 단방향 클리핑.
    # a(앞)의 끝만 b(뒤)의 시작으로 잘라낸다 — b의 시작은 절대 건드리지 않으므로
    # 좌→우 단일 패스만으로 모든 인접 쌍의 겹침이 해소됨이 보장된다(포함 관계 겹침 포함).
    observed_sorted = sorted(observed, key=lambda s: s["t_start_ms"])
    for a, b in zip(observed_sorted, observed_sorted[1:]):
        if a["t_end_ms"] > b["t_start_ms"]:
            a["t_end_ms"] = b["t_start_ms"]
            a["boundary_confidence"] = round(a["boundary_confidence"] * 0.8, 2)

    # 경계를 영상 범위로 클램프
    for s in segments:
        if s["observable"]:
            s["t_start_ms"] = max(0, min(s["t_start_ms"], video_duration_ms))
            s["t_end_ms"] = max(s["t_start_ms"], min(s["t_end_ms"], video_duration_ms))

    return segments
