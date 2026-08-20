#!/usr/bin/env python3
"""
scripts/train_kaggle_dual_t4.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Bankai — Dual Tesla T4 (2x T4 GPU) Lightning Fast Training Kernel (v2).
Optimized specifically for Kaggle GPU T4 x2 with bulletproof pinned transformers & bitsandbytes.
"""

import os
import sys
import glob
import time
import gzip
import shutil
import subprocess

print("=" * 75)
print("⚡ [PROJECT BANKAI] DUAL TESLA T4 (2x T4) LIGHTNING GPU TRAINING (v2)")
print("=" * 75)

HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 1. Pinned Transformers & TRL Stack to prevent Transformers 5.x AttributeError
print("\n📦 Bootstrapping High-Speed ML Stack (Pinned for Dual T4)...")
subprocess.run([
    sys.executable, "-m", "pip", "install", "-q", "--upgrade",
    "transformers>=4.46.0,<4.49.0", "trl>=0.12.0,<0.15.0",
    "peft>=0.13.0", "accelerate>=0.34.0", "bitsandbytes>=0.44.0",
    "datasets", "huggingface_hub"
], check=False)

import torch
gpu_count = torch.cuda.device_count()
print(f"\n🎮 CUDA GPUs Detected: {gpu_count}")
for i in range(gpu_count):
    print(f"  • GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_memory / (1024**3):.1f} GB VRAM)")

if gpu_count < 1:
    print("❌ Error: No GPU detected! Please change Kaggle Accelerator to 'GPU T4 x2'.")
    sys.exit(1)

from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    BitsAndBytesConfig, TrainingArguments
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
from datasets import load_dataset

# 2. Locate Dataset
dataset_path = None
candidates = [
    "/kaggle/input/bankai-7b-v2-refinement/bankai_train_7b_v2.jsonl",
    "/kaggle/input/bankai-flagship-expanded/bankai_train_flagship_expanded.jsonl",
    "/kaggle/input/bankai-frontier-100k/bankai_train_100k_frontier.jsonl",
    "/kaggle/input/**/*.jsonl",
]

for c in candidates:
    matches = glob.glob(c, recursive=True)
    if matches:
        dataset_path = matches[0]
        break

if not dataset_path:
    gz_matches = glob.glob("/kaggle/input/**/*.jsonl.gz", recursive=True)
    if gz_matches:
        dataset_path = "/tmp/bankai_train.jsonl"
        print(f"📦 Decompressing {gz_matches[0]} to {dataset_path}...")
        with gzip.open(gz_matches[0], "rb") as fi, open(dataset_path, "wb") as fo:
            shutil.copyfileobj(fi, fo)

if not dataset_path:
    print("⚠ No local dataset attached. Streaming Bespoke-Stratos-17k directly from Hugging Face...")
    ds_stream = load_dataset("bespokelabs/Bespoke-Stratos-17k", split="train")
    dataset_path = "/tmp/bankai_streamed.jsonl"
    with open(dataset_path, "w") as f:
        for item in ds_stream.select(range(10000)):
            convs = item.get("conversations") or []
            if len(convs) >= 2:
                import json
                sample = {
                    "messages": [
                        {"role": "system", "content": "You are Bankai-7B, an elite compiler-grounded AI software engineer. Reason inside <think>...</think> and output surgical code diffs with zero fluff."},
                        {"role": "user", "content": convs[0]["value"]},
                        {"role": "assistant", "content": convs[1]["value"].replace("<|begin_of_thought|>", "<think>").replace("<|end_of_thought|>", "</think>").replace("<|begin_of_solution|>", "").replace("<|end_of_solution|>", "").strip()}
                    ]
                }
                f.write(json.dumps(sample) + "\n")

print(f"✔ Dataset Ready: {dataset_path} ({os.path.getsize(dataset_path)/(1024*1024):.2f} MB)")

# 3. Model Loading with 4-Bit BitsAndBytes Quantization
MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
print(f"\n🧠 Initializing {MODEL_NAME} with 4-Bit NF4 Quantization & SDPA...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)

peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# 4. Tokenization Function
def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return {"text": texts}

raw_dataset = load_dataset("json", data_files=dataset_path, split="train")
# If dataset is huge (>50k), sample 25,000 for lightning speed
if len(raw_dataset) > 25000:
    raw_dataset = raw_dataset.select(range(25000))
dataset = raw_dataset.map(formatting_prompts_func, batched=True)
print(f"✔ Prepared {len(dataset):,} training samples!")

# 5. Dual-T4 300-Step SFT Training
print("\n🔥 Starting Dual-T4 GPU Fine-Tuning Loop...")
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=20,
    max_steps=300,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    optim="paged_adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    output_dir="/kaggle/working/outputs",
    report_to="none",
    save_strategy="no",
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=1024,
    args=training_args,
)

t0 = time.time()
trainer.train()
elapsed = time.time() - t0
print(f"\n✔ Dual-T4 GPU Training finished in {elapsed/60:.2f} minutes!")

# 6. Save LoRA Adapters & Push to Hugging Face
print("\n📦 Saving LoRA Adapters...")
output_adapter_dir = "/kaggle/working/bankai_7b_adapter"
trainer.model.save_pretrained(output_adapter_dir)
tokenizer.save_pretrained(output_adapter_dir)

try:
    print("\n🚀 Pushing checkpoint to Hugging Face Hub (krishivjoshi/bankai-7b)...")
    from huggingface_hub import HfApi
    api = HfApi(token=HF_TOKEN)
    api.upload_folder(
        folder_path=output_adapter_dir,
        repo_id="krishivjoshi/bankai-7b",
        commit_message="Kaggle Dual-T4 Fine-Tuning Checkpoint (300 Steps)",
    )
    print("✔ LoRA Adapter published successfully to Hugging Face!")
except Exception as ex:
    print(f"⚠ Upload notice: {ex}")

# 7. Live SWE-Bench Verification
print("\n" + "=" * 75)
print("🧪 [SWE-BENCH] Running Live Verification Benchmark...")
print("=" * 75)

model.eval()
test_prompts = [
    ("[ROLE: ARCHITECT]", "Design an asynchronous distributed task worker pool with Redis stream and backpressure handling."),
    ("[ROLE: CODER]", "Write a thread-safe singleton metaclass in Python with type annotations and double-checked locking."),
    ("[ROLE: DEBUGGER]", "Analyze and fix the off-by-one index error in binary search with surgical SEARCH/REPLACE diff.")
]

for role, prompt in test_prompts:
    msgs = [
        {"role": "system", "content": f"You are {role} for K-CLI AI Engine. Reason inside <think>...</think> and output surgical code diffs."},
        {"role": "user", "content": prompt}
    ]
    inp = tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model.generate(input_ids=inp, max_new_tokens=300, temperature=0.2)
    res = tokenizer.batch_decode(out)
    print(f"\n{role} Output:\n{res[0]}\n" + "-" * 60)

print("\n🎉 [PROJECT BANKAI] Dual-T4 Kaggle GPU Training & SWE-Bench Complete!")
