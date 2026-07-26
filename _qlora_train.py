"""路径 A step 2: QLoRA 训练 Qwen2.5-3B-Instruct。
- 4-bit NF4 + LoRA r=16 + paged_adamw_8bit
- 在 sft_v90_5strat.jsonl (30 pairs) 上 1 epoch
- 6GB 显存友好: gradient checkpointing + grad accumulation 8
- 保存 adapter 到 F:/lora_adapter/qwen3b_5strat_v1/"""
import os
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# 清理 WorkBuddy/VS Code 注入的超长 env vars（避免 accelerate clear_environment 触发 32767 限制）
for k in list(os.environ.keys()):
    if len(os.environ[k]) > 30000:
        print(f"  dropping long env var: {k} ({len(os.environ[k])} chars)")
        del os.environ[k]

import json
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

# 路径
MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
DATA_PATH = r"F:\test\2026-07-24-08-21-57\sft_v90_5strat.jsonl"
OUT_DIR = r"F:\lora_adapter\qwen3b_5strat_v1"
os.makedirs(OUT_DIR, exist_ok=True)

print("=== 加载 tokenizer + 模型（4-bit NF4）===")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = False
model.gradient_checkpointing_enable()
model = prepare_model_for_kbit_training(model)

print("=== 配置 LoRA ===")
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

print("=== 加载 SFT 数据 ===")
data = []
with open(DATA_PATH, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        # OpenAI messages 格式 → 训练 text
        msgs = d["messages"]
        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        data.append({"text": text})
print(f"训练样本: {len(data)}")

dataset = Dataset.from_list(data)

print("=== 配置 SFTTrainer ===")
sft_config = SFTConfig(
    output_dir=OUT_DIR,
    num_train_epochs=3,                # 30 对 3 epochs = 90 步
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,      # effective batch = 8
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    logging_steps=5,
    save_strategy="no",
    bf16=True,
    gradient_checkpointing=False,  # already enabled above
    max_length=1024,
    dataset_text_field="text",
    report_to=[],
    optim="paged_adamw_8bit",
)

trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=dataset,
    processing_class=tokenizer,
)

print("=== 开始训练 ===")
trainer.train()

print("=== 保存 adapter ===")
trainer.save_model(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)

print(f"训练完成，adapter 已保存到 {OUT_DIR}")
print(f"GPU peak memory: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
