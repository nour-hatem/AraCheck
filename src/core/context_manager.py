"""
src/core/context_manager.py
---------------------------
Conversation history trimming to prevent token-limit overflow.
"""
from typing import List, Dict

MAX_HISTORY_TURNS = 10
MAX_HISTORY_ITEMS = MAX_HISTORY_TURNS * 2


def trim_history(history: List[Dict]) -> List[Dict]:
    """
    Return the most recent MAX_HISTORY_ITEMS entries from the conversation history.

    Normalises both ``{role, content}`` and ``{sender, text}`` message formats.

    Args:
        history: List of message dicts.

    Returns:
        Trimmed list of at most MAX_HISTORY_ITEMS dicts.
    """
    if not history:
        return []

    normalized = []
    for item in history:
        role = item.get("role") or item.get("sender") or "user"
        content = item.get("content") or item.get("text") or ""
        normalized.append({"role": role, "content": content})

    if len(normalized) > MAX_HISTORY_ITEMS:
        normalized = normalized[-MAX_HISTORY_ITEMS:]

    return normalized
