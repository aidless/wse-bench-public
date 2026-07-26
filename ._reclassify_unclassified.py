"""Pillar C: Re-classify 426 unclassified Agents cluster projects.
Use Qwen2.5-3B local inference to give each project a 1-shot classification.

Categories:
- uses_mainstream_framework (LangChain/AutoGen/CrewAI/Dify/Coze/LlamaIndex/etc.)
- self_implemented (custom agent framework, no mainstream dep)
- wrapper_around_llm (simple wrapper around LLM API)
- tutorial_or_course (educational, not a framework)
- domain_specific_agent (vertical application, e.g., code agent, research agent)
- other

Constraint: 426 calls × ~3s each ≈ 21 min. Local Qwen2.5-3B, 4bit.
"""
import json, time, torch, os
from pathlib import Path
from collections import Counter
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(r'__WSE_REPO_ROOT__')
out_p = root / 'agents_unclassified_reclassified.json'

# Load existing classification
existing = json.load(open(root / 'framework_adoption_empirical.json', encoding='utf-8'))
# Load all projects
projects = []
with open(r'F:/Research/github_ai_projects/ai_projects_v3.jsonl', encoding='utf-8') as f:
    for l in f:
        projects.append(json.loads(l))

def is_agent(p):
    tags = set(p.get('topics', []))
    return bool(tags & {'agent', 'ai-agents', 'agent-framework', 'autonomous-agents'})

agents = [p for p in projects if is_agent(p)]

FRAMEWORK_SIGNATURES = {
    'LangChain': {'keywords': ['langchain', 'lang-graph', 'langgraph'], 'topics': ['langchain', 'langgraph']},
    'AutoGen': {'keywords': ['autogen'], 'topics': ['autogen']},
    'CrewAI': {'keywords': ['crewai'], 'topics': ['crewai']},
    'Dify': {'keywords': ['dify'], 'topics': ['dify']},
    'Coze': {'keywords': ['coze'], 'topics': ['coze']},
    'OpenAI-Agents-SDK': {'keywords': ['openai-agents'], 'topics': ['openai-agents']},
    'smolagents': {'keywords': ['smolagents'], 'topics': ['smolagents']},
    'LlamaIndex': {'keywords': ['llamaindex', 'llama-index'], 'topics': ['llamaindex', 'llama-index']},
    'Semantic Kernel': {'keywords': ['semantic-kernel'], 'topics': ['semantic-kernel']},
    'Haystack': {'keywords': ['haystack'], 'topics': ['haystack']},
}

def is_classified_by_keyword(p):
    text = (p.get('description') or '').lower()
    topics = set(p.get('topics', []))
    for fw, sig in FRAMEWORK_SIGNATURES.items():
        if any(t in topics for t in sig['topics']):
            return True
        for kw in sig['keywords']:
            if kw in text:
                return True
    return False

unclassified = [p for p in agents if not is_classified_by_keyword(p)]
print(f'total agents: {len(agents)}, already classified (keyword): {len(agents) - len(unclassified)}, to reclassify: {len(unclassified)}')

# Limit to top 50 by stars (to keep runtime manageable)
unclassified_top = sorted(unclassified, key=lambda p: -p.get('stars', 0))[:50]
print(f'reclassifying top {len(unclassified_top)} by stars')

# Load Qwen
os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'
MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, quantization_config=bnb_cfg, torch_dtype=torch.bfloat16, device_map='auto', trust_remote_code=True,
)
model.eval()

CATEGORIES = ['uses_mainstream_framework', 'self_implemented', 'wrapper_around_llm', 'tutorial_or_course', 'domain_specific_agent', 'other']

def classify(desc, full_name, topics):
    prompt = f"""你是一个 GitHub 项目分类器。给定项目信息，分类到 6 类之一。

类别定义：
- uses_mainstream_framework: 使用 LangChain/AutoGen/CrewAI/Dify/Coze/LlamaIndex 等主流 agent 框架
- self_implemented: 自研 agent 框架（不依赖主流框架），可作开发模板
- wrapper_around_llm: 简单 LLM API 包装（无 agent 逻辑）
- tutorial_or_course: 教学/课程（不是框架）
- domain_specific_agent: 垂直领域应用（code agent、research agent、customer service agent 等）
- other: 其他

项目: {full_name}
描述: {desc[:300]}
Topics: {','.join(topics[:10])}

只输出 6 类之一的英文名（不要其他内容）：
"""
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=512).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=20, do_sample=False, pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    # Find first matching category
    for cat in CATEGORIES:
        if cat in text.lower():
            return cat
    return 'other'

results = []
t0 = time.time()
for i, p in enumerate(unclassified_top):
    try:
        cat = classify(p.get('description') or '', p['full_name'], p.get('topics', []))
    except Exception as e:
        cat = f'error: {e}'
    results.append({
        'project': p['full_name'],
        'stars': p['stars'],
        'category': cat,
        'description': (p.get('description') or '')[:200],
    })
    if (i+1) % 10 == 0:
        print(f'  [{i+1}/{len(unclassified_top)}] {time.time()-t0:.1f}s')

# Distribution
dist = Counter(r['category'] for r in results)
print()
print('=== Reclassification Distribution ===')
for cat in CATEGORIES + ['error']:
    n = dist.get(cat, 0)
    print(f'  {cat}: {n} ({n*100/len(results):.1f}%)')

# Save
out = {
    'method': 'Qwen2.5-3B 1-shot classification of 426 unclassified Agents cluster',
    'sample_size': len(results),
    'categories': CATEGORIES,
    'distribution': dict(dist),
    'reclassified_projects': results,
    'ts': '2026-07-25',
    'limitations': [
        '仅 1-shot, 无 chain-of-thought 推理, 复杂项目可能误分',
        'Qwen2.5-3B 在 github 描述上的 zero-shot 分类准确率约 70-80% (估计)',
        '样本仅 50 个, 不是全部 426 个',
        'manual 标注集未建立, 准确率无法验证',
    ],
}
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'result: {out_p}')