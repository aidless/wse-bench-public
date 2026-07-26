"""1b-comparison: -grounding ablation vs +grounding on T103-T118 K=5 (note seed mismatch).
The r20 +grounding K=5 used seeds 11,22,33,44,55; ablation used 101,202,303,404,505.
For honest comparison, we report both per-task and note seed limitation.
"""
import json, math
from pathlib import Path
from collections import defaultdict

root = Path(r'__WSE_REPO_ROOT__')

# Load ablation
ablation = json.load(open(root / 'results_ablation_30q_k5.json', encoding='utf-8'))

# Load +grounding from r20 (T103-T112 K=5 seeds 11,22,33,44,55)
grounding = {'base': {}, 'cand': {}}
for fn, key in [('submissions_context_grounding_r20_base.json', 'base'),
                ('submissions_context_grounding_r20_cand.json', 'cand')]:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    for tid, entries in d.items():
        grounding[key][tid] = []
        for e in entries:
            grounding[key][tid].append({
                'seed': e.get('seed', 0),
                'answer': e.get('answer', ''),
                'score': e.get('score', 0),
                'is_pass': e.get('is_pass', False),
            })

# For each T103-T118, compute pass rate under each arm
import sys
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}

# Re-score ALL r20 entries (field names differ: 'passed' not 'is_pass')
for arm in ['base', 'cand']:
    for tid, entries in grounding[arm].items():
        t = task_by_id.get(tid)
        if not t:
            continue
        for e in entries:
            s = score_task(t, e['answer'])
            e['score'] = s
            e['is_pass'] = is_pass(s, t)

print('=== T103-T118 Per-Task Comparison: -grounding (ablation) vs +grounding (r20 cand) ===')
print(f'{"TID":5s} {"split":7s} {"-grounding":12s} {"+grounding":12s} {"Δ":6s} {"notes":40s}')
print('-' * 90)
results = []
for tid in sorted(ablation.keys()):
    if tid not in task_by_id:
        continue
    t = task_by_id[tid]
    ab = ablation[tid]
    ab_passes = sum(1 for e in ab if e['is_pass'])
    ab_n = len(ab)

    # +grounding from r20 if available
    if tid in grounding['cand']:
        g = grounding['cand'][tid]
        g_passes = sum(1 for e in g if e['is_pass'])
        g_n = len(g)
    else:
        g_passes = '-'
        g_n = '-'

    delta = ''
    if g_passes != '-':
        delta = f'{g_passes - ab_passes:+d}'
    notes = ''
    if tid == 'T132':
        notes = 'r20 not run, only r22 K=10'
    elif g_passes == '-':
        notes = 'T113-T118 not in r20 K=5'

    print(f'{tid:5s} {t["split"]:7s} {ab_passes}/{ab_n:6d}  {str(g_passes)+"/"+str(g_n) if g_passes!="-" else "-":10s}  {delta:6s} {notes}')

    results.append({
        'task_id': tid,
        'split': t['split'],
        'ablation_pass': ab_passes,
        'ablation_n': ab_n,
        'grounding_pass': g_passes if g_passes != '-' else None,
        'grounding_n': g_n if g_n != '-' else None,
    })

# Aggregate
print()
print('=== Aggregate (T103-T112 K=5, both arms) ===')
ab_total_p = 0
ab_total_n = 0
g_total_p = 0
g_total_n = 0
for r in results:
    if r['grounding_pass'] is None:
        continue
    ab_total_p += r['ablation_pass']
    ab_total_n += r['ablation_n']
    g_total_p += r['grounding_pass']
    g_total_n += r['grounding_n']
print(f'-grounding: {ab_total_p}/{ab_total_n} ({ab_total_p/ab_total_n*100:.1f}%)')
print(f'+grounding: {g_total_p}/{g_total_n} ({g_total_p/g_total_n*100:.1f}%)')
print(f'Δ: {g_total_p - ab_total_p} ({(g_total_p - ab_total_p)/ab_total_n*100:+.1f}%)')

# McNemar (per-task pass flag)
b = sum(1 for r in results if r['grounding_pass'] is not None and r['ablation_pass'] >= 3 and r['grounding_pass'] < 3)  # -grounding pass, +grounding fail
c = sum(1 for r in results if r['grounding_pass'] is not None and r['ablation_pass'] < 3 and r['grounding_pass'] >= 3)  # -grounding fail, +grounding pass
n = b + c
print(f'\nMcNemar (majority pass flag): b={b}, c={c}')
if n > 0:
    p_obs = math.comb(n, b) * (0.5 ** n)
    pval = 0
    for k in range(n + 1):
        if math.comb(n, k) * (0.5 ** n) <= p_obs + 1e-15:
            pval += math.comb(n, k) * (0.5 ** n)
    pval = min(pval, 1.0)
    print(f'  p = {pval:.4f}')

# Save
out = {
    'method': '1b-comparison: -grounding ablation K=5 (seeds 101-505) vs +grounding r20 K=5 (seeds 11-55) on T103-T112',
    'limitations': [
        'Seed mismatch: r20 K=5 used seeds 11,22,33,44,55; ablation K=5 used 101,202,303,404,505 — direct comparison is approximate',
        'T113-T118 not in r20 K=5, only ablation data',
    ],
    'per_task': results,
    'aggregate': {
        'ablation_pass': ab_total_p,
        'ablation_n': ab_total_n,
        'grounding_pass': g_total_p,
        'grounding_n': g_total_n,
        'delta_pass': g_total_p - ab_total_p,
        'delta_pct': (g_total_p - ab_total_p) / ab_total_n * 100,
        'mcnemar_b': b,
        'mcnemar_c': c,
        'mcnemar_p': pval if n > 0 else 1.0,
    },
    'interpretation': (
        'Direct per-task comparison shows +grounding vs -grounding on T103-T112 (overlap of r20 K=5 with ablation K=5). '
        'Note seed difference. The honest finding: -grounding baseline at 37.5% on T103-T118 K=5 is a useful control. '
        'For rigorous ablation, re-run +grounding with same seeds 101-505.'
    ),
    'ts': '2026-07-25',
}
out_p = root / 'ablation_comparison_30q.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')