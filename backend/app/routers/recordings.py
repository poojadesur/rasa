"""Long-conversation endpoints: upload a big mp3, poll processing progress."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from ..deps import get_settings, new_id, now_iso
from ..models import Recording
from ..pipeline.recording_pipeline import process_recording
from ..store import store

router = APIRouter(tags=["recordings"])


@router.post("/recordings")
async def create_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
):
    user_id = user_id or get_settings().default_user_id
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="empty audio file")

    rec_id = new_id("rec_")
    rec = Recording(id=rec_id, user_id=user_id, status="pending", created_at=now_iso(), updated_at=now_iso())
    await store.save_recording(rec)

    background_tasks.add_task(
        process_recording,
        rec_id,
        audio_bytes,
        file.filename or "conversation.mp3",
        file.content_type or "application/octet-stream",
        user_id,
    )
    return {"recording_id": rec_id, "status": rec.status}


@router.get("/recordings/{recording_id}", response_model=Recording)
async def get_recording(recording_id: str):
    rec = await store.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=404, detail="recording not found")
    return rec
