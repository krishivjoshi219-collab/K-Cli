#!/usr/bin/env bash
# ==============================================================================
# scripts/run_colab_training_7b.sh - Project Bankai 7B Remote SFT Orchestrator
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATASET_PATH="${ROOT_DIR}/data/bankai_train_7b_v1.jsonl"
REMOTE_SCRIPT_PATH="${SCRIPT_DIR}/train_remote_7b.py"
MODELS_DIR="${HOME}/models"
TARGET_GGUF="${MODELS_DIR}/bankai-7b.gguf"
MODELFILE_PATH="${MODELS_DIR}/Modelfile.7b"

COLAB_BIN=""
if command -v colab-cli &>/dev/null; then
    COLAB_BIN="colab-cli"
elif command -v colab &>/dev/null; then
    COLAB_BIN="colab"
elif [ -x "${HOME}/bin/colab" ]; then
    COLAB_BIN="${HOME}/bin/colab"
elif [ -x "${HOME}/k_cli/k_cli_env/bin/colab" ]; then
    COLAB_BIN="${HOME}/k_cli/k_cli_env/bin/colab"
fi

echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN}🚀 PROJECT BANKAI: 7B Remote Fine-Tuning & GGUF Sync Orchestrator${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${CYAN}• Dataset Source:${NC}     ${DATASET_PATH}"
echo -e "${CYAN}• Remote Script:${NC}      ${REMOTE_SCRIPT_PATH}"
echo -e "${CYAN}• Target Local Model:${NC} ${TARGET_GGUF}"
echo ""

mkdir -p "${MODELS_DIR}"

provision_gpu() {
    echo -e "${CYAN}⚡ Provisioning Colab GPU session (NVIDIA T4 / A100)...${NC}"
    local max_attempts=100
    local attempt=1
    local delay=30
    
    while [ $attempt -le $max_attempts ]; do
        echo -e "${CYAN}[$(date '+%H:%M:%S')] Attempt ${attempt}/${max_attempts} to allocate Colab GPU...${NC}"
        if ${COLAB_BIN} new --gpu T4; then
            echo -e "${GREEN}✔ Colab GPU runtime successfully provisioned!${NC}"
            return 0
        fi
        
        python3 -c "
try:
    from colab_cli.common import state
    for a in state.client.list_assignments():
        state.client.unassign(a.endpoint)
except Exception:
    pass
" 2>/dev/null || true

        if [ $attempt -lt $max_attempts ]; then
            echo -e "${YELLOW}Colab GPU capacity busy. Retrying in ${delay}s...${NC}"
            sleep $delay
        fi
        attempt=$((attempt + 1))
    done

    echo -e "${RED}✘ Failed to allocate Colab GPU after ${max_attempts} attempts.${NC}"
    return 1
}

ACTIVE_SESSIONS=$(${COLAB_BIN} sessions 2>&1 || true)
if [ -z "${ACTIVE_SESSIONS}" ] || echo "${ACTIVE_SESSIONS}" | grep -iq "no active"; then
    provision_gpu
fi

# Upload Hugging Face token
HF_KEY_FILE="${HOME}/BankaiProject/key.json"
HF_TOKEN=""
if [ -f "${HF_KEY_FILE}" ]; then
    HF_TOKEN=$(grep -o '"HF_API_KEY": "[^"]*' "${HF_KEY_FILE}" | cut -d'"' -f4 || true)
fi
if [ -n "${HF_TOKEN}" ]; then
    echo "${HF_TOKEN}" > /tmp/hf_token.txt
    ${COLAB_BIN} upload "/tmp/hf_token.txt" "/content/hf_token.txt" 2>/dev/null || true
    rm -f /tmp/hf_token.txt
fi

# Check if dataset already exists on remote
DATASET_EXISTS=$(${COLAB_BIN} exec -c "import os; print(os.path.exists('/content/bankai_train_7b_v1.jsonl'))" 2>/dev/null || echo "False")
if echo "${DATASET_EXISTS}" | grep -q "True"; then
    echo -e "${GREEN}✔ 7B Dataset already exists on Colab (/content/bankai_train_7b_v1.jsonl). Skipping upload.${NC}"
else
    # Compress and upload 7B dataset
    COMPRESSED_DATASET="/tmp/bankai_train_7b_v1.jsonl.gz"
    echo -e "Compressing 7B dataset for fast upload..."
    gzip -k -f -c "${DATASET_PATH}" > "${COMPRESSED_DATASET}"
    ${COLAB_BIN} upload "${COMPRESSED_DATASET}" "/content/bankai_train_7b_v1.jsonl.gz"
    echo "import subprocess; subprocess.run(['gunzip', '-f', '-k', '/content/bankai_train_7b_v1.jsonl.gz'])" | ${COLAB_BIN} exec
fi

# Upload remote training script
${COLAB_BIN} upload "${REMOTE_SCRIPT_PATH}" "/content/train_remote_7b.py"

# Launch 7B Training Execution
echo -e "\n${BOLD}${MAGENTA}🔥 Launching remote 7B Fine-Tuning Execution...${NC}\n"
${COLAB_BIN} exec -f "${REMOTE_SCRIPT_PATH}" --timeout 10800

# Download GGUF
GGUF_PATHS=(
    "/content/bankai-7b.gguf"
    "/content/drive/MyDrive/Bankai_Models/bankai_7b/bankai-7b.gguf"
    "/content/bankai_7b_model_gguf/qwen2.5-coder-7b-instruct.Q4_K_M.gguf"
    "/content/bankai_7b_model/bankai-7b.gguf"
)

DOWNLOADED=false
for r_path in "${GGUF_PATHS[@]}"; do
    if ${COLAB_BIN} download "${r_path}" "${TARGET_GGUF}" 2>/dev/null; then
        if [ -s "${TARGET_GGUF}" ]; then
            DOWNLOADED=true
            echo -e "${GREEN}✔ Downloaded 7B GGUF from ${r_path}!${NC}"
            break
        fi
    fi
done

# Ollama Modelfile for 7B
cat << 'EOF_MODEL' > "${MODELFILE_PATH}"
FROM ./bankai-7b.gguf

TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.2
PARAMETER top_p 0.95
PARAMETER repeat_penalty 1.1

SYSTEM """You are Bankai-7B, an elite compiler-grounded AI coding model operating under strict 1.0 GB RAM constraints. You specialize in complex AST code generation, surgical SEARCH/REPLACE patches, zero-fluff critique, and step-by-step technical reasoning inside <think>...</think> tags."""
EOF_MODEL

echo -e "${GREEN}✔ 7B Modelfile created at ${MODELFILE_PATH}${NC}"
