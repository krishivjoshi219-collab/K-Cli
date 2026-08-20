#!/usr/bin/env python3
"""
scripts/train_remote_7b_v2.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Bankai — Refine Fine-Tuning Pipeline (Version 2).
Executes Unsloth 4-Bit QLoRA training on 25,000 DeepSeek-R1 & Systems reasoning samples.
"""

import os
import sys
import time
import glob
import shutil
import json
import gzip
import subprocess
from pathlib import Path

def ensure_colab_dependencies() -> None:
    print("=" * 75)
    print("⚡ [PROJECT BANKAI] Checking and bootstrapping Colab 7B ML stack...")
    print("=" * 75)
    try:
        import unsloth
        import trl
        import transformers
        print("✔ [INSTALL] Dependencies already satisfied.")
    except (ImportError, ModuleNotFoundError):
        print("[INSTALL] Installing Unsloth ML stack...")
        cmd = [
            sys.executable, "-m", "pip", "install", "--upgrade",
            "unsloth", "trl", "peft", "accelerate", "bitsandbytes", "datasets", "huggingface_hub"
        ]
        subprocess.check_call(cmd)
        print("✔ [INSTALL] All dependencies installed successfully.")

def locate_and_unpack_dataset() -> Path:
    target_jsonl = Path("/content/bankai_train_7b_v2.jsonl")
    if target_jsonl.exists() and os.path.getsize(target_jsonl) > 1024 * 1024:
        print(f"✔ Dataset already unpacked at {target_jsonl} ({os.path.getsize(target_jsonl) / (1024*1024):.2f} MB)")
        return target_jsonl

    # Search for gz archive across all standard Colab locations
    search_paths = [
        "/content/bankai_train_7b_v2.jsonl.gz",
        "./bankai_train_7b_v2.jsonl.gz",
        "/root/bankai_train_7b_v2.jsonl.gz",
        "bankai_train_7b_v2.jsonl.gz",
    ]
    found_gz = None
    for p in search_paths:
        if os.path.exists(p) and os.path.getsize(p) > 1024:
            found_gz = p
            break
            
    if not found_gz:
        # Broad recursive search
        matches = glob.glob("/**/bankai_train_7b_v2.jsonl*", recursive=True)
        for m in matches:
            if m.endswith(".gz") and os.path.getsize(m) > 1024:
                found_gz = m
                break
            elif m.endswith(".jsonl") and os.path.getsize(m) > 1024 * 1024:
                return Path(m)

    if found_gz:
        print(f"📦 Found dataset archive at {found_gz}. Decompressing to {target_jsonl}...")
        target_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(found_gz, "rb") as f_in, open(target_jsonl, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"✔ Successfully unpacked dataset to {target_jsonl} ({os.path.getsize(target_jsonl) / (1024*1024):.2f} MB)")
        return target_jsonl

    raise FileNotFoundError("Could not find bankai_train_7b_v2.jsonl or .jsonl.gz anywhere on the filesystem!")

def main():
    ensure_colab_dependencies()

    print("\n" + "=" * 75)
    print("  PROJECT BANKAI — 7B REFINE FINE-TUNING (VERSION 2)")
    print("=" * 75 + "\n")

    # 1. Hyperparameters
    MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
    MAX_SEQ_LENGTH = 1024
    DTYPE = None
    LOAD_IN_4BIT = True
    
    LORA_R = 16
    LORA_ALPHA = 32
    LORA_DROPOUT = 0
    TARGET_MODULES = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]
    
    BATCH_SIZE = 2
    GRAD_ACCUM_STEPS = 4
    MAX_STEPS = 400
    LEARNING_RATE = 1.5e-4
    
    OUTPUT_GGUF_DIR = Path("/content/bankai_7b_v2_model_gguf")
    HF_REPO_ID = "krishivjoshi/bankai-7b"
    HF_TOKEN = os.environ.get("HF_TOKEN")

    # 2. Locate Dataset
    TRAIN_DATA_PATH = locate_and_unpack_dataset()

    # 3. Load Model with Unsloth Fast Kernels
    print(f"\n🧠 Initializing {MODEL_NAME} with Unsloth 4-Bit Acceleration...")
    import torch
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from datasets import load_dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=DTYPE,
        load_in_4bit=LOAD_IN_4BIT,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    # 4. Tokenize and Format Dataset
    print(f"\n📑 Loading and Tokenizing 25,000 Refine Samples...")
    from unsloth.chat_templates import get_chat_template
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="qwen-2.5",
        mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant", "system": "system"},
    )

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    raw_dataset = load_dataset("json", data_files=str(TRAIN_DATA_PATH), split="train")
    dataset = raw_dataset.map(formatting_prompts_func, batched=True)
    print(f"✔ Ready with {len(dataset):,} training samples!")

    # 5. Execute Refine Fine-Tuning
    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM_STEPS,
        warmup_steps=20,
        max_steps=MAX_STEPS,
        learning_rate=LEARNING_RATE,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="/content/outputs_7b_v2",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    print("\n🔥 Starting Bankai-7B v2 Refinement Fine-Tuning Loop...")
    t_start = time.time()
    trainer.train()
    elapsed = time.time() - t_start
    print(f"\n✔ Refinement Training complete in {elapsed / 60:.2f} minutes!")

    # 6. Quantize Directly to 4-Bit GGUF & Hub Upload
    print("\n📦 Exporting Bankai-7B v2 directly into Q4_K_M GGUF format...")
    OUTPUT_GGUF_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_gguf(
        str(OUTPUT_GGUF_DIR),
        tokenizer,
        quantization_method="q4_k_m",
    )

    if HF_TOKEN:
        try:
            print(f"\n🚀 Pushing Bankai-7B v2 GGUF to Hugging Face Hub ({HF_REPO_ID})...")
            model.push_to_hub_gguf(
                HF_REPO_ID,
                tokenizer,
                quantization_method=["q4_k_m"],
                token=HF_TOKEN,
            )
            print("✔ Bankai-7B v2 GGUF pushed successfully to Hugging Face!")
        except Exception as ex:
            print(f"⚠ Hub push notice: {ex}")

    # 7. Post-training smoke prompts. This is not an official SWE-bench run.
    print("\n" + "=" * 75)
    print("🧪 Running post-training generation smoke prompts on Refined Bankai-7B v2...")
    print("=" * 75)
    
    test_suite = [
        ("[ROLE: ARCHITECT]", "Design an asynchronous distributed task worker pool with Redis stream and backpressure handling. Provide memory bounds and formal Big-O proof."),
        ("[ROLE: CODER]", "Write a thread-safe singleton metaclass in Python with type annotations and double-checked locking."),
        ("[ROLE: DEBUGGER]", "Analyze and fix the off-by-one index error in binary search with surgical SEARCH/REPLACE diff."),
        ("[ROLE: APPSec]", "Write a FastAPI middleware for constant-time HMAC-SHA256 signature verification."),
        ("[ROLE: C++23 SPECIALIST]", "Write a lock-free queue in C++23 with memory_order_acquire/release and alignas(64).")
    ]

    FastLanguageModel.for_inference(model)
    for role, prompt in test_suite:
        print(f"\n[EVALUATION PROMPT]: {role} {prompt[:70]}...")
        msgs = [
            {"role": "system", "content": f"You are {role} for K-CLI AI Engine. Reason inside <think>...</think> and output surgical code diffs."},
            {"role": "user", "content": prompt}
        ]
        inp = tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
        out = model.generate(input_ids=inp, max_new_tokens=400, temperature=0.2)
        res = tokenizer.batch_decode(out)
        print(f"\n[GENERATION RESULT]:\n{res[0]}\n" + "-" * 60)

    print("\n🎉 [PROJECT BANKAI] Refinement Training (v2) & smoke prompts complete!")

if __name__ == "__main__":
    main()
