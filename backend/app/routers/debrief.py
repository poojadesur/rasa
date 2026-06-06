"""Debrief endpoints: kick off generation (async), poll status, optional webhook."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..deps import get_settings, new_id, now_iso, today_str
from ..models import Debrief, GenerateDebriefRequest
from ..pipeline.debrief_pipeline import generate_debrief
from ..store import store

router = APIRouter(tags=["debrief"])


@router.post("/debrief/generate")
async def create_debrief(req: GenerateDebriefRequest, background_tasks: BackgroundTasks):
    user_id = req.user_id or get_settings().default_user_id
    date = req.date or today_str()

    deb_id = new_id("deb_")
    deb = Debrief(id=deb_id, user_id=user_id, date=date, status="pending",
                  created_at=now_iso(), updated_at=now_iso())
    await store.save_debrief(deb)

    background_tasks.add_task(generate_debrief, deb_id, user_id, date, req.script)
    return {"debrief_id": deb_id, "status": "pending"}


@router.get("/debrief/{debrief_id}", response_model=Debrief)
async def get_debrief(debrief_id: str):
    deb = await store.get_debrief(debrief_id)
    if not deb:
        raise HTTPException(status_code=404, detail="debrief not found")
    return deb


@router.post("/debrief/webhook", status_code=204)
async def debrief_webhook(request: Request):
    # Optional: Tavus posts here when a video finishes. Polling is the primary path,
    # so we just accept and ignore the payload for the demo.
    await request.body()
    return None
