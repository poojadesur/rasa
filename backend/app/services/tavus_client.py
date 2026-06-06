"""Tavus CVI: creates a live avatar conversation from an emotion debrief script."""
from __future__ import annotations

from typing import Dict

import httpx

from ..config import get_settings

BASE = "https://tavusapi.com/v2"


def _headers() -> Dict[str, str]:
    return {"x-api-key": get_settings().tavus_api_key, "Content-Type": "application/json"}


async def create_cvi_conversation(script: str, name: str) -> Dict:
    s = get_settings()
    if not s.tavus_api_key:
        raise RuntimeError("TAVUS_API_KEY not set")

    system_prompt = f"""You are an emotionally intelligent daily companion giving a personalized end-of-day debrief.

Here is today's emotional summary and prepared debrief:

{script}

Your job:
- Greet them warmly and naturally
- Walk them through the emotions detected during their day
- Be empathetic and conversational, not clinical
- Ask how they're feeling now and have a genuine conversation
- Keep it to 3-5 minutes"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        persona_resp = await client.post(
            f"{BASE}/personas",
            headers=_headers(),
            json={
                "persona_name": name,
                "system_prompt": system_prompt,
                "default_replica_id": s.tavus_replica_id,
                "pipeline_mode": "full",
            },
        )
        persona_resp.raise_for_status()
        persona_id = persona_resp.json().get("persona_id")

        conv_resp = await client.post(
            f"{BASE}/conversations",
            headers=_headers(),
            json={
                "persona_id": persona_id,
                "replica_id": s.tavus_replica_id,
                "conversation_name": name,
                "conversational_context": script,
                "custom_greeting": "Hey! I've been going over how you felt today. Ready to talk through it?",
            },
        )
        conv_resp.raise_for_status()
        return conv_resp.json()
