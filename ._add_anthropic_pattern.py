"""Pillar E: Anthropic 5 patterns refactor of 7-strategy stack.
Add anthropic_pattern field to each promoted strategy.

Reference: report §11 - Workflows vs Agents (Anthropic 2024).
5 patterns: Prompt Chaining, Routing, Parallelization, Orchestrator-workers, Evaluator-optimizer
"""
import json
from pathlib import Path
from datetime import datetime

root = Path(r'__WSE_REPO_ROOT__')
reg_p = root / 'assets' / 'strategy_registry.json'
reg = json.loads(reg_p.read_text(encoding='utf-8'))

# Anthropic 5 patterns mapping (based on AI Agent report §11 + Anthropic 2024 Building Effective Agents)
PATTERN_MAP = {
    'selective_retrieval_v1': {
        'anthropic_pattern': 'Routing',
        'reasoning': '按"领域(私有/本地/新鲜)"路由——通用知识走参数记忆,事实型路由检索。Routing 模式 = 决策 + 分流。',
    },
    'citation_check_v1': {
        'anthropic_pattern': 'Routing',
        'reasoning': '按"置信度阈值"路由——高把握直答,低置信触发检索。与 selective_retrieval 互补: 后者按领域,本策略按置信度。',
    },
    'tool_arith_v1': {
        'anthropic_pattern': 'Orchestrator-workers',
        'reasoning': '主 LM 编排,worker = python 脚本执行多步算术。Orchestrator-workers 模式 = 中央调度 + 多个并行 worker。',
    },
    'schema_guard_v1': {
        'anthropic_pattern': 'Prompt Chaining',
        'reasoning': '输入→结构化核验→输出(若不合规修正)→emit。Prompt Chaining 模式 = 多步确定性处理链。',
    },
    'self_verify_v1': {
        'anthropic_pattern': 'Evaluator-optimizer',
        'reasoning': '生成→自检→不一致重解。Evaluator-optimizer 模式 = 生成器 + 评估器 + 优化循环。',
    },
    'verifier_v1': {
        'anthropic_pattern': 'Evaluator-optimizer',
        'reasoning': 'emit 前 rubric-aware 跨 rubric 验证(比 self_verify 更通用)。是 Evaluator-optimizer 模式的 emit 端优化器。',
    },
    'context_grounding_v1': {
        'anthropic_pattern': 'Prompt Chaining',
        'reasoning': '输入→先定位源 span→逐字引用原话→emit。Prompt Chaining 模式 = 多步 grounding 强制链。',
    },
}

for s in reg['strategies']:
    if s['id'] in PATTERN_MAP:
        s['anthropic_pattern'] = PATTERN_MAP[s['id']]['anthropic_pattern']
        # Append pattern reasoning to note (avoid duplicating)
        if 'anthropic_pattern_reasoning' not in s.get('note', ''):
            s['note'] = s.get('note', '') + f" | 5模式归类(r25 #{s['id'][:4]}): {PATTERN_MAP[s['id']]['anthropic_pattern']} — {PATTERN_MAP[s['id']]['reasoning']}"

# Add pattern coverage table
from collections import Counter
pattern_coverage = Counter()
for s in reg['strategies']:
    if s.get('anthropic_pattern'):
        pattern_coverage[s['anthropic_pattern']] += 1

reg['anthropic_5_patterns_v25'] = {
    'patterns': ['Prompt Chaining', 'Routing', 'Parallelization', 'Orchestrator-workers', 'Evaluator-optimizer'],
    'mapping': {s['id']: s.get('anthropic_pattern') for s in reg['strategies']},
    'coverage': dict(pattern_coverage),
    'gaps': [p for p in ['Prompt Chaining', 'Routing', 'Parallelization', 'Orchestrator-workers', 'Evaluator-optimizer'] if p not in pattern_coverage],
    'note': '5 模式中 7 策略覆盖 3 模式(Routing 2, Orchestrator-workers 1, Evaluator-optimizer 2, Prompt Chaining 2);Parallelization 0 覆盖 — 下一步可设计 parallel_synthesis_v1 把多策略结果并联后聚合(majority vote / rank aggregation)。',
    'ts': datetime.now().isoformat(timespec='seconds'),
}

reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding='utf-8')
print('anthropic_pattern fields added to', len(PATTERN_MAP), 'strategies')
print('pattern coverage:', dict(pattern_coverage))
print('gaps:', reg['anthropic_5_patterns_v25']['gaps'])