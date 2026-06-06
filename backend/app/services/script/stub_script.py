"""Offline debrief script — deterministic, warm summary built from the day's
snapshots. Used when no Gemini key is set (and as a fallback)."""
from __future__ import annotations

from collections import Counter
from typing import List

from ...models import Snapshot
from .base import ScriptGenerator


class StubScriptGenerator(ScriptGenerator):
    name = "stub"

    async def generate(self, snapshots: List[Snapshot], user_name: str) -> str:
        name = user_name or "there"
        if not snapshots:
            return (
                f"Hey {name}. I didn't catch any moments from you today — "
                f"no worries. Check in with a few voice notes tomorrow and I'll "
                f"have a real story to tell you. Rest up."
            )

        n = len(snapshots)
        avg_v = sum(s.valence for s in snapshots) / n
        labels = Counter(s.emotion_label for s in snapshots)
        triggers = Counter(s.context_tag for s in snapshots)
        top_label = labels.most_common(1)[0][0].lower()
        top_trigger = triggers.most_common(1)[0][0]

        if avg_v > 0.3:
            arc = "honestly a pretty good one"
        elif avg_v < -0.2:
            arc = "a heavy one in places"
        else:
            arc = "a real mix of ups and downs"

        trig_line = (
            f" A lot of it circled around {top_trigger}." if top_trigger != "general" else ""
        )

        return (
            f"Hey {name}, here's your day in review. I picked up on {n} "
            f"moments, and overall it was {arc}. The feeling that came through most "
            f"was {top_label}.{trig_line} "
            f"Take a second to notice that — it's data about what your days are "
            f"actually made of. Tomorrow's a fresh page. Talk soon."
        )
