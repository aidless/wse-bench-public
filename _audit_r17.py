"""轮17：6 策略栈 STRATEGY_AUDIT_V3（v102 102题 5 策略 + verifier_v1）。"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "results_audit_r17_v3.json")

# 6 策略的 target cohort
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
    "verifier": ["T097", "T098", "T099", "T100", "T101", "T102"],
}

# 由于 v90 baseline/v90 production 没有 102 题数据，我们用 v90 baseline 映射到 96 题 + 假设 v96 的 T097-T102 baseline = 当前 baseline K=10 结果 (0.050)
# 简化：v90 baseline (96 题) + verifier_v1 K=10 (T097-T102 baseline=0.05) → 6 策略栈 audit

# 实际计算：A_minus = baseline K=5/v90 scores (来自 v90 baseline)
# full = v90 production K=5 scores (来自 v90 production)
# v90 baseline 已含 T001-T096 baseline
# v90 production 已含 T001-T096 production 5 策略
# T097-T102 baseline 用 verifier_v1 K=10 baseline (3/60 per题 / 10 = 0.05)
# T097-T102 production 5 策略：v90 production 不含 T097-T102，需假设 production 5 策略对 T097-T102 也接近 1.0（v90 production K=5 在 96 题上整体 0.99）
# T097-T102 production 用 verifier_v1 candidate K=10 = 59/60 per题平均 = 0.983
# 6 策略栈 production = v90 production + verifier_v1 on T097-T102

with open(os.path.join(BASE, "results_baseline_agg5_v90.json"), encoding="utf-8") as f:
    base90 = json.load(f)["scores"]
with open(os.path.join(BASE, "results_production_agg5_v90.json"), encoding="utf-8") as f:
    prod90 = json.load(f)["scores"]

# T097-T102 baseline (K=10 平均) 和 production (6 策略栈 K=10)
verify_baseline = {"T097": 0.0, "T098": 0.0, "T099": 0.0, "T100": 0.0, "T101": 0.0, "T102": 0.3}
# 6 策略栈生产配置对 T097-T102：用 verifier_v1 candidate K=10 平均
verify_production = {"T097": 1.0, "T098": 0.9, "T099": 1.0, "T100": 1.0, "T101": 1.0, "T102": 1.0}

# 合并
full = dict(prod90)
base = dict(base90)
for tid, s in verify_production.items():
    full[tid] = s
for tid, s in verify_baseline.items():
    base[tid] = s

# 计算
audit = {}
for strat, cohort in TARGET_COHORT.items():
    minus_scores = {tid: base[tid] for tid in cohort}
    full_scores = {tid: full[tid] for tid in cohort}
    minus_mean = sum(minus_scores.values()) / len(cohort)
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

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("STRATEGY_AUDIT_V3  (6 策略栈, K=5 reference, NOISE_FLOOR=0.05)")
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
print(f"6 策略栈 NECESSARY 比例: {len(necessary)}/6")
print()
print("wrote", OUT)