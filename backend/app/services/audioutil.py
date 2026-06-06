"""Small audio helpers built on pydub/ffmpeg."""
from __future__ import annotations

import io
import tempfile
from typing import Optional

from pydub import AudioSegment


def load_segment(audio_bytes: bytes, fmt: Optional[str] = None) -> AudioSegment:
    """Decode arbitrary audio bytes (m4a/mp3/wav) into an AudioSegment."""
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)


def to_wav_tempfile(audio_bytes: bytes, fmt: Optional[str] = None) -> str:
    """Transcode audio bytes to a temp 16kHz mono WAV file and return its path.

    Hume's streaming `send_file` is known-good with WAV; 16kHz mono keeps payloads
    small and is plenty for prosody.
    """
    seg = load_segment(audio_bytes, fmt=fmt)
    seg = seg.set_frame_rate(16000).set_channels(1)
    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    seg.export(f.name, format="wav")
    f.close()
    return f.name


def to_wav_bytes(audio_bytes: bytes, fmt: Optional[str] = None) -> bytes:
    """Transcode to 16kHz mono WAV and return the bytes (for inline API uploads)."""
    seg = load_segment(audio_bytes, fmt=fmt).set_frame_rate(16000).set_channels(1)
    buf = io.BytesIO()
    seg.export(buf, format="wav")
    return buf.getvalue()


def segment_to_wav_tempfile(seg: AudioSegment) -> str:
    seg = seg.set_frame_rate(16000).set_channels(1)
    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    seg.export(f.name, format="wav")
    f.close()
    return f.name


def segment_to_wav_bytes(seg: AudioSegment) -> bytes:
    seg = seg.set_frame_rate(16000).set_channels(1)
    buf = io.BytesIO()
    seg.export(buf, format="wav")
    return buf.getvalue()


def guess_format(filename: Optional[str], content_type: Optional[str]) -> Optional[str]:
    name = (filename or "").lower()
    for ext in ("m4a", "mp3", "wav", "mp4", "aac", "ogg", "flac", "webm"):
        if name.endswith("." + ext):
            return "mp4" if ext == "m4a" else ext
    ct = (content_type or "").lower()
    if "mp4" in ct or "m4a" in ct or "aac" in ct:
        return "mp4"
    if "mpeg" in ct or "mp3" in ct:
        return "mp3"
    if "wav" in ct:
        return "wav"
    return None
