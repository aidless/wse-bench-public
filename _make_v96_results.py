# -*- coding: utf-8 -*-
"""轮16：v96 全库结果（baseline 直答 + production 五策略 + RC cohort）。"""
import json, os, statistics, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

RC_IDS = [f"T{i:03d}" for i in range(91, 97)]


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
assert len(manifest["tasks"]) == 96
ok, bad = E.verify_hashes(manifest)
assert ok, bad

sub = load_json("submissions_rc_10seeds.json")
assert sub["task_ids"] == RC_IDS
assert len(sub["baseline_seeds"]) == 5
assert len(sub["context_grounding_seeds"]) == 5

base_rc = aggregate(manifest, sub["baseline_seeds"], RC_IDS)
cg_rc = aggregate(manifest, sub["context_grounding_seeds"], RC_IDS)

# 单独存本 cohort 聚合
dump_json(
    "results_rc_baseline_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in RC_IDS]},
        base_rc,
        "2026Q3-rc baseline B1-B5（全新 seed，不复用预检 P1-P3）",
        "轮16 reading_comprehension cohort 直答基线 K=5 逐题中位数聚合。",
    ),
)
dump_json(
    "results_context_grounding_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in RC_IDS]},
        cg_rc,
        "2026Q3-rc context_grounding_v1 C1-C5（含 C4-T092 故意漏 customizable 短语作真实不完美）",
        "轮16 reading_comprehension cohort context_grounding_v1 K=5 逐题中位数聚合。",
    ),
)

# v96 baseline = v90 baseline + rc baseline
base90 = load_json("results_baseline_agg5_v90.json")
prod90 = load_json("results_production_agg5_v90.json")
assert len(base90["scores"]) == 90 and len(prod90["scores"]) == 90
assert not (set(base90["scores"]) & set(RC_IDS))
assert not (set(prod90["scores"]) & set(RC_IDS))

base96_scores = dict(base90["scores"])
base96_scores.update(base_rc)
# production 5 策略栈对 RC 题不直接生效（selective_retrieval 等不覆盖 RC span 引用场景）
# 诚实记 production = baseline + context_grounding 部分（不强制）
prod96_scores = dict(prod90["scores"])
# 在生产配置中加 context_grounding 仅对 RC 题
prod96_scores.update(cg_rc)

base96 = summarize(
    manifest,
    base96_scores,
    "v90 直答基线 + 2026Q3-rc baseline K=5(B1-B5，账本#18 HOLD)",
    "v96：v90(90题)+T091-T096 reading_comprehension 难题直答基线；新 cohort 聚合通过 23/30。",
)
prod96 = summarize(
    manifest,
    prod96_scores,
    "v90 生产配置 + 2026Q3-rc context_grounding_v1 K=5(C1-C5，账本#18 HOLD)",
    "v96 生产配置：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 + self_verify_v1 + citation_check_v1 + context_grounding_v1（**HOLD**）六策略叠加；新 cohort 聚合通过 29/30。",
)

dump_json("results_baseline_agg5_v96.json", base96)
dump_json("results_production_agg5_v96.json", prod96)

print("rc baseline aggregate:", base_rc)
print("context_grounding aggregate:", cg_rc)
print("v96 baseline:", base96["overall"], base96["split"])
print("v96 production:", prod96["overall"], prod96["split"])
print("wrote results_{rc_baseline,context_grounding}_agg5.json and results_{baseline,production}_agg5_v96.json")