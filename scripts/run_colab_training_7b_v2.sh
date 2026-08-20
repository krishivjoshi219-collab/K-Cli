#!/usr/bin/env bash
set -e

COLAB_BIN="/home/k/bin/colab"
DATASET_GZ="/home/k/k_cli/data/bankai_train_7b_v2.jsonl.gz"
SCRIPT_SRC="/home/k/k_cli/scripts/train_remote_7b_v2.py"

echo "======================================================================"
echo "⚡ [PROJECT BANKAI] Launching Bankai-7B v2 Refine Fine-Tuning on Colab GPU"
echo "======================================================================"

# Verify active session
ACTIVE=$($COLAB_BIN sessions 2>&1 || true)
if [ -z "$ACTIVE" ] || echo "$ACTIVE" | grep -iq "no active"; then
    echo "⚡ Provisioning fresh Tesla T4 GPU VM..."
    $COLAB_BIN new --gpu T4 -s bankai_v2
fi

echo "📡 Step 1: Uploading dataset (bankai_train_7b_v2.jsonl.gz, 36 MB)..."
$COLAB_BIN upload "$DATASET_GZ" "bankai_train_7b_v2.jsonl.gz"

echo "📡 Step 2: Uploading training script (train_remote_7b_v2.py)..."
$COLAB_BIN upload "$SCRIPT_SRC" "train_remote_7b_v2.py"

echo "🔥 Step 3: Executing Unsloth Refinement Training on GPU..."
$COLAB_BIN exec -f "$SCRIPT_SRC" --timeout 10800

echo "======================================================================"
echo "🎉 Bankai-7B v2 Refinement Training & SWE-Bench Complete!"
echo "======================================================================"
