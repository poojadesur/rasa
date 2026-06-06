"""Tavus video generation (independent). Renders a talking-head video from a text
script using a stock replica's own voice — no audio hosting required."""
from __future__ import annotations

from typing import Dict

import httpx

from ..config import get_settings

BASE = "https://tavusapi.com/v2"


def _headers() -> Dict[str, str]:
    return {"x-api-key": get_settings().tavus_api_key, "Content-Type": "application/json"}


async def create_video_from_script(script: str, name: str) -> Dict:
    s = get_settings()
    if not s.tavus_api_key:
        raise RuntimeError("TAVUS_API_KEY not set")
    body = {"replica_id": s.tavus_replica_id, "script": script, "video_name": name}
    if s.tavus_callback_url:
        body["callback_url"] = s.tavus_callback_url
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{BASE}/videos", headers=_headers(), json=body)
        resp.raise_for_status()
        return resp.json()


async def get_video(video_id: str) -> Dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(f"{BASE}/videos/{video_id}", headers=_headers())
        resp.raise_for_status()
        return resp.json()
