"""
Fine-tuning configuration for Qwen2.5 with QLoRA.

All hyperparameters and paths live here. Change values in this file only;
never hard-code them inside training logic.

Usage:
    from configs import Config

    cfg = Config()          # default settings
    cfg.validate()          # raises immediately if anything is wrong
    print(cfg)              # human-readable summary for logging
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import torch

logger = logging.getLogger(__name__)

# Project root is two levels above this file: <root>/configs/config.py
_ROOT: Path = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    """
    Centralised, self-validating configuration for the QLoRA fine-tuning
    pipeline.

    All paths are resolved to absolute paths at instantiation time so the
    pipeline behaves identically regardless of the working directory it is
    launched from.
    """

    # ── Data ──────────────────────────────────────────────────────────────────
    # Output of the Preprocessing pipeline (dataset_20k.csv by default).
    # Supports both .csv and .xlsx.
    data_path: Path = field(default_factory=lambda: _ROOT / "data" / "dataset_20k.csv")

    # Fraction of data held out for evaluation
    eval_split: float = 0.1

    # ── Model ─────────────────────────────────────────────────────────────────
    base_model_name: str = "Qwen/Qwen2.5-3B-Instruct"

    # Directory where HuggingFace Trainer saves checkpoints
    output_dir: Path = field(default_factory=lambda: _ROOT / "models" / "Qwen_Medical")

    # Set to a Path to resume from an existing checkpoint; None = start fresh
    # Example: _ROOT / "models" / "Qwen_Medical" / "checkpoint-1500"
    checkpoint_path: Path | None = None

    # Directory where the final LoRA adapter is saved after training
    lora_save_dir: Path = field(default_factory=lambda: _ROOT / "models" / "Qwen_Medical_LoRA")

    # ── Quantization (BitsAndBytes / QLoRA) ───────────────────────────────────
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"        # "nf4" | "fp4"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_compute_dtype: torch.dtype = field(
        default_factory=lambda: torch.float16
    )

    # ── LoRA ──────────────────────────────────────────────────────────────────
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: tuple[str, ...] = field(
        default_factory=lambda: (
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        )
    )

    # ── Training ──────────────────────────────────────────────────────────────
    train_batch_size: int = 2
    eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8

    # Effective batch size = train_batch_size × gradient_accumulation_steps = 16
    learning_rate: float = 2e-4
    max_steps: int = 2500
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01

    lr_scheduler_type: str = "cosine"
    optimizer: str = "paged_adamw_8bit"

    # ── Logging & checkpointing ────────────────────────────────────────────────
    logging_steps: int = 20
    eval_steps: int = 500
    save_steps: int = 500
    save_total_limit: int = 2           # keep only the last N checkpoints
    load_best_model_at_end: bool = True

    # ── System ────────────────────────────────────────────────────────────────
    # fp16=True  for older GPUs (T4, V100)
    # fp16=False for newer GPUs that support bf16 (A100, H100)
    use_fp16: bool = True
    seed: int = 42

    # ── Post-init ─────────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        # Ensure all paths are absolute Path objects
        self.data_path = Path(self.data_path).resolve()
        self.output_dir = Path(self.output_dir).resolve()
        self.lora_save_dir = Path(self.lora_save_dir).resolve()
        if self.checkpoint_path is not None:
            self.checkpoint_path = Path(self.checkpoint_path).resolve()

    # ── Public API ────────────────────────────────────────────────────────────

    def validate(self) -> None:
        """
        Raise a descriptive exception immediately if any configuration value
        is invalid.  Call this once at the top of main() so failures are
        caught before the model is loaded.
        """
        errors: list[str] = []

        # Data file must exist before we start loading a 7-billion-parameter model
        if not self.data_path.exists():
            errors.append(
                f"data_path not found: '{self.data_path}'\n"
                f"  → Copy the preprocessed dataset (dataset_20k.csv) to: "
                f"{self.data_path.parent}"
            )

        if not (0.0 < self.eval_split < 1.0):
            errors.append(
                f"eval_split must be in (0, 1), got {self.eval_split}"
            )

        if self.lora_r <= 0 or (self.lora_r & (self.lora_r - 1)) != 0:
            errors.append(
                f"lora_r should be a positive power of 2, got {self.lora_r}"
            )

        if self.checkpoint_path is not None and not self.checkpoint_path.exists():
            errors.append(
                f"checkpoint_path does not exist: '{self.checkpoint_path}'"
            )

        if errors:
            msg = "Config validation failed with the following errors:\n" + "\n".join(
                f"  [{i + 1}] {e}" for i, e in enumerate(errors)
            )
            raise ValueError(msg)

        logger.info("Config validated successfully.")

    def summary(self) -> str:
        """Return a human-readable multi-line string for logging at startup."""
        lines = [
            "=" * 60,
            "  Fine-Tuning Configuration",
            "=" * 60,
            f"  base_model      : {self.base_model_name}",
            f"  data_path       : {self.data_path}",
            f"  output_dir      : {self.output_dir}",
            f"  lora_save_dir   : {self.lora_save_dir}",
            f"  checkpoint_path : {self.checkpoint_path or 'None (fresh start)'}",
            "  ─── LoRA ───────────────────────────────────────────",
            f"  r={self.lora_r}  alpha={self.lora_alpha}  dropout={self.lora_dropout}",
            "  ─── Training ───────────────────────────────────────",
            f"  max_steps={self.max_steps}  lr={self.learning_rate}",
            f"  batch={self.train_batch_size}  grad_accum={self.gradient_accumulation_steps}",
            f"  effective_batch={self.train_batch_size * self.gradient_accumulation_steps}",
            f"  fp16={self.use_fp16}  seed={self.seed}",
            "=" * 60,
        ]
        return "\n".join(lines)
