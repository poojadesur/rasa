"""Check-in endpoints: upload a short clip, list today's snapshots."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..deps import get_settings, today_str
from ..models import Snapshot
from ..pipeline.checkin_pipeline import process_checkin
from ..store import store

router = APIRouter(tags=["checkins"])


@router.post("/checkins", response_model=Snapshot)
async def create_checkin(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
):
    user_id = user_id or get_settings().default_user_id
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="empty audio file")
    return await process_checkin(
        audio_bytes=audio_bytes,
        filename=file.filename or "audio.m4a",
        content_type=file.content_type or "application/octet-stream",
        user_id=user_id,
    )


@router.get("/checkins", response_model=List[Snapshot])
async def list_checkins(user_id: Optional[str] = None, date: Optional[str] = None):
    user_id = user_id or get_settings().default_user_id
    date = date or today_str()
    return await store.list_snapshots(user_id, date)


@router.get("/checkins/{snapshot_id}", response_model=Snapshot)
async def get_checkin(snapshot_id: str):
    snap = await store.get_snapshot(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return snap
