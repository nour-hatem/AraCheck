"""
MedicalAssistant
================
Handles loading the fine-tuned LoRA adapter and generating responses.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

if TYPE_CHECKING:
    from configs import Config

logger = logging.getLogger(__name__)


class MedicalAssistant:
    """
    Loads the base Qwen model and your fine-tuned LoRA adapter for inference.
    
    Parameters
    ----------
    config:
        The centralised :class:`~configs.Config` instance.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.model: PeftModel | None = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self) -> None:
        """
        Loads the base model and attaches the local LoRA weights.
        """
        lora_path = self.config.lora_save_dir
        
        if not lora_path.exists():
            raise FileNotFoundError(
                f"LoRA weights not found at {lora_path}\n"
                "Please run the training pipeline first, or download the "
                "Qwen_Medical_LoRA folder and place it in the models/ directory."
            )

        logger.info("Loading base model: %s", self.config.base_model_name)
        # We load the base model in fp16 as standard for inference
        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        logger.info("Loading fine-tuned LoRA adapter from: %s", lora_path)
        self.model = PeftModel.from_pretrained(base_model, str(lora_path))
        self.model.eval()
        
        self.tokenizer = AutoTokenizer.from_pretrained(str(lora_path))
        logger.info("Model and tokenizer loaded successfully.")

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Generates a medical response based on the user's prompt.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() before generate().")
            
        messages = [{"role": "user", "content": prompt}]
        formatted_prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        inputs = self.tokenizer(
            formatted_prompt, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        # Extract only the newly generated tokens (ignore the prompt tokens)
        input_length = inputs.input_ids.shape[1]
        generated_tokens = outputs[0][input_length:]
        
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
