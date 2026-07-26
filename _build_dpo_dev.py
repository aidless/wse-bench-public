"""Build DPO dataset from raw submissions across all strategies.
Constraint: dev-only (no hidden/fresh task answers).

For each (task, strategy, seed) pair:
- chosen: production arm passing answer
- rejected: baseline arm failing answer

Constructed from raw K=5 (or K=10 for verify v3) submissions.
"""
import json
from pathlib import Path
from collections import defaultdict

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
dev_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'dev'}
hidden_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'hidden'}
fresh_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'fresh'}

# Map task_id -> prompt
prompts = {t['id']: t['prompt'] for t in manifest['tasks']}

# Submission files and their (baseline_key, candidate_key) pairs
SUBMISSION_FILES = [
    ('submissions_fact_10seeds.json', 'baseline_seeds', 'citation_check_seeds'),
    ('submissions_hard_15seeds.json', 'baseline_seeds', 'tool_arith_seeds'),
    ('submissions_struct_10seeds.json', 'baseline_seeds', 'schema_guard_seeds'),
    ('submissions_sv_10seeds.json', 'baseline_seeds', 'self_verify_seeds'),
    ('submissions_verify_10seeds_v3.json', 'baseline_seeds', 'verifier_seeds'),
    ('submissions_rc_10seeds.json', 'baseline_seeds', 'context_grounding_seeds'),
]

pairs = []
n_total = 0
n_forbidden = 0

for fn, base_key, cand_key in SUBMISSION_FILES:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    base_seeds = d.get(base_key, [])
    cand_seeds = d.get(cand_key, [])
    if not base_seeds or not cand_seeds:
        continue
    K = len(base_seeds)
    for seed_idx in range(K):
        b = base_seeds[seed_idx]
        c = cand_seeds[seed_idx]
        # Each is {tid: [{answer, score, is_pass}, ...]} - we need the first entry per task
        for tid in b.keys():
            if tid in hidden_ids or tid in fresh_ids:
                n_forbidden += 1
                continue
            if tid not in dev_ids:
                continue
            b_entry = b[tid][0] if b[tid] else None
            c_entry = c[tid][0] if c[tid] else None
            if not b_entry or not c_entry:
                continue
            # chosen = production arm (candidate) if pass=True; rejected = baseline if pass=False
            if c_entry.get('is_pass') and not b_entry.get('is_pass'):
                pairs.append({
                    'task_id': tid,
                    'prompt': prompts.get(tid, ''),
                    'chosen': c_entry.get('answer', ''),
                    'rejected': b_entry.get('answer', ''),
                    'strategy': cand_key.replace('_seeds', ''),
                    'seed_idx': seed_idx,
                    'chosen_score': c_entry.get('score', 0.0),
                    'rejected_score': b_entry.get('score', 0.0),
                })
                n_total += 1
            # also include cand-failed / baseline-passed (rejection direction is the same)
            elif b_entry.get('is_pass') and not c_entry.get('is_pass'):
                pairs.append({
                    'task_id': tid,
                    'prompt': prompts.get(tid, ''),
                    'chosen': b_entry.get('answer', ''),
                    'rejected': c_entry.get('answer', ''),
                    'strategy': base_key.replace('_seeds', '') + '_neg',
                    'seed_idx': seed_idx,
                    'chosen_score': b_entry.get('score', 0.0),
                    'rejected_score': c_entry.get('score', 0.0),
                })
                n_total += 1

# Dedup by (prompt, chosen) and (prompt, rejected) within strategy — keep diverse examples
seen = set()
deduped = []
for pr in pairs:
    key = (pr['task_id'], pr['strategy'])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(pr)

print(f'n_total raw pairs: {n_total}')
print(f'n_forbidden (hidden/fresh): {n_forbidden}')
print(f'n_deduped (one per task-strategy): {len(deduped)}')

# Distribution by task
dist = defaultdict(int)
for pr in deduped:
    dist[pr['task_id']] += 1
print('unique tasks:', len(dist))
print('per-strategy counts:', {k: sum(1 for p in deduped if p['strategy'] == k) for k in set(p['strategy'] for p in deduped)})

# Write DPO JSONL
out_p = root / 'sft_dev_dpo_r23.jsonl'
with open(out_p, 'w', encoding='utf-8') as f:
    for pr in deduped:
        f.write(json.dumps({
            'prompt': pr['prompt'],
            'chosen': pr['chosen'],
            'rejected': pr['rejected'],
            'task_id': pr['task_id'],
            'strategy': pr['strategy'],
        }, ensure_ascii=False) + '\n')
print('written:', out_p)
print('total pairs:', len(deduped))