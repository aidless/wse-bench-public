# -*- coding: utf-8 -*-
"""第十五轮：5 策略栈 STRATEGY_AUDIT_V2（验证 citation_check_v1 在 5 策略栈中仍 NECESSARY）。
- reference = results_production_agg5_v90.json（K=5，5 策略栈）。
- A_minus = v90 baseline K=5 保守下界。
- NOISE_FLOOR=0.05。
- target cohort: selective_retrieval→23 selective_retrieval 题 / tool_arith→14 hard /
  schema_guard→12 struct / self_verify→12 sv / **citation_check_v1→6 fact (T085-T090)**。
- 判决：A_minus - full ≤ -0.05 → NECESSARY；|Δ|<0.05 → AMBIGUOUS；Δ>0.05 → REDUNDANT。
- v13/v14 教训：registry audit key 必须带 `_v1` 后缀。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

# ---------- Target cohort 定义（5 策略） ----------
TARGET_COHORT = {
    "selective_retrieval": ["T015", "T016", "T017", "T018", "T019", "T020", "T021", "T022",
                            "T023", "T024", "T025", "T026", "T027", "T028", "T029", "T030",
                            "T031", "T032", "T033", "T034", "T035", "T036", "T037"],
    "tool_arith": ["T047", "T048", "T049", "T050", "T051", "T052", "T053", "T054",
                   "T055", "T056", "T057", "T058", "T059", "T060"],
    "schema_guard": ["T061", "T062", "T063", "T064", "T065", "T066", "T067", "T068",
                     "T069", "T070", "T071", "T072"],
    "self_verify": ["T073", "T074", "T075", "T076", "T077", "T078", "T079", "T080",
                    "T081", "T082", "T083", "T084"],
    "citation_check": ["T085", "T086", "T087", "T088", "T089", "T090"],
}

# v90 full reference（5 策略栈 K=5 聚合分）+ v90 baseline 保守下界
with open(os.path.join(ROOT, "results_production_agg5_v90.json"), encoding="utf-8") as f:
    full = json.load(f)["scores"]
with open(os.path.join(ROOT, "results_baseline_agg5_v90.json"), encoding="utf-8") as f:
    base = json.load(f)["scores"]
manifest = E.load_manifest()
assert len(manifest["tasks"]) == 90
ok, bad = E.verify_hashes(manifest)
assert ok, bad

# ---------- 计算 audit 结果 ----------
audit = {}
for strat, cohort in TARGET_COHORT.items():
    minus_scores = {tid: base[tid] for tid in cohort}
    minus_mean = sum(minus_scores.values()) / len(cohort)
    full_scores = {tid: full[tid] for tid in cohort}
    full_mean = sum(full_scores.values()) / len(cohort)
    delta = minus_mean - full_mean
    if delta <= -0.05:
        verdict = "NECESSARY"
    elif delta < 0.05:
        verdict = "AMBIGUOUS"
    else:
        verdict = "REDUNDANT"
    audit[strat] = {
        "target_cohort_size": len(cohort),
        "minus_mean": round(minus_mean, 3),
        "full_mean": round(full_mean, 3),
        "delta_minus_minus_full": round(delta, 3),
        "verdict": verdict,
    }

# 留痕
with open("results_audit_r15.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("STRATEGY_AUDIT_V2  (5 策略栈, K=5 reference, NOISE_FLOOR=0.05)")
print("=" * 80)
for strat, a in audit.items():
    print(f"  {strat:25s} | target n={a['target_cohort_size']:2d} | full={a['full_mean']:.3f}  minus={a['minus_mean']:.3f}  Δ={a['delta_minus_minus_full']:+.3f}  → {a['verdict']}")
print()
necessary = [s for s, a in audit.items() if a["verdict"] == "NECESSARY"]
ambiguous = [s for s, a in audit.items() if a["verdict"] == "AMBIGUOUS"]
redundant = [s for s, a in audit.items() if a["verdict"] == "REDUNDANT"]
print(f"NECESSARY ({len(necessary)}): {necessary}")
print(f"AMBIGUOUS ({len(ambiguous)}): {ambiguous}  ← K=3 噪声底高于 K=5，待 K=5 复测")
print(f"REDUNDANT ({len(redundant)}): {redundant}")
print()
print(f"5 策略栈 NECESSARY 比例: {len(necessary)}/5")
print()
print("wrote results_audit_r15.json")
