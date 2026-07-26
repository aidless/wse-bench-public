import sys; sys.stdout.reconfigure(line_buffering=True)
"""Evaluate DPO r23 adapter on v144 (144题) hidden+fresh split.
K=1 greedy max_new_tokens=256. Compare LoRA vs base.
"""
import json, os, sys, time
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

# Only evaluate on hidden + fresh (and the new Q4-core dev tasks but exclude training-split dev tasks for honest measurement)
hidden_fresh_ids = [t['id'] for t in manifest['tasks'] if t.get('split') in ('hidden', 'fresh')]
# Add the 8 Q4-core dev tasks that are NEW (T133-T148), as these were never trained on
new_dev_ids = [t['id'] for t in manifest['tasks'] if t.get('cohort') == '2026Q4-core' and t.get('split') == 'dev']
eval_ids = set(hidden_fresh_ids) | set(new_dev_ids)
print('eval_ids:', len(eval_ids))

tasks_eval = [t for t in manifest['tasks'] if t['id'] in eval_ids]
print('tasks_eval:', len(tasks_eval))

# Forbidden: ensure no dev tasks from Q3 cohorts (which were in training data)
for t in tasks_eval:
    if t.get('cohort') == '2026Q4-core' and t.get('split') == 'dev':
        continue
    assert t.get('split') != 'dev', f'leakage: {t["id"]}'
print('no Q3 dev leak ✓')

MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
ADAPTER_PATH = r'F:/lora_adapter/qwen3b_pathA_dpo_r23_dev'
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

print('loading base model...')
t0 = time.time()
base = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_cfg,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True,
)
base.config.use_cache = False
print(f'base loaded in {time.time()-t0:.1f}s')

# Load adapter
print('loading DPO adapter...')
lora = PeftModel.from_pretrained(base, ADAPTER_PATH)
lora.eval()
print('adapter loaded')

def gen_one(model, prompt, max_new_tokens=128):
    inputs = tok(prompt, return_tensors='pt').to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


def score_arm(model, arm_label):
    results = {}
    for t in tasks_eval:
        prompt = t['prompt']
        ans = gen_one(model, prompt)
        s = score_task(t, ans)
        results[t['id']] = {
            'answer': ans,
            'score': s,
            'is_pass': is_pass(s, t),
            'split': t['split'],
        }
    return results


# Run base
print('=== BASE ===')
t0 = time.time()
base_results = score_arm(base, 'base')
print(f'base done in {time.time()-t0:.1f}s')

# Run DPO adapter (LoRA)
print('=== DPO LoRA ===')
t0 = time.time()
lora_results = score_arm(lora, 'lora')
print(f'lora done in {time.time()-t0:.1f}s')

# Compute summary
def summarize(results, label):
    n = len(results)
    passes = sum(r['is_pass'] for r in results.values())
    by_split = {}
    for tid, r in results.items():
        sp = r['split']
        by_split.setdefault(sp, {'n': 0, 'pass': 0, 'sum_score': 0})
        by_split[sp]['n'] += 1
        by_split[sp]['sum_score'] += r['score']
        if r['is_pass']:
            by_split[sp]['pass'] += 1
    for sp in by_split:
        by_split[sp]['mean_score'] = by_split[sp]['sum_score'] / by_split[sp]['n']
        by_split[sp]['pass_rate'] = by_split[sp]['pass'] / by_split[sp]['n']
    return {'label': label, 'n': n, 'pass': passes, 'pass_rate': passes / n, 'by_split': by_split}


bs = summarize(base_results, 'base')
ls = summarize(lora_results, 'dpo_lora')
print('\n=== SUMMARY ===')
print(f'base:  {bs["pass"]}/{bs["n"]} ({bs["pass_rate"]:.3f})')
print(f'lora:  {ls["pass"]}/{ls["n"]} ({ls["pass_rate"]:.3f})')
for sp in ('hidden', 'fresh', 'dev'):
    if sp in bs['by_split']:
        print(f'  {sp}: base {bs["by_split"][sp]["pass"]}/{bs["by_split"][sp]["n"]} ({bs["by_split"][sp]["pass_rate"]:.3f}, mean {bs["by_split"][sp]["mean_score"]:.3f}) '
              f'lora {ls["by_split"][sp]["pass"]}/{ls["by_split"][sp]["n"]} ({ls["by_split"][sp]["pass_rate"]:.3f}, mean {ls["by_split"][sp]["mean_score"]:.3f})')

# McNemar
b_pass = {tid: r['is_pass'] for tid, r in base_results.items()}
l_pass = {tid: r['is_pass'] for tid, r in lora_results.items()}
ids = list(b_pass.keys())
b_l_p_l = sum(1 for tid in ids if b_pass[tid] and not l_pass[tid])  # base pass, lora fail
l_l_b_p = sum(1 for tid in ids if l_pass[tid] and not b_pass[tid])  # lora pass, base fail
n = b_l_p_l + l_l_b_p
print(f'\ndiscordant: b_pass_lora_fail={b_l_p_l}, lora_pass_base_fail={l_l_b_p}')
if n > 0:
    import math
    p_obs = math.comb(n, b_l_p_l) * (0.5 ** n)
    pval = 0.0
    for k in range(n + 1):
        if math.comb(n, k) * (0.5 ** n) <= p_obs + 1e-15:
            pval += math.comb(n, k) * (0.5 ** n)
    pval = min(pval, 1.0)
    print(f'McNemar p={pval:.4f}')

# Save
out = {
    'round': 23,
    'method': 'DPO 90 dev pairs r=8 alpha=16 lr=2e-5 1 epoch beta=0.1',
    'eval_set': 'hidden + fresh + 8 Q4-core dev (no Q3 dev leakage)',
    'n_eval': len(ids),
    'base': base_results,
    'dpo_lora': lora_results,
    'summary': {'base': bs, 'dpo_lora': ls},
    'mcnemar_b_pass_l_fail': b_l_p_l,
    'mcnemar_l_pass_b_fail': l_l_b_p,
    'mcnemar_p': pval if n > 0 else 1.0,
    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
}
with open(root / 'results_dpo_r23_v144.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('saved:', root / 'results_dpo_r23_v144.json')