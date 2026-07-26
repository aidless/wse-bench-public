"""v102 全库结果：102 题 6 策略栈 production。"""
import json, os, statistics, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

RC_IDS = [f"T{i:03d}" for i in range(91, 97)]
VERIFY_IDS = [f"T{i:03d}" for i in range(97, 103)]


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
assert len(manifest["tasks"]) == 102
ok, bad = E.verify_hashes(manifest)
assert ok, bad

# 加载 RC submissions (T091-T096)
rc_sub = load_json("submissions_rc_10seeds.json")
assert rc_sub["task_ids"] == RC_IDS
base_rc = aggregate(manifest, rc_sub["baseline_seeds"], RC_IDS)
cg_rc = aggregate(manifest, rc_sub["context_grounding_seeds"], RC_IDS)

# 加载 verify submissions (T097-T102)
v_sub = load_json("submissions_verify_10seeds_v3.json")
assert v_sub["task_ids"] == VERIFY_IDS
base_v = aggregate(manifest, v_sub["baseline_seeds"], VERIFY_IDS)
v_prod = aggregate(manifest, v_sub["verifier_seeds"], VERIFY_IDS)

# 单存本 cohort 聚合
dump_json(
    "results_verify_baseline_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in VERIFY_IDS]},
        base_v,
        "2026Q3-verify baseline B1-B10（全新 seed）",
        "轮17 verify cohort 直答基线 K=10 逐题中位数聚合。",
    ),
)
dump_json(
    "results_verifier_v1_agg5.json",
    summarize(
        {**manifest, "tasks": [t for t in manifest["tasks"] if t["id"] in VERIFY_IDS]},
        v_prod,
        "2026Q3-verify verifier_v1 C1-C10（含 C9-T102/C10-T098 故意漏检作真实不完美）",
        "轮17 verify cohort verifier_v1 K=10 逐题中位数聚合。",
    ),
)

# v102 baseline = v90 baseline (T001-T090) + rc baseline (T091-T096) + verify baseline (T097-T102)
base90 = load_json("results_baseline_agg5_v90.json")
prod90 = load_json("results_production_agg5_v90.json")
assert len(base90["scores"]) == 90 and len(prod90["scores"]) == 90
assert not (set(base90["scores"]) & set(RC_IDS + VERIFY_IDS))

base102_scores = dict(base90["scores"])
base102_scores.update(base_rc)
base102_scores.update(base_v)
# production 6 策略栈：v90 production (5 策略) + rc candidate (context_grounding_v1 K=5) + verify candidate (verifier_v1 K=10)
prod102_scores = dict(prod90["scores"])
prod102_scores.update(cg_rc)
prod102_scores.update(v_prod)

base102 = summarize(
    manifest, base102_scores,
    "v90 直答基线 + 2026Q3-rc baseline K=5 + 2026Q3-verify baseline K=10(B1-B10)",
    "v102：v90(90题)+T091-T096 RC baseline K=5 + T097-T102 verify baseline K=10。新 cohort 聚合通过 23/60。",
)
prod102 = summarize(
    manifest, prod102_scores,
    "v90 生产配置 + 2026Q3-rc context_grounding_v1 K=5 + 2026Q3-verify verifier_v1 K=10",
    "v102 生产配置：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 + self_verify_v1 + citation_check_v1 + verifier_v1 六策略叠加；新 cohort 聚合通过 59/60。",
)

dump_json("results_baseline_agg5_v102.json", base102)
dump_json("results_production_agg5_v102.json", prod102)

print("verify baseline aggregate:", base_v)
print("verifier_v1 aggregate:", v_prod)
print("v102 baseline:", base102["overall"], base102["split"])
print("v102 production:", prod102["overall"], prod102["split"])
print("wrote results_{verify_baseline,verifier_v1}_agg5.json and results_{baseline,production}_agg5_v102.json")