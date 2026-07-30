"""
llm_stub.py
-----------
LLM backend — Groq (primary) with HuggingFace fallback.
Uses Qwen/2.5-32b on Groq for fast, free inference.
Handles greetings/casual chat directly without escalating to RAG.
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")

# Groq model — Qwen 2.5-32B (closest to the original Qwen 2.5-72B used on HF)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen-qwq-32b")
# HuggingFace fallback model (used only if GROQ_API_KEY is missing)
HF_MODEL   = "Qwen/Qwen2.5-7B-Instruct"

_groq_client = None
_hf_client   = None

# Common greetings, personal intro, and casual non-medical queries
_CASUAL_PATTERNS = re.compile(
    r"^(hi|hello|hey|good morning|good evening|good night|how are you|how r u|"
    r"سلام|هلا|هاي|مرحبا|أهلا|اهلا|ازيك|ازيك|"
    r"عامل ايه|عاملة ايه|كيفك|كيف حالك|كيف الحال|شو أخبارك|شو اخبارك|"
    r"صباح الخير|مساء الخير|مساء النور|صباح النور|"
    r"شكراً|شكرا|thanks|thank you|ok|okay|تمام|ماشي|bye|مع السلامة|"
    r"نعم|لا|أيوه|آه|يسعدك|يعطيك العافية|الله يعافيك|"
    r"كله تمام|كلها تمام|عظيم|تمام التمام|"
    r"انا\s+|اسمي|عمري\s+|عندي\s+\d+|من انا|مين انا|ما اسمي|كم عمري|عمري كام|اسمي ايه|"
    r"شو اسمي|ما هو اسمي|ما هو عمري|تتذكر|تذكر|فاكر)[؟?!.\s]*",
    re.IGNORECASE | re.UNICODE,
)

# Short non-medical phrases that shouldn't trigger RAG/web
_NON_MEDICAL_KEYWORDS = re.compile(
    r"(يوم|النهاردة|امبارح|بكرة|الوقت|الساعة|الطقس|اخبار|جديد|"
    r"today|yesterday|tomorrow|time|weather|news|date|"
    r"كلام|حكي|قصص|فلم|موسيقى|رياضة|كورة|مباراة)",
    re.IGNORECASE | re.UNICODE,
)


def _get_client():
    """Return a Groq client if GROQ_API_KEY is set, else fall back to HF InferenceClient."""
    global _groq_client, _hf_client
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_PUT_YOUR_GROQ_KEY_HERE":
        if _groq_client is None:
            try:
                from groq import Groq
                _groq_client = Groq(api_key=GROQ_API_KEY)
                logger.info("[llm_stub] Using Groq backend — model: %s", GROQ_MODEL)
            except ImportError:
                logger.warning("[llm_stub] groq package not installed, falling back to HF")
        if _groq_client:
            return _groq_client, GROQ_MODEL
    # Fallback: HuggingFace InferenceClient
    if _hf_client is None:
        from huggingface_hub import InferenceClient
        _hf_client = InferenceClient(api_key=HF_TOKEN)
        logger.info("[llm_stub] Using HuggingFace backend — model: %s", HF_MODEL)
    return _hf_client, HF_MODEL


def _is_greeting(query: str) -> bool:
    """Returns True if the query is a greeting, personal intro, or casual non-medical message."""
    q = query.strip()
    if _CASUAL_PATTERNS.search(q):
        return True
    # Catch short queries asking about user's identity/name/age
    keywords = ["اسمي", "عمري", "مين انا", "من انا", "مين أنت", "مين انت", "من أنت", "من انت"]
    if any(kw in q for kw in keywords) and len(q.split()) < 10:
        return True
    # Catch short casual/non-medical chit-chat (≤5 words and no medical signal)
    if len(q.split()) <= 5 and _NON_MEDICAL_KEYWORDS.search(q):
        return True
    return False



def format_messages(system_prompt: str, history: list = None, user_message: str = "") -> list:
    """Formats system prompt, conversation history, and current user message into HF/OpenAI chat format."""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-8:]:  # Keep last 8 turns for memory context
            role = msg.get("role")
            if not role:
                sender = str(msg.get("sender", "")).lower()
                role = "user" if sender in ("user", "human") else "assistant"
            content = msg.get("content") or msg.get("text") or ""
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


def generate_answer(
    query: str,
    history: list = None,
    context: str = None,
    system_prompt: str = None,
    max_tokens: int = 1024,
) -> dict:
    """
    Generates a medical answer using HuggingFace Inference API with chat memory.

    - If query is a greeting/casual message: responds warmly and returns
      confident=True so the agent doesn't escalate to RAG.
    - If context is provided (from RAG or web): uses it to ground the answer.
    - If no context: tries to answer from LLM's own medical knowledge.
      Returns confident=False if the model signals it doesn't know, so the
      agent can escalate to RAG.
    """
    if not system_prompt:
        system_prompt = (
            "You are AraDoc, a precise and helpful Arabic and English medical AI assistant. "
            "Answer clearly, accurately, and concisely in the same language the user wrote in. "
            "Do NOT hallucinate, repeat yourself, or fabricate medical facts. "
            "Stop naturally as soon as the answer is complete and fully addresses the query. "
            "If context is provided, use it strictly and cite sources as [1], [2]. "
            "If you are not sure about a medical question, say so honestly."
        )

    # --- Handle greetings & casual memory queries directly without calling RAG ---
    if not context and _is_greeting(query):
        try:
            client, model = _get_client()
            messages = format_messages(system_prompt, history, query)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=min(max_tokens, 250),
                temperature=0.5,
            )
            answer = response.choices[0].message.content.strip()
            return {"answer": answer, "confident": True}
        except Exception as e:
            logger.warning("[llm_stub] Casual chat error: %s", e)
            return {"answer": "أهلاً بك! كيف يمكنني مساعدتك في استفساراتك الطبية؟", "confident": True}

    # --- Handle context-grounded answers (RAG / Web) ---
    if context:
        user_message = (
            f"Using the following medical context, answer the question accurately.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"CRITICAL INSTRUCTION: Always output your entire response EXCLUSIVELY in the user's language (Arabic or English). "
            f"If the context contains foreign text (e.g. Chinese), TRANSLATE it into the user's language. "
            f"NEVER include Chinese or foreign non-Arabic/English characters in your output. "
            f"Rely strictly on the factual content, structure the answer clearly, and cite sources as [1], [2] where appropriate."
        )
    else:
        # --- Try answering from LLM's own knowledge ---
        user_message = (
            f"Medical question: {query}\n\n"
            f"Answer in the same language as the question. "
            f"If you are confident in your medical knowledge, provide a clear, factual answer without filler. "
            f"If you are NOT confident or this is outside medical scope, "
            f"respond with exactly: I_AM_NOT_CONFIDENT"
        )

    try:
        client, model = _get_client()
        messages = format_messages(system_prompt, history, user_message)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        answer = response.choices[0].message.content.strip()

        # If no context, check if model expressed uncertainty
        if not context:
            if "I_AM_NOT_CONFIDENT" in answer or len(answer) < 20:
                return {"answer": None, "confident": False}
            return {"answer": answer, "confident": True}

        # With context, always return the generated answer
        return {"answer": answer, "confident": True}

    except Exception as e:
        logger.error("[llm_stub] Error calling API: %s", e)
        return {"answer": None, "confident": False}
