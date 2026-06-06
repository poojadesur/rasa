"""Short voice check-in → decibel-filter to the user → Hume emotion → Snapshot."""
from __future__ import annotations

from ..deps import new_id, now_iso, store
from ..models import Snapshot
from ..services.audio_filter import filter_to_user
from ..services.audioutil import guess_format, segment_to_wav_bytes
from ..services.emotion.base import get_emotion_classifier
from ..services.media import ext_for, save_bytes


async def process_checkin(
    audio_bytes: bytes,
    filename: str,
    content_type: str,
    user_id: str,
) -> Snapshot:
    fmt = guess_format(filename, content_type)

    # Isolate the user's voice via loudness/decibel filtering, then read emotion.
    filtered, _stats = filter_to_user(audio_bytes, fmt=fmt)
    wav = segment_to_wav_bytes(filtered)
    emo = await get_emotion_classifier().classify(wav, fmt="wav", transcript=None)

    snap_id = new_id("snap_")
    audio_url = save_bytes(audio_bytes, f"{snap_id}.{ext_for(fmt)}")  # original, for playback

    snap = Snapshot(
        id=snap_id,
        user_id=user_id,
        timestamp=now_iso(),
        emotion_label=emo.label,
        valence=emo.valence,
        arousal=emo.arousal,
        intensity=emo.intensity,
        context_tag=emo.context_tag,
        transcript=None,
        summary=emo.summary,
        audio_url=audio_url,
        top_emotions=emo.top_emotions,
        source="checkin",
        provider=emo.provider,
    )
    await store.save_snapshot(snap)
    return snap
