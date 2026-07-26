"""v128 dev+hidden+fresh K=1 evaluation of PATH A r22 LoRA vs Qwen2.5-3B base.
"""
import os, json, time, sys
for k in list(os.environ):
    if len(os.environ.get(k, "")) > 30000:
        del os.environ[k]
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
sys.path.insert(0, r"F:\test\2026-07-24-08-21-57")
import eval_self_evolution as E

ROOT = r"F:\test\2026-07-24-08-21-57"
MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
ADAPTER_PATH = r"F:\lora_adapter\qwen3b_pathA_r22_dev"
OUT = r"F:\test\2026-07-24-08-21-57\results_qwen3b_lora_r22_v128.json"

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
base = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb, dtype=torch.float16, device_map="auto", trust_remote_code=True)
base.eval()

def gen(model, prompt, max_new_tokens=256):
    text = tokenizer.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.pad_token_id)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

# Get all task IDs
ids = list(tmap.keys())
print(f"evaluating {len(ids)} tasks (dev+hidden+fresh K=1 greedy)")

# First, base scores
t0 = time.time()
base_results = {}
for i, tid in enumerate(ids, 1):
    ans = gen(base, tmap[tid]["prompt"])
    sc = E.score_task(tmap[tid], ans)
    base_results[tid] = {"answer": ans, "score": sc, "passed": E.is_pass(sc, tmap[tid]), "split": tmap[tid]["split"]}
    if i % 16 == 0 or i == len(ids):
        print(f"[BASE {i}/{len(ids)}] elapsed {time.time()-t0:.0f}s", flush=True)

# Now load adapter on top of base, and run cand
print("loading adapter...")
model = PeftModel.from_pretrained(base, ADAPTER_PATH)
model.eval()
cand_results = {}
for i, tid in enumerate(ids, 1):
    ans = gen(model, tmap[tid]["prompt"])
    sc = E.score_task(tmap[tid], ans)
    cand_results[tid] = {"answer": ans, "score": sc, "passed": E.is_pass(sc, tmap[tid]), "split": tmap[tid]["split"]}
    if i % 16 == 0 or i == len(ids):
        print(f"[LoRA {i}/{len(ids)}] elapsed {time.time()-t0:.0f}s", flush=True)

# Aggregate
def summary(results, tmap, ids):
    pass_per_task = {tid: results[tid]["passed"] for tid in ids}
    overall_pass = sum(pass_per_task.values())
    overall_mean = sum(results[tid]["score"] for tid in ids) / len(ids)
    per_split = {}
    for split in ["dev", "hidden", "fresh"]:
        sids = [tid for tid in ids if tmap[tid]["split"] == split]
        per_split[split] = {
            "n": len(sids),
            "pass": sum(pass_per_task[tid] for tid in sids),
            "mean": round(sum(results[tid]["score"] for tid in sids) / len(sids), 3) if sids else 0,
        }
    return overall_pass, overall_mean, per_split, pass_per_task

base_pass, base_mean, base_split, base_pass_per_task = summary(base_results, tmap, ids)
cand_pass, cand_mean, cand_split, cand_pass_per_task = summary(cand_results, tmap, ids)

# Per-task delta
deltas = {tid: round(cand_results[tid]["score"] - base_results[tid]["score"], 3) for tid in ids}

import statistics
import math
mean_diffs = [cand_results[tid]["score"] - base_results[tid]["score"] for tid in ids]
md = statistics.mean(mean_diffs)
sd = statistics.stdev(mean_diffs)
t_stat = md / (sd / math.sqrt(len(ids))) if sd > 0 else 0
p_t = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

# discordant at strict majority (K=1 means pass if score>=1.0; for K=1 strict = same as K=5 strict for single)
b_pass = sum(1 for tid in ids if base_pass_per_task[tid] and not cand_pass_per_task[tid])
c_pass = sum(1 for tid in ids if (not base_pass_per_task[tid]) and cand_pass_per_task[tid])
p_mcnemar, _, _ = E.mcnemar_exact(b_pass, c_pass)
ci = E.bootstrap_delta_ci({tid: base_results[tid]["score"] for tid in ids}, {tid: cand_results[tid]["score"] for tid in ids}, n_boot=10000, seed=20260724)

result = {
    "round": 22,
    "type": "PATH_A_R22_LORA_V128",
    "model": "Qwen2.5-3B-Instruct + PATH A r22 LoRA (r=8, 78 dev records, 2 epochs)",
    "adapter_path": ADAPTER_PATH,
    "n_tasks": len(ids),
    "task_ids": ids,
    "base_pass": base_pass,
    "cand_pass": cand_pass,
    "base_mean": round(base_mean, 3),
    "cand_mean": round(cand_mean, 3),
    "delta_overall": round(cand_mean - base_mean, 3),
    "per_split": {"base": base_split, "cand": cand_split},
    "per_task_delta": deltas,
    "mcnemar_p": p_mcnemar,
    "discordant_base_pass_cand_fail": b_pass,
    "discordant_base_fail_cand_pass": c_pass,
    "bootstrap_ci95_overall_delta": list(ci),
    "paired_t_p": p_t,
    "paired_t_stat": t_stat,
    "method_honesty": "K=1 greedy 同 base 同 generation; LoRA 78 dev records 2 epochs, hidden/fresh 测试集严格排除(0 训练样本)。",
    "decision": "PROMOTE" if (cand_pass > base_pass and p_mcnemar < 0.05 and ci[0] > 0) else "HOLD",
    "artifact_base": "submissions_..._base.json" if False else "(inline)",
    "artifact_cand": "(inline)",
}
import json
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
# Also dump raw submissions
with open(OUT.replace(".json", "_base.json"), "w", encoding="utf-8") as f:
    json.dump(base_results, f, ensure_ascii=False, indent=2)
with open(OUT.replace(".json", "_cand.json"), "w", encoding="utf-8") as f:
    json.dump(cand_results, f, ensure_ascii=False, indent=2)
print(json.dumps({
    "n": len(ids),
    "base_pass": base_pass, "cand_pass": cand_pass,
    "delta_overall": round(cand_mean - base_mean, 3),
    "per_split": {"base": base_split, "cand": cand_split},
    "mcnemar_p": p_mcnemar,
    "ci": list(ci),
    "paired_t_p": p_t,
    "decision": result["decision"],
}, ensure_ascii=False, indent=2))
print("wrote", OUT)
