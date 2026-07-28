"""
run_inference.py — Local Inference Entry Point
==============================================

Usage
-----
Run from the project root:

    python run_inference.py

This script will start an interactive chat session with your fine-tuned model.
It expects the LoRA weights to be present in the `models/Qwen_Medical_LoRA`
directory (as defined in `configs.config.lora_save_dir`).
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Local imports ──────────────────────────────────────────────────────────────
from configs import Config
from src.inference import MedicalAssistant


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger(__name__)


def main() -> None:
    _configure_logging()
    
    cfg = Config()
    assistant = MedicalAssistant(cfg)
    
    logger.info("Initializing Qwen Medical Assistant...")
    assistant.load()
    
    print("\n" + "=" * 60)
    print("  Qwen Medical Assistant (Type 'quit' to exit)")
    print("=" * 60 + "\n")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower().strip() in ["quit", "exit", "q"]:
                print("Exiting...")
                break
                
            if not user_input.strip():
                continue
                
            response = assistant.generate(user_input)
            
            print("\nAssistant:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error("Error during generation: %s", e)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        logger.error("Inference aborted: %s", exc)
        sys.exit(1)
    except Exception:
        logger.error("Unexpected error:\n%s", traceback.format_exc())
        sys.exit(2)
