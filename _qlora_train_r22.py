"""PATH A retry: dev-only QLoRA r=8, 78 records, then v128 hidden+fresh eval."""
import os, json, time
for k in list(os.environ):
    if len(os.environ.get(k, "")) > 30000:
        del os.environ[k]
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

ROOT = r"F:\test\2026-07-24-08-21-57"
MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
DATA = os.path.join(ROOT, "sft_dev_r22_500plus.jsonl")
ADAPTER_DIR = r"F:\lora_adapter\qwen3b_pathA_r22_dev"
SEED = 20260724

print("=== training ===")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, quantization_config=bnb_config, dtype=torch.bfloat16,
    device_map="auto", trust_remote_code=True,
)
model.config.use_cache = False
model.gradient_checkpointing_enable()
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=8, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Load SFT data
records = [json.loads(line) for line in open(DATA, encoding="utf-8") if line.strip()]
print(f"records={len(records)}")

def to_text(r):
    msgs = [{"role":"user","content":r["instruction"]},{"role":"assistant","content":r["output"]}]
    return {"text": tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)}

data = [to_text(r) for r in records]
ds = Dataset.from_list(data).train_test_split(test_size=0.1, seed=SEED)
print(f"train={len(ds['train'])} eval={len(ds['test'])}")

cfg = SFTConfig(
    output_dir=ADAPTER_DIR,
    num_train_epochs=2,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    lr_scheduler_type="cosine", warmup_ratio=0.05,
    logging_steps=5,
    save_strategy="no",
    bf16=True, fp16=False,
    gradient_checkpointing=True,
    max_length=1024,
    dataset_text_field="text",
    report_to=[],
    optim="paged_adamw_8bit",
    seed=SEED,
)
trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds["train"], eval_dataset=ds["test"], processing_class=tokenizer)
t0 = time.time()
trainer.train()
trainer.save_model(ADAPTER_DIR)
tokenizer.save_pretrained(ADAPTER_DIR)
print(f"trained {time.time()-t0:.0f}s, adapter at {ADAPTER_DIR}")
