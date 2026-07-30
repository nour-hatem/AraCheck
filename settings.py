"""
settings.py
-----------
Application-level settings and feature flags for AraCheck backend.
Settings are loaded from environment variables via .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class _Settings:
    """Runtime settings — read once from environment at import time."""

    # ─── Feature Flags ────────────────────────────────────────────────────────
    # Controls whether the /transcribe (voice-to-text) endpoint is active.
    ENABLE_VOICE_INPUT: bool = os.getenv("ENABLE_VOICE_INPUT", "true").lower() == "true"

    # Controls whether the /upload-pdf ingestion endpoint is active.
    ENABLE_PDF_INGESTION: bool = os.getenv("ENABLE_PDF_INGESTION", "true").lower() == "true"

    # Controls whether the /analyze-image endpoint is active.
    ENABLE_IMAGE_ANALYSIS: bool = os.getenv("ENABLE_IMAGE_ANALYSIS", "true").lower() == "true"

    # ─── Security ─────────────────────────────────────────────────────────────
    # Admin secret key required in the x-admin-key header for flag updates.
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "changeme-aracheck-admin")

    # ─── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")


settings = _Settings()

# ─── Mutable flag registry (updated at runtime via PATCH /flags) ──────────────
_FLAGS: dict[str, bool] = {
    "ENABLE_VOICE_INPUT":    settings.ENABLE_VOICE_INPUT,
    "ENABLE_PDF_INGESTION":  settings.ENABLE_PDF_INGESTION,
    "ENABLE_IMAGE_ANALYSIS": settings.ENABLE_IMAGE_ANALYSIS,
}


def get_active_flags() -> dict[str, bool]:
    """Return a snapshot of all current feature flags."""
    return dict(_FLAGS)


def update_flag(flag_name: str, enabled: bool) -> bool:
    """
    Update a feature flag at runtime.

    Returns True if the flag was found and updated, False otherwise.
    """
    if flag_name not in _FLAGS:
        return False
    _FLAGS[flag_name] = enabled
    # Keep settings object in sync so existing code using settings.X still works
    if hasattr(settings, flag_name):
        setattr(settings, flag_name, enabled)
    return True
