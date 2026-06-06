"""Maps Hume's ~48 discrete emotion scores onto the valence/arousal circumplex.

Hume Expression Measurement returns per-utterance scores across ~48 emotions but
no valence/arousal directly. We derive them as a score-weighted average over a
static (valence, arousal) lookup, take the top-scoring emotion as the label, and
use the top score as intensity.
"""
from __future__ import annotations

from typing import List, Tuple

from ...models import EmotionScore

# name (lowercased) -> (valence in -1..1, arousal in 0..1)
EMOTION_VA = {
    "admiration": (0.6, 0.50),
    "adoration": (0.7, 0.50),
    "aesthetic appreciation": (0.6, 0.40),
    "amusement": (0.8, 0.60),
    "anger": (-0.7, 0.90),
    "anxiety": (-0.6, 0.80),
    "awe": (0.5, 0.60),
    "awkwardness": (-0.3, 0.50),
    "boredom": (-0.4, 0.20),
    "calmness": (0.5, 0.15),
    "concentration": (0.1, 0.50),
    "contemplation": (0.1, 0.35),
    "confusion": (-0.3, 0.50),
    "contempt": (-0.6, 0.60),
    "contentment": (0.7, 0.25),
    "craving": (0.2, 0.60),
    "desire": (0.4, 0.70),
    "determination": (0.4, 0.70),
    "disappointment": (-0.6, 0.40),
    "disgust": (-0.7, 0.60),
    "distress": (-0.7, 0.80),
    "doubt": (-0.3, 0.45),
    "ecstasy": (0.9, 0.90),
    "embarrassment": (-0.4, 0.55),
    "empathic pain": (-0.5, 0.50),
    "entrancement": (0.5, 0.45),
    "envy": (-0.5, 0.60),
    "excitement": (0.8, 0.90),
    "fear": (-0.8, 0.90),
    "guilt": (-0.6, 0.45),
    "horror": (-0.8, 0.95),
    "interest": (0.5, 0.55),
    "joy": (0.9, 0.70),
    "love": (0.8, 0.55),
    "nostalgia": (0.3, 0.40),
    "pain": (-0.7, 0.70),
    "pride": (0.7, 0.65),
    "realization": (0.2, 0.55),
    "relief": (0.6, 0.35),
    "romance": (0.7, 0.55),
    "sadness": (-0.7, 0.30),
    "satisfaction": (0.7, 0.40),
    "shame": (-0.6, 0.45),
    "surprise (negative)": (-0.4, 0.80),
    "surprise (positive)": (0.5, 0.80),
    "sympathy": (0.1, 0.40),
    "tiredness": (-0.3, 0.15),
    "triumph": (0.8, 0.80),
}


def derive(emotions: List[EmotionScore]) -> Tuple[float, float, str, float]:
    """Return (valence, arousal, label, intensity) from a list of emotion scores."""
    if not emotions:
        return 0.0, 0.5, "neutral", 0.5

    ordered = sorted(emotions, key=lambda e: e.score, reverse=True)
    label = ordered[0].name
    intensity = max(0.0, min(1.0, ordered[0].score))

    sum_w = sum_v = sum_a = 0.0
    for e in emotions:
        va = EMOTION_VA.get(e.name.strip().lower())
        if va is None:
            continue
        v, a = va
        sum_w += e.score
        sum_v += e.score * v
        sum_a += e.score * a

    if sum_w <= 0:
        return 0.0, 0.5, label, intensity

    valence = max(-1.0, min(1.0, sum_v / sum_w))
    arousal = max(0.0, min(1.0, sum_a / sum_w))
    return valence, arousal, label, intensity
