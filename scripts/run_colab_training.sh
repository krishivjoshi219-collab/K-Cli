#!/usr/bin/env bash
# ==============================================================================
# scripts/run_colab_training.sh - Remote Training & GGUF Sync Orchestrator
#
# Principal ML & DevOps automation script:
# 1. Enforces active Colab GPU runtime (T4) via colab-cli (stops CPU if needed).
# 2. Uploads curated training data (data/bankai_train_v2.jsonl) to Colab.
# 3. Dispatches scripts/train_remote.py for Unsloth 4-bit LoRA training (3B).
# 4. Streams remote execution logs in real-time.
# 5. Downloads the generated Q4_K_M GGUF model directly to ~/models/bankai-3b.gguf.
# 6. Generates Ollama Modelfile and outputs registration commands for bankai:3b.
# ==============================================================================

set -euo pipefail

# Visual colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Workspace paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATASET_PATH="${ROOT_DIR}/data/bankai_train_v2.jsonl"
REMOTE_SCRIPT_PATH="${SCRIPT_DIR}/train_remote.py"
MODELS_DIR="${HOME}/models"
TARGET_GGUF="${MODELS_DIR}/bankai-3b.gguf"
MODELFILE_PATH="${MODELS_DIR}/Modelfile"

# Locate colab CLI binary
COLAB_BIN=""
if command -v colab-cli &>/dev/null; then
    COLAB_BIN="colab-cli"
elif command -v colab &>/dev/null; then
    COLAB_BIN="colab"
elif [ -x "${HOME}/bin/colab" ]; then
    COLAB_BIN="${HOME}/bin/colab"
elif [ -x "${HOME}/k_cli/k_cli_env/bin/colab" ]; then
    COLAB_BIN="${HOME}/k_cli/k_cli_env/bin/colab"
elif [ -x "${HOME}/bin/colab-cli" ]; then
    COLAB_BIN="${HOME}/bin/colab-cli"
else
    echo -e "${RED}✘ Error: Neither 'colab-cli' nor 'colab' binary was found in PATH.${NC}"
    exit 1
fi

echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN}🚀 PROJECT BANKAI: Colab Remote Fine-Tuning & GGUF Sync Pipeline (3B)${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${CYAN}• Colab CLI Binary:${NC}   ${COLAB_BIN}"
echo -e "${CYAN}• Dataset Source:${NC}     ${DATASET_PATH}"
echo -e "${CYAN}• Remote Script:${NC}      ${REMOTE_SCRIPT_PATH}"
echo -e "${CYAN}• Target Local Model:${NC} ${TARGET_GGUF}"
echo ""

# ------------------------------------------------------------------------------
# 1. Validate Prerequisites
# ------------------------------------------------------------------------------
if [ ! -f "${DATASET_PATH}" ]; then
    echo -e "${RED}✘ Error: Missing dataset at ${DATASET_PATH}. Please generate or curate it first.${NC}"
    exit 1
fi

if [ ! -f "${REMOTE_SCRIPT_PATH}" ]; then
    echo -e "${RED}✘ Error: Missing remote training script at ${REMOTE_SCRIPT_PATH}${NC}"
    exit 1
fi

mkdir -p "${MODELS_DIR}"

# ------------------------------------------------------------------------------
# 2. Check or Initialize Colab Session & Enforce GPU Runtime
# ------------------------------------------------------------------------------
echo -e "${BOLD}${MAGENTA}🔍 [1/5] Checking Colab session status & hardware accelerator...${NC}"
ACTIVE_SESSIONS=$(${COLAB_BIN} sessions 2>&1 || true)
echo -e "${ACTIVE_SESSIONS}"

provision_gpu() {
    echo -e "${CYAN}⚡ Provisioning Colab GPU session (NVIDIA T4)...${NC}"
    local max_attempts=300
    local attempt=1
    local delay=30
    
    while [ $attempt -le $max_attempts ]; do
        echo -e "${CYAN}[$(date '+%H:%M:%S')] Attempt ${attempt}/${max_attempts} to allocate Colab T4 GPU...${NC}"
        if ${COLAB_BIN} new --gpu T4; then
            echo -e "${GREEN}✔ Colab GPU runtime successfully provisioned!${NC}"
            return 0
        fi
        
        # Clean up any lingering stale assignments
        python3 -c "
try:
    from colab_cli.common import state
    for a in state.client.list_assignments():
        state.client.unassign(a.endpoint)
except Exception:
    pass
" 2>/dev/null || true

        if [ $attempt -lt $max_attempts ]; then
            echo -e "${YELLOW}Colab GPU capacity under quota cooldown. Retrying in ${delay}s...${NC}"
            sleep $delay
        fi
        attempt=$((attempt + 1))
    done

    echo -e "${RED}✘ Colab GPU cooldown still active after ${max_attempts} attempts.${NC}"
    return 1
}

if echo "${ACTIVE_SESSIONS}" | grep -iq "Hardware: CPU"; then
    echo -e "${YELLOW}⚠ Active session is CPU runtime. Stopping CPU session to provision GPU (T4)...${NC}"
    ${COLAB_BIN} stop || true
    sleep 3
    provision_gpu
elif [ -z "${ACTIVE_SESSIONS}" ] || echo "${ACTIVE_SESSIONS}" | grep -iq "no active" || echo "${ACTIVE_SESSIONS}" | grep -iq "none"; then
    echo -e "${YELLOW}⚡ No active session found. Creating a new Colab GPU session (NVIDIA T4)...${NC}"
    provision_gpu
fi

# Verify GPU Hardware on Remote VM
echo -e "\n${CYAN}Verifying remote GPU environment...${NC}"
GPU_CHECK_CODE="import torch; print(f'CUDA: {torch.cuda.is_available()} | Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
GPU_CHECK_RESULT=$(echo "${GPU_CHECK_CODE}" | ${COLAB_BIN} exec 2>&1 || true)
echo -e "${GPU_CHECK_RESULT}"

if echo "${GPU_CHECK_RESULT}" | grep -iq "CUDA: False" || echo "${GPU_CHECK_RESULT}" | grep -iq "Error: No active sessions"; then
    echo -e "${RED}✘ Active Colab session has no GPU accelerator enabled or was disconnected.${NC}"
    echo -e "${YELLOW}Re-provisioning fresh T4 GPU session...${NC}"
    ${COLAB_BIN} stop || true
    sleep 3
    provision_gpu
fi

# ------------------------------------------------------------------------------
# 3. Upload Dataset, Keys & Training Script to Colab VM
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${MAGENTA}📤 [2/5] Uploading dataset & training script to Colab VM...${NC}"

# Extract and upload Hugging Face token for backup upload
HF_KEY_FILE="${HOME}/BankaiProject/key.json"
HF_TOKEN=""
if [ -f "${HF_KEY_FILE}" ]; then
    HF_TOKEN=$(grep -o '"HF_API_KEY": "[^"]*' "${HF_KEY_FILE}" | cut -d'"' -f4 || true)
fi
if [ -n "${HF_TOKEN}" ]; then
    echo -e "Uploading Hugging Face backup credentials..."
    echo "${HF_TOKEN}" > /tmp/hf_token.txt
    ${COLAB_BIN} upload "/tmp/hf_token.txt" "/content/hf_token.txt" 2>/dev/null || true
    rm -f /tmp/hf_token.txt
fi

# Compress dataset for fast, SSL-safe transfer over Jupyter REST API
COMPRESSED_DATASET="/tmp/bankai_train_v2.jsonl.gz"
echo -e "Compressing dataset for fast upload..."
gzip -k -f -c "${DATASET_PATH}" > "${COMPRESSED_DATASET}"
COMP_SIZE=$(du -h "${COMPRESSED_DATASET}" | cut -f1)
echo -e "Dataset compressed: ${COMP_SIZE}"

echo -e "Uploading compressed dataset to Colab..."
${COLAB_BIN} upload "${COMPRESSED_DATASET}" "/content/bankai_train_v2.jsonl.gz"

echo -e "Decompressing dataset on Colab VM..."
echo "import subprocess; subprocess.run(['gunzip', '-f', '-k', '/content/bankai_train_v2.jsonl.gz'])" | ${COLAB_BIN} exec

echo -e "Uploading remote training script..."
${COLAB_BIN} upload "${REMOTE_SCRIPT_PATH}" "/content/train_remote.py"
echo -e "${GREEN}✔ Uploads completed successfully.${NC}"

# ------------------------------------------------------------------------------
# 4. Dispatch Remote Fine-Tuning Execution
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${MAGENTA}🔥 [3/5] Launching remote Unsloth LoRA fine-tuning (Streaming Logs)...${NC}"
echo -e "${YELLOW}Note: Execution will train Qwen2.5-Coder-3B for 250 steps and export to GGUF & Google Drive...${NC}\n"

# Execute train_remote.py with 2 hour timeout
${COLAB_BIN} exec -f "${REMOTE_SCRIPT_PATH}" --timeout 7200

# ------------------------------------------------------------------------------
# 5. Locate and Download the GGUF Model
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${MAGENTA}📥 [4/5] Downloading exported GGUF artifact to local host...${NC}"

# Remote candidates for 3B export
GGUF_REMOTE_PATHS=(
    "/content/bankai-3b.gguf"
    "/content/drive/MyDrive/Bankai_Models/bankai_3b/bankai-3b.gguf"
    "/content/bankai_3b_model_gguf/qwen2.5-coder-3b-instruct.Q4_K_M.gguf"
    "/content/bankai_3b_model/bankai-3b.gguf"
    "/content/bankai_3b_model/bankai_3b_model-unsloth.Q4_K_M.gguf"
    "/content/bankai_3b_model-unsloth.Q4_K_M.gguf"
    "/content/bankai_3b_model/unsloth.Q4_K_M.gguf"
    "/content/bankai_3b_model/model-q4_k_m.gguf"
    "/content/bankai_3b_model/bankai-3b-q4_k_m.gguf"
)

DOWNLOADED=false
for r_path in "${GGUF_REMOTE_PATHS[@]}"; do
    echo -e "Checking remote artifact: ${r_path}..."
    if ${COLAB_BIN} download "${r_path}" "${TARGET_GGUF}" 2>/dev/null; then
        if [ -s "${TARGET_GGUF}" ]; then
            DOWNLOADED=true
            echo -e "${GREEN}✔ Successfully downloaded GGUF from ${r_path}!${NC}"
            break
        fi
    fi
done

if [ "${DOWNLOADED}" = false ]; then
    echo -e "${YELLOW}Searching remote /content for any .gguf file...${NC}"
    REMOTE_FILES=$(${COLAB_BIN} ls /content 2>/dev/null || true)
    echo "${REMOTE_FILES}"
    
    # Try finding inside /content/bankai_3b_model
    REMOTE_MODEL_FILES=$(${COLAB_BIN} ls /content/bankai_3b_model 2>/dev/null || true)
    echo "${REMOTE_MODEL_FILES}"
    
    # Download entire folder or single file if located
    echo -e "${YELLOW}Attempting generic download from /content/bankai_3b_model...${NC}"
    ${COLAB_BIN} download "/content/bankai_3b_model" "${MODELS_DIR}/bankai_3b_model" || true
    
    # Check if a .gguf was downloaded into the folder
    FOUND_GGUF=$(find "${MODELS_DIR}/bankai_3b_model" -name "*.gguf" | head -n 1 || true)
    if [ -n "${FOUND_GGUF}" ] && [ -f "${FOUND_GGUF}" ]; then
        mv "${FOUND_GGUF}" "${TARGET_GGUF}"
        DOWNLOADED=true
        echo -e "${GREEN}✔ Successfully moved downloaded GGUF to ${TARGET_GGUF}!${NC}"
    fi
fi

# Hugging Face fallback download if local download failed
if [ "${DOWNLOADED}" = false ] && [ -n "${HF_TOKEN}" ]; then
    echo -e "${YELLOW}Attempting fail-safe download from Hugging Face Hub (krishivjoshi/bankai-3b)...${NC}"
    python3 -c "
from huggingface_hub import hf_hub_download
try:
    path = hf_hub_download(repo_id='krishivjoshi/bankai-3b', filename='qwen2.5-coder-3b-instruct.Q4_K_M.gguf', token='${HF_TOKEN}', local_dir='${MODELS_DIR}')
    import shutil
    shutil.move(path, '${TARGET_GGUF}')
    print('✔ Successfully downloaded from Hugging Face!')
except Exception as e:
    print('HF download fallback notice:', e)
" || true
fi

# ------------------------------------------------------------------------------
# 6. Generate Ollama Modelfile & Print Setup Guide
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${MAGENTA}📝 [5/5] Generating Ollama Modelfile configuration...${NC}"

cat << 'EOF' > "${MODELFILE_PATH}"
FROM ./bankai-3b.gguf

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

SYSTEM """You are Bankai-3B, an elite compiler-grounded AI coding model operating under strict 1.0 GB RAM constraints. You specialize in unpadded code generation, surgical SEARCH/REPLACE patches, AST syntax validation, and step-by-step technical reasoning inside <think>...</think> tags."""
EOF

echo -e "${GREEN}✔ Modelfile created at ${MODELFILE_PATH}${NC}"

echo -e "\n${BOLD}${GREEN}======================================================================${NC}"
echo -e "${BOLD}${GREEN}🎉 PROJECT BANKAI: Remote Pipeline Complete!${NC}"
echo -e "${BOLD}${GREEN}======================================================================${NC}"
echo -e "Model Location: ${BOLD}${TARGET_GGUF}${NC}"
echo -e "\n${BOLD}To register and run your model with Ollama:${NC}"
echo -e "  1. Navigate to models directory: ${CYAN}cd ${MODELS_DIR}${NC}"
echo -e "  2. Register model:             ${CYAN}ollama create bankai:3b -f Modelfile${NC}"
echo -e "  3. Test generation:            ${CYAN}ollama run bankai:3b 'Write a fast binary search in Python'${NC}"
echo -e "  4. Use in K-CLI:               ${CYAN}k-cli run 'Write a fast binary search in Python' --model bankai:3b${NC}"
echo -e "${BOLD}${GREEN}======================================================================${NC}\n"
