"""Application settings loaded from backend/.env via pydantic-settings."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_stt_model: str = "scribe_v2"
    elevenlabs_tts_model: str = "eleven_multilingual_v2"

    # Emotion engine
    emotion_provider: str = "hume"  # hume | gemini | stub
    hume_api_key: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Script generation
    script_provider: str = "gemini"  # gemini | stub

    # Tavus
    tavus_api_key: str = ""
    tavus_replica_id: str = "r90bbd427f71"
    tavus_callback_url: str = ""

    # Infra
    redis_url: str = "redis://localhost:6379/0"
    public_base_url: str = ""
    media_dir: str = "./media"
    default_user_id: str = "demo-user"

    # Preprocessing tunables
    silence_thresh_dbfs: float = -35.0   # absolute floor for silence removal
    min_silence_ms: int = 400
    user_gate_margin_db: float = 12.0    # keep audio within this many dB of the peak (nearest/loudest = user)
    hume_chunk_seconds: int = 30         # one snapshot per chunk in the long-recording path

    @property
    def media_path(self) -> Path:
        p = Path(self.media_dir)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
