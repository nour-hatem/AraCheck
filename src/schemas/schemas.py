"""
src/schemas/schemas.py
-----------------------
Pydantic models for all API request/response contracts.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[HistoryItem] = Field(default_factory=list)

    @validator("message")
    def message_must_not_be_empty_or_too_long(cls, v: str) -> str:
        if v is None:
            raise ValueError("message is required")
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty or whitespace")
        if len(v) > 4000:
            raise ValueError("message must be at most 4000 characters")
        return v


class ChatResponse(BaseModel):
    id: str
    role: str
    content: str
    source: Optional[str] = None


class TranscribeResponse(BaseModel):
    text: str
    language: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    extracted_text: str
    visual_description: str
    error: Optional[str] = None


class PdfUploadResponse(BaseModel):
    filename: str
    total_pages: int
    total_chunks: int
    status: str
    detail: Optional[str] = None


class FlagUpdateRequest(BaseModel):
    enabled: bool
