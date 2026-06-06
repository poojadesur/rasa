"""Isolate the user's voice by decibel/loudness — no diarization API.

Two stages on the raw audio:
  1. Silence removal: drop spans quieter than an absolute floor (SILENCE_THRESH_DBFS).
  2. Loudness gate: keep only windows within USER_GATE_MARGIN_DB of the peak loudness,
     i.e. the nearest/loudest voice (the phone is on the user). Quieter, more distant
     background speakers fall away.

This is a heuristic: it won't separate two equally-loud speakers. A real diarizer can
be slotted in behind `filter_to_user` later without touching callers.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from ..config import get_settings
from .audioutil import load_segment

_GATE_WINDOW_MS = 300


def _loudness_gate(seg: AudioSegment, margin_db: float) -> AudioSegment:
    if len(seg) == 0:
        return seg
    windows = [seg[i : i + _GATE_WINDOW_MS] for i in range(0, len(seg), _GATE_WINDOW_MS)]
    levels = [w.dBFS for w in windows if w.dBFS != float("-inf")]
    if not levels:
        return seg
    threshold = max(levels) - margin_db
    kept = [w for w in windows if w.dBFS >= threshold]
    if not kept:
        return seg
    out = AudioSegment.empty()
    for w in kept:
        out += w
    return out


def filter_to_user(audio_bytes: bytes, fmt: str | None = None) -> Tuple[AudioSegment, Dict]:
    """Return (filtered_segment, stats)."""
    s = get_settings()
    seg = load_segment(audio_bytes, fmt=fmt).set_channels(1)
    orig_ms = len(seg)

    nonsilent: List[List[int]] = detect_nonsilent(
        seg, min_silence_len=s.min_silence_ms, silence_thresh=s.silence_thresh_dbfs
    )
    if nonsilent:
        speech = AudioSegment.empty()
        for a, b in nonsilent:
            speech += seg[a:b]
    else:
        speech = seg

    gated = _loudness_gate(speech, margin_db=s.user_gate_margin_db)

    stats = {
        "orig_ms": orig_ms,
        "orig_dbfs": round(seg.dBFS, 2) if seg.dBFS != float("-inf") else None,
        "after_silence_ms": len(speech),
        "filtered_ms": len(gated),
        "kept_ratio": round(len(gated) / orig_ms, 3) if orig_ms else 0.0,
    }
    return gated, stats


def chunk_segment(seg: AudioSegment, chunk_seconds: int) -> List[AudioSegment]:
    ms = max(1, chunk_seconds) * 1000
    chunks = [seg[i : i + ms] for i in range(0, len(seg), ms)]
    return chunks or [seg]
