"""End-of-day debrief: gather snapshots → script (Gemini/stub or override) →
Tavus video (independent). Falls back to a script-only debrief if Tavus is unset."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..config import get_settings
from ..deps import now_iso, store
from ..models import Debrief
from ..services.script.base import get_script_generator
from ..services.tavus_client import create_video_from_script, get_video

log = logging.getLogger("rasa.debrief")

POLL_INTERVAL_S = 8
POLL_MAX_TRIES = 45  # ~6 minutes


async def _save(deb: Debrief, **changes) -> None:
    for k, v in changes.items():
        setattr(deb, k, v)
    deb.updated_at = now_iso()
    await store.save_debrief(deb)


def _user_name(user_id: str) -> str:
    base = (user_id or "").split("-")[0].split("@")[0]
    return base.capitalize() if base and base != "demo" else "there"


async def generate_debrief(
    debrief_id: str,
    user_id: str,
    date: str,
    override_script: Optional[str] = None,
) -> Debrief:
    s = get_settings()
    deb = await store.get_debrief(debrief_id) or Debrief(
        id=debrief_id, user_id=user_id, date=date, created_at=now_iso()
    )
    # 1. Script (a failure here is a real error — there's nothing to show)
    try:
        await _save(deb, status="scripting")
        if override_script:
            script = override_script.strip()
        else:
            snaps = await store.list_snapshots(user_id, date)
            script = await get_script_generator().generate(snaps, _user_name(user_id))
        await _save(deb, script=script)
    except Exception as exc:  # noqa: BLE001
        log.exception("debrief %s scripting failed", debrief_id)
        await _save(deb, status="error", error=str(exc))
        return deb

    # 2. Tavus video — best-effort. Any failure degrades to a script-only debrief
    #    (status stays "ready") so the demo never breaks; the reason is kept in `error`.
    if not s.tavus_api_key:
        await _save(deb, status="ready")
        return deb

    try:
        await _save(deb, status="rendering")
        created = await create_video_from_script(script, f"Rasa debrief {date}")
        video_id = created.get("video_id")
        await _save(deb, share_url=created.get("hosted_url"))

        for _ in range(POLL_MAX_TRIES):
            await asyncio.sleep(POLL_INTERVAL_S)
            v = await get_video(video_id)
            status = v.get("status")
            if status == "ready":
                await _save(
                    deb,
                    status="ready",
                    video_url=v.get("download_url") or v.get("stream_url") or v.get("hosted_url"),
                    share_url=v.get("hosted_url") or deb.share_url,
                )
                return deb
            if status == "error":
                raise RuntimeError(f"Tavus returned error for video {video_id}")

        await _save(deb, status="ready", error="tavus_render_timeout")  # script-only
    except Exception as exc:  # noqa: BLE001
        log.warning("debrief %s: Tavus unavailable, falling back to script-only (%s)", debrief_id, exc)
        await _save(deb, status="ready", error=f"video_unavailable: {exc}")
    return deb
