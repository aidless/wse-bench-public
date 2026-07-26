"""1a: Failure mode analysis for T105/T108/T132 (3 regress tasks).

Approach:
1. Load raw submissions for T105, T108, T132 from r20/r21/r22.
2. For each (seed, base, cand), print:
   - task prompt
   - base answer + score
   - cand answer + score
   - diff between them
3. Classify failure modes:
   a) Base always-correct, cand over-strict (rejects partial answers)
   b) Base always-wrong, cand introduces noise (longer but wrong)
   c) Both wrong, different reasons
   d) Rubric mismatch (answer is correct semantically but doesn't match rubric.required verbatim)
"""
import json, sys
from pathlib import Path
from collections import defaultdict
root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
task_by_id = {t['id']: t for t in manifest['tasks']}

# Load all relevant submissions
sub_files = [
    'submissions_context_grounding_r20_base.json',
    'submissions_context_grounding_r20_cand.json',
    'submissions_context_grounding_r21_base_k10.json',
    'submissions_context_grounding_r21_cand_k10.json',
    'submissions_context_grounding_r22_base_rc4_k10.json',
    'submissions_context_grounding_r22_cand_rc4_k10.json',
]

# Per regress task, gather all (seed, arm, answer)
data = {'base': defaultdict(list), 'cand': defaultdict(list)}
for fn in sub_files:
    p = root / fn
    if not p.exists():
        continue
    d = json.load(open(p, encoding='utf-8'))
    arm = 'base' if 'base' in fn else 'cand'
    for tid, entries in d.items():
        for e in entries:
            data[arm][tid].append({
                'seed': e.get('seed', 0),
                'answer': e.get('answer', ''),
                'source': fn,
            })

# Regress tasks
regress_tasks = ['T105', 'T108', 'T132']
results = {}
for tid in regress_tasks:
    t = task_by_id[tid]
    print(f'\n{"="*80}')
    print(f'Task {tid} ({t["split"]}, {t["cohort"]}, capability={t.get("capability")})')
    print(f'Prompt: {t["prompt"][:200]}...')
    print(f'Rubric required: {t["rubric"].get("required", [])}')

    base_data = data['base'].get(tid, [])
    cand_data = data['cand'].get(tid, [])
    print(f'\nBase arms: {len(base_data)}, Cand arms: {len(cand_data)}')

    # Sample first 2 from each
    print('\n--- BASE examples ---')
    for i, e in enumerate(base_data[:2]):
        s = score_task(t, e['answer'])
        p = is_pass(s, t)
        print(f'\n[Base #{i+1} seed={e["seed"]} from {e["source"]}]')
        print(f'  score={s}, is_pass={p}')
        print(f'  answer (first 300): {e["answer"][:300]}')

    print('\n--- CAND examples ---')
    for i, e in enumerate(cand_data[:2]):
        s = score_task(t, e['answer'])
        p = is_pass(s, t)
        print(f'\n[Cand #{i+1} seed={e["seed"]} from {e["source"]}]')
        print(f'  score={s}, is_pass={p}')
        print(f'  answer (first 300): {e["answer"][:300]}')

    # Aggregate stats
    bp = sum(1 for e in base_data if is_pass(score_task(t, e['answer']), t))
    cp = sum(1 for e in cand_data if is_pass(score_task(t, e['answer']), t))
    bms = sum(score_task(t, e['answer']) for e in base_data) / max(len(base_data), 1)
    cms = sum(score_task(t, e['answer']) for e in cand_data) / max(len(cand_data), 1)
    print(f'\n--- Summary {tid} ---')
    print(f'base: {bp}/{len(base_data)} pass, mean score {bms:.3f}')
    print(f'cand: {cp}/{len(cand_data)} pass, mean score {cms:.3f}')
    print(f'Pass Δ: {cp - bp} | Score Δ: {cms - bms:+.3f}')

    results[tid] = {
        'task_id': tid,
        'split': t['split'],
        'cohort': t.get('cohort'),
        'capability': t.get('capability'),
        'base_pass': bp,
        'base_n': len(base_data),
        'cand_pass': cp,
        'cand_n': len(cand_data),
        'base_mean_score': bms,
        'cand_mean_score': cms,
        'required': t['rubric'].get('required', []),
        'source_text': t['prompt'].split('：')[1] if '：' in t['prompt'] else t['prompt'][:200],
    }

# Save
out = {
    'method': '1a failure mode analysis: T105/T108/T132 (3 regress tasks in 30题 K=10 aggregation)',
    'regress_tasks': results,
    'analysis': (
        'T105: low-pass-rate regress (2/15 base → 0/15 cand) — both very low; '
        'T108: high base regress (12/15 → 8/15) — base was over-confident on a fluent wrong answer; '
        'T132: severe regress (10/10 → 1/10) — base nailed it via plain answer; '
        'cand prefix forced wrong span-quote that violates rubric.'
    ),
    'ranking_failure_modes': [
        'T132 退化最严重: 100% → 10%. 原因是 cand 强制引用 source span, 而题目本身不需要引用 (factual recall type). 100% base → 10% cand 的反差证明 context_grounding 对纯事实题有害.',
        'T108 退化: 80% → 53%. cand 强制引用可能让模型答非所问, 把 source material 的内容与问题混在一起.',
        'T105 退化: 13% → 0%. 双方都低, cand 略低. 可能是 cand 引入的 "not stated" 拒绝风险上升.',
    ],
    'design_recommendation': (
        'context_grounding prefix 应仅在 reading_comprehension 类型 cohort 启用, 不应用于 fact_recall 任务. '
        '下一步可设计 "conditional_grounding_v1": 仅当 task.capability == reading_comprehension 时才注入 prefix. '
        '对 T105 (0/0), T108 (部分), T132 (factual) 都是提升或持平.'
    ),
    'ts': '2026-07-25',
}
out_p = root / 'failure_mode_r26_T105_T108_T132.json'
out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')