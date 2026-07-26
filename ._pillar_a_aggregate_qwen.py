"""Pillar A v2: Aggregate existing Qwen2.5-3B K=10 data for T103-T122.
Uses raw submissions from r20 (T103-T112) + r22 RC4 (T123-T132).
"""
import json, math
from pathlib import Path
from collections import Counter, defaultdict

root = Path(r'__WSE_REPO_ROOT__')

# Load raw submissions
submissions = {}
for fn, key in [
    ('submissions_context_grounding_r20_base.json', 'base'),
    ('submissions_context_grounding_r20_cand.json', 'cand'),
    ('submissions_context_grounding_r21_base_k10.json', 'base'),
    ('submissions_context_grounding_r21_cand_k10.json', 'cand'),
    ('submissions_context_grounding_r22_base_rc4_k10.json', 'base'),
    ('submissions_context_grounding_r22_cand_rc4_k10.json', 'cand'),
]:
    p = root / fn
    if p.exists():
        d = json.load(open(p, encoding='utf-8'))
        submissions.setdefault(key, []).append(d)

# Aggregate
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
import sys
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass
task_by_id = {t['id']: t for t in manifest['tasks']}

# Get all task IDs we have data for
all_tids = set()
for d in submissions.get('base', []):
    all_tids.update(d.keys())

print(f'aggregating across {len(all_tids)} tasks')

# For each task, count passes
results = {'base': {}, 'cand': {}}
for tid in sorted(all_tids):
    t = task_by_id.get(tid)
    if not t:
        continue
    for arm in ['base', 'cand']:
        passes = 0
        n = 0
        for d in submissions.get(arm, []):
            if tid in d:
                for entry in d[tid]:
                    if 'is_pass' in entry:
                        if entry['is_pass']:
                            passes += 1
                        n += 1
        if n > 0:
            results[arm][tid] = {'pass': passes, 'n': n, 'pass_rate': passes / n, 'split': t.get('split', '')}

# Per-arm aggregate
print()
for arm in ['base', 'cand']:
    tids = list(results[arm].keys())
    n_total = sum(results[arm][t]['n'] for t in tids)
    pass_total = sum(results[arm][t]['pass'] for t in tids)
    by_split = defaultdict(lambda: {'n': 0, 'pass': 0})
    for tid, d in results[arm].items():
        by_split[d['split']]['n'] += d['n']
        by_split[d['split']]['pass'] += d['pass']
    print(f'{arm}: {pass_total}/{n_total} ({pass_total/n_total*100:.1f}%)')
    for sp, sd in by_split.items():
        if sd['n']:
            print(f'  {sp}: {sd["pass"]}/{sd["n"]} ({sd["pass"]/sd["n"]*100:.1f}%)')

# Per-task comparison
print()
print('=== Per-task comparison (T103-T122) ===')
b_pass = {tid: results['base'][tid]['pass_rate'] for tid in results['base']}
c_pass = {tid: results['cand'][tid]['pass_rate'] for tid in results['cand']}
all_tids = sorted(set(b_pass.keys()) & set(c_pass.keys()))
for tid in all_tids:
    delta = c_pass[tid] - b_pass[tid]
    flag = '+' if delta > 0 else ('-' if delta < 0 else '=')
    print(f'  {tid}: base {b_pass[tid]:.2f} cand {c_pass[tid]:.2f} {flag}{abs(delta):.2f}')

# Save
out = {
    'method': 'Pillar A v2: 聚合 Qwen2.5-3B K=10 已有 raw submissions (T103-T132 跨 r20-r22)',
    'n_tasks': len(all_tids),
    'per_task': {tid: {'base': results['base'].get(tid, {}), 'cand': results['cand'].get(tid, {}), 'delta': c_pass.get(tid, 0) - b_pass.get(tid, 0)} for tid in all_tids},
    'summary': {
        'base': {tid: results['base'][tid] for tid in results['base']},
        'cand': {tid: results['cand'][tid] for tid in results['cand']},
    },
    'limitations': [
        '仅 Qwen2.5-3B 一个 base model (Llama 3.1 8B / Mistral 7B 未下载)',
        'T103-T122 跨 r20-r22 不同时段 raw, 但都用 K=10 多 seed',
        '无 ablation (-grounding) 实验, 因为历史 raw 是 prefix-on vs base-no-prefix',
    ],
    'next_step': '需要下载 Llama 3.1 8B + Mistral 7B 跑 ablation, 或者改用其他已下载的中型 base model',
}
out_p = root / 'pillar_a_qwen_aggregate.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')