"""Lightweight keyword-based context tagging + summary, used when we don't want a
separate LLM call (e.g. the Hume path without a Gemini key)."""
from __future__ import annotations

from typing import Optional

_BUCKETS = {
    "work": ["work", "job", "boss", "meeting", "deadline", "project", "office", "client", "interview", "coworker"],
    "family": ["family", "mom", "dad", "mother", "father", "parent", "kid", "child", "sister", "brother", "son", "daughter"],
    "relationship": ["girlfriend", "boyfriend", "partner", "wife", "husband", "date", "breakup", "love", "crush", "ex"],
    "friends": ["friend", "friends", "buddy", "hangout", "party", "roommate"],
    "health": ["sick", "doctor", "pain", "tired", "sleep", "headache", "anxiety", "stress", "therapy", "gym", "workout", "run"],
    "money": ["money", "rent", "bills", "pay", "salary", "broke", "budget", "expensive", "afford"],
    "school": ["school", "class", "exam", "study", "homework", "professor", "grade", "college", "test"],
    "food": ["food", "lunch", "dinner", "breakfast", "eat", "hungry", "coffee", "cooked", "restaurant"],
}


def tag_from_transcript(transcript: Optional[str]) -> str:
    if not transcript:
        return "general"
    text = transcript.lower()
    best, best_hits = "general", 0
    for tag, words in _BUCKETS.items():
        hits = sum(1 for w in words if w in text)
        if hits > best_hits:
            best, best_hits = tag, hits
    return best


def summary_from(label: str, transcript: Optional[str]) -> str:
    label_l = (label or "neutral").lower()
    if transcript:
        snippet = transcript.strip().split(".")[0][:80]
        if snippet:
            return f"Sounded {label_l} — “{snippet}”"
    return f"Sounded {label_l}."
