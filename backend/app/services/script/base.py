"""ScriptGenerator interface + factory. Default Gemini, stub fallback. A teammate
can plug in their own LLM by adding a class + one branch here."""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

from ...config import get_settings
from ...models import Snapshot


class ScriptGenerator(ABC):
    name = "base"

    @abstractmethod
    async def generate(self, snapshots: List[Snapshot], user_name: str) -> str:
        ...


@lru_cache
def get_script_generator() -> ScriptGenerator:
    s = get_settings()
    if s.script_provider.lower() == "gemini" and s.gemini_api_key:
        from .gemini_script import GeminiScriptGenerator
        return GeminiScriptGenerator()
    from .stub_script import StubScriptGenerator
    return StubScriptGenerator()
