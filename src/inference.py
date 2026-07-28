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
