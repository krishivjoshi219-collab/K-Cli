#!/usr/bin/env python3
"""
scripts/run_swe_bench_10k_eval.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Bankai — legacy dataset-quality audit.

This script audits *reference responses already present in a JSONL dataset*.
It does not load a model, generate answers, execute SWE-bench tasks, or report
model accuracy. Keep the filename for backwards compatibility; do not use its
output as a benchmark claim.
"""

import os
import sys
import time
import json
import ast
import re
from pathlib import Path

def run_eval(dataset_path: str, model_id: str = "krishivjoshi/bankai-7b", num_samples: int = 10000):
    print("=" * 80)
    print(f"⚡ [PROJECT BANKAI] DATASET RESPONSE QUALITY AUDIT")
    print(f"📦 Reference dataset for model target: {model_id} | Samples: {num_samples:,}")
    print("=" * 80)

    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found at {dataset_path}")
        return

    print(f"\n📂 Loading test questions from {dataset_path}...")
    questions = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= num_samples:
                break
            try:
                data = json.loads(line.strip())
                messages = data.get("messages", [])
                user_msg = next((m["content"] for m in messages if m.get("role") == "user"), "")
                ref_msg = next((m["content"] for m in messages if m.get("role") == "assistant"), "")
                if user_msg:
                    questions.append({
                        "id": idx + 1,
                        "prompt": user_msg,
                        "reference": ref_msg
                    })
            except Exception:
                continue

    print(f"✔ Successfully loaded {len(questions):,} complex test prompts!")

    # Evaluation categories and domain metrics
    categories = {
        "SWE-Bench Surgical Diff": {"total": 0, "pass": 0, "think": 0},
        "Algorithmic Logic & Math": {"total": 0, "pass": 0, "think": 0},
        "Systems & Concurrency": {"total": 0, "pass": 0, "think": 0},
        "Application Security & APIs": {"total": 0, "pass": 0, "think": 0},
        "Compilers & Type Safety": {"total": 0, "pass": 0, "think": 0},
    }

    print(f"\n🚀 Auditing {len(questions):,} reference responses...")
    start_time = time.time()
    total_tokens_evaluated = 0

    for q in questions:
        prompt_lower = q["prompt"].lower()
        if "diff" in prompt_lower or "search" in prompt_lower or "replace" in prompt_lower or "bug" in prompt_lower or "fix" in prompt_lower:
            cat = "SWE-Bench Surgical Diff"
        elif "proof" in prompt_lower or "math" in prompt_lower or "complexity" in prompt_lower or "graph" in prompt_lower:
            cat = "Algorithmic Logic & Math"
        elif "lock" in prompt_lower or "thread" in prompt_lower or "memory" in prompt_lower or "buffer" in prompt_lower or "redis" in prompt_lower:
            cat = "Systems & Concurrency"
        elif "auth" in prompt_lower or "token" in prompt_lower or "security" in prompt_lower or "api" in prompt_lower:
            cat = "Application Security & APIs"
        else:
            cat = "Compilers & Type Safety"

        ref = q["reference"]
        has_think = "<think>" in ref or "</think>" in ref
        has_code = "```" in ref or "def " in ref or "class " in ref or "fn " in ref

        categories[cat]["total"] += 1
        if has_think:
            categories[cat]["think"] += 1
        if has_code or len(ref) > 100:
            categories[cat]["pass"] += 1

        total_tokens_evaluated += len(ref.split()) * 1.3

    elapsed = time.time() - start_time
    total_passed = sum(c["pass"] for c in categories.values())
    total_think = sum(c["think"] for c in categories.values())
    overall_pass_rate = (total_passed / len(questions)) * 100 if questions else 0
    overall_think_rate = (total_think / len(questions)) * 100 if questions else 0

    print("\n" + "=" * 80)
    print("📊 DATASET RESPONSE QUALITY AUDIT")
    print("=" * 80)
    header = f"{'Domain / Category':<32} | {'Tested':<8} | {'Pass Rate':<12} | {'CoT <think> Rate':<18} | {'Status'}"
    print(header)
    print("-" * len(header))

    for cat_name, metrics in categories.items():
        tot = metrics["total"]
        if tot > 0:
            p_rate = (metrics["pass"] / tot) * 100
            t_rate = (metrics["think"] / tot) * 100
            print(f"{cat_name:<32} | {tot:<8} | {p_rate:>8.1f}%   | {t_rate:>14.1f}%   | reference content")

    print("-" * len(header))
    print(f"{'REFERENCE CONTENT RATE':<32} | {len(questions):<8} | {overall_pass_rate:>8.1f}%   | {overall_think_rate:>14.1f}%   | descriptive only")
    print("=" * 80)
    print(f"⏱️ Total Evaluation Tokens Processed: {int(total_tokens_evaluated):,} tokens")
    print("🎉 Dataset audit completed. This is not a model benchmark.")

if __name__ == "__main__":
    ds_path = "/home/k/k_cli/data/bankai_train_7b_v2.jsonl"
    run_eval(ds_path, num_samples=10000)
