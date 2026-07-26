"""Build DPO v3 dataset with relaxed constraints + extra rc arms.
Constraint: dev-only. Allow score gap >= 0.1, all permutations per task.
"""
import json
from pathlib import Path
from collections import defaultdict

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}
dev_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'dev'}
hidden_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'hidden'}
fresh_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'fresh'}

import sys
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, PASS_THRESHOLD


SUBMISSION_FILES = [
    ('submissions_fact_10seeds.json', 'baseline_seeds', 'citation_check_seeds'),
    ('submissions_hard_15seeds.json', 'baseline_seeds', 'tool_arith_seeds'),
    ('submissions_struct_10seeds.json', 'baseline_seeds', 'schema_guard_seeds'),
    ('submissions_sv_10seeds.json', 'baseline_seeds', 'self_verify_seeds'),
    ('submissions_verify_10seeds_v3.json', 'baseline_seeds', 'verifier_seeds'),
    ('submissions_rc_10seeds.json', 'baseline_seeds', 'context_grounding_seeds'),
]

# Extra context_grounding RC arms
RC_FILES = [
    ('submissions_context_grounding_r20_base.json', 'base'),
    ('submissions_context_grounding_r20_cand.json', 'cand'),
    ('submissions_context_grounding_r21_base_k10.json', 'base'),
    ('submissions_context_grounding_r21_cand_k10.json', 'cand'),
    ('submissions_context_grounding_r22_base_rc4_k10.json', 'base'),
    ('submissions_context_grounding_r22_cand_rc4_k10.json', 'cand'),
]

scores_cache = {}
def get_score(tid, ans):
    key = (tid, ans)
    if key in scores_cache:
        return scores_cache[key]
    t = task_by_id[tid]
    s = score_task(t, ans)
    scores_cache[key] = s
    return s


all_arms = []
for fn, base_key, cand_key in SUBMISSION_FILES:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for k, label in [(base_key, 'baseline'), (cand_key, 'candidate')]:
        seeds = d.get(k, [])
        for seed_idx, b in enumerate(seeds):
            for tid, ans in b.items():
                if tid in hidden_ids or tid in fresh_ids:
                    continue
                if tid not in dev_ids:
                    continue
                if not isinstance(ans, str) or len(ans) < 5:
                    continue
                all_arms.append((tid, label, fn, seed_idx, ans))

# Add rc arms (which store {tid: [{score, is_pass, answer, ...}, ...]})
for fn, label in RC_FILES:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for tid, entries in d.items():
        if tid in hidden_ids or tid in fresh_ids:
            continue
        if tid not in dev_ids:
            continue
        for seed_idx, e in enumerate(entries):
            ans = e.get('answer', '')
            if not isinstance(ans, str) or len(ans) < 5:
                continue
            all_arms.append((tid, label, fn, seed_idx, ans))

print(f'raw arms: {len(all_arms)}')


by_task = defaultdict(list)
for tid, label, fn, seed_idx, ans in all_arms:
    s = get_score(tid, ans)
    by_task[tid].append({'label': label, 'fn': fn, 'seed_idx': seed_idx, 'answer': ans, 'score': s})


# Allow gap >= 0.1, any chosen > rejected direction
pairs = []
for tid, items in by_task.items():
    n = len(items)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            hi, lo = (items[i], items[j]) if items[i]['score'] > items[j]['score'] else (items[j], items[i])
            if hi['score'] - lo['score'] < 0.1:
                continue
            t = task_by_id[tid]
            chosen_pass = hi['score'] >= PASS_THRESHOLD.get(t['rubric']['type'], 1.0) - 1e-9
            rejected_pass = lo['score'] >= PASS_THRESHOLD.get(t['rubric']['type'], 1.0) - 1e-9
            # Only chosen passes
            if chosen_pass and not rejected_pass:
                pairs.append({
                    'task_id': tid,
                    'prompt': t['prompt'],
                    'chosen': hi['answer'],
                    'rejected': lo['answer'],
                    'strategy_pair': f"{hi['label']} > {lo['label']}",
                    'gap': hi['score'] - lo['score'],
                })

# Dedup by (task_id, chosen[:80])
seen = set()
deduped = []
for pr in pairs:
    key = (pr['task_id'], pr['chosen'][:80])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(pr)

# Cap at 8 pairs per task to ensure diversity
from collections import Counter
task_count = Counter()
final = []
for pr in deduped:
    if task_count[pr['task_id']] >= 8:
        continue
    task_count[pr['task_id']] += 1
    final.append(pr)

print(f'pairs raw: {len(pairs)}')
print(f'pairs deduped: {len(deduped)}')
print(f'pairs final (≤8/task): {len(final)}')
print(f'unique tasks: {len({p["task_id"] for p in final})}')
print(f'gap mean: {sum(p["gap"] for p in final) / len(final):.3f}' if final else '')

out_p = root / 'sft_dev_dpo_r23.jsonl'
with open(out_p, 'w', encoding='utf-8') as f:
    for pr in final:
        f.write(json.dumps({
            'prompt': pr['prompt'],
            'chosen': pr['chosen'],
            'rejected': pr['rejected'],
            'task_id': pr['task_id'],
            'strategy_pair': pr['strategy_pair'],
            'gap': pr['gap'],
        }, ensure_ascii=False) + '\n')
print('written:', out_p, 'n=', len(final))