"""
src/main.py
-----------
AraCheck FastAPI backend — entry point.

Endpoints:
  POST /chat           — Medical AI agent chat
  POST /transcribe     — Audio -> text (Whisper STT)
  POST /analyze-image  — Medical image analysis (VLM)
  POST /upload-pdf     — PDF ingestion into Qdrant
  GET  /flags          — List feature flags
  PATCH /flags/{name}  — Toggle a feature flag (requires x-admin-key)
  GET  /health         — Health check

Run from the project root with:
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import uuid
import tempfile
import logging
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aracheck")


def _parse_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", getattr(settings, "ALLOWED_ORIGINS", ""))
    if not raw or raw.strip() == "*":
        return ["*"]
    defaults = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]
    parsed = [o.strip() for o in raw.split(",") if o.strip()]
    for d in defaults:
        if d not in parsed:
            parsed.append(d)
    return parsed


# ─── Settings (must be imported early — also triggers .env loading) ───────────
from src.settings import settings, get_active_flags, update_flag

# ─── Agent & pipeline imports ─────────────────────────────────────────────────
from src.agent_pipeline.graph import ask
from src.agent_pipeline.image_understanding import analyze_medical_image
from src.core.context_manager import trim_history

# ─── Schema imports ───────────────────────────────────────────────────────────
from src.schemas import (
    ChatRequest,
    ChatResponse,
    TranscribeResponse,
    ErrorResponse,
    ImageAnalysisResponse,
    PdfUploadResponse,
    FlagUpdateRequest,
)

# ─── Validation imports ───────────────────────────────────────────────────────
from src.core.validation import (
    validate_audio_file,
    validate_audio_bytes,
    validate_image_file,
    validate_image_bytes,
    validate_pdf_file,
    validate_pdf_bytes,
)

# ─── RAG ingestion import ─────────────────────────────────────────────────────
from src.rag_ingestion.pdf_ingestor import process_and_ingest_pdf


limiter = Limiter(key_func=get_remote_address)


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "تم تجاوز الحد المسموح من الطلبات، حاول مرة أخرى بعد قليل"},
    )


# ─── Whisper — lazy-loaded on first /transcribe call ─────────────────────────
_whisper_model = None


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            whisper_size = os.getenv("WHISPER_MODEL", "small")
            _whisper_model = whisper.load_model(whisper_size)
            logger.info(f"[whisper] Model loaded: {whisper_size}")
        except Exception:
            logger.error("[whisper] Failed to load model", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="خدمة تحويل الصوت غير متاحة حالياً، يرجى المحاولة لاحقاً.",
            )
    return _whisper_model


async def _global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


app = FastAPI(title="AraCheck API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, _global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ─── Chat ─────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    """Run the AraCheck medical agent and return its response."""
    try:
        trimmed_history = trim_history([item.model_dump() for item in req.history])
        result = ask(req.message, trimmed_history)

        answer = result.get("answer") or "عذراً، لم أتمكن من العثور على إجابة واضحة."
        source = result.get("source") or "unknown"

        return ChatResponse(
            id=str(uuid.uuid4()),
            role="assistant",
            content=answer,
            source=source,
        )
    except Exception:
        logger.error("Chat processing failed", exc_info=True)
        err = ErrorResponse(detail="Chat processing failed", error_code="chat_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err.dict(),
        )


# ─── Transcribe (Voice -> Text) ───────────────────────────────────────────────

@app.post("/transcribe", response_model=TranscribeResponse)
@limiter.limit("10/minute")
async def transcribe_endpoint(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("ar"),
):
    """Receive an audio file and return its Whisper transcription strictly using the selected language (ar/en)."""
    if not settings.ENABLE_VOICE_INPUT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ميزة تحويل الصوت إلى نص معطلة مؤقتاً من قبل المسؤول.",
        )

    validate_audio_file(file)
    contents = await file.read()
    validate_audio_bytes(contents)

    target_lang = "en" if language.lower() in ("en", "english") else "ar"

    suffix = os.path.splitext(file.filename or "audio.webm")[-1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    # Language-specific Whisper prompt for domain vocabulary priming
    if target_lang == "ar":
        prompt_text = (
            "استشارة طبية باللغة العربية والعامية المصرية الفصيحة: "
            "عندي صداع، ألم، سخونية، حرارة، مغص، علاج، دواء، سلام عليكم، حاسس بتعب، ضغط، سكر، عامل ايه، ازيك، اخبارك، كله تمام."
        )
    else:
        prompt_text = (
            "Medical consultation in English: "
            "I have a headache, fever, pain, cough, prescription, medicine, symptoms, doctor, how are you."
        )

    try:
        groq_key = os.getenv("GROQ_API_KEY", "")
        # Groq Cloud Whisper (primary)
        if groq_key and groq_key != "gsk_PUT_YOUR_GROQ_KEY_HERE":
            try:
                from groq import Groq
                groq_client = Groq(api_key=groq_key)
                with open(tmp_path, "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(os.path.basename(tmp_path), audio_file.read()),
                        model="whisper-large-v3",
                        prompt=prompt_text,
                        response_format="json",
                        language=target_lang,
                        temperature=0.0,
                    )
                text = (transcription.text or "").strip()
                logger.info(f"[transcribe] Groq whisper-large-v3 successful (lang={target_lang})")
                return TranscribeResponse(text=text, language=target_lang)
            except Exception as ge:
                logger.warning(f"[transcribe] Groq Whisper failed ({ge}), falling back to local model.")

        # Local Whisper (fallback)
        model = get_whisper()

        result = model.transcribe(
            tmp_path,
            language=target_lang,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=prompt_text,
        )
        text = result.get("text", "").strip()
        return TranscribeResponse(text=text, language=target_lang)

    except HTTPException:
        raise
    except Exception:
        logger.error("Transcription failed", exc_info=True)
        err = ErrorResponse(
            detail="فشل تحويل الصوت إلى نص، يرجى المحاولة مرة أخرى.",
            error_code="transcription_error",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err.dict(),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            logger.error("Failed to delete temporary transcription file", exc_info=True)


# ─── Image Analysis ───────────────────────────────────────────────────────────

@app.post("/analyze-image", response_model=ImageAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_image_endpoint(request: Request, file: UploadFile = File(...)):
    """Receive a medical image and return extracted text + visual description."""
    if not settings.ENABLE_IMAGE_ANALYSIS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ميزة تحليل الصور معطلة مؤقتاً من قبل المسؤول.",
        )

    validate_image_file(file)
    contents = await file.read()
    validate_image_bytes(contents)

    suffix = os.path.splitext(file.filename or "image.jpg")[-1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = analyze_medical_image(tmp_path)
        return ImageAnalysisResponse(
            extracted_text=result.get("extracted_text", ""),
            visual_description=result.get("visual_description", ""),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error("Image analysis failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ImageAnalysisResponse(
                extracted_text="", visual_description="", error=str(e)
            ).dict(),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            logger.error("Failed to delete temporary image file", exc_info=True)


# ─── Feature Flags ────────────────────────────────────────────────────────────

@app.get("/flags")
async def get_flags_endpoint():
    """Return all current feature flags."""
    return get_active_flags()


@app.patch("/flags/{flag_name}")
async def update_flag_endpoint(
    flag_name: str,
    req: FlagUpdateRequest,
    request: Request,
):
    """Toggle a feature flag (requires x-admin-key header)."""
    admin_key = request.headers.get("x-admin-key")
    if admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="مفتاح الإدارة غير صحيح أو مفقود.",
        )

    if not update_flag(flag_name, req.enabled):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"الـ Flag '{flag_name}' غير موجود.",
        )

    logger.info(f"[Feature Flag] {flag_name} -> {req.enabled}")
    return {"flag": flag_name, "enabled": req.enabled, "status": "updated"}


# ─── PDF Upload & Ingestion ───────────────────────────────────────────────────

@app.post("/upload-pdf", response_model=PdfUploadResponse)
@limiter.limit("5/minute")
async def upload_pdf_endpoint(request: Request, file: UploadFile = File(...)):
    """Upload a medical PDF and ingest it into the Qdrant vector database."""
    if not settings.ENABLE_PDF_INGESTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ميزة رفع ومعالجة كتب الـ PDF معطلة مؤقتاً من قبل المسؤول.",
        )

    validate_pdf_file(file)
    contents = await file.read()
    validate_pdf_bytes(contents)

    filename = file.filename or "medical_document.pdf"
    suffix = os.path.splitext(filename)[-1] or ".pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = process_and_ingest_pdf(tmp_path, filename=filename)
        return PdfUploadResponse(
            filename=result["filename"],
            total_pages=result["total_pages"],
            total_chunks=result["total_chunks"],
            status=result["status"],
        )
    except ValueError as ve:
        logger.warning(f"PDF validation warning: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("PDF ingestion failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=PdfUploadResponse(
                filename=filename,
                total_pages=0,
                total_chunks=0,
                status="error",
                detail=f"فشلت معالجة ملف الـ PDF: {str(e)}",
            ).dict(),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            logger.error("Failed to delete temporary PDF file", exc_info=True)


# ─── Dev runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
