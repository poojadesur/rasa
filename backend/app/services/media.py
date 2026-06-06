"""Saving + public-URL helpers for files served under /media."""
from __future__ import annotations

from ..config import get_settings


def media_url(filename: str) -> str:
    s = get_settings()
    base = s.public_base_url.rstrip("/") if s.public_base_url else ""
    return f"{base}/media/{filename}"


def save_bytes(data: bytes, filename: str) -> str:
    s = get_settings()
    path = s.media_path / filename
    path.write_bytes(data)
    return media_url(filename)


def ext_for(fmt: str | None) -> str:
    if not fmt:
        return "bin"
    return "m4a" if fmt == "mp4" else fmt
