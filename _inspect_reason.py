import json
d = json.load(open(r'__WSE_REPO_ROOT__/submissions_reason_10seeds.json', encoding='utf-8'))
print('keys:', list(d.keys()))
for k, v in d.items():
    if k.endswith('_seeds'):
        print(k, 'K=', len(v))
        if v and isinstance(v[0], dict):
            # show first task's first seed
            first_tid = list(v[0].keys())[0]
            print('  first task:', first_tid, 'first seed:', list(v[0][first_tid][0].keys()) if v[0][first_tid] else 'empty')
    elif k == 'task_ids':
        print(k, 'first 6:', v[:6], 'len', len(v))