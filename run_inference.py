"""
run_inference.py — Local Inference Entry Point
==============================================

Usage
-----
    # API mode (default) — no local model download required:
    python3 run_inference.py

    # Local mode — requires GPU + base model download (~6 GB):
    python3 run_inference.py --local

Note: API mode uses the *base* Qwen model via HuggingFace's Serverless
Inference API.  Local mode loads the base model and merges your
fine-tuned LoRA adapter on top of it, giving production-quality results.
"""

from __future__ import annotations

import argparse
import logging
import sys
import traceback
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Load .env so HF_TOKEN is available ────────────────────────────────────────
_env_path = _ROOT / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen Medical Assistant CLI")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local model + LoRA adapter instead of HF API.",
    )
    return parser.parse_args()


def main() -> None:
    _configure_logging()
    args = _parse_args()

    backend = "local" if args.local else "api"
    cfg = Config()

    logger.info("Starting Qwen Medical Assistant (backend=%s)", backend)
    assistant = MedicalAssistant(cfg, backend=backend)
    assistant.load()

    print("\n" + "=" * 60)
    print(f"  Qwen Medical Assistant  [{backend.upper()} MODE]")
    print("  Type 'quit' to exit")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("Exiting...")
                break
            if not user_input:
                continue

            response = assistant.generate(user_input)
            print(f"\nAssistant:\n{'-' * 60}\n{response}\n{'-' * 60}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as exc:
            logger.error("Generation error: %s", exc)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Aborted: %s", exc)
        sys.exit(1)
    except Exception:
        logger.error("Unexpected error:\n%s", traceback.format_exc())
        sys.exit(2)
