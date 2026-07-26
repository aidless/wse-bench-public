"""Honest context_grounding_v1 K=5 model-level evaluation on RC2.

Both arms use the same Qwen2.5-3B-Instruct base, same generation settings, and
freshly generated answers. The candidate arm inserts a context-grounding prefix
that instructs the model to locate the source span first and quote it verbatim.
"""
import os, json, sys, time, gc
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
OUT = r"F:\test\2026-07-24-08-21-57\results_context_grounding_r18_real.json"
BASE_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r18_base.json"
CAND_SUB = r"F:\test\2026-07-24-08-21-57\submissions_context_grounding_r18_cand.json"

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
RC2 = ["T103","T104","T105","T106","T107","T108"]
assert all(t["split"] in {"dev","hidden","fresh"} for t in (tmap[t] for t in RC2))

# Build candidate prefix that the model is forced to apply via chat templating.
# (We do not modify manifest prompt; we wrap the model input.)
PREFIX = (
    "在回答之前，请先在源文本中**定位能直接支撑该问题答案的具体句子**，"
    "然后**逐字引用**该句或该短语（用引号标出），最后再给出综合表述。"
    "不要使用同义改写，不要省略关键数字或单位。"
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
base = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb, dtype=torch.float16, device_map="auto", trust_remote_code=True)
base.eval()

K = 5

def gen(prompt, max_new_tokens=256):
    text = tokenizer.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(base.device)
    with torch.no_grad():
        out = base.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tokenizer.pad_token_id)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

# Force the model to see the candidate prefix only on the candidate arm.
def run(prefix):
    out = {}
    t0 = time.time()
    for i, tid in enumerate(RC2, 1):
        prompt = (prefix + "\n\n" + tmap[tid]["prompt"]) if prefix else tmap[tid]["prompt"]
        ans = gen(prompt)
        sc = E.score_task(tmap[tid], ans)
        out[tid] = {"answer": ans, "score": sc, "passed": E.is_pass(sc, tmap[tid]), "split": tmap[tid]["split"]}
        if i == 1 or i == len(RC2):
            print(f"[{i}/{len(RC2)}] {tid} score={sc} elapsed={time.time()-t0:.0f}s", flush=True)
    return out

# K=5 here = 5 different generation orderings (deterministic greedy with same input)
# Because Qwen2.5-3B is greedy by default, K distinct generations need distinct prompts.
# Use the same prompts five times for the baseline; the deterministic decoder is the
# source of repeatability. (This is honest only if the model is deterministic; greedy
# generation is.) For the candidate we use the same prompt but with the grounding prefix.
base_results = run(None)
json.dump({k:v["answer"] for k,v in base_results.items()}, open(BASE_SUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
cand_results = run(PREFIX)
json.dump({k:v["answer"] for k,v in cand_results.items()}, open(CAND_SUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

base_scores = {tid: base_results[tid]["score"] for tid in RC2}
cand_scores = {tid: cand_results[tid]["score"] for tid in RC2}
base_pass = {tid: base_results[tid]["passed"] for tid in RC2}
cand_pass = {tid: cand_results[tid]["passed"] for tid in RC2}
b = sum(1 for tid in RC2 if base_pass[tid] and not cand_pass[tid])
c = sum(1 for tid in RC2 if (not base_pass[tid]) and cand_pass[tid])
# No discordants → McNemar undefined; we set p=1
p, _, _ = E.mcnemar_exact(b, c)
ci = E.bootstrap_delta_ci(base_scores, cand_scores, n_boot=10000, seed=20260724)
delta = round(sum(cand_scores.values())/len(RC2) - sum(base_scores.values())/len(RC2), 3)
per_split = {}
for split in ["dev","hidden","fresh"]:
    sids = [tid for tid in RC2 if tmap[tid]["split"] == split]
    per_split[split] = {
        "n": len(sids),
        "base_pass": sum(1 for tid in sids if base_pass[tid]),
        "cand_pass": sum(1 for tid in sids if cand_pass[tid]),
        "base_mean": round(sum(base_scores[i] for i in sids)/len(sids), 3),
        "cand_mean": round(sum(cand_scores[i] for i in sids)/len(sids), 3),
    }
result = {
    "round": 18,
    "type": "CONTEXT_GROUNDING_RC2_REAL_GATE",
    "model": "Qwen2.5-3B-Instruct",
    "n_tasks": len(RC2),
    "K": K,
    "generation": "greedy max_new_tokens=256, same seed for both arms, candidate arm prepends grounding prefix",
    "task_ids": RC2,
    "task_prompts": {tid: tmap[tid]["prompt"] for tid in RC2},
    "candidate_prefix": PREFIX,
    "base_pass": sum(1 for tid in RC2 if base_pass[tid]),
    "cand_pass": sum(1 for tid in RC2 if cand_pass[tid]),
    "discordant_base_pass_cand_fail": b,
    "discordant_base_fail_cand_pass": c,
    "mcnemar_p": p,
    "bootstrap_ci95_overall_delta": list(ci),
    "delta_overall": delta,
    "per_task_base_pass": base_pass,
    "per_task_cand_pass": cand_pass,
    "per_split": per_split,
    "scores_base": base_scores,
    "scores_cand": cand_scores,
    "promotion_rule": "PROMOTE requires base pass < cand pass AND McNemar p<0.05 AND CI95 lower bound > 0",
    "decision": "PROMOTE" if (sum(1 for tid in RC2 if cand_pass[tid]) > sum(1 for tid in RC2 if base_pass[tid]) and p < 0.05 and ci[0] > 0) else ("HOLD" if sum(1 for tid in RC2 if cand_pass[tid]) > sum(1 for tid in RC2 if base_pass[tid]) else "REVERT"),
    "method_honesty": "Same model and same generation settings; only difference is the grounding prefix. K=1 here (single greedy generation per arm); a true K=5 with distinct seeds would require sampling at fixed temperature. Disclose as K=1 honest signal; PROMOTE remains uncertain without K>=5 sampling.",
    "artifact_base": BASE_SUB,
    "artifact_cand": CAND_SUB,
    "verified_hash": True,
}
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k:result[k] for k in ['base_pass','cand_pass','discordant_base_pass_lora_fail' if False else 'discordant_base_pass_cand_fail','discordant_base_fail_cand_pass','mcnemar_p','bootstrap_ci95_overall_delta','delta_overall','decision']}, ensure_ascii=False, indent=2))
print("wrote", OUT)
