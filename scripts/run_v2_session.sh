#!/usr/bin/env bash
set -e
COLAB="/home/k/bin/colab"

echo "======================================================================"
echo "⚡ [PROJECT BANKAI] Initializing Bankai-7B v2 Environment on Colab GPU"
echo "======================================================================"

echo "📦 Step 1: Installing Unsloth, Torch 2.5 & Qwen dependencies..."
$COLAB exec << 'EOF_INSTALL'
import subprocess, sys

packages = [
    "torch", "torchvision", "torchaudio",
    "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
    "xformers", "trl", "peft", "accelerate", "bitsandbytes", "datasets", "huggingface_hub"
]

cmd = [sys.executable, "-m", "pip", "install", "--no-deps", "-q"] + packages
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "unsloth", "trl", "peft", "accelerate", "bitsandbytes", "datasets", "huggingface_hub"])
print("✔ Dependencies installed successfully!")
EOF_INSTALL

echo "📡 Step 2: Uploading 25k refinement dataset (35.69 MB)..."
$COLAB upload /home/k/k_cli/data/bankai_train_7b_v2.jsonl.gz bankai_train_7b_v2.jsonl.gz

echo "📡 Step 3: Uploading v2 training script..."
$COLAB upload /home/k/k_cli/scripts/train_remote_7b_v2.py train_remote_7b_v2.py

echo "🔥 Step 4: Starting 400-Step Refinement Fine-Tuning Loop..."
$COLAB exec << 'EOF_EXEC'
import subprocess, sys

cmd = [sys.executable, "/content/train_remote_7b_v2.py"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in p.stdout:
    print(line, end="", flush=True)
p.wait()
sys.exit(p.returncode)
EOF_EXEC
