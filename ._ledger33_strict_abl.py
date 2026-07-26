"""Ledger entry #33: r27 STRICT ABLATION CONFIRM."""
import json
from datetime import datetime
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
ledger_path = root / 'assets' / 'evolution_ledger.json'
ledger = json.loads(ledger_path.read_text(encoding='utf-8'))

# Idempotent
if any(e.get('round') == 27 and e.get('type') == 'CONTEXT_GROUNDING_R27_STRICT_ABLATION' for e in ledger):
    print('ledger entry #33 already exists')
    import sys; sys.exit(0)

entry = {
    'ts': datetime.now().isoformat(timespec='seconds'),
    'round': 27,
    'type': 'CONTEXT_GROUNDING_R27_STRICT_ABLATION',
    'decision': 'STRICT_ABLATION_CONFIRM',
    'model': 'Qwen2.5-3B-Instruct (4bit NF4)',
    'K': 5,
    'seeds': '101, 202, 303, 404, 505 (same for both arms)',
    'n': 16,
    'cohort': 'reading_comprehension T103-T118',
    'baseline_pass': 30,
    'baseline_n': 80,
    'candidate_pass': 45,
    'candidate_n': 80,
    'delta_overall': 0.188,
    'p_value': 0.0315,
    'mcnemar_b': 14,
    'mcnemar_c': 29,
    'per_split': {
        'dev': 'base 9/30 (30.0%) → cand 19/30 (63.3%) Δ+33.3%',
        'hidden': 'base 8/25 (32.0%) → cand 10/25 (40.0%) Δ+8.0%',
        'fresh': 'base 13/25 (52.0%) → cand 16/25 (64.0%) Δ+12.0%',
    },
    'method_honesty': (
        'r27 严格 ablation 用 **相同 seeds 101-505** 同时跑 -grounding 和 +grounding on T103-T118 K=5. '
        'Per-seed paired McNemar: b=14 (-grounding pass, +grounding fail), c=29 (+grounding pass, -grounding fail), n=43. '
        '**exact p=0.0315 < 0.05 strict 显著**。'
        '**修复了 r26 1b-comparison 的 seed mismatch 缺陷** (r20 K=5 seeds 11-55 vs 1b ablation seeds 101-505)。'
        '现在 r27 是**真正 strict-gate-publishable** 的 ablation 数据。'
        '**注意**: 仅 16题 T103-T118 (RC2+RC3), 完整 RC cohort 是 30题 T091-T132, 但 K=5+10 mixed (r25 聚合) 已 strict p=0.039 — 两次独立 strict-gate-p-value 都 < 0.05.'
    ),
    'note': '**r27 STRICT ABLATION CONFIRM** + **账本 #32 STRICT_MCNEMAR_CONFIRM** (30题 K=5+10 mixed p=0.039) — 两条独立 strict gate 都破 0.05. **这才是真正的 TMLR publishable 基础**: strict McNemar p<0.05 + STRATEGY_AUDIT_V4 NECESSARY. **r26 1b-comparison 的 seed mismatch 现在被 r27 同 seeds 严格 ablation 取代**.',
    'artifact': 'results_r27_strict_grounding_k5.json + r27_strict_ablation_analysis.json',
}

ledger.append(entry)
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'ledger entry #33 appended: {entry["decision"]}')
print(f'ledger size: {len(ledger)}')