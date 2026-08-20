#!/usr/bin/env python3
"""
Project Bankai — Kaggle CPU Fast Training
Strategy: CPU + bfloat16 + 30 steps + 512 tokens → completes in ~35 mins
Target: krishivjoshi/bankai-10b + krishivjoshi/bankai-7b
"""
import os, sys, glob, time, gzip, shutil, subprocess

print("=" * 70)
print("  PROJECT BANKAI — FAST CPU TRAINING — KAGGLE")
print("=" * 70)

HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
print(f"\n💻 Mode: CPU (Kaggle assigns P100/PyTorch2.5 incompatible — using host RAM)")
print(f"   CPU threads available: {torch.get_num_threads()}")
torch.set_num_threads(4)

# ── Install ──────────────────────────────────────────────────────────────────
print("\n📦 Installing packages...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "peft==0.11.1", "accelerate>=0.33.0",
    "datasets", "huggingface_hub"], check=False, capture_output=True)

from transformers import (AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from huggingface_hub import HfApi

# ── Locate Dataset ────────────────────────────────────────────────────────────
dataset_path = None
for p in [
    "/kaggle/input/bankai-flagship-expanded/bankai_train_flagship_expanded.jsonl",
    "/kaggle/input/bankai-frontier-100k/bankai_train_100k_frontier.jsonl",
]:
    if os.path.exists(p):
        dataset_path = p; break

if not dataset_path:
    gz = glob.glob("/kaggle/input/**/*.jsonl.gz", recursive=True)
    if gz:
        dataset_path = "/tmp/bankai_train.jsonl"
        with gzip.open(gz[0], 'rb') as fi, open(dataset_path, 'wb') as fo:
            shutil.copyfileobj(fi, fo)
    else:
        found = glob.glob("/kaggle/input/**/*.jsonl", recursive=True)
        if found: dataset_path = found[0]

print(f"✔ Dataset: {dataset_path}")

# ── Load Model (CPU bfloat16) ─────────────────────────────────────────────────
model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
print(f"\n🧠 Loading {model_id} on CPU (bfloat16)...")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id, device_map="cpu",
    trust_remote_code=True, torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
)
model.config.use_cache = False

# ── LoRA (r=8 for CPU speed) ──────────────────────────────────────────────────
peft_cfg = LoraConfig(
    task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
    lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "v_proj"],  # only 2 modules → 2x faster on CPU
)
model = get_peft_model(model, peft_cfg)
model.print_trainable_parameters()

# ── Tokenize (2000 samples, 512 tokens → fast) ────────────────────────────────
print(f"\n📑 Tokenizing dataset (2000 samples, max_length=512)...")
ds = load_dataset("json", data_files=dataset_path, split="train")
ds = ds.select(range(min(2000, len(ds))))

def tokenize(examples):
    texts = [tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False) for c in examples["messages"]]
    enc = tokenizer(texts, truncation=True, max_length=512, padding=False)
    enc["labels"] = enc["input_ids"].copy()
    return enc

tokenized = ds.map(tokenize, batched=True, remove_columns=ds.column_names)
print(f"✔ Tokenized {len(tokenized):,} samples")

# ── Train (30 steps × 8 accumulation = 240 microbatches ≈ 35 mins) ───────────
MAX_STEPS = 30
print(f"\n🔥 Training {MAX_STEPS} steps on CPU (~35 minutes)...")
args = TrainingArguments(
    output_dir="/kaggle/working/bankai_model",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    warmup_steps=5,
    max_steps=MAX_STEPS,
    learning_rate=3e-4,
    bf16=False, fp16=False,
    use_cpu=True,
    logging_steps=5,
    weight_decay=0.01,
    optim="adamw_torch",
    lr_scheduler_type="cosine",
    seed=3407,
    report_to="none",
    dataloader_num_workers=0,
)

trainer = Trainer(
    model=model, args=args, train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(
        tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
    ),
)

t0 = time.time()
trainer.train()
elapsed = (time.time() - t0) / 60
model.save_pretrained("/kaggle/working/bankai_model")
tokenizer.save_pretrained("/kaggle/working/bankai_model")
print(f"✔ Training complete in {elapsed:.1f} minutes! Saved to /kaggle/working/bankai_model")

# ── Push to Hugging Face ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  UPLOADING TO HUGGING FACE HUB")
print("=" * 70)
api = HfApi(token=HF_TOKEN)

for repo in ["krishivjoshi/bankai-10b", "krishivjoshi/bankai-7b"]:
    print(f"\n🚀 Pushing to {repo}...")
    try:
        model.push_to_hub(repo, token=HF_TOKEN, private=True)
        tokenizer.push_to_hub(repo, token=HF_TOKEN, private=True)
        print(f"✔ Uploaded to {repo}")
    except Exception as e:
        print(f"⚠ push_to_hub failed ({e}) — trying upload_folder...")
        try:
            api.upload_folder(
                folder_path="/kaggle/working/bankai_model",
                repo_id=repo, repo_type="model",
                commit_message="Bankai LoRA v1 — Project Bankai",
            )
            print(f"✔ upload_folder to {repo} succeeded!")
        except Exception as e2:
            print(f"❌ Both methods failed for {repo}: {e2}")

print("\n" + "=" * 70)
print("  PROJECT BANKAI — COMPLETE!")
print("  https://huggingface.co/krishivjoshi/bankai-10b")
print("  https://huggingface.co/krishivjoshi/bankai-7b")
print("=" * 70)
