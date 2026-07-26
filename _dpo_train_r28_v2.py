"""DPO training r28 v2 (plan 4.1): 101 pairs, beta=0.05 from 6 strategies, Qwen2.5-3B + QLoRA.
Reference policy = base Qwen2.5-3B (no LoRA adapter).
Trains for 1 epoch with batch size 1 (gradient accumulation 4).

WorkBuddy-host env var patch (2026-07-26): ACC_PRODUCT_CONFIG_V3 (35万字符)
    causes accelerate's clear_environment -> ValueError > 32767 char limit.
    Prune oversized env vars BEFORE importing accelerate/transformers/trl.
"""
import json, os, sys, math, random, time
from pathlib import Path
from dataclasses import dataclass

# ---- env hygiene (must run before heavy imports) ----
_MAX_ENV_LEN = 8000  # safety threshold; HF/PATH etc all fit under this
for _k in list(os.environ.keys()):
    if len(os.environ[_k]) > _MAX_ENV_LEN:
        del os.environ[_k]
# Pass through what we need
os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import DPOConfig, DPOTrainer

root = Path(r'__WSE_REPO_ROOT__')

# Read DPO data
pairs = []
with open(root / 'sft_dev_dpo_pillar_d_v2_combined.jsonl', encoding='utf-8') as f:
    for line in f:
        pairs.append(json.loads(line))
print('DPO pairs:', len(pairs))

# Load model + tokenizer
MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

print('loading base model...')
t0 = time.time()
base = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_cfg,
    torch_dtype=torch.float16,
    device_map='auto',
    trust_remote_code=True,
)
base = prepare_model_for_kbit_training(base)
print(f'base loaded in {time.time()-t0:.1f}s')

# Disable cache for training
base.config.use_cache = False
base.gradient_checkpointing_enable()
base.enable_input_require_grads()

lora_cfg = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias='none',
    task_type='CAUSAL_LM',
    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
)

# Prepare DPO data format
from datasets import Dataset
dpo_data = []
for pr in pairs:
    dpo_data.append({
        'prompt': pr['prompt'],
        'chosen': pr['chosen'],
        'rejected': pr['rejected'],
    })
dpo_dataset = Dataset.from_list(dpo_data)

# DPO config
out_dir = r'F:/lora_adapter/qwen3b_pathA_dpo_r28_v2'
os.makedirs(out_dir, exist_ok=True)

cfg = DPOConfig(
    output_dir=out_dir,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    gradient_checkpointing=True,
    learning_rate=2e-5,
    lr_scheduler_type='cosine',
    warmup_steps=5,
    logging_steps=2,
    save_strategy='no',
    bf16=True,
    fp16=False,
    max_length=512,
    beta=0.05,
    seed=42,
    report_to='none',
)

trainer = DPOTrainer(
    model=base,
    ref_model=None,  # use peft adapter disabling for ref
    args=cfg,
    train_dataset=dpo_dataset,
    processing_class=tok,
    peft_config=lora_cfg,
)
print('trainer created')

t0 = time.time()
trainer.train()
print(f'training done in {time.time()-t0:.1f}s')

# Save adapter
trainer.save_model(out_dir)
print('adapter saved:', out_dir)

# Training meta
import json as json_mod
meta = {
    'n_pairs': len(pairs),
    'lr': 2e-5,
    'r': 8,
    'alpha': 16,
    'epochs': 1,
    'beta': 0.05,
    'training_time_sec': time.time() - t0,
    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'model': 'Qwen2.5-3B-Instruct',
    'method': 'DPO with 6-strategy stack dev-only K=5/K=10 raw',
    'n_unique_tasks': len(set(p['task_id'] for p in pairs)),
    'gap_mean': sum(p['gap'] for p in pairs) / len(pairs),
}
with open(os.path.join(out_dir, 'training_meta.json'), 'w', encoding='utf-8') as f:
    json_mod.dump(meta, f, ensure_ascii=False, indent=2)
print('meta saved')