"""Build a leakage-safe dev-only SFT set for PATH_A retry (round 18).
Only current manifest dev tasks are eligible; hidden/fresh are never read into training.
"""
import json, os, sys
from collections import Counter, defaultdict

ROOT = r"F:\test\2026-07-24-08-21-57"
sys.path.insert(0, ROOT)
import eval_self_evolution as E

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
if not ok:
    raise SystemExit(f"HASH LOCK FAILED: {bad[:3]}")
tmap = {t["id"]: t for t in manifest["tasks"]}
dev_ids = {t["id"] for t in manifest["tasks"] if t.get("split") == "dev"}

# Prefer promoted-strategy answers for their target cohorts, then core baseline answers.
SOURCES = [
    ("verifier_v1", "submissions_verify_10seeds_v3.json", "verifier_seeds"),
    ("citation_check_v1", "submissions_fact_10seeds.json", "citation_check_seeds"),
    ("self_verify_v1", "submissions_sv_10seeds.json", "self_verify_seeds"),
    ("schema_guard_v1", "submissions_struct_10seeds.json", "schema_guard_seeds"),
    ("tool_arith_v1", "submissions_hard_15seeds.json", "tool_arith_seeds"),
    ("context_grounding_v1", "submissions_rc_10seeds.json", "context_grounding_seeds"),
    ("core_baseline", "submissions_baseline.json", None),
    ("core_baseline", "submissions_baseline_seed2.json", None),
    ("core_baseline", "submissions_baseline_seed3.json", None),
    ("core_baseline", "submissions_baseline_seed4.json", None),
    ("core_baseline", "submissions_baseline_seed5.json", None),
    ("reason_candidate", "submissions_reason_10seeds.json", "candidate_seeds"),
]

# Keep up to three distinct passing answers per task, preserving source priority.
seen_answers = defaultdict(set)
records = []
source_counts = Counter()
for strategy, filename, seed_key in SOURCES:
    path = os.path.join(ROOT, filename)
    if not os.path.exists(path):
        continue
    data = json.load(open(path, encoding="utf-8"))
    if seed_key is None:
        seeds = [data]
    else:
        seeds = data.get(seed_key, [])
    for seed_idx, seed in enumerate(seeds):
        if not isinstance(seed, dict):
            continue
        for tid, answer in seed.items():
            if tid not in dev_ids or tid not in tmap:
                continue
            answer = str(answer).strip()
            if not answer or answer in seen_answers[tid] or len(seen_answers[tid]) >= 3:
                continue
            score = E.score_task(tmap[tid], answer)
            if not E.is_pass(score, tmap[tid]):
                continue
            seen_answers[tid].add(answer)
            records.append({
                "instruction": tmap[tid]["prompt"],
                "input": "",
                "output": answer,
                "task_id": tid,
                "split": "dev",
                "capability": tmap[tid].get("capability"),
                "source_strategy": strategy,
                "source_file": filename,
                "source_seed": seed_idx + 1,
                "score": score,
            })
            source_counts[strategy] += 1

# Hard guard: no hidden/fresh examples and no answer-key fields.
assert records, "No dev-only passing records found"
assert all(r["split"] == "dev" for r in records)
assert all(r["task_id"] in dev_ids for r in records)
assert all("reference" not in r and "rubric" not in r for r in records)

out_jsonl = os.path.join(ROOT, "sft_dev_r18.jsonl")
with open(out_jsonl, "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

by_task = Counter(r["task_id"] for r in records)
by_axis = Counter(r["capability"] for r in records)
manifest_out = {
    "version": "pathA-r18-dev-only-v1",
    "n_records": len(records),
    "n_tasks": len(by_task),
    "task_ids": sorted(by_task),
    "records_per_task": dict(sorted(by_task.items())),
    "by_capability": dict(by_axis),
    "by_source_strategy": dict(source_counts),
    "allowed_split": "dev",
    "forbidden_splits": ["hidden", "fresh"],
    "scorer": "eval_self_evolution.py current score_task/is_pass",
    "preregistration": "preregistration_pathA_r18.json",
}
with open(os.path.join(ROOT, "sft_dev_r18_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest_out, f, ensure_ascii=False, indent=2)

print(f"dev-only records={len(records)} tasks={len(by_task)}")
print("by capability:", dict(by_axis))
print("by strategy:", dict(source_counts))
print("output:", out_jsonl)
print("task ids:", sorted(by_task))
