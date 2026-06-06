"""Long conversation mp3 → decibel-filter to the user → chunk → Hume per chunk →
many time-stamped Snapshots (the user's emotional arc across the conversation)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ..config import get_settings
from ..deps import new_id, now_iso, store
from ..models import Recording, Snapshot
from ..services.audio_filter import chunk_segment, filter_to_user
from ..services.audioutil import guess_format, segment_to_wav_bytes
from ..services.emotion.base import get_emotion_classifier

log = logging.getLogger("rasa.recording")


async def _touch(rec: Recording) -> None:
    rec.updated_at = now_iso()
    await store.save_recording(rec)


async def process_recording(
    recording_id: str,
    audio_bytes: bytes,
    filename: str,
    content_type: str,
    user_id: str,
) -> Recording:
    s = get_settings()
    rec = await store.get_recording(recording_id) or Recording(
        id=recording_id, user_id=user_id, created_at=now_iso()
    )
    try:
        rec.status = "isolating"
        await _touch(rec)

        fmt = guess_format(filename, content_type)
        filtered, stats = filter_to_user(audio_bytes, fmt=fmt)
        rec.speaker_levels = {"orig_dbfs": stats.get("orig_dbfs"), "kept_ratio": stats.get("kept_ratio")}

        chunks = chunk_segment(filtered, s.hume_chunk_seconds)
        rec.chunk_count = len(chunks)
        rec.status = "analyzing"
        await _touch(rec)

        # Anchor timestamps so the final chunk lands ~now.
        total = len(chunks) * s.hume_chunk_seconds
        base = datetime.now(timezone.utc) - timedelta(seconds=total)

        classifier = get_emotion_classifier()
        for i, ch in enumerate(chunks):
            if len(ch) < 200:
                rec.chunks_done = i + 1
                await _touch(rec)
                continue
            wav = segment_to_wav_bytes(ch)
            emo = await classifier.classify(wav, fmt="wav", transcript=None)
            ts = (base + timedelta(seconds=i * s.hume_chunk_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
            snap = Snapshot(
                id=new_id("snap_"),
                user_id=user_id,
                timestamp=ts,
                emotion_label=emo.label,
                valence=emo.valence,
                arousal=emo.arousal,
                intensity=emo.intensity,
                context_tag=emo.context_tag,
                transcript=None,
                summary=emo.summary,
                top_emotions=emo.top_emotions,
                source="recording",
                recording_id=recording_id,
                provider=emo.provider,
            )
            await store.save_snapshot(snap)
            rec.snapshot_ids.append(snap.id)
            rec.chunks_done = i + 1
            await _touch(rec)

        rec.status = "ready"
        await _touch(rec)
    except Exception as exc:  # noqa: BLE001
        log.exception("recording %s failed", recording_id)
        rec.status = "error"
        rec.error = str(exc)
        await _touch(rec)
    return rec
