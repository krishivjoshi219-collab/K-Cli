# ╔══════════════════════════════════════════════════════════════════╗
# ║  PROJECT BANKAI — Google Colab 7B Training                      ║
# ║  Target: krishivjoshi/bankai-7b                                  ║
# ║  GPU: T4 / A100 (Colab Free / Pro)                              ║
# ╚══════════════════════════════════════════════════════════════════╝

# CELL 1: Install packages
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "peft==0.11.1", "bitsandbytes>=0.43.0", "accelerate>=0.33.0",
    "datasets", "huggingface_hub", "trl", "transformers"], check=False)

# CELL 2: Setup
import os, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForSeq2Seq
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
from datasets import load_dataset
from huggingface_hub import HfApi

HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN

# Verify GPU
assert torch.cuda.is_available(), "Enable GPU in Runtime → Change Runtime Type!"
props = torch.cuda.get_device_properties(0)
print(f"✔ GPU: {props.name} ({props.total_memory/(1024**3):.1f} GB VRAM)")

# CELL 3: Load dataset from Hugging Face
print("📑 Loading dataset from Hugging Face...")
dataset = load_dataset("krishivjoshi/bankai-flagship-expanded", split="train", token=HF_TOKEN)
dataset = dataset.select(range(min(8000, len(dataset))))
print(f"✔ Loaded {len(dataset):,} samples")

# CELL 4: Load model in 4-bit NF4
model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
print(f"🧠 Loading {model_id} in 4-bit NF4...")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True
)
model = AutoModelForCausalLM.from_pretrained(
    model_id, quantization_config=bnb_cfg,
    device_map="auto", trust_remote_code=True, torch_dtype=torch.float16
)
model = prepare_model_for_kbit_training(model)

# CELL 5: Attach LoRA
peft_cfg = LoraConfig(
    task_type=TaskType.CAUSAL_LM, r=32, lora_alpha=64,
    lora_dropout=0.05, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
model = get_peft_model(model, peft_cfg)
model.print_trainable_parameters()

# CELL 6: Tokenize
def tokenize(examples):
    texts = [tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False) for c in examples["messages"]]
    enc = tokenizer(texts, truncation=True, max_length=1024, padding=False)
    enc["labels"] = enc["input_ids"].copy()
    return enc

tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
print(f"✔ Tokenized {len(tokenized):,} samples")

# CELL 7: Train
MAX_STEPS = 200
args = TrainingArguments(
    output_dir="/content/bankai_7b_model",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    warmup_steps=20,
    max_steps=MAX_STEPS,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    weight_decay=0.01,
    optim="paged_adamw_8bit",
    lr_scheduler_type="cosine",
    seed=3407,
    report_to="none",
)

trainer = Trainer(
    model=model, args=args, train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True)
)

print(f"🔥 Training {MAX_STEPS} steps on GPU...")
t0 = time.time()
trainer.train()
model.save_pretrained("/content/bankai_7b_model")
tokenizer.save_pretrained("/content/bankai_7b_model")
print(f"✔ Done in {(time.time()-t0)/60:.2f} minutes!")

# CELL 8: Push to Hugging Face
for repo in ["krishivjoshi/bankai-7b"]:
    print(f"🚀 Pushing to {repo}...")
    try:
        model.push_to_hub(repo, token=HF_TOKEN, private=True)
        tokenizer.push_to_hub(repo, token=HF_TOKEN, private=True)
        print(f"✔ Uploaded to {repo}")
    except Exception as e:
        print(f"Fallback upload: {e}")
        api = HfApi(token=HF_TOKEN)
        api.upload_folder(folder_path="/content/bankai_7b_model", repo_id=repo, repo_type="model")
        print(f"✔ Fallback upload to {repo} done!")

print("=" * 60)
print("  BANKAI 7B COLAB TRAINING COMPLETE!")
print("=" * 60)
