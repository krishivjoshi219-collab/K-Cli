#!/usr/bin/env python3
"""
scripts/train_remote_7b.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
Remote Unsloth LoRA Fine-Tuning & GGUF Export for Project Bankai (7B Coder).

Executes directly on remote Colab / GPU runtime:
- Base Model: `unsloth/Qwen2.5-Coder-7B-Instruct` (4-bit QLoRA)
- Dataset: `/content/bankai_train_7b_v1.jsonl`
- Steps: 300 steps (Batch=2, Accum=4, Warmup=20, LR=2e-4) with adaptive fallback to Batch=1, Accum=8 on OOM
- Persistent GDrive Backup: `/content/drive/MyDrive/Bankai_Models/bankai_7b/`
- Hugging Face Backup: `krishivjoshi/bankai-7b`
- Export: 4-bit `q4_k_m` GGUF
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 1. Dependency Auto-Bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def ensure_colab_dependencies() -> None:
    print("=" * 70)
    print("⚡ [PROJECT BANKAI] Checking and bootstrapping Colab 7B ML stack...")
    print("=" * 70)

    try:
        import unsloth
        import unsloth_zoo
        import trl
        import transformers
    except (ImportError, ModuleNotFoundError):
        print("[INSTALL] Installing Unsloth ML stack...")
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
        subprocess.check_call(cmd)
        print("✔ [INSTALL] All dependencies installed successfully.")
    else:
        print("✔ [INSTALL] Dependencies already satisfied.")


ensure_colab_dependencies()

# CRITICAL: Import unsloth BEFORE transformers/trl/peft
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template

import torch
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer


# ─────────────────────────────────────────────────────────────────────────────
# 2. Main 7B Training & Export Workflow
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    DATASET_PATH = Path("/content/bankai_train_7b_v1.jsonl")
    OUTPUT_GGUF_DIR = Path("/content/bankai_7b_model")
    GDRIVE_MODEL_DIR = Path("/content/drive/MyDrive/Bankai_Models/bankai_7b")
    HF_REPO_ID = "krishivjoshi/bankai-7b"
    BASE_MODEL_NAME = "unsloth/Qwen2.5-Coder-7B-Instruct"
    MAX_SEQ_LENGTH = 2048
    MAX_STEPS = 300
    WARMUP_STEPS = 20
    LEARNING_RATE = 2e-4
    BATCH_SIZE = 2
    GRAD_ACCUM_STEPS = 4

    print("\n" + "=" * 70)
    print("🚀 [PROJECT BANKAI] Starting Remote 7B Fine-Tuning Pipeline")
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
    print("📥 Loading and preparing 7B dataset from JSONL...")
    records = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Loaded {len(records):,} training samples.")
    dataset = Dataset.from_list(records)

    # 3. Load Base 7B Model with 4-bit Quantization
    print(f"\n🧠 Loading base model '{BASE_MODEL_NAME}' in 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
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
    print("\n🔧 Attaching LoRA adapters to 7B model (r=16, alpha=16)...")
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

    # 6. Configure Trainer (with Adaptive Memory Fallback)
    print("\n⚙ Configuring SFTTrainer & AdamW 8-bit optimizer...")
    
    def build_trainer(batch_size: int, grad_accum: int) -> SFTTrainer:
        training_args = TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=grad_accum,
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
            output_dir="/content/outputs_7b",
            report_to="none",
        )
        kwargs = {
            "model": model,
            "train_dataset": dataset,
            "dataset_text_field": "text",
            "max_seq_length": MAX_SEQ_LENGTH,
            "dataset_num_proc": 2,
            "packing": False,
            "args": training_args,
        }
        try:
            return SFTTrainer(processing_class=tokenizer, **kwargs)
        except TypeError:
            try:
                return SFTTrainer(tokenizer=tokenizer, **kwargs)
            except TypeError:
                return SFTTrainer(**kwargs)

    try:
        trainer = build_trainer(BATCH_SIZE, GRAD_ACCUM_STEPS)
        print("\n🔥 Executing 7B LoRA Fine-Tuning (Batch=2, Accum=4)...")
        start_time = time.time()
        trainer_stats = trainer.train()
    except (torch.cuda.OutOfMemoryError, RuntimeError) as oom_err:
        if "out of memory" in str(oom_err).lower() or "cuda" in str(oom_err).lower():
            print("\n⚠ CUDA OOM detected! Dynamically adapting to Batch=1, Accum=8...")
            torch.cuda.empty_cache()
            trainer = build_trainer(batch_size=1, grad_accum=8)
            start_time = time.time()
            trainer_stats = trainer.train()
        else:
            raise oom_err

    elapsed = time.time() - start_time
    print(f"\n✔ 7B Training complete in {elapsed / 60:.2f} minutes!")

    # 7. Export Directly to 4-Bit GGUF
    print("\n📦 Exporting fine-tuned 7B model directly into Q4_K_M GGUF format...")
    OUTPUT_GGUF_DIR.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained_gguf(
        str(OUTPUT_GGUF_DIR),
        tokenizer,
        quantization_method="q4_k_m",
    )

    # Search and locate generated GGUF files
    all_ggufs = glob.glob("/content/**/*.gguf", recursive=True)
    for g in all_ggufs:
        if "q4_k_m" in g.lower() or "qwen" in g.lower():
            import shutil
            shutil.copy(g, "/content/bankai-7b.gguf")
            OUTPUT_GGUF_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(g, f"{OUTPUT_GGUF_DIR}/bankai-7b.gguf")
            print(f"✔ Mirrored GGUF to /content/bankai-7b.gguf ({os.path.getsize(g) / (1024 * 1024):.2f} MB)")
            
            # Persistent Google Drive Sync
            if gdrive_available:
                try:
                    target_gdrive_file = GDRIVE_MODEL_DIR / "bankai-7b.gguf"
                    shutil.copy(g, str(target_gdrive_file))
                    print(f"✔ Persisted 7B GGUF to Google Drive: {target_gdrive_file} ({os.path.getsize(g) / (1024 * 1024):.2f} MB)")
                except Exception as ex:
                    print(f"⚠ Failed to copy to Google Drive: {ex}")
            break

    # 8. Hugging Face Hub Backup
    if hf_token:
        try:
            print(f"\n🚀 Uploading 7B GGUF to Hugging Face Hub ({HF_REPO_ID})...")
            model.push_to_hub_gguf(
                HF_REPO_ID,
                tokenizer,
                quantization_method=["q4_k_m"],
                token=hf_token,
            )
        except Exception as hf_ex:
            print(f"⚠ Hugging Face upload notice: {hf_ex}")

    # 9. In-Colab Live K-CLI Verification & Reasoning Test
    print("\n" + "=" * 70)
    print("🧪 [TEST] Running Live K-CLI Reasoning Benchmark directly on Colab GPU...")
    print("=" * 70)

    test_prompts = [
        ("[ROLE: ARCHITECT]", "Design an asynchronous distributed task worker pool with Redis stream and backpressure handling. Provide memory bounds and formal Big-O proof."),
        ("[ROLE: CODER]", "Write a thread-safe singleton metaclass in Python with type annotations and double-checked locking."),
        ("[ROLE: DEBUGGER]", "Analyze and fix the off-by-one index error in binary search:\n```python\ndef bs(arr, t):\n    l, r = 0, len(arr)\n    while l <= r:\n        m = (l + r) // 2\n        if arr[m] == t: return m\n        elif arr[m] < t: l = m\n        else: r = m\n    return -1\n```\nProvide surgical SEARCH/REPLACE block."),
    ]

    FastLanguageModel.for_inference(model)
    for role, user_prompt in test_prompts:
        print(f"\n[EVALUATION PROMPT]: {role} {user_prompt[:80]}...")
        messages = [
            {"role": "system", "content": f"You are {role} for K-CLI AI Engine (Project Bankai). Reason inside <think>...</think> and emit pure unpadded code with zero fluff."},
            {"role": "user", "content": f"{role} {user_prompt}"},
        ]
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
        outputs = model.generate(input_ids=inputs, max_new_tokens=300, use_cache=True, temperature=0.2)
        decoded = tokenizer.batch_decode(outputs)
        print(f"\n[GENERATION RESULT]:\n{decoded[0]}")
        print("-" * 60)

    print("\n" + "=" * 70)
    print("🎉 [PROJECT BANKAI] 7B Fine-Tuning & Live In-Colab Verification Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
