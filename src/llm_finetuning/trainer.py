"""
TrainingManager
===============
Configures HuggingFace ``Trainer`` / ``TrainingArguments`` and manages the
train → save lifecycle.

Responsibilities
----------------
* Compute warmup steps dynamically from ``warmup_ratio`` so they scale
  automatically when ``max_steps`` or the effective batch size changes.
* Ensure output directories exist before any write attempt.
* Resume from a checkpoint transparently when ``config.checkpoint_path``
  is set.
* Save LoRA adapter weights and tokenizer to ``config.lora_save_dir``.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from transformers import (
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

if TYPE_CHECKING:
    from configs import Config
    from datasets import Dataset
    from peft import PeftModel
    from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)


class TrainingManager:
    """
    Thin wrapper around HuggingFace ``Trainer`` that keeps all
    ``TrainingArguments`` in sync with :class:`~configs.Config`.

    Parameters
    ----------
    config:
        Centralised configuration instance.
    model:
        LoRA-wrapped model returned by :class:`~src.ModelManager`.
    tokenizer:
        Tokenizer returned by :class:`~src.ModelManager`.
    train_ds:
        Training dataset returned by :class:`~src.DatasetBuilder`.
    eval_ds:
        Evaluation dataset returned by :class:`~src.DatasetBuilder`.
    """

    def __init__(
        self,
        config: Config,
        model: PeftModel,
        tokenizer: PreTrainedTokenizerBase,
        train_ds: Dataset,
        eval_ds: Dataset,
    ) -> None:
        self.config    = config
        self.model     = model
        self.tokenizer = tokenizer
        self.train_ds  = train_ds
        self.eval_ds   = eval_ds
        self._trainer: Trainer | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def setup(self) -> None:
        """Build ``TrainingArguments`` and initialise the ``Trainer``."""
        warmup_steps = self._compute_warmup_steps()

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        args = TrainingArguments(
            output_dir=str(self.config.output_dir),

            # Batch
            per_device_train_batch_size=self.config.train_batch_size,
            per_device_eval_batch_size=self.config.eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,

            # Optimisation
            learning_rate=self.config.learning_rate,
            max_steps=self.config.max_steps,
            warmup_steps=warmup_steps,
            weight_decay=self.config.weight_decay,
            optim=self.config.optimizer,
            lr_scheduler_type=self.config.lr_scheduler_type,

            # Precision
            fp16=self.config.use_fp16,

            # Logging
            logging_steps=self.config.logging_steps,

            # Evaluation
            eval_strategy="steps",
            eval_steps=self.config.eval_steps,

            # Checkpointing
            save_strategy="steps",
            save_steps=self.config.save_steps,
            save_total_limit=self.config.save_total_limit,
            load_best_model_at_end=self.config.load_best_model_at_end,

            # Reproducibility
            seed=self.config.seed,

            # Disable external experiment trackers (Weights & Biases, etc.)
            report_to="none",
        )

        self._trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=self.train_ds,
            eval_dataset=self.eval_ds,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,  # causal LM — no masked-language modelling
            ),
            processing_class=self.tokenizer,
        )

        logger.info(
            "Trainer ready — %d training steps, warmup=%d",
            self.config.max_steps,
            warmup_steps,
        )

    def train(self) -> None:
        """
        Start (or resume) training.

        Resumes automatically from ``config.checkpoint_path`` when set.
        """
        if self._trainer is None:
            raise RuntimeError("Call setup() before train().")

        checkpoint = (
            str(self.config.checkpoint_path)
            if self.config.checkpoint_path
            else None
        )

        if checkpoint:
            logger.info("Resuming training from checkpoint: %s", checkpoint)
        else:
            logger.info("Starting training from scratch.")

        self._trainer.train(resume_from_checkpoint=checkpoint)

    def save(self) -> None:
        """
        Persist the final LoRA adapter weights and tokenizer.

        The directory is created if it does not exist, so this works on a
        fresh environment without any manual ``mkdir``.
        """
        if self._trainer is None:
            raise RuntimeError("Call train() before save().")

        save_dir = self.config.lora_save_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Saving LoRA adapter to: %s", save_dir)
        self._trainer.model.save_pretrained(str(save_dir))
        self.tokenizer.save_pretrained(str(save_dir))
        logger.info("Model saved successfully.")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _compute_warmup_steps(self) -> int:
        """
        Derive the number of warmup steps from ``warmup_ratio`` so the
        value scales automatically with dataset size and batch size.

        Formula:
            effective_batch = train_batch_size × gradient_accumulation_steps
            steps_per_epoch = ceil(len(train_ds) / effective_batch)
            warmup_steps    = round(warmup_ratio × steps_per_epoch)
        """
        effective_batch = (
            self.config.train_batch_size
            * self.config.gradient_accumulation_steps
        )
        steps_per_epoch = math.ceil(len(self.train_ds) / effective_batch)
        warmup = max(1, round(self.config.warmup_ratio * steps_per_epoch))
        logger.debug(
            "Warmup: %d steps (ratio=%.2f, steps_per_epoch=%d)",
            warmup,
            self.config.warmup_ratio,
            steps_per_epoch,
        )
        return warmup
