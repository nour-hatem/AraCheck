"""
src/settings.py
---------------
Application settings and runtime feature flags.
Loads environment variables from ..env (or legacy '.env') relative to the project root.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_dotenv_path = _PROJECT_ROOT / "..env"
if not _dotenv_path.exists():
    _dotenv_path = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_dotenv_path)


class _Settings:
    """Runtime settings — populated from environment variables at import time."""

    # Feature flags
    ENABLE_VOICE_INPUT: bool = os.getenv("ENABLE_VOICE_INPUT", "true").lower() == "true"
    ENABLE_PDF_INGESTION: bool = os.getenv("ENABLE_PDF_INGESTION", "true").lower() == "true"
    ENABLE_IMAGE_ANALYSIS: bool = os.getenv("ENABLE_IMAGE_ANALYSIS", "true").lower() == "true"

    # Security
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "changeme-aracheck-admin")

    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")

    # Resolved paths
    PROJECT_ROOT: Path = _PROJECT_ROOT
    CONFIGS_DIR: Path = _PROJECT_ROOT / "configs"
    SCRIPTS_DIR: Path = _PROJECT_ROOT / "scripts"
    LOGS_DIR: Path = _PROJECT_ROOT / "logs"


settings = _Settings()

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
    if hasattr(settings, flag_name):
        setattr(settings, flag_name, enabled)
    return True
