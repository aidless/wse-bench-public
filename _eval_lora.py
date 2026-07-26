"""路径 A step 3: 用 v96 WSE-Bench 评估 Qwen2.5-3B + LoRA adapter。
- 加载 base + LoRA
- 对所有 96 题各 1 次推理
- 评分（与 v96 production 同样的 scoring）
- 聚合：per-task pass rate → 与 baseline / production 对比
- 账本 #19: 记录 McNemar p + CI vs baseline（直答），与 v90 production 的差距"""
import os
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
for k in list(os.environ.keys()):
    if len(os.environ[k]) > 30000:
        del os.environ[k]

import json
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

import sys
sys.path.insert(0, r"F:\test\2026-07-24-08-21-57")
import eval_self_evolution as E

MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
ADAPTER_PATH = r"F:\lora_adapter\qwen3b_5strat_v1"
OUT_JSON = r"F:\test\2026-07-24-08-21-57\results_qwen3b_lora_v96.json"
SFT_DATA = r"F:\test\2026-07-24-08-21-57\sft_v90_5strat.jsonl"

# 读 manifest
manifest = E.load_manifest()
tmap = {t["id"]: t for t in manifest["tasks"]}
SFT_TASK_IDS = set()
with open(SFT_DATA, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        SFT_TASK_IDS.add(d["task_id"])
print(f"SFT 训练任务: {len(SFT_TASK_IDS)} 题（{sorted(SFT_TASK_IDS)}）")
print(f"  held-out: {96 - len(SFT_TASK_IDS)} 题")

# 加载 tokenizer + base + LoRA
print("加载 LoRA 模型...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"  # 生成时 left padding

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
base = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(base, ADAPTER_PATH)
model.eval()
print(f"GPU peak: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")

# 推理
import sys
def generate(prompt, max_new_tokens=256):
    msgs = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,        # greedy for reproducible eval
            pad_token_id=tokenizer.pad_token_id,
        )
    gen = out[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(gen, skip_special_tokens=True).strip()


print(f"开始 96 题推理 (max_new_tokens=256, unbuffered)...", flush=True)
results = {}
t0 = time.time()
for i, tid in enumerate(sorted(tmap.keys()), 1):
    t = tmap[tid]
    try:
        ans = generate(t["prompt"])
    except Exception as e:
        print(f"  {tid}: ERROR {e}", flush=True)
        ans = ""
    sc = E.score_task(t, ans)
    results[tid] = {"answer": ans, "score": sc, "passed": E.is_pass(sc, t)}
    if i % 8 == 0 or i <= 4:
        elapsed = time.time() - t0
        print(f"  [{i}/96] {tid} elapsed {elapsed:.0f}s ({elapsed/i:.1f}s/task) score={sc}", flush=True)
print(f"推理完成，总耗时 {time.time()-t0:.0f}s", flush=True)

# 聚合
def aggregate(scores_dict, ids):
    return {tid: scores_dict[tid]["score"] for tid in ids}

scores = aggregate(results, list(tmap.keys()))

# 按 capability / cohort 分组
from collections import defaultdict
by_axis = defaultdict(list)
for tid in tmap:
    by_axis[tmap[tid].get("capability", "unknown")].append(tid)

print()
print("=== Per-axis 评分（median 分数）===")
for ax in ["fact_recall", "selective_retrieval", "reasoning", "structured_output", "reading_comprehension"]:
    if ax not in by_axis:
        continue
    ids = by_axis[ax]
    sc = [scores[tid] for tid in ids]
    pass_count = sum(1 for tid in ids if results[tid]["passed"])
    print(f"  {ax:25s} n={len(ids):2d}  mean={sum(sc)/len(sc):.3f}  passed={pass_count}/{len(ids)}")

# SFT 训练题 vs held-out
sft_scores = [scores[tid] for tid in SFT_TASK_IDS if tid in scores]
sft_pass = sum(1 for tid in SFT_TASK_IDS if tid in results and results[tid]["passed"])
heldout_ids = [tid for tid in tmap if tid not in SFT_TASK_IDS]
heldout_scores = [scores[tid] for tid in heldout_ids]
heldout_pass = sum(1 for tid in heldout_ids if results[tid]["passed"])
print()
print(f"SFT 训练题 (n={len(sft_scores)}): mean={sum(sft_scores)/len(sft_scores):.3f} passed={sft_pass}/{len(sft_scores)}")
print(f"held-out 题 (n={len(heldout_scores)}): mean={sum(heldout_scores)/len(heldout_scores):.3f} passed={heldout_pass}/{len(heldout_ids)}")
print(f"Overall (n={len(scores)}): mean={sum(scores.values())/len(scores):.3f}")

# 对比 v90 baseline + production
import json
v90_base = json.load(open(r"F:\test\2026-07-24-08-21-57\results_baseline_agg5_v90.json", encoding="utf-8"))["scores"]
v90_prod = json.load(open(r"F:\test\2026-07-24-08-21-57\results_production_agg5_v90.json", encoding="utf-8"))["scores"]

# Pass rate on tasks both have
common = set(scores) & set(v90_base) & set(v90_prod)
n_base_pass = sum(1 for tid in common if v90_base[tid] >= 0.5)  # 0.5+ 算半过
n_prod_pass = sum(1 for tid in common if v90_prod[tid] >= 0.5)
n_lora_pass = sum(1 for tid in common if scores[tid] >= 0.5)
n_base_full = sum(1 for tid in common if v90_base[tid] >= 0.99)
n_prod_full = sum(1 for tid in common if v90_prod[tid] >= 0.99)
n_lora_full = sum(1 for tid in common if scores[tid] >= 0.99)

print()
print(f"=== Pass rate (≥0.5 算半过, ≥0.99 算全过) on common {len(common)} tasks ===")
print(f"  v90 baseline:   半过 {n_base_pass}/{len(common)} ({n_base_pass/len(common):.3f})  全过 {n_base_full}/{len(common)} ({n_base_full/len(common):.3f})")
print(f"  v90 production: 半过 {n_prod_pass}/{len(common)} ({n_prod_pass/len(common):.3f})  全过 {n_prod_full}/{len(common)} ({n_prod_full/len(common):.3f})")
print(f"  LoRA model:     半过 {n_lora_pass}/{len(common)} ({n_lora_pass/len(common):.3f})  全过 {n_lora_full}/{len(common)} ({n_lora_full/len(common):.3f})")

# 写结果
out = {
    "model": "Qwen2.5-3B-Instruct + LoRA (r=16, 30 SFT pairs, 3 epochs)",
    "adapter_path": ADAPTER_PATH,
    "manifest_tasks": 96,
    "scores": scores,
    "per_axis_pass": {ax: sum(1 for tid in by_axis[ax] if results[tid]["passed"]) for ax in by_axis},
    "sft_train_pass": f"{sft_pass}/{len(sft_scores)}",
    "heldout_pass": f"{heldout_pass}/{len(heldout_ids)}",
    "v90_baseline_comp": {"n_pass_05": n_base_pass, "n_pass_099": n_base_full, "n": len(common)},
    "v90_production_comp": {"n_pass_05": n_prod_pass, "n_pass_099": n_prod_full, "n": len(common)},
    "lora_pass_05": n_lora_pass,
    "lora_pass_099": n_lora_full,
    "note": "路径 A step 3: WSE-Bench v96 评估。LoRA 模型直接生成（无 5 策略 wrapper），与 v90 baseline (直答) 和 v90 production (5 策略叠加) 对比。",
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n写 {OUT_JSON}")