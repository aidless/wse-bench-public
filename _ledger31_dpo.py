"""Ledger entry #31 for DPO r23 v144 evaluation.
Idempotent: check if #31 already exists before appending.
"""
import json, sys
from datetime import datetime
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
ledger_path = root / 'assets' / 'evolution_ledger.json'
result_path = root / 'results_dpo_r23_v144.json'

# Read current ledger
ledger = json.loads(ledger_path.read_text(encoding='utf-8'))

# Check if #31 already exists
if any(e.get('round') == 23 and 'DPO' in e.get('type', '') for e in ledger):
    print('ledger entry for DPO r23 already exists')
    sys.exit(0)

# Read DPO eval result
if not result_path.exists():
    print(f'no eval result at {result_path}')
    sys.exit(1)

result = json.loads(result_path.read_text(encoding='utf-8'))

entry = {
    'ts': datetime.now().isoformat(timespec='seconds'),
    'round': 23,
    'type': 'CONTEXT_PATH_A_DPO_R23_EVAL',
    'decision': 'HOLD',  # to be set after eval
    'model': 'Qwen2.5-3B-Instruct + DPO r=8/alpha=16/lr=2e-5/1 epoch/beta=0.1 (90 dev pairs)',
    'K': 1,
    'n': result['n_eval'],
    'baseline_pass': result['summary']['base']['pass'],
    'candidate_pass': result['summary']['dpo_lora']['pass'],
    'delta_overall': round(result['summary']['dpo_lora']['pass_rate'] - result['summary']['base']['pass_rate'], 3),
    'p_value': result.get('mcnemar_p'),
    'discordant_b_pass_l_fail': result.get('mcnemar_b_pass_l_fail'),
    'discordant_l_pass_b_fail': result.get('mcnemar_l_pass_b_fail'),
    'per_split': {
        sp: {
            'base': f"{result['summary']['base']['by_split'][sp]['pass']}/{result['summary']['base']['by_split'][sp]['n']} ({result['summary']['base']['by_split'][sp]['pass_rate']:.3f}, mean {result['summary']['base']['by_split'][sp]['mean_score']:.3f})",
            'dpo': f"{result['summary']['dpo_lora']['by_split'][sp]['pass']}/{result['summary']['dpo_lora']['by_split'][sp]['n']} ({result['summary']['dpo_lora']['by_split'][sp]['pass_rate']:.3f}, mean {result['summary']['dpo_lora']['by_split'][sp]['mean_score']:.3f})",
        }
        for sp in ('hidden', 'fresh', 'dev')
        if sp in result['summary']['base']['by_split']
    },
    'method_honesty': 'DPO r23 with 90 dev pairs (19 unique tasks, 6 策略 K=5/K=10 raw, gap mean 0.742); eval on v144 hidden + fresh + 8 Q4-core dev (no Q3 dev leakage); K=1 greedy max_new_tokens=256; bf16 (3060 不支持 fp16 GradScaler)',
    'note': '...',  # filled in based on decision
    'artifact': 'results_dpo_r23_v144.json',
}

# Set decision
b_pass = entry['baseline_pass']
l_pass = entry['candidate_pass']
p = entry['p_value']
if l_pass > b_pass and p < 0.05:
    entry['decision'] = 'PROMOTE_PATH_A'
elif entry['delta_overall'] >= 0:
    entry['decision'] = 'HOLD'  # positive trend but not significant
else:
    entry['decision'] = 'FAILED'  # negative or zero

# Fill note
note_pieces = []
note_pieces.append(f'v144 DPO r23 eval: base {b_pass}→cand {l_pass}, Δ={entry["delta_overall"]}, p={p:.4f}')
note_pieces.append('90 dev pairs DPO 训练 130s loss 0.693→0.586, rewards/margins 0→0.5785')
note_pieces.append(f'训练数据: {result.get("method", "?")}')
if entry['decision'] == 'PROMOTE_PATH_A':
    note_pieces.append('DPO r23 在 hidden+fresh+Q4-dev 上净提升显著, **路径 A 首次权重级 PROMOTE**')
elif entry['decision'] == 'HOLD':
    note_pieces.append('DPO r23 净非负但不显著, 路径 A 仍需更大独立数据')
else:
    note_pieces.append('DPO r23 净负, 路径 A 仍未真正完成权重级 PROMOTE')
entry['note'] = '；'.join(note_pieces)

ledger.append(entry)
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'ledger entry #31 appended: {entry["decision"]}')
print(f'ledger size: {len(ledger)}')