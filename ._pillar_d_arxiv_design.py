"""Pillar D v2: 路径 A 重启 - 跨域 ≥500 DPO pairs from arxiv benchmarks.

Design:
- Use arxiv benchmark data (ARC, GSM8K, MMLU train) with verified correct/incorrect answers
- 500+ chosen/rejected pairs across 5+ domains
- DPO training: β=0.05 (tight KL), r=16, lr=5e-6, 2 epochs
- K=5 eval on v144 hidden+fresh

Since we don't have direct access to arxiv benchmarks, we construct a synthetic-but-honest
'difficult cases' dataset by:
1. Taking WSE-Bench hard 14 题 (T047-T060) where base 0% → these are the "rejected" answers
2. Pairing with the K=5 best answers from raw submissions that DID pass (the "chosen")

This gives 14 hard 题 × 5 successful attempts = 70 high-quality pairs.
For 500+ we need 7x more domains. Let me also include:
- struct 12 题 (T061-T072) with K=5 success/fail
- sv 12 题 (T073-T084) with K=5 success/fail
- fact 6 题 (T085-T090) with K=5 success/fail

Total: 14+12+12+6 = 44 题 × 5 = 220 base answers. Filter to high-confidence pairs.
"""
import json, sys, random
from pathlib import Path
from collections import defaultdict
root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}

# Aggregate raw submissions across strategies
sub_files = [
    ('submissions_hard_15seeds.json', ['baseline_seeds', 'tool_arith_seeds', 'decompose_seeds']),
    ('submissions_struct_10seeds.json', ['baseline_seeds', 'schema_guard_seeds']),
    ('submissions_sv_10seeds.json', ['baseline_seeds', 'self_verify_seeds']),
    ('submissions_fact_10seeds.json', ['baseline_seeds', 'citation_check_seeds']),
    ('submissions_verify_10seeds_v3.json', ['baseline_seeds', 'verifier_seeds']),
    ('submissions_rc_10seeds.json', ['baseline_seeds', 'context_grounding_seeds']),
]

# Collect (task_id, prompt, answer, score, is_pass) tuples
all_arms = []  # list of (tid, prompt, answer, score, is_pass, source, seed)
for fn, keys in sub_files:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for k in keys:
        for seed_idx, b in enumerate(d.get(k, [])):
            for tid, ans in b.items():
                t = task_by_id.get(tid)
                if not t:
                    continue
                if not isinstance(ans, str) or len(ans) < 5:
                    continue
                s = score_task(t, ans)
                all_arms.append((tid, t['prompt'], ans, s, is_pass(s, t), f'{fn}:{k}', seed_idx))

print(f'collected {len(all_arms)} arms')

# Filter to dev-only
dev_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'dev'}
dev_arms = [a for a in all_arms if a[0] in dev_ids]
print(f'dev arms: {len(dev_arms)}')

# Build chosen/rejected pairs per task: chosen = best passing, rejected = worst failing
# Limit gap >= 0.2 to ensure signal
pairs = []
by_task = defaultdict(list)
for tid, prompt, ans, score, passed, src, seed in dev_arms:
    by_task[tid].append({'prompt': prompt, 'answer': ans, 'score': score, 'is_pass': passed, 'source': src, 'seed': seed})

for tid, items in by_task.items():
    passing = [it for it in items if it['is_pass']]
    failing = [it for it in items if not it['is_pass']]
    if not passing or not failing:
        continue
    # Best passing, worst failing
    passing_sorted = sorted(passing, key=lambda x: -x['score'])
    failing_sorted = sorted(failing, key=lambda x: x['score'])
    best = passing_sorted[0]
    worst = failing_sorted[0]
    if best['score'] - worst['score'] < 0.2:
        continue
    pairs.append({
        'task_id': tid,
        'prompt': best['prompt'],
        'chosen': best['answer'],
        'rejected': worst['answer'],
        'chosen_score': best['score'],
        'rejected_score': worst['score'],
        'gap': best['score'] - worst['score'],
        'chosen_source': best['source'],
    })

# Cap at 5 pairs per task for diversity
random.seed(42)
task_count = defaultdict(int)
final = []
# Sort by gap desc
for pr in sorted(pairs, key=lambda x: -x['gap']):
    if task_count[pr['task_id']] >= 3:
        continue
    final.append(pr)
    task_count[pr['task_id']] += 1

print(f'pairs before dedup: {len(pairs)}')
print(f'pairs final (≤3/task): {len(final)}')
print(f'unique tasks: {len({p["task_id"] for p in final})}')
print(f'gap mean: {sum(p["gap"] for p in final) / len(final) if final else 0:.3f}')

# Write
out_p = root / 'sft_dev_dpo_pillar_d_v2.jsonl'
with open(out_p, 'w', encoding='utf-8') as f:
    for pr in final:
        f.write(json.dumps({
            'prompt': pr['prompt'],
            'chosen': pr['chosen'],
            'rejected': pr['rejected'],
            'task_id': pr['task_id'],
            'gap': pr['gap'],
            'chosen_source': pr['chosen_source'],
        }, ensure_ascii=False) + '\n')
print(f'written: {out_p}')