"""클라우드 전송 전 얼굴 블러 — detector 주입으로 mediapipe 없이 검증."""
import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from camca_web.anonymizer import anonymize_video


@pytest.fixture
def tiny_video(tmp_path):
    """8프레임 64x64 합성 영상 — 중앙에 밝은 사각형(가짜 얼굴)."""
    path = tmp_path / "src.mp4"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (64, 64))
    for _ in range(8):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        frame[16:48, 16:48] = 255
        w.write(frame)
    w.release()
    return path


def fake_detector(frame_rgb):
    return [(16, 16, 32, 32)]


def test_anonymize_blurs_face_region(tiny_video, tmp_path):
    dst = tmp_path / "anon.mp4"
    result = anonymize_video(tiny_video, dst, face_detector=fake_detector)
    assert dst.exists()
    assert result.total_frames == 8
    assert result.blurred_frames == 8
    cap = cv2.VideoCapture(str(dst))
    ok, frame = cap.read()
    cap.release()
    assert ok
    # 블러 후 얼굴 영역은 원본(전부 255)보다 분산이 생기고 경계가 흐려짐
    face = frame[20:44, 20:44]
    assert float(face.std()) > 0.0 or int(face.mean()) < 255


def test_no_detection_counts_zero_blur(tiny_video, tmp_path):
    result = anonymize_video(tiny_video, tmp_path / "anon2.mp4",
                             face_detector=lambda f: [])
    assert result.total_frames == 8
    assert result.blurred_frames == 0
