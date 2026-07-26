import json
d = json.load(open(r'__WSE_REPO_ROOT__/submissions_fact_10seeds.json', encoding='utf-8'))
b = d['baseline_seeds'][0]
tid = list(b.keys())[0]
v = b[tid]
print('task', tid, 'type', type(v), 'len', len(v) if hasattr(v, '__len__') else 'n/a')
print('first elem:', repr(v[0])[:300])
if len(v) > 1:
    print('second elem:', repr(v[1])[:300])