"""
run_training.py — Fine-Tuning Pipeline Entry Point
====================================================

Usage
-----
Run from the project root (the directory containing this file):

    python run_training.py

The script:
  1. Validates the configuration (fails immediately with a clear message
     if something is wrong — before loading the model).
  2. Loads the Qwen2.5-3B-Instruct base model with 4-bit QLoRA.
  3. Formats the dataset using the Qwen chat template.
  4. Runs the HuggingFace Trainer for `max_steps` steps.
  5. Saves the final LoRA adapter weights to `config.lora_save_dir`.
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
# Insert the project root into sys.path so that `configs` and `src` are
# importable regardless of which directory the script is launched from.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Local imports ──────────────────────────────────────────────────────────────
from configs import Config
from src import DatasetBuilder, ModelManager, TrainingManager


# ── Logging setup ──────────────────────────────────────────────────────────────
def _configure_logging() -> None:
    """
    Set up a consistent logging format for the whole pipeline.
    Adjust the level to ``logging.DEBUG`` for more verbose output.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger(__name__)


# ── Pipeline ───────────────────────────────────────────────────────────────────
def main() -> None:
    _configure_logging()

    # ── Step 0: Load and validate configuration ────────────────────────────────
    cfg = Config()
    cfg.validate()              # raises ValueError with actionable message if invalid
    logger.info(cfg.summary())

    # ── Step 1: Load model + tokenizer ────────────────────────────────────────
    # Model must be loaded first so its tokenizer is available for chat
    # template formatting in the next step.
    model_manager = ModelManager(cfg)
    model, tokenizer = model_manager.setup()

    # ── Step 2: Build datasets ─────────────────────────────────────────────────
    dataset_builder = DatasetBuilder(cfg, tokenizer)
    train_ds, eval_ds = dataset_builder.build()

    # ── Step 3: Configure trainer ──────────────────────────────────────────────
    training_manager = TrainingManager(cfg, model, tokenizer, train_ds, eval_ds)
    training_manager.setup()

    # ── Step 4: Train ──────────────────────────────────────────────────────────
    training_manager.train()

    # ── Step 5: Save LoRA adapters ─────────────────────────────────────────────
    training_manager.save()

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as exc:
        # Configuration or data errors — print cleanly without a full traceback
        logger.error("Pipeline aborted: %s", exc)
        sys.exit(1)
    except Exception:
        # Unexpected errors — show the full traceback for debugging
        logger.error("Unexpected error:\n%s", traceback.format_exc())
        sys.exit(2)
