"""STRATEGY_AUDIT_V4: context_grounding_v1 marginal contribution test.

Per SKILL.md v15 protocol: A_minus = reference - target_strategy, reference = production 7-strategy.
Honest limitation: we don't have full 7-strategy stack on RC cohort. So we report:

1) Simplified V4: A_minus (baseline, no strategies) vs A_full (baseline + context_grounding only)
   on reading_comprehension 30题 K=10 from r25 aggregation.
2) Compare Δ to v3 audit's NECESSARY 阈值 (Δ < -0.05 noise floor)

This is "necessity test in isolation" not "marginal contribution in 7-strategy stack".
The full V4 marginal test would need 7-strategy vs 6-strategy run (separate experiment).
"""
import json, math
from pathlib import Path
from collections import Counter, defaultdict

root = Path(r'__WSE_REPO_ROOT__')
sys_path = str(root)
import sys
sys.path.insert(0, sys_path)
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}

# Reading comprehension cohort (T091-T132 minus dev splits that may be in training)
RC_IDS = ['T091','T092','T093','T094','T095','T096', # RC
          'T103','T104','T105','T106','T107','T108', # RC2
          'T109','T110','T111','T112','T113','T114','T115','T116','T117','T118', # RC3
          'T123','T124','T125','T126','T127','T128','T129','T130','T131','T132'] # RC4

# Load all r20+r21+r22 raw data
def load_submissions(file_patterns):
    """Returns {tid: {arm: [entries]}} where arm is 'base' or 'cand'."""
    data = {}
    for fn, arm in file_patterns:
        p = root / fn
        if not p.exists():
            continue
        d = json.load(open(p, encoding='utf-8'))
        for tid, entries in d.items():
            data.setdefault(tid, {'base': [], 'cand': []})[arm].extend(entries)
    return data

subs = load_submissions([
    ('submissions_context_grounding_r20_base.json', 'base'),
    ('submissions_context_grounding_r20_cand.json', 'cand'),
    ('submissions_context_grounding_r21_base_k10.json', 'base'),
    ('submissions_context_grounding_r21_cand_k10.json', 'cand'),
    ('submissions_context_grounding_r22_base_rc4_k10.json', 'base'),
    ('submissions_context_grounding_r22_cand_rc4_k10.json', 'cand'),
])

# Compute pass rate per task per arm
results = {'base': {}, 'cand': {}}
for arm in ['base', 'cand']:
    for tid in RC_IDS:
        entries = subs.get(tid, {}).get(arm, [])
        if not entries:
            continue
        t = task_by_id.get(tid)
        if not t:
            continue
        n = len(entries)
        # Re-score if no is_pass field
        for e in entries:
            if 'is_pass' not in e:
                s = score_task(t, e['answer'])
                e['is_pass'] = is_pass(s, t)
                e['score'] = s
            elif 'passed' in e and 'is_pass' not in e:
                e['is_pass'] = e['passed']
        passes = sum(1 for e in entries if e.get('is_pass'))
        results[arm][tid] = {
            'n': n,
            'pass': passes,
            'pass_rate': passes / n,
        }

# A_minus = baseline (no context_grounding, no other strategies on RC cohort)
# A_full = production (with context_grounding only on RC cohort)
print('=== STRATEGY_AUDIT_V4 (simplified): context_grounding_v1 marginal on RC cohort ===')
print()
per_task = []
for tid in sorted(set(results['base'].keys()) | set(results['cand'].keys())):
    bd = results['base'].get(tid, {'n': 0, 'pass': 0, 'pass_rate': 0})
    cd = results['cand'].get(tid, {'n': 0, 'pass': 0, 'pass_rate': 0})
    delta = cd['pass_rate'] - bd['pass_rate']
    t = task_by_id[tid]
    per_task.append({
        'task_id': tid,
        'split': t.get('split', ''),
        'base_n': bd['n'],
        'base_pass': bd['pass'],
        'base_rate': bd['pass_rate'],
        'cand_n': cd['n'],
        'cand_pass': cd['pass'],
        'cand_rate': cd['pass_rate'],
        'delta': delta,
    })
    flag = '+' if delta > 0 else ('-' if delta < 0 else '=')
    print(f'  {tid} ({t["split"]:6s}): base {bd["pass"]:>3d}/{bd["n"]:<3d} ({bd["pass_rate"]*100:4.0f}%) cand {cd["pass"]:>3d}/{cd["n"]:<3d} ({cd["pass_rate"]*100:4.0f}%) {flag}{abs(delta)*100:4.0f}%')

# Aggregate
base_n = sum(p['base_n'] for p in per_task)
base_p = sum(p['base_pass'] for p in per_task)
cand_n = sum(p['cand_n'] for p in per_task)
cand_p = sum(p['cand_pass'] for p in per_task)
delta_overall = (cand_p - base_p) / base_n
print()
print(f'Base: {base_p}/{base_n} ({base_p/base_n*100:.1f}%)')
print(f'Cand: {cand_p}/{cand_n} ({cand_p/cand_n*100:.1f}%)')
print(f'Δ overall: {delta_overall*100:+.1f}%')

# Per-split
print()
print('=== Per-split ===')
for split in ['dev', 'hidden', 'fresh']:
    bp = sum(p['base_pass'] for p in per_task if p['split'] == split)
    bn = sum(p['base_n'] for p in per_task if p['split'] == split)
    cp = sum(p['cand_pass'] for p in per_task if p['split'] == split)
    cn = sum(p['cand_n'] for p in per_task if p['split'] == split)
    if bn and cn:
        print(f'  {split}: base {bp}/{bn} ({bp/bn*100:.1f}%) cand {cp}/{cn} ({cp/cn*100:.1f}%) Δ {(cp-bp)/bn*100:+.1f}%')

# McNemar
b = sum(1 for p in per_task if p['base_rate'] >= 0.5 and p['cand_rate'] < 0.5)
c = sum(1 for p in per_task if p['base_rate'] < 0.5 and p['cand_rate'] >= 0.5)
n = b + c
print(f'\nMcNemar: b={b}, c={c}, n={n}')
if n > 0:
    p_obs = math.comb(n, b) * (0.5 ** n)
    pval = 0
    for k in range(n + 1):
        if math.comb(n, k) * (0.5 ** n) <= p_obs + 1e-15:
            pval += math.comb(n, k) * (0.5 ** n)
    pval = min(pval, 1.0)
    print(f'  p = {pval:.4f}')

# Decision per V4 protocol
# A_minus_full = baseline pass_rate (per_task average)
A_minus_full = base_p / base_n
# reference pass_rate
A_full = cand_p / cand_n
delta_minus_full = A_minus_full - A_full  # if < -0.05 → NECESSARY
print()
print(f'A_minus (baseline): {A_minus_full*100:.1f}%')
print(f'reference (with cg): {A_full*100:.1f}%')
print(f'Δ_minus_full = {delta_minus_full*100:+.1f}%')
if delta_minus_full < -0.05:
    verdict = 'NECESSARY'
else:
    verdict = 'AMBIGUOUS (Δ<0.05 noise floor)'
print(f'V4 simplified verdict for context_grounding_v1 on RC cohort: {verdict}')

# Save
out = {
    'method': 'STRATEGY_AUDIT_V4 simplified: context_grounding_v1 marginal contribution',
    'cohort': 'reading_comprehension (T091-T132, 30题)',
    'method_detail': 'A_minus = baseline K=5/K=10 (no prefix); reference = with context_grounding prefix',
    'per_task': per_task,
    'aggregate': {
        'base_pass': base_p,
        'base_n': base_n,
        'base_rate': A_minus_full,
        'cand_pass': cand_p,
        'cand_n': cand_n,
        'cand_rate': A_full,
        'delta_overall': delta_overall,
        'delta_minus_full': delta_minus_full,
        'mcnemar_b': b,
        'mcnemar_c': c,
        'mcnemar_p': pval if n > 0 else 1.0,
    },
    'verdict': verdict,
    'limitations': [
        'V4 simplified: not full 7-strategy stack vs 6-strategy stack without cg; only isolated contribution test',
        'K-inconsistency: K=5 (r20) + K=10 (r21/r22) mixed',
        'reading_comprehension cohort only — context_grounding not tested on other cohorts',
        'Per V3 audit framework: NECESSARY = Δ_minus_full < -0.05 (5x noise floor)',
    ],
    'next_step': 'Full V4 marginal: 7-strategy stack vs 6-strategy stack on RC cohort (need fresh 6-strategy run; not yet available)',
    'ts': '2026-07-25',
}
out_p = root / 'strategy_audit_v4.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')