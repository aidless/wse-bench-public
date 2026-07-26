# -*- coding: utf-8 -*-
"""轮11：从真实 K=5 原始提交生成 structured_output 聚合结果，并合并为 v72 全库口径。"""
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

STRUCT_IDS = [f"T{i:03d}" for i in range(61, 73)]


def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def dump_json(name, obj):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def aggregate_struct(manifest, seeds):
    seed_scores = [E.score_all(manifest, seed)["scores"] for seed in seeds]
    return {
        tid: round(float(statistics.median([scores[tid] for scores in seed_scores])), 3)
        for tid in STRUCT_IDS
    }


def summarize(manifest, scores, seeds_note, note):
    active = [t for t in manifest["tasks"] if t.get("cohort_status", "active") == "active"]
    expected_ids = {t["id"] for t in active}
    assert set(scores) == expected_ids, (len(scores), len(expected_ids), sorted(expected_ids - set(scores)))
    split = {}
    for split_name in ("dev", "hidden", "fresh"):
        ids = [t["id"] for t in active if t["split"] == split_name]
        split[split_name] = round(sum(scores[tid] for tid in ids) / len(ids), 3)
    return {
        "scores": scores,
        "split": split,
        "overall": round(sum(scores.values()) / len(scores), 3),
        "verified": True,
        "seeds": seeds_note,
        "aggregation": "per-question median",
        "manifest_tasks": len(active),
        "note": note,
    }


manifest = E.load_manifest()
assert len(manifest["tasks"]) == 72
ok, bad = E.verify_hashes(manifest)
assert ok, bad
sub = load_json("submissions_struct_10seeds.json")
assert sub["task_ids"] == STRUCT_IDS
assert len(sub["baseline_seeds"]) == 5
assert len(sub["schema_guard_seeds"]) == 5

base_struct = aggregate_struct(manifest, sub["baseline_seeds"])
guard_struct = aggregate_struct(manifest, sub["schema_guard_seeds"])

dump_json(
    "results_struct_baseline_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in STRUCT_IDS]},
        base_struct,
        "2026Q3-struct baseline B1-B5（全新 seed，不复用预检 P1-P3）",
        "轮11 structured_output cohort 直答基线 K=5 逐题中位数聚合。",
    ),
)
dump_json(
    "results_struct_schema_guard_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in STRUCT_IDS]},
        guard_struct,
        "2026Q3-struct schema_guard_v1 G1-G5",
        "轮11 structured_output cohort schema_guard_v1 K=5 逐题中位数聚合。",
    ),
)

base60 = load_json("results_baseline_agg5_v60.json")
prod60 = load_json("results_production_agg5_v60.json")
assert len(base60["scores"]) == 60 and len(prod60["scores"]) == 60
assert not (set(base60["scores"]) & set(STRUCT_IDS))

base72_scores = dict(base60["scores"])
base72_scores.update(base_struct)
prod72_scores = dict(prod60["scores"])
prod72_scores.update(guard_struct)

base72 = summarize(
    manifest,
    base72_scores,
    "v60 直答基线 + 2026Q3-struct baseline K=5(B1-B5，账本#12)",
    "v72：v60(60题)+T061-T072 structured_output 陷阱题直答基线；新 cohort 聚合通过 7/12。",
)
prod72 = summarize(
    manifest,
    prod72_scores,
    "v60 生产配置 + 2026Q3-struct schema_guard_v1 K=5(G1-G5，账本#12 PROMOTE)",
    "v72 生产配置：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 三策略叠加；新 cohort 聚合通过 12/12。",
)

dump_json("results_baseline_agg5_v72.json", base72)
dump_json("results_production_agg5_v72.json", prod72)

print("structured baseline aggregate:", base_struct)
print("structured guard aggregate:", guard_struct)
print("v72 baseline:", base72["overall"], base72["split"])
print("v72 production:", prod72["overall"], prod72["split"])
print("wrote results_{struct_baseline,struct_schema_guard}_agg5.json and results_{baseline,production}_agg5_v72.json")
