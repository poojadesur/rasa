"""Shared helpers: time, ids, and re-exports of settings/store singletons."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .config import get_settings  # noqa: F401  (re-export)
from .store import store  # noqa: F401  (re-export)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def new_id(prefix: str = "") -> str:
    base = uuid.uuid4().hex[:12]
    return f"{prefix}{base}" if prefix else base
