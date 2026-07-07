"""Vision telemetry extractor — MediaPipe-based landmarks at fixed sampling intervals.

Extracts five visual indicators per frame:
  - lip_distance_px:           inter-lip vertical distance (mouth seal)
  - head_pitch_deg:            head forward-tilt angle (airway position)
  - index_finger_acceleration: dominant index finger Y-acceleration (actuation)
  - wrist_zero_crossing_rate:  wrist Y-velocity sign changes (shaking validation)
  - chest_expansion_ratio:     shoulder-width relative to baseline (inhalation depth)

All quantities are derived from MediaPipe FaceMesh + Hands + Pose landmarks.

Note: MediaPipe is a ~30MB optional dependency. Install via:
    pip install camca[telemetry]
"""
from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from typing import Any

from .thresholds import SAMPLE_INTERVAL_MS


def _ensure_mediapipe():
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        return cv2, mp, np
    except ImportError:
        raise ImportError(
            "mediapipe / opencv-python not installed. "
            "Install with: pip install camca[telemetry]"
        )


# MediaPipe landmark indices we use
LIP_UPPER_IDX = 13
LIP_LOWER_IDX = 14
NOSE_TIP_IDX = 1
CHIN_IDX = 152
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
INDEX_FINGER_TIP = 8  # Hands landmark
WRIST = 0             # Hands landmark


class VisionTelemetryExtractor:
    """Extracts per-sample vision telemetry from a video.

    Usage:
        extractor = VisionTelemetryExtractor()
        samples = extractor.extract("patient.mp4", sample_interval_ms=100)
    """

    def __init__(self):
        cv2, mp, np = _ensure_mediapipe()
        self._cv2, self._mp, self._np = cv2, mp, np
        self._face = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=False
        )
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False, max_num_hands=2
        )
        self._pose = mp.solutions.pose.Pose(static_image_mode=False)

        # State for velocity/acceleration tracking
        self._prev_index_y: float | None = None
        self._prev_index_vy: float | None = None
        self._wrist_y_history: deque = deque(maxlen=5)
        self._shoulder_width_baseline: float | None = None
        # v0.2.1: finger acceleration smoothing
        self._accel_history: deque = deque(maxlen=3)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._face.close()
        self._hands.close()
        self._pose.close()

    # ---- Single-frame metrics ----

    def lip_distance_px(self, frame_rgb) -> float:
        results = self._face.process(frame_rgb)
        if not results.multi_face_landmarks:
            return 0.0
        lm = results.multi_face_landmarks[0].landmark
        h, w = frame_rgb.shape[:2]
        u = lm[LIP_UPPER_IDX]
        l = lm[LIP_LOWER_IDX]
        return float(math.hypot((u.x - l.x) * w, (u.y - l.y) * h))

    def head_pitch_deg(self, frame_rgb) -> float:
        """Estimate head pitch angle in clinical degrees.

        v0.2.1 fix: previous calculation used unnormalized z-coordinate giving
        values 100-118° for neutral pose. Corrected to use image-space nose-chin
        vector with empirical baseline offset, mapping neutral forward gaze to ~0°.

        Range:
          - 0° ± 5°: forward gaze (neutral)
          - +10° to +20°: slight chin-up (optimal pMDI inhalation airway)
          - +30°+: excessive chin-up (airway suboptimal)
          - negative: chin-down (airway compromised)
        """
        results = self._face.process(frame_rgb)
        if not results.multi_face_landmarks:
            return 0.0
        lm = results.multi_face_landmarks[0].landmark
        h, w = frame_rgb.shape[:2]
        nose = lm[NOSE_TIP_IDX]
        chin = lm[CHIN_IDX]
        # Use normalized image-space vector + reference length (face height ~0.15 of frame)
        dy_norm = chin.y - nose.y  # normalized [0,1]
        # Reference: neutral pose has dy_norm ≈ 0.12 (face oriented forward)
        # Pitch (degrees): scale residual deviation from reference, sign convention
        # positive = chin up (face raised), negative = chin down
        REFERENCE_DY_NORMAL = 0.12
        SCALE_DEG_PER_NORM = 250.0  # empirical calibration: ±0.04 norm ≈ ±10°
        pitch = (REFERENCE_DY_NORMAL - dy_norm) * SCALE_DEG_PER_NORM
        return float(round(pitch, 1))

    def chest_expansion_ratio(self, frame_rgb) -> float:
        results = self._pose.process(frame_rgb)
        if not results.pose_landmarks:
            return 1.0
        lm = results.pose_landmarks.landmark
        left = lm[LEFT_SHOULDER]
        right = lm[RIGHT_SHOULDER]
        h, w = frame_rgb.shape[:2]
        width_px = math.hypot((left.x - right.x) * w, (left.y - right.y) * h)
        if self._shoulder_width_baseline is None:
            self._shoulder_width_baseline = width_px
            return 1.0
        if self._shoulder_width_baseline > 0:
            return round(width_px / self._shoulder_width_baseline, 3)
        return 1.0

    def index_finger_acceleration(self, frame_rgb, dt_sec: float) -> float:
        """Y-axis acceleration of dominant index finger (px/sec²).

        Positive = moving down (canister press direction). Returns 0 if hand not detected.
        """
        results = self._hands.process(frame_rgb)
        if not results.multi_hand_landmarks:
            self._prev_index_y = None
            self._prev_index_vy = None
            return 0.0
        # Use the first detected hand
        lm = results.multi_hand_landmarks[0].landmark
        h, _ = frame_rgb.shape[:2], None
        index_y_px = lm[INDEX_FINGER_TIP].y * h

        if self._prev_index_y is None or dt_sec <= 0:
            self._prev_index_y = index_y_px
            self._prev_index_vy = 0.0
            return 0.0
        vy = (index_y_px - self._prev_index_y) / dt_sec  # px/sec
        ay = (vy - (self._prev_index_vy or 0.0)) / dt_sec  # px/sec²
        self._prev_index_y = index_y_px
        self._prev_index_vy = vy
        # v0.2.1 fix: 3-frame moving average to reduce noise
        self._accel_history.append(ay)
        smoothed = sum(self._accel_history) / len(self._accel_history)
        return round(float(smoothed), 1)

    def wrist_zero_crossing_rate(self, frame_rgb) -> int:
        """Count zero-crossings of wrist Y-velocity over recent 5 samples (~500ms)."""
        results = self._hands.process(frame_rgb)
        if not results.multi_hand_landmarks:
            return 0
        wrist_y = results.multi_hand_landmarks[0].landmark[WRIST].y
        self._wrist_y_history.append(wrist_y)
        if len(self._wrist_y_history) < 3:
            return 0
        velocities = [
            self._wrist_y_history[i + 1] - self._wrist_y_history[i]
            for i in range(len(self._wrist_y_history) - 1)
        ]
        # Count sign changes
        crossings = 0
        for i in range(1, len(velocities)):
            if (velocities[i - 1] > 0 and velocities[i] < 0) or \
               (velocities[i - 1] < 0 and velocities[i] > 0):
                crossings += 1
        return crossings

    def hand_mouth_distance_px(self, frame_rgb) -> float:
        """검지 끝과 입 중심 사이 픽셀 거리. 얼굴/손 미검출 시 0.0 (unknown)."""
        face = self._face.process(frame_rgb)
        hands = self._hands.process(frame_rgb)
        if not face.multi_face_landmarks or not hands.multi_hand_landmarks:
            return 0.0
        h, w = frame_rgb.shape[:2]
        flm = face.multi_face_landmarks[0].landmark
        mouth_x = (flm[LIP_UPPER_IDX].x + flm[LIP_LOWER_IDX].x) / 2 * w
        mouth_y = (flm[LIP_UPPER_IDX].y + flm[LIP_LOWER_IDX].y) / 2 * h
        tip = hands.multi_hand_landmarks[0].landmark[INDEX_FINGER_TIP]
        return float(round(math.hypot(tip.x * w - mouth_x, tip.y * h - mouth_y), 1))

    # ---- Full video extraction ----

    def extract(
        self,
        video_path: Path | str,
        sample_interval_ms: int = SAMPLE_INTERVAL_MS,
    ) -> list[dict[str, Any]]:
        """Extract telemetry samples from the entire video.

        Returns a list of dicts, one per sample interval:
            {
                "timestamp_ms": int,
                "lip_distance_px": float,
                "head_pitch_deg": float,
                "index_finger_acceleration": float,
                "wrist_zero_crossing_rate": int,
                "chest_expansion_ratio": float,
            }
        """
        cv2 = self._cv2
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(fps * sample_interval_ms / 1000))
        dt_sec = frame_interval / fps

        samples: list[dict[str, Any]] = []
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % frame_interval == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ts_ms = int((frame_idx / fps) * 1000)
                samples.append({
                    "timestamp_ms": ts_ms,
                    "lip_distance_px": round(self.lip_distance_px(rgb), 1),
                    "head_pitch_deg": round(self.head_pitch_deg(rgb), 1),
                    "index_finger_acceleration": self.index_finger_acceleration(rgb, dt_sec),
                    "wrist_zero_crossing_rate": self.wrist_zero_crossing_rate(rgb),
                    "chest_expansion_ratio": self.chest_expansion_ratio(rgb),
                    "hand_mouth_distance_px": self.hand_mouth_distance_px(rgb),
                })
            frame_idx += 1

        cap.release()
        return samples


def extract_vision_telemetry(
    video_path: Path | str,
    sample_interval_ms: int = SAMPLE_INTERVAL_MS,
) -> list[dict[str, Any]]:
    """Convenience wrapper — extract vision telemetry from a video file."""
    with VisionTelemetryExtractor() as extractor:
        return extractor.extract(video_path, sample_interval_ms)
