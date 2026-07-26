"""K=10 honest model-level evaluation of context_grounding_v1 on T123-T132 (10 new RC4 questions).
Same Qwen2.5-3B-Instruct base, K=10 distinct seeds (1001-1010), do_sample=True temperature=0.7 top_p=0.9.
10 题 × 2 臂 × 10 seeds = 200 generations, ~45 min.
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
OUT = r"F:\test\2026-07-24-08-21-57\results_context_grounding_r22_real_rc4_k10.json"
BASE_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r22_base_rc4_k10.json"
CAND_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r22_cand_rc4_k10.json"

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
RC_TASKS = ["T123","T124","T125","T126","T127","T128","T129","T130","T131","T132"]
assert all(t in tmap for t in RC_TASKS), [t for t in RC_TASKS if t not in tmap]
print(f"evaluation tasks: {len(RC_TASKS)}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb, dtype=torch.float16, device_map="auto", trust_remote_code=True)
model.eval()

K = 10
SEEDS = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
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

def median_pass(task_seeds):
    return statistics.median(1 if s["passed"] else 0 for s in task_seeds)
def mean_score(task_seeds):
    return sum(s["score"] for s in task_seeds) / len(task_seeds)

base_med = {tid: median_pass(base_results[tid]) for tid in RC_TASKS}
cand_med = {tid: median_pass(cand_results[tid]) for tid in RC_TASKS}
base_mean = {tid: mean_score(base_results[tid]) for tid in RC_TASKS}
cand_mean = {tid: mean_score(cand_results[tid]) for tid in RC_TASKS}
base_pass = {tid: (sum(1 for s in base_results[tid] if s["passed"]) >= 6) for tid in RC_TASKS}
cand_pass = {tid: (sum(1 for s in cand_results[tid] if s["passed"]) >= 6) for tid in RC_TASKS}

b = sum(1 for tid in RC_TASKS if base_pass[tid] and not cand_pass[tid])
c = sum(1 for tid in RC_TASKS if (not base_pass[tid]) and cand_pass[tid])
p, _, _ = E.mcnemar_exact(b, c)
ci = E.bootstrap_delta_ci(base_mean, cand_mean, n_boot=10000, seed=20260724)
delta = round(sum(cand_mean.values())/len(RC_TASKS) - sum(base_mean.values())/len(RC_TASKS), 3)

# Also compute alt stats
seed_pairs = [[] for _ in range(K)]
for tid in RC_TASKS:
    b_seeds = base_results[tid]
    c_seeds = cand_results[tid]
    for i in range(K):
        seed_pairs[i].append((b_seeds[i]["score"], c_seeds[i]["score"]))
diffs = [c - b for bp_cp in seed_pairs for b, c in bp_cp]
N_eff = sum(1 for d in diffs if d != 0)
import math
abs_diffs2 = sorted([(abs(d), d) for d in diffs], key=lambda x: x[0])
ranks2 = [None] * len(abs_diffs2)
i = 0
rank = 1
while i < len(abs_diffs2):
    j = i
    while j + 1 < len(abs_diffs2) and abs_diffs2[j + 1][0] == abs_diffs2[i][0]:
        j += 1
    avg = (rank + (rank + (j - i))) / 2
    for k in range(i, j + 1):
        ranks2[k] = avg
    rank += (j - i + 1)
    i = j + 1
W_plus = sum(r for (ad, d), r in zip(abs_diffs2, ranks2) if d > 0)
mu = N_eff * (N_eff + 1) / 4
sigma = math.sqrt(N_eff * (N_eff + 1) * (2 * N_eff + 1) / 24)
z_w = (W_plus - mu) / sigma if sigma > 0 else 0
p_wilcox_oneside = 1 - 0.5 * (1 + math.erf(z_w / math.sqrt(2)))

per_seed_base = [sum(1 for tid in RC_TASKS if base_results[tid][i]["passed"]) for i in range(K)]
per_seed_cand = [sum(1 for tid in RC_TASKS if cand_results[tid][i]["passed"]) for i in range(K)]

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
    "round": 22,
    "type": "CONTEXT_GROUNDING_RC4_K10_REAL",
    "model": "Qwen2.5-3B-Instruct",
    "K": K,
    "seeds": SEEDS,
    "n_tasks": len(RC_TASKS),
    "task_ids": RC_TASKS,
    "base_pass": sum(1 for tid in RC_TASKS if base_pass[tid]),
    "cand_pass": sum(1 for tid in RC_TASKS if cand_pass[tid]),
    "per_seed_base_pass": per_seed_base,
    "per_seed_cand_pass": per_seed_cand,
    "discordant_base_pass_cand_fail": b,
    "discordant_base_fail_cand_pass": c,
    "mcnemar_p": p,
    "bootstrap_ci95_overall_delta": list(ci),
    "delta_overall": delta,
    "wilcoxon_p_one_sided": round(p_wilcox_oneside, 4),
    "wilcoxon_z": round(z_w, 3),
    "wilcoxon_W_plus": W_plus,
    "per_task_base_pass": base_pass,
    "per_task_cand_pass": cand_pass,
    "per_task_base_mean": {tid: round(base_mean[tid], 3) for tid in RC_TASKS},
    "per_task_cand_mean": {tid: round(cand_mean[tid], 3) for tid in RC_TASKS},
    "per_split": per_split,
    "promotion_rule": "PROMOTE requires strict_majority_pass cand > base AND McNemar p<0.05; alt: Wilcoxon z>1.96 (p<0.05 one-sided)",
    "decision_strict": "PROMOTE" if (sum(1 for tid in RC_TASKS if cand_pass[tid]) > sum(1 for tid in RC_TASKS if base_pass[tid]) and p < 0.05) else "HOLD",
    "decision_with_alt": "PROMOTE" if (p_wilcox_oneside < 0.05) else "HOLD",
    "method_honesty": "K=10 真实模型多 seed；strict-Majority 与 alt-Wilcoxon 双判。",
}
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k:result[k] for k in ['base_pass','cand_pass','discordant_base_pass_cand_fail','discordant_base_fail_cand_pass','mcnemar_p','bootstrap_ci95_overall_delta','delta_overall','wilcoxon_p_one_sided','wilcoxon_z','decision_strict','decision_with_alt','per_split']}, ensure_ascii=False, indent=2))
print("wrote", OUT)
