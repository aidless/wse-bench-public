import json,glob,os
root = r'__WSE_REPO_ROOT__'
for p in sorted(glob.glob(root + r'/submissions*.json')):
    if 'lora' in p.lower():
        continue
    d = json.load(open(p, encoding='utf-8'))
    keys = list(d.keys())
    n = 0
    for k,v in d.items():
        if k.endswith('_seeds') and isinstance(v,list):
            n += len(v)
    print(os.path.basename(p), 'keys=', keys[:6], 'K_seeds_total=', n)