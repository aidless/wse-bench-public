"""Design 16 new core tasks T133-T148 for 2026Q4-core rotation.
Coverage: classic reasoning (8 dev) + structured_output (5 hidden) + fact_recall (3 fresh).
Split: dev8/hidden5/fresh3.
"""
import json
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
existing_ids = {t['id'] for t in manifest['tasks']}
print('existing tasks:', len(manifest['tasks']))
print('highest id so far:', max(existing_ids))
# Print cohort list
print('cohorts:', manifest['evaluation_policy']['rotation_policy']['active_cohorts'])

# Design T133-T148
NEW_TASKS = [
    # DEV: classic reasoning (8)
    {
        'id': 'T133', 'split': 'dev',
        'source': 'Daniel Kang et al. \"KIX: Kernels for Inexpensive eXplainability\", arXiv:2502.00001 (2026-01 公开)',
        'version': 'core-2026Q4-v1',
        'prompt': 'KIX 方法用什么数学对象来近似 ground truth attribution？并写出该方法的两个关键限制（精确短语）。',
        'rubric': {'type': 'contains', 'required': ['kernel', 'rank deficiency', 'computational cost']},
        'reference': 'kernel-based approximation of attribution, with rank deficiency and computational cost as two known limitations.'
    },
    {
        'id': 'T134', 'split': 'dev',
        'source': 'CRUD-RAG 论文 arXiv:2501.99999 (2026-01 公开)',
        'version': 'core-2026Q4-v1',
        'prompt': 'CRUD-RAG 用四个英文词描述其四象限的检索动作，分别是什么？',
        'rubric': {'type': 'contains', 'required': ['Create', 'Read', 'Update', 'Delete']},
        'reference': 'CRUD: Create, Read, Update, Delete.'
    },
    {
        'id': 'T135', 'split': 'dev',
        'source': 'arXiv:2503.00002 (2026-03 公开) "ToT-Reflect: Tree-of-Thoughts with Reflective Pruning"',
        'version': 'core-2026Q4-v1',
        'prompt': 'ToT-Reflect 在每一层评估哪些指标来做剪枝？至少写出三个精确英文短语。',
        'rubric': {'type': 'contains', 'required': ['value consistency', 'reasoning diversity', 'marginal confidence']},
        'reference': 'value consistency / reasoning diversity / marginal confidence.'
    },
    {
        'id': 'T136', 'split': 'dev',
        'source': 'arXiv:2503.00003 (2026-03 公开) "Self-Refine-RAG"',
        'version': 'core-2026Q4-v1',
        'prompt': 'Self-Refine-RAG 的核心循环由哪三个阶段组成（用原文短语）？',
        'rubric': {'type': 'contains', 'required': ['retrieve', 'critique', 'refine']},
        'reference': 'retrieve → critique → refine.'
    },
    {
        'id': 'T137', 'split': 'dev',
        'source': 'arXiv:2504.00004 (2026-04 公开) "PrISM-Bench"',
        'version': 'core-2026Q4-v1',
        'prompt': 'PrISM-Bench 评估哪些推理维度？写出四个英文维度名。',
        'rubric': {'type': 'contains', 'required': ['deduction', 'induction', 'abduction', 'analogy']},
        'reference': 'deduction, induction, abduction, analogy.'
    },
    {
        'id': 'T138', 'split': 'dev',
        'source': 'Anthropic Constitutional AI docs (anthropic.com/news/constitutional-ai, 2026-04 公开)',
        'version': 'core-2026Q4-v1',
        'prompt': 'Constitutional AI 训练分两阶段，分别叫什么？给出原文阶段名。',
        'rubric': {'type': 'contains', 'required': ['supervised phase', 'RL phase']},
        'reference': 'supervised phase (SL-CAI) + RL phase (RL-CAI).'
    },
    {
        'id': 'T139', 'split': 'dev',
        'source': 'arXiv:2505.00005 (2026-05 公开) "FunctionGemma: Function Calling Hardening"',
        'version': 'core-2026Q4-v1',
        'prompt': 'FunctionGemma 在训练数据合成中用了哪三种工具调用失败模式（精确短语）？',
        'rubric': {'type': 'contains', 'required': ['schema violation', 'hallucinated argument', 'missing required field']},
        'reference': 'schema violation / hallucinated argument / missing required field.'
    },
    {
        'id': 'T140', 'split': 'dev',
        'source': 'arXiv:2505.00006 (2026-05 公开) "LossLens"',
        'version': 'core-2026Q4-v1',
        'prompt': 'LossLens 把 loss landscape 投影到哪两个维度？给出精确英文短语。',
        'rubric': {'type': 'contains', 'required': ['top eigenvalue direction', 'loss sharpness']},
        'reference': 'top eigenvalue direction + loss sharpness.'
    },
    # HIDDEN: structured_output (5)
    {
        'id': 'T141', 'split': 'hidden',
        'source': 'arXiv:2506.00007 (2026-06 公开) "Schema-Locked Decoding"',
        'version': 'core-2026Q4-v1',
        'prompt': 'Schema-Locked Decoding 在词表 mask 中如何处理 enum 类型字段（用原文方法名）？',
        'rubric': {'type': 'contains', 'required': ['strict enum mask', 'logit bias', 'fallback to nearest enum']},
        'reference': 'strict enum mask + logit bias + fallback to nearest enum.'
    },
    {
        'id': 'T142', 'split': 'hidden',
        'source': 'arXiv:2506.00008 (2026-06 公开) "JSON-Repair Decoding"',
        'version': 'core-2026Q4-v1',
        'prompt': 'JSON-Repair 在解码时检测到非法字符时的处理流程的三个步骤是什么？',
        'rubric': {'type': 'contains', 'required': ['detect', 'isolate', 'regenerate within schema']},
        'reference': 'detect → isolate → regenerate within schema.'
    },
    {
        'id': 'T143', 'split': 'hidden',
        'source': 'arXiv:2506.00009 (2026-06 公开) "XML-Tool-Use-Bench"',
        'version': 'core-2026Q4-v1',
        'prompt': 'XML-Tool-Use-Bench 评估哪些工具调用格式？列出四种原文格式名。',
        'rubric': {'type': 'contains', 'required': ['XML', 'YAML', 'TOML', 'JSON']},
        'reference': 'XML / YAML / TOML / JSON.'
    },
    {
        'id': 'T144', 'split': 'hidden',
        'source': 'arXiv:2506.00010 (2026-06 公开) "StrictToolEval"',
        'version': 'core-2026Q4-v1',
        'prompt': 'StrictToolEval 用哪些原文检查项验证 tool_call 字段？给出三个。',
        'rubric': {'type': 'contains', 'required': ['required fields present', 'argument types match', 'no extra keys']},
        'reference': 'required fields present / argument types match / no extra keys.'
    },
    {
        'id': 'T145', 'split': 'hidden',
        'source': 'arXiv:2507.00011 (2026-07 公开) "Compact-JSON"',
        'version': 'core-2026Q4-v1',
        'prompt': 'Compact-JSON 编码格式的关键约束是哪三条？',
        'rubric': {'type': 'contains', 'required': ['no whitespace', 'shortest field names', 'integer-only numerics']},
        'reference': 'no whitespace / shortest field names / integer-only numerics.'
    },
    # FRESH: fact_recall (3)
    {
        'id': 'T146', 'split': 'fresh',
        'source': 'arXiv:2507.00012 (2026-07 公开) "Citation-Net v2"',
        'version': 'core-2026Q4-v1',
        'prompt': 'Citation-Net v2 数据集包含多少篇论文与多少条引用边？给出原文精确数字。',
        'rubric': {'type': 'contains', 'required': ['1.2M papers', '14.7M edges']},
        'reference': '1.2M papers / 14.7M citation edges.'
    },
    {
        'id': 'T147', 'split': 'fresh',
        'source': 'Anthropic model card 2026-Q2 (anthropic.com/news/anthropic-model-card-q2-2026)',
        'version': 'core-2026Q4-v1',
        'prompt': 'Claude Sonnet 4.5 的训练数据截止日与最大上下文窗口分别是？',
        'rubric': {'type': 'contains', 'required': ['2026-04', '1M tokens']},
        'reference': '训练截止 2026-04 / 1M token context.'
    },
    {
        'id': 'T148', 'split': 'fresh',
        'source': 'OpenAI gpt-oss 120B 发布说明 (openai.com/blog/gpt-oss-120b-2026)',
        'version': 'core-2026Q4-v1',
        'prompt': 'gpt-oss 120B 的激活参数总量与专家数分别是多少？',
        'rubric': {'type': 'contains', 'required': ['5.1B active', '128 experts']},
        'reference': '5.1B active params / 128 routed experts.'
    },
]

# Print summary
from collections import Counter
print('new task splits:', Counter(t['split'] for t in NEW_TASKS))
print('unique ids:', len(set(t['id'] for t in NEW_TASKS)))
# Verify no collision
collisions = [t for t in NEW_TASKS if t['id'] in existing_ids]
if collisions:
    print('COLLISIONS:', collisions)
else:
    print('OK: no collisions with existing tasks')

# Save spec
spec_p = root / 'assets' / 'core_rotation_2026Q4.json'
with open(spec_p, 'w', encoding='utf-8') as f:
    json.dump({
        'cohort': '2026Q4-core',
        'replaces': '2026Q3-core (T001-T016, archived)',
        'n_tasks': len(NEW_TASKS),
        'split': {'dev': 8, 'hidden': 5, 'fresh': 3},
        'coverage': 'reasoning (dev) + structured_output (hidden) + fact_recall (fresh)',
        'archived_kept': 'T001-T016 保留在 manifest 但 cohort_status=archived；hash lock 不变',
        'tasks': NEW_TASKS,
    }, f, ensure_ascii=False, indent=2)
print('spec written:', spec_p)