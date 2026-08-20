#!/usr/bin/env python3
"""
scripts/train_remote.py - Remote Unsloth LoRA Fine-Tuning & GGUF Export for Project Bankai

Self-contained fine-tuning script executed directly on the remote Google Colab VM.
- Auto-bootstraps missing packages: Unsloth, unsloth_zoo, TRL, Transformers, PEFT, Accelerate, bitsandbytes.
- Imports unsloth at the very top before transformers/trl/peft/datasets.
- Ingests ChatML-formatted dataset from /content/bankai_train_v2.jsonl.
- Quantized 4-bit LoRA SFT on `unsloth/Qwen2.5-Coder-3B-Instruct`.
- Emits quantized GGUF (`q4_k_m`) model to /content/bankai_3b_model.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# =====================================================================
# 1. Dependency Auto-Bootstrap
# =====================================================================

def ensure_colab_dependencies() -> None:
    """Verifies and automatically installs required Unsloth & ML stack on Colab."""
    print("=" * 70)
    print("⚡ [PROJECT BANKAI] Checking and bootstrapping Colab ML dependencies...")
    print("=" * 70)

    try:
        import unsloth
        import unsloth_zoo
        import trl
        import transformers
    except (ImportError, ModuleNotFoundError):
        print("[INSTALL] Missing dependencies detected. Installing Unsloth stack...")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "unsloth",
            "unsloth_zoo",
            "trl",
            "peft",
            "accelerate",
            "bitsandbytes",
            "datasets",
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print("✔ [INSTALL] All dependencies installed successfully.")
    else:
        print("✔ [INSTALL] Dependencies already satisfied.")


# Run bootstrap check before importing ML libraries
ensure_colab_dependencies()

# CRITICAL: Import unsloth BEFORE transformers, trl, peft, or datasets
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template

import torch
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer


# =====================================================================
# 2. Main Fine-Tuning & Export Workflow
# =====================================================================

def main() -> None:
    DATASET_PATH = Path("/content/bankai_train_v2.jsonl")
    OUTPUT_GGUF_DIR = Path("/content/bankai_3b_model")
    GDRIVE_MODEL_DIR = Path("/content/drive/MyDrive/Bankai_Models/bankai_3b")
    HF_REPO_ID = "krishivjoshi/bankai-3b"
    BASE_MODEL_NAME = "unsloth/Qwen2.5-Coder-3B-Instruct"
    MAX_SEQ_LENGTH = 2048
    MAX_STEPS = 250
    WARMUP_STEPS = 20
    LEARNING_RATE = 2e-4
    BATCH_SIZE = 2
    GRAD_ACCUM_STEPS = 4

    print("\n" + "=" * 70)
    print("🚀 [PROJECT BANKAI] Starting Remote Fine-Tuning Pipeline (3B Coder)")
    print(f"• Base Model: {BASE_MODEL_NAME} (4-bit)")
    print(f"• Dataset: {DATASET_PATH}")
    print(f"• Max Sequence Length: {MAX_SEQ_LENGTH}")
    print(f"• Target Steps: {MAX_STEPS} (Batch={BATCH_SIZE}, Accum={GRAD_ACCUM_STEPS}, Warmup={WARMUP_STEPS}, LR={LEARNING_RATE})")
    print(f"• Output GGUF Dir: {OUTPUT_GGUF_DIR}")
    print(f"• Persistent GDrive Dir: {GDRIVE_MODEL_DIR}")
    print(f"• Hugging Face Repo: {HF_REPO_ID}")
    print("=" * 70 + "\n")

    # 1. Mount Google Drive for Persistent Storage
    gdrive_available = False
    try:
        from google.colab import drive
        print("⚡ [STORAGE] Auto-mounting Google Drive to /content/drive...")
        drive.mount("/content/drive", force_remount=False)
        GDRIVE_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        gdrive_available = True
        print(f"✔ [STORAGE] Google Drive mounted successfully at {GDRIVE_MODEL_DIR}")
    except Exception as e:
        print(f"⚠ [STORAGE] Google Drive mount notice: {e}")

    # Read Hugging Face Token for Fail-safe Backup
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not hf_token and os.path.exists("/content/hf_token.txt"):
        try:
            with open("/content/hf_token.txt", "r", encoding="utf-8") as f:
                hf_token = f.read().strip()
        except Exception:
            pass

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found at {DATASET_PATH}. Please upload it first.")

    # 2. Load Dataset
    print("📥 Loading and preparing dataset from JSONL...")
    records = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Loaded {len(records)} training samples.")
    dataset = Dataset.from_list(records)

    # 3. Load Base Model with 4-bit Quantization
    print(f"\n🧠 Loading base model '{BASE_MODEL_NAME}' in 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detection
        load_in_4bit=True,
    )

    # 4. Configure ChatML Template
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="chatml",
        mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
    )

    def format_chatml(batch: dict) -> dict:
        texts = []
        for messages in batch["messages"]:
            formatted = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
            texts.append(formatted)
        return {"text": texts}

    print("Formatting dataset with ChatML template (<|im_start|> / <|im_end|>)...")
    dataset = dataset.map(format_chatml, batched=True)

    # 5. Attach LoRA PEFT Adapters
    print("\n🔧 Attaching LoRA adapters (r=16, alpha=16)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        max_seq_length=MAX_SEQ_LENGTH,
    )

    # 6. Configure Trainer
    print("\n⚙ Configuring SFTTrainer & AdamW 8-bit optimizer...")
    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM_STEPS,
        warmup_steps=WARMUP_STEPS,
        max_steps=MAX_STEPS,
        learning_rate=LEARNING_RATE,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="/content/outputs",
        report_to="none",
    )

    trainer_kwargs = {
        "model": model,
        "train_dataset": dataset,
        "dataset_text_field": "text",
        "max_seq_length": MAX_SEQ_LENGTH,
        "dataset_num_proc": 2,
        "packing": False,
        "args": training_args,
    }
    try:
        trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError:
        try:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)
        except TypeError:
            trainer = SFTTrainer(**trainer_kwargs)

    # 7. Execute Training
    print("\n🔥 Executing LoRA Fine-Tuning...")
    start_time = time.time()
    trainer_stats = trainer.train()
    elapsed = time.time() - start_time
    print(f"\n✔ Training complete in {elapsed / 60:.2f} minutes!")

    # 8. Export Directly to 4-Bit GGUF
    print("\n📦 Exporting fine-tuned model directly into Q4_K_M GGUF format...")
    OUTPUT_GGUF_DIR.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained_gguf(
        str(OUTPUT_GGUF_DIR),
        tokenizer,
        quantization_method="q4_k_m",
    )

    # Search and locate generated GGUF files
    all_ggufs = glob.glob("/content/**/*.gguf", recursive=True)
    primary_gguf = None
    for g in all_ggufs:
        if "q4_k_m" in g.lower() or "qwen" in g.lower():
            primary_gguf = g
            import shutil
            shutil.copy(g, "/content/bankai-3b.gguf")
            OUTPUT_GGUF_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(g, f"{OUTPUT_GGUF_DIR}/bankai-3b.gguf")
            print(f"✔ Mirrored GGUF to /content/bankai-3b.gguf ({os.path.getsize(g) / (1024 * 1024):.2f} MB)")
            
            # Persistent Google Drive Sync
            if gdrive_available:
                try:
                    target_gdrive_file = GDRIVE_MODEL_DIR / "bankai-3b.gguf"
                    shutil.copy(g, str(target_gdrive_file))
                    print(f"✔ Persisted GGUF to Google Drive: {target_gdrive_file} ({os.path.getsize(g) / (1024 * 1024):.2f} MB)")
                except Exception as ex:
                    print(f"⚠ Failed to copy to Google Drive: {ex}")
            break

    # 9. Hugging Face Hub Backup (Secondary Fail-safe)
    if hf_token:
        try:
            print(f"\n🚀 Uploading GGUF to Hugging Face Hub ({HF_REPO_ID})...")
            model.push_to_hub_gguf(
                HF_REPO_ID,
                tokenizer,
                quantization_method=["q4_k_m"],
                token=hf_token,
            )
            print(f"✔ Successfully uploaded model to Hugging Face: https://huggingface.co/{HF_REPO_ID}")
        except Exception as hf_ex:
            print(f"⚠ Hugging Face upload notice: {hf_ex}")

    gguf_candidates = (
        glob.glob(f"{OUTPUT_GGUF_DIR}/*.gguf")
        + glob.glob(f"{OUTPUT_GGUF_DIR}_gguf/*.gguf")
        + glob.glob("/content/**/*.gguf", recursive=True)
    )

    print("\n" + "=" * 70)
    print("🎉 [PROJECT BANKAI] Fine-Tuning & Persistent Export Successful!")
    if gguf_candidates:
        print("Generated GGUF artifacts:")
        for path in set(gguf_candidates):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  • {path} ({size_mb:.2f} MB)")
    if gdrive_available:
        print(f"Persistent Google Drive folder: {GDRIVE_MODEL_DIR}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
