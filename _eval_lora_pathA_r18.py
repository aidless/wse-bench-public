"""Clean PATH_A r18 diagnostic: same base, same prompts/settings, hidden+fresh only.
No promotion/ledger write is performed here; it produces an auditable result for review.
"""
import os, json, time, gc, sys
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
ADAPTER_PATH = r"F:\lora_adapter\qwen3b_pathA_r18_dev"
OUT = os.path.join(ROOT, "results_lora_pathA_r18_hiddenfresh.json")
BASE_SUB = os.path.join(ROOT, "submissions_base_pathA_r18_hiddenfresh.json")
CAND_SUB = os.path.join(ROOT, "submissions_lora_pathA_r18_hiddenfresh.json")

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
if not ok:
    raise SystemExit(f"HASH LOCK FAILED: {bad[:3]}")
tasks = [t for t in manifest["tasks"] if t.get("split") in {"hidden", "fresh"}]
tmap = {t["id"]: t for t in tasks}
ids = [t["id"] for t in tasks]
print(f"evaluation tasks={len(ids)} hidden={sum(t['split']=='hidden' for t in tasks)} fresh={sum(t['split']=='fresh' for t in tasks)}", flush=True)

# Same tokenizer/model/generation settings for base and adapter.
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
base = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb, dtype=torch.float16, device_map="auto", trust_remote_code=True)
base.eval()

def generate(model, prompt):
    text = tokenizer.apply_chat_template([{"role":"user", "content":prompt}], tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=256, do_sample=False, pad_token_id=tokenizer.pad_token_id)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

def run(model, label):
    out = {}
    t0 = time.time()
    for i, tid in enumerate(ids, 1):
        ans = generate(model, tmap[tid]["prompt"])
        sc = E.score_task(tmap[tid], ans)
        out[tid] = {"answer": ans, "score": sc, "passed": E.is_pass(sc, tmap[tid]), "split": tmap[tid]["split"]}
        if i == 1 or i % 10 == 0 or i == len(ids):
            print(f"{label} [{i}/{len(ids)}] {tid} score={sc} elapsed={time.time()-t0:.0f}s", flush=True)
    return out

base_results = run(base, "BASE")
json.dump({k:v["answer"] for k,v in base_results.items()}, open(BASE_SUB,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
# Attach adapter after base pass; base weights remain the same reference for this process.
model = PeftModel.from_pretrained(base, ADAPTER_PATH)
model.eval()
cand_results = run(model, "LORA")
json.dump({k:v["answer"] for k,v in cand_results.items()}, open(CAND_SUB,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

base_scores = {tid: base_results[tid]["score"] for tid in ids}
cand_scores = {tid: cand_results[tid]["score"] for tid in ids}
base_pass = {tid: base_results[tid]["passed"] for tid in ids}
cand_pass = {tid: cand_results[tid]["passed"] for tid in ids}
b = sum(base_pass[tid] and not cand_pass[tid] for tid in ids)
c = sum((not base_pass[tid]) and cand_pass[tid] for tid in ids)
p, _, _ = E.mcnemar_exact(b, c)
ci = E.bootstrap_delta_ci(base_scores, cand_scores, n_boot=10000, seed=20260724)
per_split = {}
for split in ["hidden", "fresh"]:
 sids = [tid for tid in ids if tmap[tid]["split"] == split]
 per_split[split] = {
  "n": len(sids),
  "base_mean": round(sum(base_scores[i] for i in sids)/len(sids),3),
  "lora_mean": round(sum(cand_scores[i] for i in sids)/len(sids),3),
  "base_pass": sum(base_pass[i] for i in sids),
  "lora_pass": sum(cand_pass[i] for i in sids),
 }
result = {
 "round": 18,
 "type": "PATH_A_RETRY_DIAGNOSTIC",
 "model": "Qwen2.5-3B-Instruct + dev-only LoRA r8",
 "adapter_path": ADAPTER_PATH,
 "n_tasks": len(ids),
 "task_ids": ids,
 "training_data": "sft_dev_r18.jsonl (dev only; hidden/fresh excluded)",
 "generation": {"max_new_tokens":256,"do_sample":False,"same_process_base_then_lora":True},
 "base_pass": sum(base_pass.values()),
 "lora_pass": sum(cand_pass.values()),
 "discordant_base_pass_lora_fail": b,
 "discordant_base_fail_lora_pass": c,
 "mcnemar_p": p,
 "bootstrap_ci95_overall_delta": list(ci),
 "delta_overall": round(sum(cand_scores.values())/len(ids)-sum(base_scores.values())/len(ids),3),
 "per_split": per_split,
 "scores_base": base_scores,
 "scores_lora": cand_scores,
 "verified_hash": True,
 "decision": "DIAGNOSTIC_ONLY",
 "promotion_rule": "not applied; requires independent K>=5 replication and p<0.05 + CI low>0",
}
json.dump(result, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k:result[k] for k in ['base_pass','lora_pass','discordant_base_pass_lora_fail','discordant_base_fail_lora_pass','mcnemar_p','bootstrap_ci95_overall_delta','delta_overall','per_split']}, ensure_ascii=False), flush=True)
