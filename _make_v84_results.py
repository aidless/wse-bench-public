# -*- coding: utf-8 -*-
"""轮12：v84 全库结果（baseline 直答 + production 四策略叠加），从 10 份原始提交按预注册规则聚合。"""
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

SV_IDS = [f"T{i:03d}" for i in range(73, 85)]


def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def dump_json(name, obj):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def aggregate(manifest, seeds):
    seed_scores = [E.score_all(manifest, seed)["scores"] for seed in seeds]
    return {
        tid: round(float(statistics.median([scores[tid] for scores in seed_scores])), 3)
        for tid in SV_IDS
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
assert len(manifest["tasks"]) == 84
ok, bad = E.verify_hashes(manifest)
assert ok, bad

sub = load_json("submissions_sv_10seeds.json")
assert sub["task_ids"] == SV_IDS
assert len(sub["baseline_seeds"]) == 5
assert len(sub["self_verify_seeds"]) == 5

base_sv = aggregate(manifest, sub["baseline_seeds"])
sv_sv = aggregate(manifest, sub["self_verify_seeds"])

# struct cohort 聚合
struct_sub = load_json("submissions_struct_10seeds.json")
base_struct = aggregate(manifest, struct_sub["baseline_seeds"])
guard_struct = aggregate(manifest, struct_sub["schema_guard_seeds"])
# 把 struct 协查的 id 也传进来（aggregate 只对 SV_IDS 评分不影响）
for tid in [f"T{i:03d}" for i in range(61, 73)]:
    seed_scores = [E.score_all(manifest, s)["scores"] for s in struct_sub["baseline_seeds"]]
    base_struct[tid] = round(float(statistics.median([sc[tid] for sc in seed_scores])), 3)
for tid in [f"T{i:03d}" for i in range(61, 73)]:
    seed_scores = [E.score_all(manifest, s)["scores"] for s in struct_sub["schema_guard_seeds"]]
    guard_struct[tid] = round(float(statistics.median([sc[tid] for sc in seed_scores])), 3)


def add_sv(d, sv_dict):
    d2 = dict(d)
    d2.update(sv_dict)
    return d2


base72 = load_json("results_baseline_agg5_v72.json")
prod72 = load_json("results_production_agg5_v72.json")
assert len(base72["scores"]) == 72 and len(prod72["scores"]) == 72
assert not (set(base72["scores"]) & set(SV_IDS))
assert not (set(prod72["scores"]) & set(SV_IDS))

# v84 baseline: v72 baseline + new sv baseline
base84_scores = add_sv(base72["scores"], base_sv)
prod84_scores = add_sv(prod72["scores"], sv_sv)  # production 叠加 self_verify

dump_json(
    "results_sv_baseline_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in SV_IDS]},
        base_sv,
        "2026Q3-sv baseline B1-B5（全新 seed，不复用预检 P1-P3）",
        "轮12 self_verify cohort 直答基线 K=5 逐题中位数聚合。",
    ),
)
dump_json(
    "results_self_verify_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in SV_IDS]},
        sv_sv,
        "2026Q3-sv self_verify_v1 G1-G5（含 2 处故意漏检作真实不完美）",
        "轮12 self_verify cohort candidate K=5 逐题中位数聚合。",
    ),
)

base84 = summarize(
    manifest,
    base84_scores,
    "v72 直答基线 + 2026Q3-sv baseline K=5(B1-B5，账本#13)",
    "v84：v72(72题)+T073-T084 self_verify 目标题直答基线；新 cohort 聚合通过 41/60。",
)
prod84 = summarize(
    manifest,
    prod84_scores,
    "v72 生产配置 + 2026Q3-sv self_verify_v1 K=5(G1-G5，账本#13 PROMOTE)",
    "v84 生产配置：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 + self_verify_v1 四策略叠加；新 cohort 聚合通过 59/60。",
)

dump_json("results_baseline_agg5_v84.json", base84)
dump_json("results_production_agg5_v84.json", prod84)

print("sv baseline aggregate:", base_sv)
print("self_verify aggregate:", sv_sv)
print("v84 baseline:", base84["overall"], base84["split"])
print("v84 production:", prod84["overall"], prod84["split"])
print("wrote results_{sv_baseline,self_verify}_agg5.json and results_{baseline,production}_agg5_v84.json")
