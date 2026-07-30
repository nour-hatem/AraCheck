"""
validation.py
-------------
File upload validation utilities for audio, image, and PDF files.
"""
from fastapi import UploadFile, HTTPException, status

# ─── Size Limits ──────────────────────────────────────────────────────────────
MAX_AUDIO_SIZE = 25 * 1024 * 1024   # 25 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_PDF_SIZE   = 25 * 1024 * 1024   # 25 MB

# ─── Allowed MIME Types ───────────────────────────────────────────────────────
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/mpeg",    # mp3
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
}

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

ALLOWED_PDF_TYPES = {
    "application/pdf",
    "application/x-pdf",
}


# ─── Audio ────────────────────────────────────────────────────────────────────

def validate_audio_file(file: UploadFile) -> None:
    """Validate the MIME type of an uploaded audio file."""
    content_type = (file.content_type or "").lower()
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Missing content type for uploaded file", "error_code": "missing_content_type"},
        )
    # Some clients report 'audio/mp4; codecs="..."' — use startswith
    if not any(content_type.startswith(t) for t in ALLOWED_AUDIO_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": f"Unsupported audio content type: {content_type}", "error_code": "unsupported_audio_type"},
        )


def validate_audio_bytes(contents: bytes) -> None:
    """Validate the raw bytes of an uploaded audio file."""
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Uploaded file is empty", "error_code": "empty_file"},
        )
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"detail": f"Uploaded file is too large (limit {MAX_AUDIO_SIZE} bytes)", "error_code": "file_too_large"},
        )


# ─── Image ────────────────────────────────────────────────────────────────────

def validate_image_file(file: UploadFile) -> None:
    """Validate the MIME type of an uploaded image file."""
    content_type = (file.content_type or "").lower()
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Missing content type for uploaded file", "error_code": "missing_content_type"},
        )
    if not any(content_type.startswith(t) for t in ALLOWED_IMAGE_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": f"Unsupported image content type: {content_type}", "error_code": "unsupported_image_type"},
        )


def validate_image_bytes(contents: bytes) -> None:
    """Validate raw bytes for an uploaded image."""
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Uploaded image is empty", "error_code": "empty_file"},
        )
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"detail": f"Uploaded image is too large (limit {MAX_IMAGE_SIZE} bytes)", "error_code": "image_too_large"},
        )


# ─── PDF ──────────────────────────────────────────────────────────────────────

def validate_pdf_file(file: UploadFile) -> None:
    """Validate the MIME type of an uploaded PDF file."""
    content_type = (file.content_type or "").lower()
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Missing content type for uploaded file", "error_code": "missing_content_type"},
        )
    if not any(content_type.startswith(t) for t in ALLOWED_PDF_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": f"Unsupported file type: {content_type}. Only PDF files are accepted.", "error_code": "unsupported_pdf_type"},
        )


def validate_pdf_bytes(contents: bytes) -> None:
    """Validate raw bytes for an uploaded PDF file."""
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Uploaded PDF file is empty", "error_code": "empty_file"},
        )
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"detail": f"Uploaded PDF is too large (limit {MAX_PDF_SIZE} bytes)", "error_code": "file_too_large"},
        )
