# AraCheck — Fine-Tuning Branch

QLoRA fine-tuning pipeline for **Qwen2.5-3B-Instruct** on the AHD medical Q&A dataset.

## Project Structure

```
.
├── configs/
│   ├── __init__.py
│   └── config.py          # All hyperparameters and paths — edit here only
├── src/
│   ├── __init__.py
│   ├── dataset_builder.py  # Loads data → Qwen chat-template format
│   ├── inference.py        # Local generation logic (MedicalAssistant)
│   ├── model_manager.py    # 4-bit quantization + LoRA adapter setup
│   └── trainer.py          # HuggingFace Trainer wrapper
├── data/                   # ← place dataset_20k.csv here (gitignored)
├── models/                 # ← checkpoints saved here (gitignored)
├── run_inference.py        # Interactive CLI for testing the model
├── run_training.py         # Entry point for fine-tuning
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Data

Copy the preprocessed dataset from the Preprocessing branch into `data/`:

```bash
cp <path_to_preprocessing_output>/dataset_20k.csv data/
```

Expected columns: `Question`, `Answer`.

## Configuration

All parameters live in `configs/config.py`. Key settings:

| Parameter | Default | Description |
|---|---|---|
| `base_model_name` | `Qwen/Qwen2.5-3B-Instruct` | HuggingFace model ID |
| `lora_r` | `16` | LoRA rank |
| `lora_alpha` | `32` | LoRA scaling factor |
| `learning_rate` | `2e-4` | Peak learning rate |
| `max_steps` | `2500` | Total training steps |
| `use_fp16` | `True` | Set to `False` for A100/H100 (use bf16) |

To resume from a checkpoint:
```python
# In configs/config.py
checkpoint_path: Path | None = _ROOT / "models" / "Qwen_Medical" / "checkpoint-1500"
```

## Running

```bash
python run_training.py
```

The pipeline will:
1. Validate the config and fail immediately with a clear message if anything is wrong.
2. Load the model with 4-bit quantization.
3. Format the dataset using the Qwen chat template.
4. Train for `max_steps` steps, saving checkpoints every `save_steps` steps.
5. Save the final LoRA adapter to `models/Qwen_Medical_LoRA/`.

## Local Inference (Testing the Model)

Once the model is trained, or if you downloaded the pre-trained `Qwen_Medical_LoRA` weights (e.g., from Kaggle/HuggingFace), you can test the model interactively.

If you downloaded the weights manually, place the folder inside the `models/` directory so it looks like this:
```text
models/
└── Qwen_Medical_LoRA/
    ├── adapter_model.safetensors
    ├── adapter_config.json
    ├── tokenizer.json
    └── ...
```

Run the interactive CLI:

```bash
python run_inference.py
```

This will load the base model, merge your local LoRA adapter on top of it, and open an interactive chat session in your terminal where you can prompt the medical assistant.

## Requirements

- CUDA-capable GPU (minimum 16 GB VRAM recommended for 3B model with QLoRA)
- Python 3.10+
