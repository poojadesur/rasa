"""Domain + API models. Field names are snake_case to match the iOS Codable
decoder configured with .convertFromSnakeCase."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EmotionScore(BaseModel):
    name: str
    score: float


class EmotionResult(BaseModel):
    """Output of an EmotionClassifier for a single audio chunk."""
    valence: float = 0.0          # -1 (negative) .. 1 (positive)
    arousal: float = 0.5          # 0 (calm) .. 1 (excited)
    label: str = "neutral"        # dominant emotion label
    intensity: float = 0.5        # 0 .. 1
    context_tag: str = "general"  # short trigger/topic tag
    summary: str = ""             # one-line human summary
    top_emotions: List[EmotionScore] = Field(default_factory=list)
    provider: str = "stub"        # which engine produced this


class Snapshot(BaseModel):
    id: str
    user_id: str
    timestamp: str                # ISO8601 UTC
    emotion_label: str
    valence: float
    arousal: float
    intensity: float
    context_tag: str
    transcript: Optional[str] = None
    summary: str = ""
    audio_url: Optional[str] = None
    top_emotions: List[EmotionScore] = Field(default_factory=list)
    source: str = "checkin"       # checkin | recording
    recording_id: Optional[str] = None
    provider: str = "stub"


# ---- Dashboard ----

class HeatmapBucket(BaseModel):
    hour: int
    avg_valence: float
    count: int


class SeriesPoint(BaseModel):
    timestamp: str
    valence: float
    arousal: float


class TriggerStat(BaseModel):
    context_tag: str
    count: int
    avg_valence: float


class LabelCount(BaseModel):
    label: str
    count: int


class DashboardResponse(BaseModel):
    user_id: str
    date: str
    streak_days: int
    checkin_count: int
    avg_valence: float
    avg_arousal: float
    heatmap: List[HeatmapBucket]
    series: List[SeriesPoint]
    top_triggers: List[TriggerStat]
    labels_breakdown: List[LabelCount]


# ---- Debrief ----

class Debrief(BaseModel):
    id: str
    user_id: str
    date: str
    status: str = "pending"  # pending|scripting|synthesizing|rendering|ready|error
    script: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    share_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class GenerateDebriefRequest(BaseModel):
    user_id: Optional[str] = None
    date: Optional[str] = None
    script: Optional[str] = None  # optional: drive Tavus with this text directly


# ---- Recording (long conversation) ----

class Recording(BaseModel):
    id: str
    user_id: str
    status: str = "pending"  # pending|transcribing|isolating|analyzing|ready|error
    created_at: str = ""
    updated_at: str = ""
    ego_speaker: Optional[str] = None
    speaker_levels: dict = Field(default_factory=dict)  # speaker -> avg dBFS
    chunk_count: int = 0
    chunks_done: int = 0
    snapshot_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = None
