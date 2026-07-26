import json
d = json.load(open(r'__WSE_REPO_ROOT__/submissions_fact_10seeds.json', encoding='utf-8'))
print('full keys:', list(d.keys()))
b = d['baseline_seeds'][0]
print('b first 3 tasks type and value:')
for tid in list(b.keys())[:3]:
    v = b[tid]
    print(tid, 'type', type(v).__name__, 'len', len(v) if hasattr(v, '__len__') else '-', 'sample', repr(v)[:80])
print('---')
# Look at full structure
print('b[T085] first 80 chars:', repr(b.get('T085', ''))[:80])
print('c[T085] first 80 chars:', repr(d['citation_check_seeds'][0].get('T085', ''))[:80])
# Are the same indices passing/failing?
# Find a task where they differ
for tid in b.keys():
    bv = b[tid]
    cv = d['citation_check_seeds'][0][tid]
    if bv != cv:
        print(f'task {tid} differs: baseline={repr(bv)[:80]} candidate={repr(cv)[:80]}')
        # count differences
        bp = sum(1 for c in bv if c == 'l')  # assume 'l' = lower-pass = ?
        cp = sum(1 for c in cv if c == 'l')
        print(f'   baseline pass count: {bp}/{len(bv)}; candidate pass count: {cp}/{len(cv)}')
        break