"""Owner: Member 5.

Utilities for combining chat history, RAG context, and image analysis
into one bounded prompt context for the medical assistant.
"""
from __future__ import annotations
from collections.abc import Sequence

def _format_history_message(message: dict[str, str], max_message_chars: int) -> str:
    """Format one chat message into a prompt-friendly line block.
    Args:
        message: A single chat history item with role and content fields.
        max_message_chars: Maximum number of characters to keep from the
            message content before truncating it.
    Returns:
        A single formatted line ready to include in the prompt context.
    """
    role = message.get("role", "").strip().lower()
    content = message.get("content", "").strip()
    if len(content) > max_message_chars:
        content = content[:max_message_chars] + "..."
    if role == "assistant":
        prefix = "Assistant"
    else:
        prefix = "User"

    return f"{prefix}: {content}"

def _format_image_context(image_context: dict[str, str | None]) -> str:
    """Format image analysis output into a readable prompt section.

    Args:
        image_context: Image analysis data with extracted text, visual
            description, and optional error information.

    Returns:
        A readable prompt section for image-derived context.
    """
    parts: list[str] = []

    extracted_text = (image_context.get("extracted_text") or "").strip()
    visual_description = (image_context.get("visual_description") or "").strip()
    error = (image_context.get("error") or "").strip()

    if extracted_text:
        parts.append(f"Extracted text:\n{extracted_text}")
    if visual_description:
        parts.append(f"Visual description:\n{visual_description}")
    if error:
        parts.append(f"Image analysis note:\n{error}")

    return "\n\n".join(parts)

def build_context(
    query: str,
    chat_history: list[dict[str, str]] | None = None,
    rag_context: str | None = None,
    image_context: dict[str, str | None] | None = None,
    max_history_messages: int = 5,
    max_message_chars: int = 500,
) -> str:
    """Combine prompt inputs while capping chat history to avoid context bloat.
    Args:
        query: The current user query.
        chat_history: Optional list of recent chat messages.
        rag_context: Optional retrieved context from the RAG layer.
        image_context: Optional image analysis payload with extracted text
            and visual description.
        max_history_messages: Maximum number of recent chat messages to keep.
        max_message_chars: Maximum number of characters to keep per message
            before truncating long chat history content.
    Returns:
        A single prompt-ready string with query, history, RAG, and image
        sections separated clearly.
    """
    sections: list[str] = [f"Current query:\n{query.strip()}"]
    if chat_history:
        history_limit = max(0, max_history_messages)
        recent_history: Sequence[dict[str, str]] = chat_history[-history_limit:] if history_limit else []
        formatted_history = [
            _format_history_message(message, max_message_chars)
            for message in recent_history
            if message.get("content", "").strip()
        ]
        if formatted_history:
            sections.append("Chat history:\n" + "\n".join(formatted_history))
    if rag_context and rag_context.strip():
        sections.append("RAG context:\n" + rag_context.strip())

    if image_context:
        formatted_image_context = _format_image_context(image_context)
        if formatted_image_context:
            sections.append("Image context:\n" + formatted_image_context)
    return "\n\n---\n\n".join(sections)
