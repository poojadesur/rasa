"""Builds the Strava/Garmin-style dashboard aggregates from stored snapshots."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List

from ..models import (
    DashboardResponse,
    HeatmapBucket,
    LabelCount,
    SeriesPoint,
    Snapshot,
    TriggerStat,
)
from ..store import store


def _parse(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def _streak(user_id: str, date: str) -> int:
    days = await store.list_days(user_id)
    if date not in days:
        return 0
    streak = 0
    cur = datetime.strptime(date, "%Y-%m-%d").date()
    while cur.strftime("%Y-%m-%d") in days:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak


async def build_dashboard(user_id: str, date: str) -> DashboardResponse:
    snaps: List[Snapshot] = await store.list_snapshots(user_id, date)
    count = len(snaps)

    avg_v = round(sum(s.valence for s in snaps) / count, 3) if count else 0.0
    avg_a = round(sum(s.arousal for s in snaps) / count, 3) if count else 0.0

    # heatmap: 24 hourly buckets
    by_hour_v = defaultdict(float)
    by_hour_n = defaultdict(int)
    for s in snaps:
        h = _parse(s.timestamp).astimezone(timezone.utc).hour
        by_hour_v[h] += s.valence
        by_hour_n[h] += 1
    heatmap = [
        HeatmapBucket(
            hour=h,
            avg_valence=round(by_hour_v[h] / by_hour_n[h], 3) if by_hour_n[h] else 0.0,
            count=by_hour_n[h],
        )
        for h in range(24)
    ]

    series = [SeriesPoint(timestamp=s.timestamp, valence=s.valence, arousal=s.arousal) for s in snaps]

    # triggers by context_tag
    trig_n = defaultdict(int)
    trig_v = defaultdict(float)
    for s in snaps:
        trig_n[s.context_tag] += 1
        trig_v[s.context_tag] += s.valence
    top_triggers = sorted(
        [
            TriggerStat(context_tag=t, count=trig_n[t], avg_valence=round(trig_v[t] / trig_n[t], 3))
            for t in trig_n
        ],
        key=lambda x: x.count,
        reverse=True,
    )[:6]

    # label breakdown
    label_n = defaultdict(int)
    for s in snaps:
        label_n[s.emotion_label] += 1
    labels_breakdown = sorted(
        [LabelCount(label=k, count=v) for k, v in label_n.items()],
        key=lambda x: x.count,
        reverse=True,
    )

    return DashboardResponse(
        user_id=user_id,
        date=date,
        streak_days=await _streak(user_id, date),
        checkin_count=count,
        avg_valence=avg_v,
        avg_arousal=avg_a,
        heatmap=heatmap,
        series=series,
        top_triggers=top_triggers,
        labels_breakdown=labels_breakdown,
    )
