"""
src/schemas/__init__.py
-----------------------
Pydantic models for all API request/response contracts.
Re-exports everything from the main schemas module.
"""
from src.schemas.schemas import (
    HistoryItem,
    ChatRequest,
    ChatResponse,
    TranscribeResponse,
    ErrorResponse,
    ImageAnalysisResponse,
    PdfUploadResponse,
    FlagUpdateRequest,
)

__all__ = [
    "HistoryItem",
    "ChatRequest",
    "ChatResponse",
    "TranscribeResponse",
    "ErrorResponse",
    "ImageAnalysisResponse",
    "PdfUploadResponse",
    "FlagUpdateRequest",
]
