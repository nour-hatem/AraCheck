"""
whisper_stt.py
--------------
Speech-to-text transcription module using Whisper.
"""
import logging
import whisper

logger = logging.getLogger(__name__)

WHISPER_MODEL_SIZE = "base"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(WHISPER_MODEL_SIZE)
        logger.info(f"[whisper_stt] Model loaded: {WHISPER_MODEL_SIZE}")
    return _model


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    model = get_model()
    result = model.transcribe(audio_path, language=language)

    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language"),
    }
