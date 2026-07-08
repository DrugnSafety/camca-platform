"""PIPA 방어 경계 — 원본은 로컬에만, 클라우드에는 이 모듈의 산출물만 나간다.

MediaPipe FaceDetection으로 얼굴 bbox를 찾아 가우시안 블러. detector는
주입 가능해 CI에서는 mediapipe 없이 fake detector로 검증한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Detector = Callable[["object"], list[tuple[int, int, int, int]]]


@dataclass
class AnonymizeResult:
    output_path: Path
    total_frames: int
    blurred_frames: int


def _mediapipe_detector() -> Detector:
    import mediapipe as mp
    fd = mp.solutions.face_detection.FaceDetection(model_selection=1,
                                                   min_detection_confidence=0.4)

    def detect(frame_rgb):
        res = fd.process(frame_rgb)
        boxes = []
        if res.detections:
            h, w = frame_rgb.shape[:2]
            for d in res.detections:
                bb = d.location_data.relative_bounding_box
                boxes.append((int(bb.xmin * w), int(bb.ymin * h),
                              int(bb.width * w), int(bb.height * h)))
        return boxes

    return detect


def anonymize_video(src: Path | str, dst: Path | str,
                    face_detector: Detector | None = None) -> AnonymizeResult:
    import cv2

    detector = face_detector or _mediapipe_detector()
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out = cv2.VideoWriter(str(dst), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    total = blurred = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        total += 1
        boxes = detector(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if boxes:
            blurred += 1
            for (x, y, bw, bh) in boxes:
                # 여유 마진 20% — bbox가 얼굴보다 작게 잡히는 경우 대비
                mx, my = int(bw * 0.2), int(bh * 0.2)
                x0, y0 = max(0, x - mx), max(0, y - my)
                x1, y1 = min(w, x + bw + mx), min(h, y + bh + my)
                if x1 > x0 and y1 > y0:
                    roi = frame[y0:y1, x0:x1]
                    frame[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (51, 51), 30)
        out.write(frame)
    cap.release()
    out.release()
    return AnonymizeResult(output_path=Path(dst), total_frames=total,
                           blurred_frames=blurred)
