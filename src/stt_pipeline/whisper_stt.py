"""
whisper_stt.py
--------------
Owner: Member 4 (Agent & Web Search & Voice)
"""
import whisper

WHISPER_MODEL_SIZE = "base"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(WHISPER_MODEL_SIZE)
        print(f"[whisper_stt] Model loaded: {WHISPER_MODEL_SIZE}")
    return _model


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    model = get_model()
    result = model.transcribe(audio_path, language=language)

    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language"),
    }
