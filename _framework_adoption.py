"""Empirical framework adoption analysis.
From AI Agent 报告 §11 + GitHub 1517 projects (cluster=Agents 342 个),
cross-classify frameworks and produce empirical adoption rates.
"""
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

root = Path(r'__WSE_REPO_ROOT__')
github_p = Path(r'F:/Research/github_ai_projects/ai_projects_v3.jsonl')
out_p = root / 'framework_adoption_empirical.json'

# Load projects
projects = []
with open(github_p, encoding='utf-8') as f:
    for l in f:
        projects.append(json.loads(l))

# Filter Agents cluster (topical: agent / ai-agents / agent-framework / autonomous-agents)
def is_agent(p):
    tags = set(p.get('topics', []))
    return bool(tags & {'agent', 'ai-agents', 'agent-framework', 'autonomous-agents'})

agents_projects = [p for p in projects if is_agent(p)]
print(f'total projects: {len(projects)}, agents cluster: {len(agents_projects)}')

# Framework signatures: keywords in description + topics
FRAMEWORK_SIGNATURES = {
    'LangChain': {
        'keywords': ['langchain', 'lang-graph', 'langgraph', 'lc-'],
        'topics': ['langchain', 'langgraph'],
    },
    'AutoGen': {
        'keywords': ['autogen', 'microsoft autogen', 'msr-autogen'],
        'topics': ['autogen'],
    },
    'CrewAI': {
        'keywords': ['crewai', 'crew-ai', 'crew ai'],
        'topics': ['crewai'],
    },
    'Dify': {
        'keywords': ['dify', 'dify-ai', 'difyai'],
        'topics': ['dify'],
    },
    'Coze': {
        'keywords': ['coze', 'cozeai', 'coze-bot'],
        'topics': ['coze'],
    },
    'OpenAI-Agents-SDK': {
        'keywords': ['openai-agents', 'openai agents sdk', 'openai-agents-python'],
        'topics': ['openai-agents'],
    },
    'smolagents': {
        'keywords': ['smolagents', 'smol-agent', 'huggingface smol'],
        'topics': ['smolagents'],
    },
    'LlamaIndex': {
        'keywords': ['llamaindex', 'llama-index', 'gpt-index'],
        'topics': ['llamaindex', 'llama-index'],
    },
    'Semantic Kernel': {
        'keywords': ['semantic-kernel', 'semantic kernel', 'sk-', 'microsoft/sk'],
        'topics': ['semantic-kernel'],
    },
    'Haystack': {
        'keywords': ['haystack', 'deepset-haystack'],
        'topics': ['haystack'],
    },
}


def classify_project(p):
    """Return list of frameworks this project uses (one or more)."""
    text = (p.get('description') or '').lower()
    topics = set(p.get('topics', []))
    matched = []
    for fw, sig in FRAMEWORK_SIGNATURES.items():
        # Check topics first (authoritative)
        if any(t in topics for t in sig['topics']):
            matched.append(fw)
            continue
        # Check description keywords
        for kw in sig['keywords']:
            if kw in text:
                matched.append(fw)
                break
    return matched


# Classify
classified = []
unclassified = 0
for p in agents_projects:
    fws = classify_project(p)
    if fws:
        classified.append({'project': p['full_name'], 'stars': p['stars'], 'language': p.get('language'), 'frameworks': fws, 'description': (p.get('description') or '')[:200]})
    else:
        unclassified += 1

print(f'agents classified: {len(classified)} ({len(classified)*100/len(agents_projects):.1f}%)')
print(f'agents unclassified: {unclassified}')

# Counts per framework
fw_counts = Counter()
fw_stars = defaultdict(int)
for c in classified:
    for fw in c['frameworks']:
        fw_counts[fw] += 1
        fw_stars[fw] += c['stars']

# Cross-tab: how many projects use exactly 1 / 2 / 3 / etc. frameworks
single_fw = sum(1 for c in classified if len(c['frameworks']) == 1)
multi_fw = sum(1 for c in classified if len(c['frameworks']) > 1)

# Top projects per framework
fw_top = defaultdict(list)
for c in classified:
    for fw in c['frameworks']:
        fw_top[fw].append({'name': c['project'], 'stars': c['stars']})

for fw, items in fw_top.items():
    items.sort(key=lambda x: -x['stars'])
    fw_top[fw] = items[:5]

# Save
result = {
    'analysis_ts': '2026-07-25',
    'data_source': 'ai_projects_v3.jsonl (1517 projects from GitHub Search API, 30 topics × 3 pages)',
    'cluster_filter': 'agent / ai-agents / agent-framework / autonomous-agents topics',
    'n_agents_cluster': len(agents_projects),
    'n_classified': len(classified),
    'n_unclassified': unclassified,
    'classification_rate': len(classified) / len(agents_projects),
    'n_single_framework': single_fw,
    'n_multi_framework': multi_fw,
    'framework_adoption_rates': {
        fw: {
            'count': fw_counts[fw],
            'pct_of_agents': fw_counts[fw] / len(agents_projects) * 100,
            'total_stars': fw_stars[fw],
            'mean_stars': fw_stars[fw] / fw_counts[fw] if fw_counts[fw] else 0,
            'top_5_by_stars': fw_top[fw],
        }
        for fw in sorted(fw_counts.keys(), key=lambda x: -fw_counts[x])
    },
    'empirical_vs_whitepaper_comparison': {
        'whitepaper_claim': '报告 §11 列 LangChain/LangGraph 为最大社区, AutoGen 学术影响, CrewAI API 简洁, Dify/Coze 低代码',
        'empirical_data': {fw: f"{fw_counts[fw]}/{len(agents_projects)} ({fw_counts[fw]/len(agents_projects)*100:.1f}%, 总星 {fw_stars[fw]:,})" for fw in fw_counts},
        'contradictions': [],
        'confirmations': [],
    },
    'limitations': [
        'GitHub Search API 在 30 topic × 3 page 后被限速 (HTTP 403), 实际全样本可能更大',
        'framework 分类基于 description + topics 关键词, 可能有 false positive (项目同时提到多个框架)',
        '本数据集不含 stars < 100 的小项目 (按 query 设了 stars:>50 或 >100 过滤)',
        '未区分 "uses framework as dependency" vs "is a framework", 单个 framework 项目可能误分类',
    ],
    'novel_findings': [],
}

# Detect contradictions/confirmations
fw_order = [fw for fw, _ in fw_counts.most_common()]
top_fw = fw_order[0] if fw_order else None
if top_fw == 'LangChain':
    result['empirical_vs_whitepaper_comparison']['confirmations'].append(f'LangChain 实证采用率最高 ({fw_counts[top_fw]} 项目), 与报告 §11 描述一致')
elif top_fw and top_fw != 'LangChain':
    result['empirical_vs_whitepaper_comparison']['contradictions'].append(f'报告称 LangChain 主导, 但实证 {top_fw} 居首 ({fw_counts[top_fw]} 项目)')

if fw_counts.get('LangChain', 0) < fw_counts.get('AutoGen', 0):
    result['empirical_vs_whitepaper_comparison']['contradictions'].append('AutoGen 采用率超过 LangChain — 与报告描述不符')
elif fw_counts.get('LangChain', 0) > fw_counts.get('AutoGen', 0) * 2:
    result['empirical_vs_whitepaper_comparison']['confirmations'].append('LangChain 采用率超过 AutoGen 2x+, 主导地位明显')

# Sort multi/single
result['framework_diversity'] = {
    'single_framework_only': single_fw,
    'multi_framework_uses': multi_fw,
    'multi_framework_pct': multi_fw / len(classified) if classified else 0,
}

# Save
out_p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'result: {out_p}')
print()
print('=== Framework Adoption Rates ===')
print(f'agents cluster total: {len(agents_projects)}')
for fw, cnt in fw_counts.most_common():
    pct = cnt / len(agents_projects) * 100
    print(f'  {fw:20s}: {cnt:4d} ({pct:5.1f}%) | total_stars={fw_stars[fw]:>10,} | top: {fw_top[fw][0]["name"] if fw_top[fw] else "-"} ({fw_top[fw][0]["stars"] if fw_top[fw] else 0}★)')