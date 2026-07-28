"""Audio telemetry extractor — librosa-based RMS dB energy at fixed sampling intervals.

Output: per-100ms audio_energy_db values aligned with vision telemetry.

The key clinical insight (from Gemini CDSS reference): the moment audio_energy_db
drops abruptly to baseline = inhalation end + breath-hold start. This is more
reliable than visual chest expansion (which plateaus before breath-hold).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from .thresholds import SAMPLE_INTERVAL_MS, AUDIO_BASELINE_DB


def _ensure_librosa():
    try:
        import librosa
        import numpy as np
        return librosa, np
    except ImportError:
        raise ImportError(
            "librosa not installed. Install with: pip install camca[telemetry]"
        )


def extract_audio_energy_db(
    video_path: Path | str,
    sample_interval_ms: int = SAMPLE_INTERVAL_MS,
    sr: int = 16000,
) -> list[tuple[int, float]]:
    """Extract per-window RMS energy in dB at the given interval.

    Args:
        video_path: Path to input video (or audio file).
        sample_interval_ms: Sampling interval in milliseconds (default 100ms).
        sr: Target sample rate for audio loading.

    Returns:
        List of (timestamp_ms, audio_energy_db) tuples spanning the entire file.
        Empty audio windows return baseline dB value (typically 35).
    """
    librosa, np = _ensure_librosa()
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Audio source not found: {video_path}")

    # librosa.load handles both .mp4 (via audioread) and audio files
    try:
        y, sr = librosa.load(str(video_path), sr=sr, mono=True)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load audio from {video_path}: {e}. "
            "Note: librosa requires ffmpeg or audioread for video formats."
        )

    samples_per_window = int(sr * sample_interval_ms / 1000)
    if samples_per_window == 0:
        return []

    output: list[tuple[int, float]] = []
    n_windows = (len(y) + samples_per_window - 1) // samples_per_window

    for w_idx in range(n_windows):
        start = w_idx * samples_per_window
        end = min(start + samples_per_window, len(y))
        chunk = y[start:end]
        if len(chunk) == 0:
            db = AUDIO_BASELINE_DB
        else:
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            # Convert RMS to dB SPL-style relative value
            # 20 * log10(rms) with epsilon to avoid log(0); add reference offset
            db = 20.0 * math.log10(max(rms, 1e-6)) + 90.0
            db = max(min(db, 120.0), 0.0)  # clamp to plausible range
        output.append((w_idx * sample_interval_ms, round(db, 1)))

    return output


def smooth_db_series(
    db_series: list[tuple[int, float]],
    window_size: int = 3,
) -> list[tuple[int, float]]:
    """Apply moving-average smoothing to reduce single-frame noise.

    Args:
        db_series: Output of extract_audio_energy_db
        window_size: Moving average window (number of samples)
    """
    if len(db_series) < window_size:
        return db_series
    half = window_size // 2
    out = []
    for i, (ts, _) in enumerate(db_series):
        lo = max(0, i - half)
        hi = min(len(db_series), i + half + 1)
        avg = sum(db for _, db in db_series[lo:hi]) / (hi - lo)
        out.append((ts, round(avg, 1)))
    return out


def detect_audio_events(
    db_series: list[tuple[int, float]],
    inhalation_min_db: float = 50.0,
    breath_hold_max_db: float = 40.0,
) -> dict[str, list[int]]:
    """Detect notable audio events (inhalation onset/offset, silence).

    Returns:
        {
            "inhalation_onsets_ms": [list of ms timestamps],
            "inhalation_offsets_ms": [...],
            "silence_periods_ms": [(start_ms, end_ms), ...],
        }
    """
    inh_onsets, inh_offsets = [], []
    silence_periods = []
    in_inhalation = False
    silence_start = None

    for ts, db in db_series:
        if db >= inhalation_min_db and not in_inhalation:
            inh_onsets.append(ts)
            in_inhalation = True
            silence_start = None
        elif db < inhalation_min_db and in_inhalation:
            inh_offsets.append(ts)
            in_inhalation = False
        if db <= breath_hold_max_db:
            if silence_start is None:
                silence_start = ts
        else:
            if silence_start is not None:
                silence_periods.append((silence_start, ts))
                silence_start = None
    if silence_start is not None and db_series:
        silence_periods.append((silence_start, db_series[-1][0]))

    return {
        "inhalation_onsets_ms": inh_onsets,
        "inhalation_offsets_ms": inh_offsets,
        "silence_periods_ms": silence_periods,
    }
