"""Dashboard endpoint: streak, heatmap, series, triggers, label breakdown."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from ..deps import get_settings, today_str
from ..models import DashboardResponse
from ..services.dashboard import build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(user_id: Optional[str] = None, date: Optional[str] = None):
    user_id = user_id or get_settings().default_user_id
    date = date or today_str()
    return await build_dashboard(user_id, date)
