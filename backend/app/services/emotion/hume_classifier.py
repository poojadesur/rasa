"""Hume Expression Measurement (prosody) — default emotion engine.

Built on the collaborator's known-good streaming pattern:
    client.expression_measurement.stream.connect() -> socket.send_file(path, Config(prosody={}))
    result.prosody.predictions[*].emotions[*].{name, score}

Streaming accepts <=5s per payload, so longer clips are split into ~4.5s windows
sent over a single connection and averaged.
"""
from __future__ import annotations

import os
from typing import List, Optional

from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config

from ...config import get_settings
from ...models import EmotionResult, EmotionScore
from ..audioutil import load_segment, segment_to_wav_tempfile
from ..context_tag import summary_from, tag_from_transcript
from . import valence_arousal
from .base import EmotionClassifier

WINDOW_MS = 4500


class HumeEmotionClassifier(EmotionClassifier):
    name = "hume"

    def __init__(self) -> None:
        self._api_key = get_settings().hume_api_key

    async def classify(
        self,
        audio_bytes: bytes,
        fmt: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> EmotionResult:
        seg = load_segment(audio_bytes, fmt=fmt).set_frame_rate(16000).set_channels(1)
        windows = [seg[i : i + WINDOW_MS] for i in range(0, max(len(seg), 1), WINDOW_MS)] or [seg]

        agg: dict[str, float] = {}
        n = 0
        tmp_paths: List[str] = []
        try:
            client = AsyncHumeClient(api_key=self._api_key)
            async with client.expression_measurement.stream.connect() as socket:
                for w in windows:
                    if len(w) < 200:  # skip <0.2s slivers
                        continue
                    path = segment_to_wav_tempfile(w)
                    tmp_paths.append(path)
                    result = await socket.send_file(path, config=Config(prosody={}))
                    prosody = getattr(result, "prosody", None)
                    preds = getattr(prosody, "predictions", None) if prosody else None
                    if not preds:
                        continue
                    for p in preds:
                        n += 1
                        for e in p.emotions:
                            agg[e.name] = agg.get(e.name, 0.0) + e.score
        finally:
            for p in tmp_paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass

        emotions = [EmotionScore(name=k, score=v / n) for k, v in agg.items()] if n else []
        valence, arousal, label, intensity = valence_arousal.derive(emotions)
        top5 = sorted(emotions, key=lambda e: e.score, reverse=True)[:5]

        return EmotionResult(
            valence=round(valence, 3),
            arousal=round(arousal, 3),
            label=label,
            intensity=round(intensity, 3),
            context_tag=tag_from_transcript(transcript),
            summary=summary_from(label, transcript),
            top_emotions=top5,
            provider="hume",
        )
