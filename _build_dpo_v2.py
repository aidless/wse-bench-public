"""Build DPO dataset by scoring raw submissions per task rubric.
For each (task, strategy, seed): chosen = high-score answer; rejected = low-score answer.

Constraint: dev-only (no hidden/fresh).
"""
import json, re
from pathlib import Path
from collections import defaultdict

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}
dev_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'dev'}
hidden_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'hidden'}
fresh_ids = {t['id'] for t in manifest['tasks'] if t.get('split') == 'fresh'}

# Reuse scoring from eval_self_evolution.py
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


# Score every (task, arm) raw answer once
scores_cache = {}
def get_score(tid, ans):
    key = (tid, ans)
    if key in scores_cache:
        return scores_cache[key]
    t = task_by_id[tid]
    s = score_task(t, ans)
    scores_cache[key] = s
    return s


# Collect per-task: list of (answer, score, source, seed)
all_arms = []  # (tid, source, seed, answer)
for fn, base_key, cand_key in SUBMISSION_FILES:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for k, label in [(base_key, 'baseline'), (cand_key, 'cand')]:
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

print(f'raw arms collected: {len(all_arms)}')

# Per task, group by arm & score
by_task = defaultdict(list)
for tid, label, fn, seed_idx, ans in all_arms:
    s = get_score(tid, ans)
    by_task[tid].append({'label': label, 'fn': fn, 'seed_idx': seed_idx, 'answer': ans, 'score': s})


# Build DPO pairs: for each task, find pairs where chosen score > rejected score by gap >= 0.2
pairs = []
for tid, items in by_task.items():
    items_sorted = sorted(items, key=lambda x: x['score'])
    if len(items_sorted) < 2:
        continue
    # Best vs worst
    for i in range(len(items_sorted)):
        for j in range(i+1, len(items_sorted)):
            lo, hi = items_sorted[i], items_sorted[j]
            if hi['score'] - lo['score'] >= 0.2:
                # Use this as a pair: chosen = hi, rejected = lo
                t = task_by_id[tid]
                is_chosen_pass = hi['score'] >= PASS_THRESHOLD.get(t['rubric']['type'], 1.0) - 1e-9
                is_rejected_pass = lo['score'] >= PASS_THRESHOLD.get(t['rubric']['type'], 1.0) - 1e-9
                # Only include pairs where chosen passes and rejected fails
                if is_chosen_pass and not is_rejected_pass:
                    pairs.append({
                        'task_id': tid,
                        'prompt': t['prompt'],
                        'chosen': hi['answer'],
                        'rejected': lo['answer'],
                        'strategy_pair': f"{hi['label']}_{hi['fn']}@{hi['seed_idx']} > {lo['label']}_{lo['fn']}@{lo['seed_idx']}",
                        'chosen_score': hi['score'],
                        'rejected_score': lo['score'],
                    })

# Dedup by (task_id, chosen)
seen = set()
deduped = []
for pr in pairs:
    key = (pr['task_id'], pr['chosen'][:80])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(pr)

print(f'pairs before dedup: {len(pairs)}')
print(f'pairs after dedup: {len(deduped)}')
print('unique tasks:', len({p['task_id'] for p in deduped}))
print('score gap mean:', sum(p['chosen_score'] - p['rejected_score'] for p in deduped) / len(deduped) if deduped else 0)

# Write DPO JSONL
out_p = root / 'sft_dev_dpo_r23.jsonl'
with open(out_p, 'w', encoding='utf-8') as f:
    for pr in deduped:
        f.write(json.dumps({
            'prompt': pr['prompt'],
            'chosen': pr['chosen'],
            'rejected': pr['rejected'],
            'task_id': pr['task_id'],
            'strategy_pair': pr['strategy_pair'],
            'chosen_score': pr['chosen_score'],
            'rejected_score': pr['rejected_score'],
        }, ensure_ascii=False) + '\n')
print('written:', out_p, 'n=', len(deduped))