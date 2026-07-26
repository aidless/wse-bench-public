"""Fix: add hash field for new Q4-core tasks (and any task missing hash).
"""
import sys, json, hashlib
sys.path.insert(0, r'__WSE_REPO_ROOT__')
from eval_self_evolution import canon
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
manifest_p = root / 'assets' / 'bench_manifest.json'
manifest = json.load(open(manifest_p, encoding='utf-8'))

fixed = 0
for t in manifest['tasks']:
    expected_hash = hashlib.sha256(canon(t)).hexdigest()
    if t.get('hash') != expected_hash:
        # For new tasks (no hash yet), add it.
        # For existing tasks with mismatched hash (due to cohort_status change), update it.
        t['hash'] = expected_hash
        fixed += 1

print(f'fixed {fixed} tasks')
print('total tasks:', len(manifest['tasks']))

# Verify
bad = 0
for t in manifest['tasks']:
    if t.get('hash') != hashlib.sha256(canon(t)).hexdigest():
        bad += 1
print(f'still bad: {bad}')

with open(manifest_p, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('manifest saved')