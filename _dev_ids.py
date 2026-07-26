import json
m = json.load(open(r'__WSE_REPO_ROOT__/assets/bench_manifest.json', encoding='utf-8'))
dev_ids = [t['id'] for t in m['tasks'] if t.get('split') == 'dev']
print('dev tasks', len(dev_ids), dev_ids)
print('all tasks', len(m['tasks']))
print('cohorts', m['evaluation_policy']['rotation_policy']['active_cohorts'])