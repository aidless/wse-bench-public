"""audit sensitive residue before open-sourcing"""
import re, sys
from pathlib import Path

# regex compiled independently, all backslashes doubled in source string
PATTERNS = [
    (r'E:\\peS2o_kb_faiss', 'private KB path'),
    (r'541,733', 'private number'),
    (r'541,713', 'private number'),
    (r'刘泽文', 'real name'),
    (r'齐鲁', 'school prefix'),
    (r'枣庄', 'school city'),
    (r'泰玄小站', 'private project'),
    (r'泰玄', 'private project'),
    (r'116\.62\.69\.83', 'server ip'),
    (r'wanxiangapp', 'private domain'),
    (r'2038796100751', 'private ICP order'),
    (r'163\.com|qq\.com', 'private email domain'),
    (r'47\.98\.106\.182', 'private server ip'),
]
EXTS = ('.py', '.md', '.json', '.sh', '.log', '.txt')
hits = {}
for f in Path('.').iterdir():
    if f.suffix not in EXTS: continue
    if not f.is_file(): continue
    try: s = f.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    for pat, label in PATTERNS:
        m = re.findall(pat, s)
        if m:
            hits.setdefault(label, []).append((f.name, len(m)))
for label, files in hits.items():
    print(f'{label}: {len(files)} file(s)')
    for fn, n in files[:5]: print(f'   {fn} ({n})')
    if len(files) > 5: print(f'   ... and {len(files)-5} more')
print(f'\nTOTAL patterns with hits: {len(hits)}')
sys.exit(0 if not hits else 1)