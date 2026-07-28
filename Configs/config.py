import torch

class Config:
    """Centralized configuration for the project."""
    
    # Data paths
    RAW_DATA_PATH = "data/AHD_english.xlsx"
    PROCESSED_DATA_PATH = "data/processed_medical_data.csv"
    
    # Model paths and identifiers
    BASE_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
    OUTPUT_DIR = "models/Qwen_Medical"
    CHECKPOINT_PATH = "models/Qwen_Medical/checkpoint-1500"
    LORA_SAVE_DIR = "models/Qwen_Medical_LoRA"
    
    # Hugging Face Hub
    HF_REPO_ID = "nour-hatem/Qwen-Medical"
    HF_TOKEN = "YOUR_HF_TOKEN_HERE"
    
    # Quantization settings
    LOAD_IN_4BIT = True
    BNB_4BIT_COMPUTE_DTYPE = torch.float16
    
    # LoRA settings
    LORA_R = 16
    LORA_ALPHA = 32
    LORA_DROPOUT = 0.05
    
    # Training settings
    TRAIN_BATCH_SIZE = 2
    EVAL_BATCH_SIZE = 2
    GRADIENT_ACCUMULATION_STEPS = 8
    LEARNING_RATE = 2e-4
    MAX_STEPS = 2500
    WARMUP_RATIO = 0.03
    WEIGHT_DECAY = 0.01
    
    # Generation settings
    MAX_NEW_TOKENS = 256
    TEMPERATURE = 0.7
    TOP_P = 0.9
    REPETITION_PENALTY = 1.2
