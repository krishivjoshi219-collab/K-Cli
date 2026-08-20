#!/usr/bin/env python3
"""
Project Bankai — Zero-Local-RAM Cloud Evaluation Suite
Executes 100% in Kaggle High-Memory Cloud Environment.
"""
import os, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

print("=" * 70)
print("  PROJECT BANKAI — CLOUD INFERENCE & PERSONA EVALUATION SUITE")
print("=" * 70)

HF_REPO = "krishivjoshi/bankai-7b"
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"

print(f"\n🧠 Loading base model ({BASE_MODEL}) + LoRA adapter ({HF_REPO}) in cloud...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.bfloat16,
    device_map="auto", trust_remote_code=True
)

try:
    model = PeftModel.from_pretrained(base_model, HF_REPO)
    print("✔ Fine-tuned LoRA adapters loaded successfully!")
except Exception as e:
    print(f"Loading direct repo: {e}")
    model = base_model

model.eval()

TEST_SUITE = [
    ("ARCHITECT", "Design a zero-copy lock-free ring buffer for Linux in C++23. Include invariant proofs of cache-line alignment and ABA prevention."),
    ("CODER", "Write a high-performance Python AST transformer that automatically injects a thread-safe latency timer around every async function without modifying docstrings."),
    ("DEBUGGER", "Fix the broken epoll event loop with socket leak under EAGAIN with surgical SEARCH/REPLACE diff blocks."),
    ("CRITIC", "Review a Raft consensus heartbeat implementation for split-brain vulnerabilities and write formal invariant proofs."),
    ("RUSTDESK_SPECIALIST", "Write a secure, low-latency relay connection handler for RustDesk in Rust with zero-copy packet forwarding and end-to-end encryption verification.")
]

for role, prompt in TEST_SUITE:
    print("\n" + "=" * 70)
    print(f"🧪 [CLOUD EVAL: {role}]")
    print(f"PROMPT: {prompt}")
    print("=" * 70)
    msgs = [
        {"role": "system", "content": f"You are Bankai ({role} persona). Provide pure reasoning inside <think>...</think> and output surgical, unpadded code."},
        {"role": "user", "content": prompt}
    ]
    inp = tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt")
    if torch.cuda.is_available():
        inp = inp.to("cuda")
    with torch.no_grad():
        out = model.generate(input_ids=inp, max_new_tokens=500, temperature=0.2)
    resp = tokenizer.decode(out[0][inp.shape[1]:], skip_special_tokens=True)
    print(f"\n[MODEL OUTPUT]:\n{resp}\n")

print("\n" + "=" * 70)
print("  CLOUD EVALUATION COMPLETE ✔")
print("=" * 70)
