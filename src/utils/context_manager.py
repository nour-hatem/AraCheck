def truncate_context(history: list, max_tokens: int = 2000) -> list:
    """
    Truncates the chat history to fit within a given token limit.
    This is a simple word-count based approximation.
    """
    truncated = []
    current_tokens = 0
    for msg in reversed(history):
        msg_len = len(msg.get("content", "").split())
        if current_tokens + msg_len > max_tokens:
            break
        truncated.insert(0, msg)
        current_tokens += msg_len
    return truncated
