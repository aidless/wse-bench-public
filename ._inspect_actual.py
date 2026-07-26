import json
p = r'__WSE_REPO_ROOT__/submissions_context_grounding_r20_base.json'
d = json.load(open(p, encoding='utf-8'))
print('keys:', list(d.keys())[:3])
# T103
tid = 'T103'
v = d.get(tid)
print(f'{tid}: type {type(v).__name__}, sample {repr(v)[:300] if v else None}')