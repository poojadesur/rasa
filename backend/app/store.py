"""Storage layer. Uses Redis when reachable, otherwise an in-memory fallback
behind the same async interface (so the app runs even without redis-server)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

import redis.asyncio as aioredis

from .config import get_settings
from .models import Debrief, Recording, Snapshot


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _date_of(ts: str) -> str:
    return _parse_iso(ts).astimezone(timezone.utc).strftime("%Y-%m-%d")


def _epoch_of(ts: str) -> float:
    return _parse_iso(ts).timestamp()


class Store:
    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None
        self.backend = "memory"
        # in-memory structures
        self._kv: Dict[str, str] = {}
        self._sets: Dict[str, set] = {}
        self._zsets: Dict[str, Dict[str, float]] = {}

    async def init(self) -> str:
        settings = get_settings()
        try:
            r = aioredis.from_url(settings.redis_url, decode_responses=True)
            await r.ping()
            self._redis = r
            self.backend = "redis"
        except Exception:
            self._redis = None
            self.backend = "memory"
        return self.backend

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()

    # ---- low-level primitives (redis or memory) ----
    async def _set(self, key: str, value: str) -> None:
        if self._redis:
            await self._redis.set(key, value)
        else:
            self._kv[key] = value

    async def _get(self, key: str) -> Optional[str]:
        if self._redis:
            return await self._redis.get(key)
        return self._kv.get(key)

    async def _sadd(self, key: str, member: str) -> None:
        if self._redis:
            await self._redis.sadd(key, member)
        else:
            self._sets.setdefault(key, set()).add(member)

    async def _smembers(self, key: str) -> set:
        if self._redis:
            return set(await self._redis.smembers(key))
        return set(self._sets.get(key, set()))

    async def _zadd(self, key: str, member: str, score: float) -> None:
        if self._redis:
            await self._redis.zadd(key, {member: score})
        else:
            self._zsets.setdefault(key, {})[member] = score

    async def _zrange(self, key: str) -> List[str]:
        if self._redis:
            return await self._redis.zrange(key, 0, -1)
        zs = self._zsets.get(key, {})
        return [m for m, _ in sorted(zs.items(), key=lambda kv: kv[1])]

    # ---- snapshots ----
    async def save_snapshot(self, snap: Snapshot) -> None:
        date = _date_of(snap.timestamp)
        await self._set(f"checkin:{snap.id}", snap.model_dump_json())
        await self._zadd(f"checkins:{snap.user_id}:{date}", snap.id, _epoch_of(snap.timestamp))
        await self._sadd(f"days:{snap.user_id}", date)

    async def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        raw = await self._get(f"checkin:{snapshot_id}")
        return Snapshot.model_validate_json(raw) if raw else None

    async def list_snapshots(self, user_id: str, date: str) -> List[Snapshot]:
        ids = await self._zrange(f"checkins:{user_id}:{date}")
        out: List[Snapshot] = []
        for sid in ids:
            raw = await self._get(f"checkin:{sid}")
            if raw:
                out.append(Snapshot.model_validate_json(raw))
        return out

    async def list_days(self, user_id: str) -> set:
        return await self._smembers(f"days:{user_id}")

    # ---- debriefs ----
    async def save_debrief(self, debrief: Debrief) -> None:
        await self._set(f"debrief:{debrief.id}", debrief.model_dump_json())
        await self._set(f"debrief:by_day:{debrief.user_id}:{debrief.date}", debrief.id)

    async def get_debrief(self, debrief_id: str) -> Optional[Debrief]:
        raw = await self._get(f"debrief:{debrief_id}")
        return Debrief.model_validate_json(raw) if raw else None

    async def get_debrief_id_for_day(self, user_id: str, date: str) -> Optional[str]:
        return await self._get(f"debrief:by_day:{user_id}:{date}")

    # ---- recordings ----
    async def save_recording(self, rec: Recording) -> None:
        await self._set(f"recording:{rec.id}", rec.model_dump_json())

    async def get_recording(self, recording_id: str) -> Optional[Recording]:
        raw = await self._get(f"recording:{recording_id}")
        return Recording.model_validate_json(raw) if raw else None


store = Store()
