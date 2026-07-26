"""Pillar A v3: Aggregate existing Qwen2.5-3B K=10 data for T103-T132, re-scoring each entry."""
import json, sys
from pathlib import Path
from collections import Counter, defaultdict

root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}

# Load raw submissions
files = [
    ('submissions_context_grounding_r20_base.json', 'base'),
    ('submissions_context_grounding_r20_cand.json', 'cand'),
    ('submissions_context_grounding_r21_base_k10.json', 'base'),
    ('submissions_context_grounding_r21_cand_k10.json', 'cand'),
    ('submissions_context_grounding_r22_base_rc4_k10.json', 'base'),
    ('submissions_context_grounding_r22_cand_rc4_k10.json', 'cand'),
]

# Aggregate: per task, per arm, list of entries {seed, answer, score, is_pass}
all_data = {'base': defaultdict(list), 'cand': defaultdict(list)}

for fn, arm in files:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for tid, entries in d.items():
        t = task_by_id.get(tid)
        if not t:
            continue
        for e in entries:
            ans = e.get('answer', '')
            s = score_task(t, ans)
            all_data[arm][tid].append({
                'seed': e.get('seed', 0),
                'score': s,
                'is_pass': is_pass(s, t),
                'split': t.get('split'),
            })

# Per-task pass rate
results = {'base': {}, 'cand': {}}
for arm in ['base', 'cand']:
    for tid, entries in all_data[arm].items():
        n = len(entries)
        pass_count = sum(1 for e in entries if e['is_pass'])
        results[arm][tid] = {
            'n': n,
            'pass': pass_count,
            'pass_rate': pass_count / n if n else 0,
            'split': entries[0]['split'],
            'mean_score': sum(e['score'] for e in entries) / n,
        }

# Summary
print('=== Aggregated Qwen2.5-3B K=10 on T103-T132 (30题) ===')
for arm in ['base', 'cand']:
    tids = list(results[arm].keys())
    n_total = sum(results[arm][t]['n'] for t in tids)
    pass_total = sum(results[arm][t]['pass'] for t in tids)
    by_split = defaultdict(lambda: {'n': 0, 'pass': 0, 'mean_score_sum': 0, 'n_seeds': 0})
    for tid, d in results[arm].items():
        by_split[d['split']]['n'] += 1
        by_split[d['split']]['pass'] += d['pass']
        by_split[d['split']]['mean_score_sum'] += d['mean_score'] * d['n']
        by_split[d['split']]['n_seeds'] += d['n']
    print(f'\n{arm}: {pass_total}/{n_total} ({pass_total/n_total*100:.1f}%)')
    for sp, sd in by_split.items():
        if sd['n_seeds']:
            print(f'  {sp}: {sd["pass"]}/{sd["n_seeds"]} ({sd["pass"]/sd["n_seeds"]*100:.1f}%, mean score {sd["mean_score_sum"]/sd["n_seeds"]:.3f})')

# Per-task comparison
print('\n=== Per-task comparison (T103-T132) ===')
all_tids = sorted(set(results['base'].keys()) & set(results['cand'].keys()))
for tid in all_tids:
    bd = results['base'][tid]
    cd = results['cand'][tid]
    delta_rate = cd['pass_rate'] - bd['pass_rate']
    delta_mean = cd['mean_score'] - bd['mean_score']
    flag = '+' if delta_rate > 0 else ('-' if delta_rate < 0 else '=')
    print(f'  {tid} ({bd["split"]:6s}): base {bd["pass"]}/{bd["n"]} ({bd["pass_rate"]*100:4.0f}%) cand {cd["pass"]}/{cd["n"]} ({cd["pass_rate"]*100:4.0f}%) pass Δ {flag}{abs(delta_rate)*100:4.0f}%, mean Δ {delta_mean:+.3f}')

# Save
out = {
    'method': 'Pillar A v3: 聚合 Qwen2.5-3B K=10 已有 raw submissions (T103-T132 30题, r20-r22 跨时段)',
    'n_tasks': len(all_tids),
    'per_task': {tid: {'base': results['base'][tid], 'cand': results['cand'][tid]} for tid in all_tids},
    'summary_by_split': {},
    'limitations': [
        '仅 Qwen2.5-3B 一个 base model',
        'T103-T122 含 r20 (K=5) + r21 (K=10) + r22 (RC4 K=10) 跨不同时段',
        'K 不统一 (T103-T112 主要是 K=5 或 K=10; T123-T132 全部 K=10)',
    ],
}
for arm in ['base', 'cand']:
    by_split = defaultdict(lambda: {'n_tasks': 0, 'pass': 0, 'n_seeds': 0})
    for tid, d in results[arm].items():
        by_split[d['split']]['n_tasks'] += 1
        by_split[d['split']]['pass'] += d['pass']
        by_split[d['split']]['n_seeds'] += d['n']
    out['summary_by_split'][arm] = {sp: dict(sd) for sp, sd in by_split.items()}

out_p = root / 'pillar_a_qwen_aggregate_v3.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')