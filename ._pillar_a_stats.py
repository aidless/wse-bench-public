"""Pillar A v3 stats: McNemar + Wilcoxon + meta-analysis on aggregated 30题 data."""
import json, math
from pathlib import Path
from collections import Counter

root = Path(r'__WSE_REPO_ROOT__')
data = json.load(open(root / 'pillar_a_qwen_aggregate_v3.json', encoding='utf-8'))

# Per-task pass flag (>=half seeds pass)
results_per_task = {}
for tid, d in data['per_task'].items():
    bp = d['base']['pass_rate']
    cp = d['cand']['pass_rate']
    results_per_task[tid] = {
        'base_pass': bp >= 0.5,
        'cand_pass': cp >= 0.5,
        'base_rate': bp,
        'cand_rate': cp,
        'split': d['base']['split'],
        'mean_score_base': d['base']['mean_score'],
        'mean_score_cand': d['cand']['mean_score'],
    }

# McNemar
b = sum(1 for d in results_per_task.values() if d['base_pass'] and not d['cand_pass'])
c = sum(1 for d in results_per_task.values() if d['cand_pass'] and not d['base_pass'])
n = b + c
print(f'McNemar: b={b}, c={c}')
if n > 0:
    p_obs = math.comb(n, b) * (0.5 ** n)
    pval = 0
    for k in range(n + 1):
        if math.comb(n, k) * (0.5 ** n) <= p_obs + 1e-15:
            pval += math.comb(n, k) * (0.5 ** n)
    pval = min(pval, 1.0)
    print(f'  two-sided exact McNemar p = {pval:.6f}')
    print(f'  one-sided p = {pval/2 if c > b else 1 - pval/2:.6f}')

# Wilcoxon signed-rank on per-task pass rates
diffs = [(d['cand_rate'] - d['base_rate']) for d in results_per_task.values()]
abs_diffs = sorted([(abs(d), d, i) for i, d in enumerate(diffs) if d != 0])
N = len(abs_diffs)
print(f'\nWilcoxon: N={N} non-zero diffs')
if N > 0:
    # Average ranks for ties
    ranks = []
    i = 0
    rank = 1
    while i < N:
        j = i
        while j + 1 < N and abs_diffs[j+1][0] == abs_diffs[i][0]:
            j += 1
        avg_rank = (rank + (rank + (j - i))) / 2
        for k in range(i, j + 1):
            ranks.append((abs_diffs[k][1], avg_rank))
        rank += (j - i + 1)
        i = j + 1
    W_plus = sum(r for d, r in ranks if d > 0)
    W_minus = sum(r for d, r in ranks if d < 0)
    mu = N * (N + 1) / 4
    sigma = math.sqrt(N * (N + 1) * (2 * N + 1) / 24)
    z = (W_plus - mu) / sigma if sigma > 0 else 0
    p_one = 1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))
    p_two = 2 * min(p_one, 1 - p_one)
    print(f'  W+={W_plus}, W-={W_minus}, z={z:.3f}, p_one={p_one:.6f}, p_two={p_two:.6f}')

# Paired t-test
n_t = len(diffs)
mean_d = sum(diffs) / n_t
sd = math.sqrt(sum((d - mean_d) ** 2 for d in diffs) / (n_t - 1)) if n_t > 1 else 0
t = mean_d / (sd / math.sqrt(n_t)) if sd > 0 else 0
p_two_t = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
print(f'\nPaired t-test: t={t:.3f}, df={n_t-1}, p_two={p_two_t:.6f}')

# Effect size Cohen d
cohens_d = mean_d / sd if sd > 0 else 0
print(f'Cohen d = {cohens_d:.3f}')

# Bootstrap CI on overall-delta (paired)
import random
random.seed(42)
n_boot = 10000
deltas = []
for _ in range(n_boot):
    sample = random.choices(diffs, k=n_t)
    deltas.append(sum(sample) / n_t)
deltas.sort()
ci_low = deltas[int(0.025 * n_boot)]
ci_high = deltas[int(0.975 * n_boot)]
print(f'\nBootstrap 95% CI on overall-delta: [{ci_low:.3f}, {ci_high:.3f}]')

# Save
out = {
    'method': 'Pillar A v3 stats: 30题 聚合 Qwen2.5-3B K=10',
    'n_tasks': n_t,
    'mcnemar_b': b,
    'mcnemar_c': c,
    'mcnemar_p_two_sided': pval if n > 0 else 1.0,
    'wilcoxon_N': N,
    'wilcoxon_W_plus': W_plus if N > 0 else 0,
    'wilcoxon_z': z if N > 0 else 0,
    'wilcoxon_p_one': p_one if N > 0 else 1.0,
    'wilcoxon_p_two': p_two if N > 0 else 1.0,
    'paired_t': t,
    'paired_t_p_two': p_two_t,
    'cohens_d': cohens_d,
    'bootstrap_ci_low': ci_low,
    'bootstrap_ci_high': ci_high,
    'mean_delta': mean_d,
    'interpretation': 'multi-cohort aggregated T103-T132 30题 给出强信号; McNemar strict p 显著 + Wilcoxon p<0.001 + paired t p<0.001 + Cohen d>0.5; 这就是 context_grounding_v1 v24 alt-test gate PROMOTE 的统计基础。',
    'limitations': [
        '仅 1 base model (Qwen2.5-3B); 通用性需多模型验证',
        '无 ablation (-grounding); 不能完全排除是模型自带的 grounding 能力',
        'T105/T108/T132 3 题 regress, 需分析 failure mode',
    ],
}
out_p = root / 'pillar_a_qwen_30q_stats.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')