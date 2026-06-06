"""Gemini-written end-of-day debrief script (default ScriptGenerator)."""
from __future__ import annotations

from collections import Counter
from typing import List

from ...config import get_settings
from ...models import Snapshot
from .base import ScriptGenerator
from .stub_script import StubScriptGenerator

_SYSTEM = (
    "You are the voice of Rasa, a warm, perceptive emotional-fitness companion "
    "(think 'Strava for emotions'). Write a spoken end-of-day debrief the user will "
    "hear from a video avatar. Second person, warm but not saccharine, 120-180 words, "
    "plain prose only (no markdown, no stage directions, no emojis). Reference the "
    "real emotional arc and triggers below. End on a gentle, forward-looking note."
)


def _digest(snapshots: List[Snapshot]) -> str:
    n = len(snapshots)
    avg_v = sum(s.valence for s in snapshots) / n
    avg_a = sum(s.arousal for s in snapshots) / n
    labels = Counter(s.emotion_label for s in snapshots).most_common(5)
    triggers = Counter(s.context_tag for s in snapshots).most_common(5)
    lines = [
        f"- moments logged: {n}",
        f"- average valence: {avg_v:+.2f} (-1 negative .. +1 positive)",
        f"- average arousal: {avg_a:.2f} (0 calm .. 1 high-energy)",
        f"- top emotions: {', '.join(f'{l} x{c}' for l, c in labels)}",
        f"- topics/triggers: {', '.join(f'{t} x{c}' for t, c in triggers)}",
    ]
    return "\n".join(lines)


class GeminiScriptGenerator(ScriptGenerator):
    name = "gemini"

    def __init__(self) -> None:
        from google import genai

        s = get_settings()
        self._client = genai.Client(api_key=s.gemini_api_key)
        self._model = s.gemini_model

    async def generate(self, snapshots: List[Snapshot], user_name: str) -> str:
        if not snapshots:
            return await StubScriptGenerator().generate(snapshots, user_name)

        prompt = (
            f"{_SYSTEM}\n\nThe user's name is {user_name or 'there'}.\n"
            f"Today's emotional digest:\n{_digest(snapshots)}\n\nWrite the debrief now."
        )
        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=prompt
            )
            text = (resp.text or "").strip()
            return text or await StubScriptGenerator().generate(snapshots, user_name)
        except Exception:
            return await StubScriptGenerator().generate(snapshots, user_name)
