"""Ledger entry #32: context_grounding_v1 STRICT-McNemar CONFIRM via STRATEGY_AUDIT_V4."""
import json
from datetime import datetime
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
ledger_path = root / 'assets' / 'evolution_ledger.json'
ledger = json.loads(ledger_path.read_text(encoding='utf-8'))

# Idempotent
if any(e.get('round') == 27 and e.get('type') == 'CONTEXT_GROUNDING_RC_V4_CONFIRM' for e in ledger):
    print('ledger entry #32 already exists')
    import sys; sys.exit(0)

entry = {
    'ts': datetime.now().isoformat(timespec='seconds'),
    'round': 27,
    'type': 'CONTEXT_GROUNDING_RC_V4_CONFIRM',
    'decision': 'STRICT_MCNEMAR_CONFIRM',
    'model': 'Qwen2.5-3B-Instruct (4bit NF4)',
    'K': '5+10 mixed (K=5 r20 + K=10 r21/r22)',
    'n': 30,
    'cohort': 'reading_comprehension (RC+RC2+RC3+RC4 = T091-T132)',
    'baseline_pass': 103,
    'baseline_n': 250,
    'candidate_pass': 171,
    'candidate_n': 250,
    'delta_overall': 0.272,
    'p_value': 0.0391,
    'mcnemar_b': 1,
    'mcnemar_c': 8,
    'per_split': {
        'dev': 'base 25/100 (25.0%) → cand 54/100 (54.0%) Δ+29%',
        'hidden': 'base 27/90 (30.0%) → cand 64/90 (71.1%) Δ+41%',
        'fresh': 'base 51/60 (85.0%) → cand 53/60 (88.3%) Δ+3%',
    },
    'method_honesty': 'r25 30题 strict-McNemar 聚合 (账本 #29 时的 p=0.125 是 10题 K=5) 现在 r27 用 30题 K=5+10 聚合得 p=0.0391 — **strict gate CONFIRM** (仍受 K-inconsistency caveat 但已显著)。V4 simplified audit: A_minus (no prefix) 41.2% vs reference (with prefix) 68.4% on RC cohort, Δ_minus_full=-27.2% (5.4x noise floor) → NECESSARY。',
    'note': '**r27 双重确认**: (1) strict-McNemar p=0.0391 < 0.05 破门 (2) STRATEGY_AUDIT_V4 NECESSARY on RC cohort 30题。**账本 #32 正式记录 strict-McNemar CONFIRM**。之前账本 #29 v24 alt-test gate PROMOTE 现在被 strict gate 反向支持。诚实 caveat: K-inconsistent (5+10) + 仅 1 base model (Qwen) + isolated contribution test (非 7-vs-6-strategy 全 ablation)。',
    'artifact': 'results_ablation_30q_k5.json + strategy_audit_v4.json + pillar_a_qwen_30q_stats.json',
}

ledger.append(entry)
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'ledger entry #32 appended: {entry["decision"]}')
print(f'ledger size: {len(ledger)}')