import json
for fn in ['submissions_fact_10seeds.json', 'submissions_hard_15seeds.json', 'submissions_struct_10seeds.json', 'submissions_sv_10seeds.json', 'submissions_verify_10seeds_v3.json', 'submissions_rc_10seeds.json']:
    p = f'__WSE_REPO_ROOT__/{fn}'
    d = json.load(open(p, encoding='utf-8'))
    print(fn, 'cohort', d.get('cohort'), 'task_ids', len(d.get('task_ids', [])))
    for k in d:
        if k.endswith('_seeds'):
            sample = d[k][0] if d[k] else None
            print(' ', k, 'K=', len(d[k]), 'sample_keys', list(sample.keys()) if isinstance(sample, dict) else type(sample).__name__)