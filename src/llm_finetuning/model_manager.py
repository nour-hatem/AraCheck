"""
ModelManager
============
Handles all HuggingFace model and tokenizer setup for QLoRA fine-tuning:

  1. Load the Qwen2.5 tokenizer.
  2. Load the base model with 4-bit BitsAndBytes quantization.
  3. Enable gradient checkpointing.
  4. Prepare the model for k-bit training (freezes base weights).
  5. Attach LoRA adapters via PEFT.

After calling :meth:`setup`, the returned ``(model, tokenizer)`` tuple is
ready to be handed directly to the Trainer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

if TYPE_CHECKING:
    from configs import Config
    from peft import PeftModel
    from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Encapsulates model loading, quantization, and LoRA setup.

    Parameters
    ----------
    config:
        The centralised :class:`~configs.Config` instance.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._model: PeftModel | None = None
        self._tokenizer: PreTrainedTokenizerBase | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def setup(self) -> tuple[PeftModel, PreTrainedTokenizerBase]:
        """
        Execute the full model setup sequence and return
        ``(lora_model, tokenizer)``.

        Raises
        ------
        RuntimeError
            If no CUDA-capable GPU is detected.
        """
        self._check_device()
        self._tokenizer = self._load_tokenizer()
        model = self._load_quantized_model()
        model = self._prepare_for_lora(model)
        self._model = self._attach_lora(model)
        self._log_trainable_params()
        return self._model, self._tokenizer

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_device(self) -> None:
        if not torch.cuda.is_available():
            raise RuntimeError(
                "No CUDA-capable GPU detected. "
                "QLoRA fine-tuning requires at least one GPU."
            )
        device_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info("GPU detected: %s (%.1f GB VRAM)", device_name, vram_gb)

    def _load_tokenizer(self) -> PreTrainedTokenizerBase:
        logger.info("Loading tokenizer: %s", self.config.base_model_name)
        tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True,
        )
        # Qwen2.5 does not define a dedicated pad token; reuse eos.
        # padding_side="right" avoids shape mismatches during causal training.
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        return tokenizer

    def _load_quantized_model(self) -> AutoModelForCausalLM:
        logger.info(
            "Loading model with 4-bit quantization: %s",
            self.config.base_model_name,
        )
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.config.load_in_4bit,
            bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.config.bnb_4bit_use_double_quant,
            bnb_4bit_compute_dtype=self.config.bnb_4bit_compute_dtype,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=self.config.bnb_4bit_compute_dtype,
        )
        # Disable the built-in cache — incompatible with gradient checkpointing
        model.config.use_cache = False
        return model

    def _prepare_for_lora(self, model: AutoModelForCausalLM) -> AutoModelForCausalLM:
        """Enable gradient checkpointing and freeze quantized base weights."""
        model.gradient_checkpointing_enable()
        return prepare_model_for_kbit_training(model)

    def _attach_lora(self, model: AutoModelForCausalLM) -> PeftModel:
        logger.info(
            "Attaching LoRA adapters (r=%d, alpha=%d) to: %s",
            self.config.lora_r,
            self.config.lora_alpha,
            list(self.config.lora_target_modules),
        )
        lora_cfg = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(self.config.lora_target_modules),
        )
        return get_peft_model(model, lora_cfg)

    def _log_trainable_params(self) -> None:
        """Log the ratio of LoRA-trainable vs frozen base-model parameters."""
        total     = sum(p.numel() for p in self._model.parameters())
        trainable = sum(p.numel() for p in self._model.parameters() if p.requires_grad)
        logger.info(
            "Trainable parameters: %s / %s (%.4f%%)",
            f"{trainable:,}",
            f"{total:,}",
            100.0 * trainable / total,
        )
