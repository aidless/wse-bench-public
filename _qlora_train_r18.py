"""PATH_A round 18 retry: leakage-safe dev-only low-intrusion QLoRA.
Windows/RTX3060 path; no Unsloth. Uses the locally cached Qwen2.5-3B snapshot.
"""
import os, json, gc, time
# WorkBuddy injects an oversized env var that breaks accelerate cleanup on Windows.
for k in list(os.environ):
    if len(os.environ.get(k, "")) > 30000:
        print(f"dropping long env var: {k} ({len(os.environ[k])} chars)")
        del os.environ[k]
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

ROOT = r"F:\test\2026-07-24-08-21-57"
MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
DATA_PATH = os.path.join(ROOT, "sft_dev_r18.jsonl")
OUT_DIR = r"F:\lora_adapter\qwen3b_pathA_r18_dev"
os.makedirs(OUT_DIR, exist_ok=True)
SEED = 20260724

print("=== PATH A r18 dev-only retry ===")
print(f"data={DATA_PATH}")
print(f"out={OUT_DIR}")
print(f"torch={torch.__version__} cuda={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA unavailable")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = False
model.gradient_checkpointing_enable()
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

records = [json.loads(line) for line in open(DATA_PATH, encoding="utf-8") if line.strip()]
assert records and all(r.get("split") == "dev" for r in records)

def to_text(r):
    msgs = [{"role": "user", "content": r["instruction"]}]
    msgs.append({"role": "assistant", "content": r["output"]})
    return {"text": tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)}

data = [to_text(r) for r in records]
dataset = Dataset.from_list(data)
# Small held-out slice is only for monitoring; hidden/fresh never enter this file.
split = dataset.train_test_split(test_size=0.1, seed=SEED)
print(f"records={len(records)} train={len(split['train'])} eval={len(split['test'])}")

cfg = SFTConfig(
    output_dir=OUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    logging_steps=5,
    eval_strategy="steps",
    eval_steps=25,
    save_strategy="no",
    fp16=False,
    bf16=True,
    gradient_checkpointing=True,
    max_length=1024,
    dataset_text_field="text",
    report_to=[],
    optim="paged_adamw_8bit",
    seed=SEED,
)
trainer = SFTTrainer(
    model=model,
    args=cfg,
    train_dataset=split["train"],
    eval_dataset=split["test"],
    processing_class=tokenizer,
)
print("=== train start ===")
t0 = time.time()
trainer.train()
print(f"=== train done {time.time()-t0:.1f}s ===")
trainer.save_model(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
meta = {
    "round": 18,
    "data": "sft_dev_r18.jsonl",
    "n_records": len(records),
    "train_records": len(split["train"]),
    "eval_records": len(split["test"]),
    "hidden_fresh_used": False,
    "base_model": MODEL_PATH,
    "lora_r": 8,
    "lora_alpha": 16,
    "learning_rate": 2e-5,
    "epochs": 1,
    "seed": SEED,
    "elapsed_seconds": round(time.time()-t0, 2),
    "gpu_peak_gb": round(torch.cuda.max_memory_allocated()/1e9, 3),
}
json.dump(meta, open(os.path.join(OUT_DIR, "training_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(meta, ensure_ascii=False))
