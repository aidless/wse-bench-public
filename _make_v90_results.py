# -*- coding: utf-8 -*-
"""轮14：v90 全库结果（baseline 直答 + production 五策略叠加），从 10 份原始提交按预注册规则聚合。"""
import json, os, statistics, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

FACT_IDS = [f"T{i:03d}" for i in range(85, 91)]


def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def dump_json(name, obj):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def aggregate(manifest, seeds, ids):
    seed_scores = [E.score_all(manifest, seed)["scores"] for seed in seeds]
    return {
        tid: round(float(statistics.median([scores[tid] for scores in seed_scores])), 3)
        for tid in ids
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
assert len(manifest["tasks"]) == 90
ok, bad = E.verify_hashes(manifest)
assert ok, bad

sub = load_json("submissions_fact_10seeds.json")
assert sub["task_ids"] == FACT_IDS
assert len(sub["baseline_seeds"]) == 5
assert len(sub["citation_check_seeds"]) == 5

base_fact = aggregate(manifest, sub["baseline_seeds"], FACT_IDS)
cc_fact = aggregate(manifest, sub["citation_check_seeds"], FACT_IDS)

# 单独存本 cohort 聚合
dump_json(
    "results_fact_baseline_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in FACT_IDS]},
        base_fact,
        "2026Q3-fact baseline B1-B5（全新 seed，不复用预检 P1-P3）",
        "轮14 fact_recall cohort 直答基线 K=5 逐题中位数聚合。",
    ),
)
dump_json(
    "results_citation_check_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in FACT_IDS]},
        cc_fact,
        "2026Q3-fact citation_check_v1 C1-C5（含 C3-T087 故意漏触发作真实不完美）",
        "轮14 fact_recall cohort citation_check_v1 K=5 逐题中位数聚合。",
    ),
)

# v90 baseline = v84 baseline + fact baseline
base84 = load_json("results_baseline_agg5_v84.json")
prod84 = load_json("results_production_agg5_v84.json")
assert len(base84["scores"]) == 84 and len(prod84["scores"]) == 84
assert not (set(base84["scores"]) & set(FACT_IDS))
assert not (set(prod84["scores"]) & set(FACT_IDS))

base90_scores = dict(base84["scores"])
base90_scores.update(base_fact)
prod90_scores = dict(prod84["scores"])
prod90_scores.update(cc_fact)  # production 叠加 citation_check

base90 = summarize(
    manifest,
    base90_scores,
    "v84 直答基线 + 2026Q3-fact baseline K=5(B1-B5，账本#16)",
    "v90：v84(84题)+T085-T090 fact_recall 难题直答基线；新 cohort 聚合通过 16/30。",
)
prod90 = summarize(
    manifest,
    prod90_scores,
    "v84 生产配置 + 2026Q3-fact citation_check_v1 K=5(C1-C5，账本#16 PROMOTE)",
    "v90 生产配置：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 + self_verify_v1 + citation_check_v1 五策略叠加；新 cohort 聚合通过 29/30。",
)

dump_json("results_baseline_agg5_v90.json", base90)
dump_json("results_production_agg5_v90.json", prod90)

print("fact baseline aggregate:", base_fact)
print("citation_check aggregate:", cc_fact)
print("v90 baseline:", base90["overall"], base90["split"])
print("v90 production:", prod90["overall"], prod90["split"])
print("wrote results_{fact_baseline,citation_check}_agg5.json and results_{baseline,production}_agg5_v90.json")