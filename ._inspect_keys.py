import json
d = json.load(open(r'__WSE_REPO_ROOT__/submissions_fact_10seeds.json', encoding='utf-8'))
print('keys per seed:')
b = d['baseline_seeds'][0]
print('first 6 tasks:')
for tid in list(b.keys())[:6]:
    v = b[tid]
    print(tid, 'type', type(v).__name__, 'len', len(v), 'first 100:', repr(v)[:100])
print()
# How does eval score these?
# Look at eval_self_evolution.py for the scoring logic
import subprocess
r = subprocess.run(['grep', '-n', 'is_pass', '__WSE_REPO_ROOT__/eval_self_evolution.py'], capture_output=True, text=True)
print('grep is_pass:', r.stdout[:2000])