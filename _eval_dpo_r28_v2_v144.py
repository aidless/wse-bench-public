"""Evaluate DPO r28 v2 adapter (beta=0.05) on the v144 protocol:
hidden + fresh + Q4-core dev (2026Q4) = n up to ~140 tasks.

Mirrors _eval_dpo_r23_v144.py but with the r28 v2 adapter path and the
WSE_REPO_ROOT env var honored (this file is shipped in v1.0.x of the
public repo). K=1, greedy, max_new_tokens=128.

Outputs:
  results_dpo_r28_v2_v144.json  (per-task details)
  _r28_dpo_v2_v144_summary.json (pass/fail + by_split)
"""
import json, os, sys, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

root = Path(os.environ.get('WSE_REPO_ROOT', r'__WSE_REPO_ROOT__'))
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))

# Same protocol as r23: hidden + fresh + Q4-core dev (never-trained-on tasks)
hidden_fresh_ids = [t['id'] for t in manifest['tasks']
                    if t.get('split') in ('hidden', 'fresh')]
new_dev_ids = [t['id'] for t in manifest['tasks']
               if t.get('cohort') == '2026Q4-core' and t.get('split') == 'dev']
eval_ids = set(hidden_fresh_ids) | set(new_dev_ids)

tasks_eval = [t for t in manifest['tasks'] if t['id'] in eval_ids]
print(f'eval_ids: {len(eval_ids)} (hidden+fresh={len(hidden_fresh_ids)}, '
      f'Q4-core dev={len(new_dev_ids)})')

# Anti-leakage assertion
for t in tasks_eval:
    if t.get('cohort') == '2026Q4-core' and t.get('split') == 'dev':
        continue
    assert t.get('split') != 'dev', f'leakage: {t["id"]}'
print('no Q3 dev leak ✓')

MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
ADAPTER_PATH = r'F:/lora_adapter/qwen3b_pathA_dpo_r28_v2'

tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                             bnb_4bit_use_double_quant=True,
                             bnb_4bit_compute_dtype=torch.bfloat16)
print('loading base ...')
t0 = time.time()
base = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, quantization_config=bnb_cfg, torch_dtype=torch.bfloat16,
    device_map='auto', trust_remote_code=True)
print(f'  base loaded in {time.time()-t0:.1f}s')

print('loading DPO v2 adapter ...')
lora = PeftModel.from_pretrained(base, ADAPTER_PATH)
lora.eval()
print('  adapter loaded')


def gen_one(model, prompt, max_new_tokens=128):
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)


def score_arm(model, label):
    rows = {}
    for t in tasks_eval:
        full_prompt = t['prompt']
        ans = gen_one(model, full_prompt)
        s = score_task(t, ans)
        rows[t['id']] = {'task_id': t['id'], 'seed': 0, 'answer': ans[:300],
                         'score': float(s), 'is_pass': bool(is_pass(s, t)),
                         'split': t['split'], 'cohort': t.get('cohort')}
        print(f'  [{label}] {t["id"]} pass={rows[t["id"]]["is_pass"]} '
              f'(score={s:.2f}, split={t["split"]})')
    return rows


print('=== base (Qwen2.5-3B-Instruct) ===')
t0 = time.time()
base_res = score_arm(base, 'base')
print(f'base done in {time.time()-t0:.0f}s')

print('=== DPO v2 LoRA ===')
t0 = time.time()
lora_res = score_arm(lora, 'dpo_v2')
print(f'dpo v2 done in {time.time()-t0:.0f}s')


def summarize(results, label):
    n = len(results)
    passes = sum(r['is_pass'] for r in results.values())
    by_split = {}
    for tid, r in results.items():
        sp = r['split']
        by_split.setdefault(sp, {'n': 0, 'pass': 0, 'sum_score': 0.0})
        by_split[sp]['n'] += 1
        by_split[sp]['sum_score'] += r['score']
        if r['is_pass']:
            by_split[sp]['pass'] += 1
    for sp in by_split:
        by_split[sp]['mean_score'] = by_split[sp]['sum_score'] / by_split[sp]['n']
        by_split[sp]['pass_rate'] = by_split[sp]['pass'] / by_split[sp]['n']
    return {'label': label, 'n': n, 'pass': passes,
            'pass_rate': passes / n if n else 0,
            'by_split': by_split}


b = summarize(base_res, 'base')
d = summarize(lora_res, 'dpo_v2')

# McNemar on paired (b,c) discordant counts
import math
b_count, c_count = 0, 0
for tid in [t['id'] for t in tasks_eval]:
    bp = base_res[tid]['is_pass']; cp = lora_res[tid]['is_pass']
    if bp and not cp: b_count += 1
    elif cp and not bp: c_count += 1


def exact_mcnemar(b, c):
    from math import comb
    k = b + c
    if k == 0:
        return 1.0
    lo = min(b, c)
    return min(1.0, sum(comb(k, i) for i in range(0, lo + 1)) / 2 ** k * 2)


print(f'\n=== summary ===')
print(f'  base:      pass={b["pass"]}/{b["n"]} ({b["pass_rate"]*100:.1f}%)')
print(f'  dpo_v2:    pass={d["pass"]}/{d["n"]} ({d["pass_rate"]*100:.1f}%)')
print(f'  discordant: b={b_count} c={c_count}')
print(f'  McNemar p={exact_mcnemar(b_count, c_count):.4f}')
print(f'  delta={(d["pass"] - b["pass"])/max(b["n"],1):.3f}')

OUT = root / 'results_dpo_r28_v2_v144.json'
OUT.write_text(json.dumps({'base': base_res, 'dpo_v2_lora': lora_res}, ensure_ascii=False, indent=1),
               encoding='utf-8')

summary = {
    'design': {'K': 1, 'greedy': True, 'max_new_tokens': 128,
               'adapter_path': ADAPTER_PATH, 'beta': 0.05,
               'n_pairs': len(tasks_eval)},
    'base': b,
    'dpo_v2': d,
    'paired': {'b': b_count, 'c': c_count,
               'mcnemar_p': exact_mcnemar(b_count, c_count),
               'delta_pass': (d['pass'] - b['pass']) / max(b['n'], 1)}
}
SUMMARY = root / '_r28_dpo_v2_v144_summary.json'
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {OUT}\nsaved: {SUMMARY}')
