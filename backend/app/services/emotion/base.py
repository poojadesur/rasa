"""EmotionClassifier interface + factory with graceful fallback.

Tries the configured provider first, then any other provider whose key is present,
then the offline stub. So the app always returns *something* sensible.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from ...config import get_settings
from ...models import EmotionResult


class EmotionClassifier(ABC):
    name = "base"

    @abstractmethod
    async def classify(
        self,
        audio_bytes: bytes,
        fmt: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> EmotionResult:
        ...


@lru_cache
def get_emotion_classifier() -> EmotionClassifier:
    s = get_settings()
    requested = s.emotion_provider.lower()

    for provider in [requested, "hume", "gemini", "stub"]:
        if provider == "hume" and s.hume_api_key:
            from .hume_classifier import HumeEmotionClassifier
            return HumeEmotionClassifier()
        if provider == "gemini" and s.gemini_api_key:
            from .gemini_classifier import GeminiEmotionClassifier
            return GeminiEmotionClassifier()
        if provider == "stub":
            from .stub_classifier import StubEmotionClassifier
            return StubEmotionClassifier()

    from .stub_classifier import StubEmotionClassifier
    return StubEmotionClassifier()
