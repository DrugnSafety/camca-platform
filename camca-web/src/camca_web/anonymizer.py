"""PIPA 방어 경계 — 원본은 로컬에만, 클라우드에는 이 모듈의 산출물만 나간다.

MediaPipe FaceDetection으로 얼굴 bbox를 찾아 가우시안 블러. detector는
주입 가능해 CI에서는 mediapipe 없이 fake detector로 검증한다.

Coverage 시맨틱: ``blur_coverage`` 는 "얼굴이 1개 이상 검출되어 블러 처리된
프레임 수 / 전체 프레임 수" 이다. 이는 "모든 프레임이 블러됐는가"를 의미하지
않는다 — 프레임에 얼굴이 전혀 없는 것은 정상이므로 blurred == total 을
강제하면 안 된다. 클라우드 경계에 이 모듈을 사용하는 호출자는 반드시
``min_coverage`` 를 설정하거나, 설정하지 않을 경우 ``AnonymizeResult.blur_coverage``
를 감사(audit)하여 검출 실패로 인한 미블러 프레임 유출이 없는지 확인해야 한다.

오디오: cv2.VideoWriter 는 비디오만 기록하며 산출물에는 오디오 트랙이 없다.
이는 의도된 동작이다 — 오디오 기반 텔레메트리(예: 흡입 사운드 분석)는 반드시
이 블러 처리 이전에 원본(로컬) 영상에서 추출해야 하며, 원본 오디오는 절대
클라우드로 전송되지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Detector = Callable[["object"], list[tuple[int, int, int, int]]]


class AnonymizationCoverageError(ValueError):
    """blur_coverage가 min_coverage 미만일 때 발생 — 산출물은 삭제된 상태다."""

    def __init__(self, coverage: float, min_coverage: float):
        self.coverage = coverage
        self.min_coverage = min_coverage
        super().__init__(
            f"blur_coverage={coverage:.4f} is below min_coverage={min_coverage:.4f}; "
            "output file was deleted"
        )


@dataclass
class AnonymizeResult:
    output_path: Path
    total_frames: int
    blurred_frames: int

    @property
    def blur_coverage(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return self.blurred_frames / self.total_frames


def _mediapipe_detector() -> Detector:
    try:
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError(
            "mediapipe is not installed. Install it with "
            "pip install 'camca-web[anonymizer]', or inject a face_detector."
        ) from exc
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
                    face_detector: Detector | None = None,
                    min_coverage: float | None = None) -> AnonymizeResult:
    import cv2

    detector = face_detector or _mediapipe_detector()
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out = cv2.VideoWriter(str(dst), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    total = blurred = 0
    try:
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
                        # 블러 커널을 얼굴 크기에 비례시킨다 (고정 커널은 큰
                        # 얼굴에서 식별 가능한 잔여 디테일을 남길 수 있다).
                        k = max(31, (max(bw, bh) // 2) * 2 + 1)
                        sigma = k / 3
                        frame[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (k, k), sigma)
            out.write(frame)
    finally:
        cap.release()
        out.release()

    result = AnonymizeResult(output_path=Path(dst), total_frames=total,
                             blurred_frames=blurred)

    if min_coverage is not None and result.blur_coverage < min_coverage:
        coverage = result.blur_coverage
        Path(dst).unlink(missing_ok=True)
        raise AnonymizationCoverageError(coverage, min_coverage)

    return result
