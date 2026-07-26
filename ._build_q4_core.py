"""Build 144题 manifest: 128 (Q3) + 16 new Q4-core.
Mark T001-T016 as cohort_status=archived but keep them.
Add 2026Q4-core to active cohorts.
"""
import json
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
spec = json.load(open(root / 'assets' / 'core_rotation_2026Q4.json', encoding='utf-8'))

# Add new tasks
existing_ids = {t['id'] for t in manifest['tasks']}
for nt in spec['tasks']:
    assert nt['id'] not in existing_ids, f'collision {nt["id"]}'
    nt['cohort'] = '2026Q4-core'
    nt['cohort_status'] = 'active'
    nt['capability'] = {
        'T133': 'reasoning', 'T134': 'reasoning', 'T135': 'reasoning', 'T136': 'reasoning',
        'T137': 'reasoning', 'T138': 'reasoning', 'T139': 'reasoning', 'T140': 'reasoning',
        'T141': 'structured_output', 'T142': 'structured_output', 'T143': 'structured_output',
        'T144': 'structured_output', 'T145': 'structured_output',
        'T146': 'fact_recall', 'T147': 'fact_recall', 'T148': 'fact_recall',
    }.get(nt['id'], 'reasoning')
    manifest['tasks'].append(nt)

# Archive T001-T016 (Q3-core)
archived_ids = set()
for t in manifest['tasks']:
    if t['id'] in {'T001','T002','T003','T004','T005','T006','T011','T012','T013','T015'}:
        t['cohort_status'] = 'archived'
        archived_ids.add(t['id'])
# (T007-T010, T014, T016 are also core? Let me check)
# Actually T001-T016 are the core cohort per the v96 manifest.
for t in manifest['tasks']:
    if t.get('cohort') == '2026Q3-core' and t['id'].startswith('T0'):
        t['cohort_status'] = 'archived'
        archived_ids.add(t['id'])

print('archived Q3-core tasks:', sorted(archived_ids))

# Add Q4-core to active cohorts
cohorts = manifest['evaluation_policy']['rotation_policy']['active_cohorts']
if '2026Q4-core' not in cohorts:
    cohorts.append('2026Q4-core')
# Add Q3-core to archived list (for reference)
rotation = manifest['evaluation_policy']['rotation_policy']
rotation.setdefault('archived_cohorts', [])
if '2026Q3-core' not in rotation['archived_cohorts']:
    rotation['archived_cohorts'].append('2026Q3-core')

# Bump metadata
manifest['evaluation_policy']['n_tasks_total'] = len(manifest['tasks'])
manifest['evaluation_policy']['splits'] = {
    s: sum(1 for t in manifest['tasks'] if t.get('split') == s)
    for s in ['dev', 'hidden', 'fresh']
}
manifest['evaluation_policy']['capabilities'] = sorted({t.get('capability') for t in manifest['tasks'] if t.get('capability')})

print('manifest tasks:', len(manifest['tasks']))
print('splits:', manifest['evaluation_policy']['splits'])
print('active cohorts:', cohorts)

out_p = root / 'assets' / 'bench_manifest.json'
with open(out_p, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('manifest written:', out_p)