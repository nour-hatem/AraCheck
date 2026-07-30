"""
context_manager.py
------------------
Manages conversation history trimming to avoid exceeding token limits
when passing history to the agent pipeline.
"""
from typing import List, Dict

# Maximum number of recent conversation turns to keep.
# Each turn = 1 user message + 1 assistant message (2 items).
MAX_HISTORY_TURNS = 10
MAX_HISTORY_ITEMS = MAX_HISTORY_TURNS * 2


def trim_history(history: List[Dict]) -> List[Dict]:
    """
    Trim conversation history to the most recent MAX_HISTORY_ITEMS entries.

    Keeps only the last N messages to prevent context overflow when sending
    history to the LLM. Always returns a list of dicts with 'role' and 'content'.

    Args:
        history: List of message dicts with 'role' and 'content' keys.

    Returns:
        Trimmed list (at most MAX_HISTORY_ITEMS items).
    """
    if not history:
        return []

    # Normalize: accept both {role, content} and {sender, text} formats
    normalized = []
    for item in history:
        role = item.get("role") or item.get("sender") or "user"
        content = item.get("content") or item.get("text") or ""
        normalized.append({"role": role, "content": content})

    # Keep only the most recent turns
    if len(normalized) > MAX_HISTORY_ITEMS:
        normalized = normalized[-MAX_HISTORY_ITEMS:]

    return normalized
