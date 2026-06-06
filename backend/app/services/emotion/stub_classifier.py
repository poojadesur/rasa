"""Offline emotion classifier — plausible randomized output so the app/dashboard
is fully demoable without any API keys (Phase 0)."""
from __future__ import annotations

import hashlib
import random
from typing import Optional

from ...models import EmotionResult, EmotionScore
from .base import EmotionClassifier

_PALETTE = [
    ("Joy", 0.9, 0.7),
    ("Calmness", 0.5, 0.15),
    ("Excitement", 0.8, 0.9),
    ("Contentment", 0.7, 0.25),
    ("Anxiety", -0.6, 0.8),
    ("Tiredness", -0.3, 0.15),
    ("Sadness", -0.7, 0.3),
    ("Interest", 0.5, 0.55),
    ("Determination", 0.4, 0.7),
    ("Boredom", -0.4, 0.2),
]


class StubEmotionClassifier(EmotionClassifier):
    name = "stub"

    async def classify(
        self,
        audio_bytes: bytes,
        fmt: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> EmotionResult:
        # Deterministic per-clip seed so repeated calls on the same bytes match.
        seed = int(hashlib.sha1(audio_bytes[:4096] or b"x").hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        label, valence, arousal = rng.choice(_PALETTE)
        intensity = round(rng.uniform(0.4, 0.95), 3)
        # jitter
        valence = max(-1.0, min(1.0, valence + rng.uniform(-0.1, 0.1)))
        arousal = max(0.0, min(1.0, arousal + rng.uniform(-0.1, 0.1)))
        top = [EmotionScore(name=label, score=intensity)]
        from ..context_tag import summary_from, tag_from_transcript
        return EmotionResult(
            valence=round(valence, 3),
            arousal=round(arousal, 3),
            label=label,
            intensity=intensity,
            context_tag=tag_from_transcript(transcript),
            summary=summary_from(label, transcript),
            top_emotions=top,
            provider="stub",
        )
