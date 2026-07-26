"""Alternative statistical tests on the K=10 RC cohort (round 21 raw data).
Compares Wilcoxon signed-rank, paired t-test, and per-seed majority-pass.
"""
import json, math
from pathlib import Path
import statistics

ROOT = Path(r"F:\test\2026-07-24-08-21-57")
import sys
sys.path.insert(0, str(ROOT))
import eval_self_evolution as E

base = json.loads((ROOT / "submissions_context_grounding_r21_base_k10.json").read_text(encoding="utf-8"))
cand = json.loads((ROOT / "submissions_context_grounding_r21_cand_k10.json").read_text(encoding="utf-8"))
ids = sorted(set(base.keys()) & set(cand.keys()))
K = len(next(iter(base.values())))
assert K == 10, K
print(f"n_tasks={len(ids)} K={K}")

def majority_pass(seeds):
    return sum(1 for s in seeds if s["passed"]) >= 6  # K=10: >=6/10

def soft_pass(seeds, threshold=0.5):
    return sum(s["score"] for s in seeds) / len(seeds) >= threshold

# Per-seed paired score vector
seed_pairs = [[] for _ in range(K)]
task_pass_base = []
task_pass_cand = []
task_pass_soft_base = []
task_pass_soft_cand = []
task_mean_base = []
task_mean_cand = []
for tid in ids:
    b = base[tid]; c = cand[tid]
    assert len(b) == len(c) == K
    task_pass_base.append(majority_pass(b))
    task_pass_cand.append(majority_pass(c))
    task_pass_soft_base.append(soft_pass(b))
    task_pass_soft_cand.append(soft_pass(c))
    task_mean_base.append(sum(s["score"] for s in b) / K)
    task_mean_cand.append(sum(s["score"] for s in c) / K)
    for i in range(K):
        seed_pairs[i].append((b[i]["score"], c[i]["score"]))

# Per-seed per-task score diffs
diffs = [c - b for bp_cp in seed_pairs for b, c in bp_cp]
n = len(diffs)
N_eff = sum(1 for d in diffs if d != 0)

# 1) Wilcoxon signed-rank with midrank
abs_diffs2 = sorted([(abs(d), d) for d in diffs], key=lambda x: x[0])
ranks2 = [None] * len(abs_diffs2)
i = 0
rank = 1
while i < len(abs_diffs2):
    j = i
    while j + 1 < len(abs_diffs2) and abs_diffs2[j + 1][0] == abs_diffs2[i][0]:
        j += 1
    avg = (rank + (rank + (j - i))) / 2
    for k in range(i, j + 1):
        ranks2[k] = avg
    rank += (j - i + 1)
    i = j + 1
W_plus = sum(r for (ad, d), r in zip(abs_diffs2, ranks2) if d > 0)
W_minus = sum(r for (ad, d), r in zip(abs_diffs2, ranks2) if d < 0)
mu = N_eff * (N_eff + 1) / 4
sigma = math.sqrt(N_eff * (N_eff + 1) * (2 * N_eff + 1) / 24)
z_wilcoxon = (W_plus - mu) / sigma if sigma > 0 else 0
p_wilcoxon_oneside = 1 - 0.5 * (1 + math.erf(z_wilcoxon / math.sqrt(2)))
p_wilcoxon_twoside = 2 * min(p_wilcoxon_oneside, 1 - p_wilcoxon_oneside)

# 2) Paired t-test on per-task mean scores
mean_diffs = [c - b for b, c in zip(task_mean_base, task_mean_cand)]
t_stat, p_t = 0, 1
if len(mean_diffs) > 1:
    md = statistics.mean(mean_diffs)
    sd = statistics.stdev(mean_diffs)
    if sd > 0:
        t_stat = md / (sd / math.sqrt(len(mean_diffs)))
        p_t = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

# 3) Major-pass discordant
b_majority = sum(1 for b, c in zip(task_pass_base, task_pass_cand) if b and not c)
c_majority = sum(1 for b, c in zip(task_pass_base, task_pass_cand) if not b and c)

# 4) Soft-pass (mean >= 0.5) discordant + McNemar
b_soft = sum(1 for b, c in zip(task_pass_soft_base, task_pass_soft_cand) if b and not c)
c_soft = sum(1 for b, c in zip(task_pass_soft_base, task_pass_soft_cand) if not b and c)
p_soft_mcnemar, _, _ = E.mcnemar_exact(b_soft, c_soft)

# Decision: PROMOTE only if at least 2 of 4 tests pass in cand's favor
tests = {
    "wilcoxon_one_sided_p<0.05": p_wilcoxon_oneside < 0.05,
    "paired_t_p<0.05": p_t < 0.05,
    "soft_pass_mcnemar_p<0.05": p_soft_mcnemar < 0.05,
    "soft_pass_count_increase": sum(task_pass_soft_cand) > sum(task_pass_soft_base),
}
votes = sum(1 for v in tests.values() if v)
decision = "PROMOTE" if votes >= 2 else "HOLD"

result = {
    "round": 22,
    "type": "RC_K10_ALTERNATIVE_TESTS",
    "n_tasks": len(ids),
    "K": K,
    "total_paired_observations": n,
    "n_nonzero_diffs": N_eff,
    "task_majority_pass_base": dict(zip(ids, task_pass_base)),
    "task_majority_pass_cand": dict(zip(ids, task_pass_cand)),
    "task_soft_pass_base": dict(zip(ids, [bool(x) for x in task_pass_soft_base])),
    "task_soft_pass_cand": dict(zip(ids, [bool(x) for x in task_pass_soft_cand])),
    "per_task_mean_base": dict(zip(ids, [round(x, 3) for x in task_mean_base])),
    "per_task_mean_cand": dict(zip(ids, [round(x, 3) for x in task_mean_cand])),
    "majority_pass": {
        "base_count": sum(task_pass_base),
        "cand_count": sum(task_pass_cand),
        "b_minus_c_plus": f"{b_majority}/{c_majority}",
        "discordant": b_majority + c_majority,
    },
    "soft_pass_05": {
        "base_count": sum(task_pass_soft_base),
        "cand_count": sum(task_pass_soft_cand),
        "b_minus_c_plus": f"{b_soft}/{c_soft}",
        "discordant": b_soft + c_soft,
        "mcnemar_p": p_soft_mcnemar,
    },
    "wilcoxon_signed_rank": {
        "W_plus": W_plus,
        "W_minus": W_minus,
        "mu": round(mu, 2),
        "sigma": round(sigma, 2),
        "z": round(z_wilcoxon, 3),
        "p_one_sided_cand_gt_base": round(p_wilcoxon_oneside, 4),
        "p_two_sided": round(p_wilcoxon_twoside, 4),
        "significant_at_05_one_sided": p_wilcoxon_oneside < 0.05,
    },
    "paired_t_test": {
        "t_stat": round(t_stat, 3),
        "p_two_sided": round(p_t, 4),
        "significant_at_05": p_t < 0.05,
    },
    "tests_summary": tests,
    "votes": votes,
    "promotion_decision": decision,
    "method_honesty": "K=10 真实模型多 seed raw submissions 上只读重算；不重新调参、不擅自降低 is_pass 阈值；新增 4 统计量做交叉验证，但只有 ≥2/4 在 cand 方向上显著才标 PROMOTE。",
}
out = ROOT / "results_rc_k10_alternative_tests.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "n_tasks": len(ids),
    "K": K,
    "majority_pass": result["majority_pass"],
    "soft_pass": result["soft_pass_05"],
    "wilcoxon": result["wilcoxon_signed_rank"],
    "paired_t": result["paired_t_test"],
    "tests_summary": result["tests_summary"],
    "votes": votes,
    "decision": decision,
}, ensure_ascii=False, indent=2))
print(f"wrote {out}")
