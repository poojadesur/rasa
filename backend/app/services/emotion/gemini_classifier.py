"""Gemini emotion classifier (fallback). Sends the raw audio to a multimodal
Gemini model and asks for strict JSON {valence, arousal, label, ...}."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ...config import get_settings
from ...models import EmotionResult, EmotionScore
from ..audioutil import to_wav_bytes
from .base import EmotionClassifier

_PROMPT = (
    "You are an affective-computing model. Listen to this voice clip and assess the "
    "speaker's emotional state from BOTH their words and their vocal tone (prosody). "
    "Return: valence (-1 very negative .. 1 very positive), arousal (0 calm .. 1 excited), "
    "a single dominant emotion label (one word, capitalized), intensity (0..1), a short "
    "context_tag (e.g. work, family, health, money, general), and a one-line summary."
)


class _GeminiEmotion(BaseModel):
    valence: float
    arousal: float
    label: str
    intensity: float
    context_tag: str
    summary: str


class GeminiEmotionClassifier(EmotionClassifier):
    name = "gemini"

    def __init__(self) -> None:
        from google import genai  # lazy import

        s = get_settings()
        self._client = genai.Client(api_key=s.gemini_api_key)
        self._model = s.gemini_model

    async def classify(
        self,
        audio_bytes: bytes,
        fmt: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> EmotionResult:
        from google.genai import types

        wav = to_wav_bytes(audio_bytes, fmt=fmt)
        prompt = _PROMPT
        if transcript:
            prompt += f"\n\nTranscript (for context): {transcript[:1500]}"

        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=wav, mime_type="audio/wav"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_GeminiEmotion,
                ),
            )
            parsed: _GeminiEmotion = resp.parsed  # type: ignore[assignment]
            return EmotionResult(
                valence=max(-1.0, min(1.0, parsed.valence)),
                arousal=max(0.0, min(1.0, parsed.arousal)),
                label=parsed.label or "neutral",
                intensity=max(0.0, min(1.0, parsed.intensity)),
                context_tag=parsed.context_tag or "general",
                summary=parsed.summary or "",
                top_emotions=[EmotionScore(name=parsed.label or "neutral", score=parsed.intensity)],
                provider="gemini",
            )
        except Exception as exc:  # neutral default on any failure
            return EmotionResult(
                valence=0.0, arousal=0.5, label="neutral", intensity=0.5,
                context_tag="general", summary=f"(emotion unavailable: {exc})",
                provider="gemini",
            )
