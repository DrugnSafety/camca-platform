"""Telemetry pipeline — combines vision + audio extraction into unified 0.1s stream.

Output schema (Pydantic-compatible):
    {
      "timestamp_ms": int,
      "audio_energy_db": float,
      "lip_distance_px": float,
      "head_pitch_deg": float,
      "index_finger_acceleration": float,
      "wrist_zero_crossing_rate": int,
      "chest_expansion_ratio": float,
      "hand_mouth_distance_px": float
    }
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .thresholds import SAMPLE_INTERVAL_MS, AUDIO_BASELINE_DB


TELEMETRY_KEYS = [
    "timestamp_ms",
    "audio_energy_db",
    "lip_distance_px",
    "head_pitch_deg",
    "index_finger_acceleration",
    "wrist_zero_crossing_rate",
    "chest_expansion_ratio",
    "hand_mouth_distance_px",
]


@dataclass
class TelemetrySample:
    """Single 0.1s telemetry sample."""
    timestamp_ms: int
    audio_energy_db: float
    lip_distance_px: float
    head_pitch_deg: float
    index_finger_acceleration: float
    wrist_zero_crossing_rate: int
    chest_expansion_ratio: float
    hand_mouth_distance_px: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_telemetry(
    video_path: Path | str,
    sample_interval_ms: int = SAMPLE_INTERVAL_MS,
    skip_vision: bool = False,
    skip_audio: bool = False,
) -> list[dict[str, Any]]:
    """Extract combined vision + audio telemetry from a video.

    Args:
        video_path: Input .mp4 (or any ffmpeg-readable video)
        sample_interval_ms: Sampling rate (default 100ms = 10Hz)
        skip_vision: If True, skip MediaPipe — vision fields filled with neutral values
        skip_audio: If True, skip librosa — audio field filled with baseline

    Returns:
        List of telemetry sample dicts, one per sample interval, time-aligned.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    # Vision extraction (optional)
    if skip_vision:
        vision_samples = []
    else:
        from .mediapipe_extractor import extract_vision_telemetry
        vision_samples = extract_vision_telemetry(video_path, sample_interval_ms)

    # Audio extraction (optional)
    if skip_audio:
        audio_db_series = []
    else:
        from .audio_extractor import extract_audio_energy_db, smooth_db_series
        audio_db_series = smooth_db_series(
            extract_audio_energy_db(video_path, sample_interval_ms)
        )

    # Align by timestamp_ms — vision is authoritative; merge audio by nearest match
    audio_lookup = {ts: db for ts, db in audio_db_series}

    if vision_samples:
        # Vision-led merge
        merged: list[dict[str, Any]] = []
        for s in vision_samples:
            ts = s["timestamp_ms"]
            merged.append({
                "timestamp_ms": ts,
                "audio_energy_db": audio_lookup.get(ts, AUDIO_BASELINE_DB),
                **{k: v for k, v in s.items() if k != "timestamp_ms"},
            })
        return merged
    elif audio_db_series:
        # Audio-only (no vision available or skipped)
        return [
            {
                "timestamp_ms": ts,
                "audio_energy_db": db,
                "lip_distance_px": 0.0,
                "head_pitch_deg": 0.0,
                "index_finger_acceleration": 0.0,
                "wrist_zero_crossing_rate": 0,
                "chest_expansion_ratio": 1.0,
                "hand_mouth_distance_px": 0.0,
            }
            for ts, db in audio_db_series
        ]
    else:
        # Nothing extracted
        return []


def compact_telemetry_for_prompt(
    samples: list[dict[str, Any]],
    target_interval_ms: int = 250,
    field_renames: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Downsample + optionally rename fields for token-efficient VLM prompts.

    The 100ms native sampling produces a long array. For VLM prompts, downsampling
    to 250ms (4Hz) typically preserves clinical information while reducing tokens
    by 60%.

    Args:
        samples: Original 100ms telemetry
        target_interval_ms: Target sampling interval (default 250ms)
        field_renames: Optional dict of {original_key: short_key} for token savings
    """
    if not samples:
        return []

    native_interval = samples[1]["timestamp_ms"] - samples[0]["timestamp_ms"] if len(samples) > 1 else 100
    if target_interval_ms <= native_interval:
        return samples

    stride = max(1, target_interval_ms // native_interval)
    downsampled = samples[::stride]

    if field_renames:
        return [{field_renames.get(k, k): v for k, v in s.items()} for s in downsampled]
    return downsampled
