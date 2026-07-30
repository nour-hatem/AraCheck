"""
MedicalAssistant
================
Supports two inference backends:

  local  — loads the base model locally, merges the fine-tuned LoRA
           adapter on top of it, and runs inference on-device.
           Requires a GPU and ~6 GB of free VRAM / RAM.

  api    — calls the base model through HuggingFace's Serverless
           Inference API.  No local model download required.
           Useful for development, CI testing, and machines without
           a capable GPU.

           Note: the API mode uses the *base* Qwen model, not the
           fine-tuned LoRA weights. Use local mode for production
           results that reflect your training.

Usage
-----
    from src.inference import MedicalAssistant

    # API mode (no GPU / download required)
    assistant = MedicalAssistant(cfg, backend="api")
    assistant.load()
    print(assistant.generate("What are symptoms of diabetes?"))

    # Local mode (GPU + base model download required)
    assistant = MedicalAssistant(cfg, backend="local")
    assistant.load()
    print(assistant.generate("What are symptoms of diabetes?"))
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import torch

if TYPE_CHECKING:
    from configs import Config

logger = logging.getLogger(__name__)

Backend = Literal["local", "api"]


class MedicalAssistant:
    """
    Unified interface for running inference against the fine-tuned
    Qwen2.5 model, regardless of which backend is used.

    Parameters
    ----------
    config:
        The centralised :class:`~configs.Config` instance.
    backend:
        ``"local"`` — loads model + LoRA weights locally.
        ``"api"``   — uses HuggingFace Serverless Inference API.
    """

    def __init__(self, config: Config, backend: Backend = "local") -> None:
        self.config  = config
        self.backend: Backend = backend

        self._model     = None
        self._tokenizer = None
        self._client    = None      # HF InferenceClient (api mode only)

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load the model/client based on the chosen backend."""
        if self.backend == "api":
            self._load_api()
        else:
            self._load_local()

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """Generate a medical response for the given user prompt."""
        if self.backend == "api":
            return self._generate_api(prompt, max_new_tokens)
        return self._generate_local(prompt, max_new_tokens)

    # ── API backend ───────────────────────────────────────────────────────────

    def _load_api(self) -> None:
        """Initialise the HuggingFace InferenceClient."""
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError(
                "huggingface_hub is required for API mode. "
                "Run: pip install huggingface_hub"
            )

        import os
        token = os.environ.get("HF_TOKEN") or None

        logger.info(
            "API mode: connecting to HF Inference API for '%s'",
            self.config.api_model_name,
        )
        self._client = InferenceClient(
            model=self.config.api_model_name,
            token=token,
        )
        logger.info("HF InferenceClient ready.")

    def _generate_api(self, prompt: str, max_new_tokens: int) -> str:
        """Generate a response via the HF Serverless Inference API."""
        if self._client is None:
            raise RuntimeError("Call load() before generate().")

        messages = [{"role": "user", "content": prompt}]
        response = self._client.chat.completions.create(
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
        )
        return response.choices[0].message.content

    # ── Local backend ─────────────────────────────────────────────────────────

    def _load_local(self) -> None:
        """Load the base model locally and merge the LoRA adapter."""
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        lora_path = self.config.lora_save_dir
        if not lora_path.exists():
            raise FileNotFoundError(
                f"LoRA weights not found at: {lora_path}\n"
                "Run the training pipeline first, or download "
                "Qwen_Medical_LoRA into the models/ directory."
            )

        if not torch.cuda.is_available():
            logger.warning(
                "No CUDA GPU detected — loading base model on CPU. "
                "This will be very slow. Consider using backend='api' for testing."
            )

        logger.info("Loading base model: %s", self.config.base_model_name)
        device = "auto" if torch.cuda.is_available() else "cpu"
        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            device_map=device,
            dtype=torch.float16,
        )

        logger.info("Merging LoRA adapter from: %s", lora_path)
        self._model = PeftModel.from_pretrained(base_model, str(lora_path))
        self._model.eval()

        self._tokenizer = AutoTokenizer.from_pretrained(str(lora_path))
        logger.info("Local model loaded successfully.")

    def _generate_local(self, prompt: str, max_new_tokens: int) -> str:
        """Generate a response using the locally loaded PeftModel."""
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Call load() before generate().")

        messages = [{"role": "user", "content": prompt}]
        formatted = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        device = next(self._model.parameters()).device
        inputs = self._tokenizer(formatted, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        input_length = inputs.input_ids.shape[1]
        generated_tokens = outputs[0][input_length:]
        return self._tokenizer.decode(generated_tokens, skip_special_tokens=True)


def generate_answer(
    query: str,
    history: list = None,
    context: str = None,
    system_prompt: str = None,
    max_tokens: int = 1024,
) -> dict:
    from configs import Config
    import re
    
    try:
        cfg = Config()
    except Exception:
        # Fallback dummy config if needed
        class DummyConfig:
            api_model_name = "Qwen/Qwen2.5-7B-Instruct"
        cfg = DummyConfig()
    
    # Use API backend for testing easily without GPU
    assistant = MedicalAssistant(cfg, backend="api")
    try:
        assistant.load()
    except Exception as e:
        logger.warning(f"Failed to load API backend: {e}. Falling back to llm_stub...")
        try:
            from src.agent_pipeline.llm_stub import generate_answer as fallback_generate
            return fallback_generate(query, history=history, context=context, system_prompt=system_prompt, max_tokens=max_tokens)
        except ImportError:
            return {"answer": None, "confident": False}

    if not system_prompt:
        system_prompt = (
            "You are AraDoc, a precise and helpful Arabic and English medical AI assistant. "
            "Answer clearly, accurately, and concisely in the same language the user wrote in. "
            "Do NOT hallucinate, repeat yourself, or fabricate medical facts. "
            "Stop naturally as soon as the answer is complete and fully addresses the query. "
            "If context is provided, use it strictly and cite sources as [1], [2]. "
            "If you are not sure about a medical question, say so honestly."
        )

    # Check for greeting
    greeting_patterns = re.compile(
        r"^(hi|hello|hey|سلام|هلا|هاي|مرحبا|مرحبا|أهلا|اهلا|ازيك|ازيك|"
        r"عامل ايه|عاملة ايه|كيفك|كيف حالك|شو أخبارك|صباح الخير|مساء الخير|"
        r"شكراً|شكرا|thanks|thank you|ok|okay|تمام|ماشي|bye|مع السلامة)[؟?!.\s]*$",
        re.IGNORECASE | re.UNICODE,
    )
    if not context and greeting_patterns.match(query.strip()):
        prompt = f"System: {system_prompt}\nUser: {query}"
        try:
            answer = assistant.generate(prompt, max_new_tokens=min(max_tokens, 150))
            return {"answer": answer.strip(), "confident": True}
        except Exception:
            return {"answer": "أهلاً بك! كيف يمكنني مساعدتك في استفساراتك الطبية؟", "confident": True}

    if context:
        prompt = (
            f"System: {system_prompt}\n\n"
            f"Using the following medical context, answer the question accurately.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"CRITICAL INSTRUCTION: Always output your entire response EXCLUSIVELY in the user's language (Arabic or English). "
            f"If the context contains foreign text (e.g. Chinese), TRANSLATE it into the user's language. "
            f"NEVER include Chinese or foreign non-Arabic/English characters in your output. "
            f"Rely strictly on the factual content, structure the answer clearly, and cite sources as [1], [2] where appropriate."
        )
    else:
        prompt = (
            f"System: {system_prompt}\n\n"
            f"Medical question: {query}\n\n"
            f"Answer in the same language as the question. "
            f"If you are confident in your medical knowledge, provide a clear, factual answer without filler. "
            f"If you are NOT confident or this is outside medical scope, "
            f"respond with exactly: I_AM_NOT_CONFIDENT"
        )
    
    try:
        answer = assistant.generate(prompt, max_new_tokens=max_tokens).strip()
        if not context:
            if "I_AM_NOT_CONFIDENT" in answer or len(answer) < 20:
                return {"answer": None, "confident": False}
        return {"answer": answer, "confident": True}
    except Exception as e:
        logger.error(f"[inference] Error generating answer: {e}")
        return {"answer": None, "confident": False}
