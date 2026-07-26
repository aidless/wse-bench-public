"""GitHub API 1000 AI/ML/agentic projects scan.
Strategy: Use GitHub Search API (public, no auth for low rate) with topic filters,
multiple query variants, deduplication by full_name.

Topics: llm, agent, rag, fine-tuning, multimodal, reasoning, code-generation, evals,
inference, vector-db, embedding, prompt-engineering, ai-agents, agent-framework,
deep-learning, transformer, diffusion, speech, robotics, etc.

Constraint: ≥100 stars per project to filter quality.
"""
import json, time, urllib.request, urllib.parse, os
from pathlib import Path

OUT_DIR = Path(r'F:/Research/github_ai_projects')
OUT_DIR.mkdir(parents=True, exist_ok=True)

QUERIES = [
    'topic:llm stars:>200',
    'topic:agent stars:>200',
    'topic:rag stars:>150',
    'topic:fine-tuning stars:>100',
    'topic:multimodal stars:>100',
    'topic:reasoning stars:>100',
    'topic:code-generation stars:>100',
    'topic:evals stars:>50',
    'topic:inference stars:>100',
    'topic:vector-db stars:>100',
    'topic:embedding stars:>50',
    'topic:prompt-engineering stars:>50',
    'topic:ai-agents stars:>200',
    'topic:agent-framework stars:>100',
    'topic:transformer stars:>200',
    'topic:diffusion stars:>200',
    'topic:speech stars:>100',
    'topic:robotics stars:>200',
    'topic:machine-learning stars:>500',
    'topic:deep-learning stars:>500',
    'topic:llm-inference stars:>100',
    'topic:llm-agent stars:>100',
    'topic:large-language-models stars:>200',
    'topic:llm-evaluation stars:>50',
    'topic:openai stars:>200',
    'topic:huggingface stars:>100',
    'topic:pytorch stars:>1000',
    'topic:jax stars:>100',
    'topic:mlops stars:>200',
    'topic:ml-platform stars:>50',
]

BASE = 'https://api.github.com/search/repositories'

def search(q, page=1, per_page=100):
    params = {'q': q, 'sort': 'stars', 'order': 'desc', 'per_page': per_page, 'page': page}
    url = BASE + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'workbuddy-github-scan-1000',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'  err {q[:40]} page {page}: {e}')
        return None


seen = {}
err_count = 0
total_pages = 0

for q in QUERIES:
    print(f'== {q} ==')
    for page in range(1, 4):  # up to 300 per query
        total_pages += 1
        r = search(q, page=page, per_page=100)
        if r is None:
            err_count += 1
            if err_count > 5:
                print('too many errors, stopping')
                break
            time.sleep(3)
            continue
        items = r.get('items', [])
        if not items:
            break
        for it in items:
            fn = it.get('full_name')
            if not fn or fn in seen:
                continue
            seen[fn] = {
                'full_name': fn,
                'html_url': it.get('html_url'),
                'description': (it.get('description') or '')[:300],
                'stars': it.get('stargazers_count', 0),
                'language': it.get('language'),
                'topics': it.get('topics', []),
                'updated_at': it.get('updated_at'),
                'created_at': it.get('created_at'),
                'license': (it.get('license') or {}).get('spdx_id'),
                'archived': it.get('archived', False),
                'source_query': q,
            }
        if len(items) < 100:
            break
        time.sleep(1.5)
    print(f'  cumulative: {len(seen)}')

print(f'\ntotal queries: {len(QUERIES)}')
print(f'total pages fetched: {total_pages}')
print(f'unique projects: {len(seen)}')
print(f'errors: {err_count}')

# Sort by stars desc
items = sorted(seen.values(), key=lambda x: -x['stars'])

# Write v3
out_p = OUT_DIR / 'ai_projects_v3.jsonl'
with open(out_p, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')
print(f'written: {out_p} (n={len(items)})')