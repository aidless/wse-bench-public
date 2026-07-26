"""Build a dev-only SFT dataset of 500+ unique passing answers across promoted strategies.
Uses all the existing K=5 raw submissions, deduplicates by (task_id, answer), filters by
is_pass=True, and restricts to dev split only (strictly excluding hidden/fresh).
"""
import json, os
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(r"F:\test\2026-07-24-08-21-57")
import sys
sys.path.insert(0, str(ROOT))
import eval_self_evolution as E

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
dev_ids = {t["id"] for t in manifest["tasks"] if t.get("split") == "dev"}
print(f"manifest: {len(manifest['tasks'])} tasks, dev={len(dev_ids)}")

# Source files: existing K=5 (or K=10) raw submissions from all 7 promoted strategies
SOURCES = {
    "selective_retrieval_v1": ("submissions_selective_seed2.json", None),  # baseline; baseline doesn't help as SFT
    "tool_arith_v1": ("submissions_hard_15seeds.json", "tool_arith_seeds"),
    "schema_guard_v1": ("submissions_struct_10seeds.json", "schema_guard_seeds"),
    "self_verify_v1": ("submissions_sv_10seeds.json", "self_verify_seeds"),
    "citation_check_v1": ("submissions_fact_10seeds.json", "citation_check_seeds"),
    "verifier_v1": ("submissions_verify_10seeds_v3.json", "verifier_seeds"),
    "context_grounding_v1": ("submissions_context_grounding_r22_cand_rc4_k10.json", None),  # raw K=10
}

# Path A round 18 dev-only SFT already used select 95 records; we'll generate a fresh 500+ SFT.
# Collect (task_id, answer) pairs that pass is_pass.
seen_answers = defaultdict(set)  # task_id -> set of answers
records = []
strategy_counts = Counter()

for strategy, (filename, seed_key) in SOURCES.items():
    path = ROOT / filename
    if not path.exists():
        print(f"  skip {strategy}: {filename} not found")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    # Build flat list of (task_id, answer) pairs
    flat_pairs = []
    if seed_key is None:
        # raw is {tid: {seed: {answer, score, passed}}} or {tid: answer} depending on file
        for tid, payload in data.items():
            if tid not in tmap:
                continue
            if tid not in dev_ids:
                continue
            if isinstance(payload, dict) and "answer" in payload and "score" in payload:
                flat_pairs.append((tid, payload["answer"]))
            elif isinstance(payload, dict) and all(isinstance(v, dict) and "answer" in v for v in payload.values()):
                for seed_key_inner, payload_inner in payload.items():
                    flat_pairs.append((tid, payload_inner["answer"]))
            elif isinstance(payload, str):
                flat_pairs.append((tid, payload))
            else:
                # r22 cand raw is {tid: [{seed, answer, score, passed}, ...]}
                if isinstance(payload, list):
                    for entry in payload:
                        if isinstance(entry, dict) and "answer" in entry:
                            flat_pairs.append((tid, entry["answer"]))
    else:
        seeds = data.get(seed_key, [])
        for seed in seeds:
            for tid, payload in seed.items():
                if tid not in tmap or tid not in dev_ids:
                    continue
                if isinstance(payload, dict) and "answer" in payload:
                    flat_pairs.append((tid, payload["answer"]))
                elif isinstance(payload, str):
                    flat_pairs.append((tid, payload))
    for tid, answer in flat_pairs:
        if tid not in dev_ids:
            continue
        answer = str(answer).strip()
        if not answer:
            continue
        # Filter by is_pass against current scorer
        sc = E.score_task(tmap[tid], answer)
        if not E.is_pass(sc, tmap[tid]):
            continue
        # Dedup per (task_id, answer)
        if answer in seen_answers[tid]:
            continue
        # Cap at 8 per (task_id, strategy) to keep balance
        per_strat_per_task = sum(1 for r in records if r["task_id"] == tid and r["source_strategy"] == strategy)
        if per_strat_per_task >= 8:
            continue
        seen_answers[tid].add(answer)
        records.append({
            "task_id": tid,
            "split": tmap[tid]["split"],
            "capability": tmap[tid].get("capability"),
            "instruction": tmap[tid]["prompt"],
            "input": "",
            "output": answer,
            "source_strategy": strategy,
            "source_file": filename,
            "score": sc,
        })
        strategy_counts[strategy] += 1

# Dedupe by (task_id, output) globally
seen = set()
unique_records = []
for r in records:
    key = (r["task_id"], r["output"])
    if key in seen:
        continue
    seen.add(key)
    unique_records.append(r)

# Distribute by task
task_counts = Counter(r["task_id"] for r in unique_records)
print(f"total records: {len(unique_records)}")
print(f"by strategy: {dict(strategy_counts)}")
print(f"unique tasks: {len(task_counts)}")
print(f"top tasks: {task_counts.most_common(10)}")

# Write SFT jsonl
out_jsonl = ROOT / "sft_dev_r22_500plus.jsonl"
with open(out_jsonl, "w", encoding="utf-8") as f:
    for r in unique_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"wrote {out_jsonl}: {len(unique_records)} records")

# Write manifest
manifest_out = {
    "version": "pathA-r22-dev-only-500plus",
    "n_records": len(unique_records),
    "n_tasks": len(task_counts),
    "task_ids": sorted(task_counts),
    "allowed_split": "dev",
    "forbidden_splits": ["hidden", "fresh"],
    "scorer": "eval_self_evolution.py current score_task/is_pass",
    "by_source_strategy": dict(strategy_counts),
    "by_task_count_top10": task_counts.most_common(10),
    "preregistration": "preregistration_pathA_r22.json (TBD)",
}
(ROOT / "sft_dev_r22_500plus_manifest.json").write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote manifest")
