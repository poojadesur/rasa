# Rasa — "Strava for Emotions" 🎭

Listen to your voice, read your emotions, and get an end-of-day video debrief.

```
audio in ──> decibel/loudness filter (isolate the user) ──> Hume prosody ──> emotion reading
                                                                                   │
                                                            stored as snapshots ───┤
                                                                                   ▼
                                              Strava-style dashboard (streak, heatmap, triggers)
                                                                                   │
                                              end of day ──> script ──> Tavus video debrief
```

## Stack
- **Backend:** Python / FastAPI + Redis (in-memory fallback).
- **iOS:** SwiftUI (iOS 17+), generated with XcodeGen.
- **Emotion:** Hume Expression Measurement (prosody) — pluggable, with a Gemini fallback.
- **Isolation:** pure decibel/loudness filtering (pydub) — no diarization API.
- **Debrief video:** Tavus (independent; takes a text script, renders a talking-head).

## Backend

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
redis-server --daemonize yes          # optional; falls back to in-memory
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Keys live in `backend/.env` (gitignored). Already set: `HUME_API_KEY`.
Add when ready:
- `TAVUS_API_KEY` → enables the talking-head video (otherwise debrief is script-only).
- `GEMINI_API_KEY` → upgrades the debrief writer (and is an emotion fallback). Stub writer works without it.

### Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/checkins` (multipart `file`, `user_id`) | short clip → filter → Hume → one Snapshot |
| GET | `/checkins?user_id=&date=` | today's snapshots |
| POST | `/recordings` (multipart `file`) | long mp3 → filter → chunk → many Snapshots (async; poll) |
| GET | `/recordings/{id}` | processing progress |
| GET | `/dashboard?user_id=` | streak, heatmap, series, triggers, labels |
| POST | `/debrief/generate` `{user_id, date?, script?}` | async script → Tavus video |
| GET | `/debrief/{id}` | poll status / final video |
| GET | `/health` | liveness + active storage/emotion provider |

Tunables in `.env`: `EMOTION_PROVIDER` (hume|gemini|stub), `SCRIPT_PROVIDER` (gemini|stub),
`SILENCE_THRESH_DBFS`, `USER_GATE_MARGIN_DB` (loudness gate width), `HUME_CHUNK_SECONDS`.

## Web app (recommended for the demo)

The backend serves a self-contained web client at the root. Just run the backend, then:

```
open http://localhost:8000/
```

Records via the browser mic, hits the same API, and shows Check-in / Timeline / Stats / Debrief.
Use **`localhost`** (a secure context, so the mic works). A phone over the LAN IP uses plain HTTP,
which browsers block from the mic — for phone use, front it with an HTTPS tunnel.

## iOS

```bash
cd ios
xcodegen generate      # creates Rasa.xcodeproj
open Rasa.xcodeproj     # run on a simulator or device from Xcode
```

If Xcode says "No supported iOS devices are available": install a simulator runtime
(`xcodebuild -downloadPlatform iOS`, or Xcode → Settings → Components → iOS 18.4) and pick an
iPhone from the destination menu, or connect a device and set a signing team.

Point the app at the backend in `ios/Rasa/Config.swift`:
- **Simulator:** `http://127.0.0.1:8000` (default — shares the Mac's network).
- **Real device:** your Mac's LAN IP, e.g. `http://192.168.x.x:8000`.

Tabs: **Check in** (tap-to-record; toggle "long session" for a full conversation) ·
**Timeline** · **Stats** (streak / heatmap / mood chart) · **Debrief**.

## Notes
- Hume's streaming API accepts ≤5s payloads; the classifier auto-windows longer clips and averages.
- The loudness gate keeps audio within `USER_GATE_MARGIN_DB` of the peak (nearest/loudest = the user). It won't separate two equally-loud speakers — a real diarizer can slot in behind `services/audio_filter.py:filter_to_user` without touching callers.
- Rotate the Hume key after the hackathon (it was shared in plaintext).
