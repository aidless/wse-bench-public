"""K=5 honest model-level evaluation of context_grounding_v1 on T103-T118 (12题).

Each of K=5 independent seeds runs both arms (base vs candidate) on each task.
We use do_sample=True with fixed temperature 0.7 and 5 different seeds to obtain
5 distinct generations per arm per task. This is the only way to get K=5
real model generations under a deterministic-feeling eval protocol.

Output: raw submissions to JSON, per-task pass per seed, McNemar over the
pooled K seeds, and bootstrap CI for overall delta.
"""
import os, json, sys, time, gc, statistics
for k in list(os.environ):
    if len(os.environ.get(k, "")) > 30000:
        del os.environ[k]
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
sys.path.insert(0, r"F:\test\2026-07-24-08-21-57")
import eval_self_evolution as E

ROOT = r"F:\test\2026-07-24-08-21-57"
MODEL_PATH = r"F:\hf_cache\models\Qwen--Qwen2.5-3B-Instruct\snapshots\master"
OUT = r"F:\test\2026-07-24-08-21-57\results_context_grounding_r20_real.json"
BASE_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r20_base.json"
CAND_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r20_cand.json"

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
RC_TASKS = ["T103","T104","T105","T106","T107","T108","T109","T110","T111","T112","T113","T114","T115","T116","T117","T118"]
# Trim to 12 tasks to keep K=5 * 12 * 2 ≈ 120 generations feasible.
RC_TASKS = ["T103","T104","T105","T106","T107","T108","T109","T110","T111","T110","T111","T112"]
RC_TASKS = sorted(set(RC_TASKS))
assert all(t in tmap for t in RC_TASKS), [t for t in RC_TASKS if t not in tmap]
print(f"evaluation tasks: {len(RC_TASKS)}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb, dtype=torch.float16, device_map="auto", trust_remote_code=True)
model.eval()

K = 5
SEEDS = [11, 22, 33, 44, 55]
PREFIX = (
    "在回答之前，请先在源文本中**定位能直接支撑该问题答案的具体句子**，"
    "然后**逐字引用**该句或该短语（用引号标出），最后再给出综合表述。"
    "不要使用同义改写，不要省略关键数字或单位。"
)
TEMPERATURE = 0.7
MAX_NEW_TOKENS = 256

def gen(prompt, seed):
    torch.manual_seed(seed)
    text = tokenizer.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=0.9,
            pad_token_id=tokenizer.pad_token_id,
        )
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

def run(prefix):
    out = {}
    t0 = time.time()
    for i, tid in enumerate(RC_TASKS, 1):
        seed_results = []
        for k_idx, seed in enumerate(SEEDS):
            prompt = (prefix + "\n\n" + tmap[tid]["prompt"]) if prefix else tmap[tid]["prompt"]
            ans = gen(prompt, seed)
            sc = E.score_task(tmap[tid], ans)
            seed_results.append({"seed": seed, "answer": ans, "score": sc, "passed": E.is_pass(sc, tmap[tid])})
        out[tid] = seed_results
        passes = [s["passed"] for s in seed_results]
        print(f"[{i}/{len(RC_TASKS)}] {tid} passes={sum(passes)}/{K} split={tmap[tid]['split']} elapsed={time.time()-t0:.0f}s", flush=True)
    return out

print("=== BASE (no prefix) ===", flush=True)
base_results = run(None)
json.dump({k: v for k, v in base_results.items()}, open(BASE_SUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("=== CAND (context_grounding prefix) ===", flush=True)
cand_results = run(PREFIX)
json.dump({k: v for k, v in cand_results.items()}, open(CAND_SUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# Per-task median score (K=5 seed pass rate → mean as continuous, median over seeds as discrete)
def median_pass(task_seeds):
    return statistics.median(1 if s["passed"] else 0 for s in task_seeds)
def mean_score(task_seeds):
    return sum(s["score"] for s in task_seeds) / len(task_seeds)

base_med = {tid: median_pass(base_results[tid]) for tid in RC_TASKS}
cand_med = {tid: median_pass(cand_results[tid]) for tid in RC_TASKS}
base_mean = {tid: mean_score(base_results[tid]) for tid in RC_TASKS}
cand_mean = {tid: mean_score(cand_results[tid]) for tid in RC_TASKS}
# Per-task pass with 0.5 threshold (median pass with tie → use >0.5 as pass criterion)
base_pass = {tid: (sum(1 for s in base_results[tid] if s["passed"]) >= 3) for tid in RC_TASKS}
cand_pass = {tid: (sum(1 for s in cand_results[tid] if s["passed"]) >= 3) for tid in RC_TASKS}

# Pooled McNemar: count pairs where base fail / cand pass vs base pass / cand fail
b = sum(1 for tid in RC_TASKS if base_pass[tid] and not cand_pass[tid])
c = sum(1 for tid in RC_TASKS if (not base_pass[tid]) and cand_pass[tid])
p, _, _ = E.mcnemar_exact(b, c)
ci = E.bootstrap_delta_ci(base_mean, cand_mean, n_boot=10000, seed=20260724)
delta = round(sum(cand_mean.values())/len(RC_TASKS) - sum(base_mean.values())/len(RC_TASKS), 3)

# Per-seed pass counts (raw)
def per_seed_pass(results, tids):
    out = []
    for i in range(K):
        out.append(sum(1 for tid in tids if results[tid][i]["passed"]))
    return out

per_split = {}
for split in ["dev","hidden","fresh"]:
    sids = [tid for tid in RC_TASKS if tmap[tid]["split"] == split]
    per_split[split] = {
        "n": len(sids),
        "base_pass": sum(1 for tid in sids if base_pass[tid]),
        "cand_pass": sum(1 for tid in sids if cand_pass[tid]),
        "base_mean": round(sum(base_mean[i] for i in sids)/len(sids), 3) if sids else 0,
        "cand_mean": round(sum(cand_mean[i] for i in sids)/len(sids), 3) if sids else 0,
    }

result = {
    "round": 20,
    "type": "CONTEXT_GROUNDING_RC2_RC3_K5_REAL",
    "model": "Qwen2.5-3B-Instruct",
    "K": K,
    "seeds": SEEDS,
    "temperature": TEMPERATURE,
    "n_tasks": len(RC_TASKS),
    "task_ids": RC_TASKS,
    "candidate_prefix": PREFIX,
    "base_pass": sum(1 for tid in RC_TASKS if base_pass[tid]),
    "cand_pass": sum(1 for tid in RC_TASKS if cand_pass[tid]),
    "per_seed_base_pass": per_seed_pass(base_results, RC_TASKS),
    "per_seed_cand_pass": per_seed_pass(cand_results, RC_TASKS),
    "discordant_base_pass_cand_fail": b,
    "discordant_base_fail_cand_pass": c,
    "mcnemar_p": p,
    "bootstrap_ci95_overall_delta": list(ci),
    "delta_overall": delta,
    "per_task_base_pass": base_pass,
    "per_task_cand_pass": cand_pass,
    "per_task_base_mean": {tid: round(base_mean[tid], 3) for tid in RC_TASKS},
    "per_task_cand_mean": {tid: round(cand_mean[tid], 3) for tid in RC_TASKS},
    "per_split": per_split,
    "scores_base": base_mean,
    "scores_cand": cand_mean,
    "promotion_rule": "PROMOTE requires cand_pass > base_pass AND McNemar p<0.05 AND CI95 lower bound > 0",
    "decision": "PROMOTE" if (sum(1 for tid in RC_TASKS if cand_pass[tid]) > sum(1 for tid in RC_TASKS if base_pass[tid]) and p < 0.05 and ci[0] > 0) else "HOLD",
    "method_honesty": "K=5 distinct seeds with do_sample=True (temperature=0.7, top_p=0.9) for both arms on the same base; per-task pass = majority of 5 (>=3/5).",
    "artifact_base": BASE_SUB,
    "artifact_cand": CAND_SUB,
    "verified_hash": True,
}
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k:result[k] for k in ['base_pass','cand_pass','discordant_base_pass_cand_fail','discordant_base_fail_cand_pass','mcnemar_p','bootstrap_ci95_overall_delta','delta_overall','per_split','decision']}, ensure_ascii=False, indent=2))
print("wrote", OUT)
