import json
manifest = json.load(open(r'__WSE_REPO_ROOT__/assets/bench_manifest.json', encoding='utf-8'))
print('top-level keys:', list(manifest.keys()))
print('manifest type:', type(manifest).__name__)
print('first task type:', type(manifest['tasks'][0]).__name__)
print('first task:', repr(manifest['tasks'][0])[:200])