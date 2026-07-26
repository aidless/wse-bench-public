"""r28 prefix component ablation (plan 2.1).

Q: Which component of GROUNDING_PREFIX drives the #33 gain?
Components:
  C1 role   = "You are an expert reading-comprehension assistant."
  C2 quote  = "Answer ONLY by quoting exact source spans (verbatim phrases)
               from the provided material. Do not paraphrase."
  C3 abstain= 'If the material does not directly contain the answer, say
               "not stated in the source".'
Arms (new, 4): role_only, quote_only, abstain_only, quote_abstain.
Reused arms  : base (results_ablation_30q_k5.json), full (+grounding,
               results_r27_strict_grounding_k5.json) — same tasks T103-T118,
               same seeds 101-505, same protocol => directly comparable.
Analysis: paired McNemar of each arm vs base; component attribution table.
NOTE: multiple comparisons (4 arms) -> report Holm-adjusted p as well.
"""
import json, os, time, sys
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(os.environ.get('WSE_REPO_ROOT', r'__WSE_REPO_ROOT__'))
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
EVAL_IDS = [f'T{i:03d}' for i in range(103, 119)]
tasks_eval = sorted([t for t in manifest['tasks'] if t['id'] in EVAL_IDS], key=lambda t: t['id'])
K = 5
SEEDS = [101, 202, 303, 404, 505]

C1 = "You are an expert reading-comprehension assistant."
C2 = "Answer ONLY by quoting exact source spans (verbatim phrases) from the provided material. Do not paraphrase."
C3 = 'If the material does not directly contain the answer, say "not stated in the source".'

ARMS = {
    'role_only':    C1 + "\n\n",
    'quote_only':   C2 + "\n\n",
    'abstain_only': C3 + "\n\n",
    'quote_abstain': C2 + " " + C3 + "\n\n",
}

CKPT = root / '_r28_prefix_ablation_ckpt.json'
OUT = root / 'results_r28_prefix_ablation_k5.json'
SUMMARY = root / '_r28_prefix_ablation_summary.json'
ckpt = json.loads(CKPT.read_text(encoding='utf-8')) if CKPT.exists() else {a: {} for a in ARMS}

MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb,
                                             torch_dtype=torch.bfloat16, device_map='auto',
                                             trust_remote_code=True)
model.eval()
print('model loaded')


def gen_one(prompt, seed):
    torch.manual_seed(seed)
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=0.7,
                             top_p=0.9, pad_token_id=tok.eos_token_id, repetition_penalty=1.05)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


for arm, prefix in ARMS.items():
    print(f'=== arm {arm} ===', flush=True)
    for t in tasks_eval:
        if t['id'] in ckpt[arm] and len(ckpt[arm][t['id']]) == K:
            continue
        rows = []
        for seed in SEEDS:
            ans = gen_one(prefix + t['prompt'], seed)
            s = score_task(t, ans)
            rows.append({'seed': seed, 'answer': ans, 'score': s,
                         'is_pass': bool(is_pass(s, t)), 'split': t['split']})
        ckpt[arm][t['id']] = rows
        CKPT.write_text(json.dumps(ckpt, ensure_ascii=False), encoding='utf-8')
        print(f'  {t["id"]}: {sum(r["is_pass"] for r in rows)}/{K}', flush=True)

OUT.write_text(json.dumps(ckpt, ensure_ascii=False, indent=1), encoding='utf-8')

# ---- analysis vs reused base arm ----
base = json.loads((root / 'results_ablation_30q_k5.json').read_text(encoding='utf-8'))
full = json.loads((root / 'results_r27_strict_grounding_k5.json').read_text(encoding='utf-8'))

def mcnemar_exact(b, c):
    from math import comb
    k = b + c
    if k == 0:
        return 1.0
    lo = min(b, c)
    return min(1.0, sum(comb(k, i) for i in range(0, lo + 1)) / 2 ** k * 2)

def compare(arm_data, label):
    b = c = 0
    npass = 0
    for tid in EVAL_IDS:
        for rb, rc_ in zip(base[tid], arm_data[tid]):
            assert rb['seed'] == rc_['seed']
            npass += rc_['is_pass']
            if rb['is_pass'] and not rc_['is_pass']: b += 1
            elif rc_['is_pass'] and not rb['is_pass']: c += 1
    n = len(EVAL_IDS) * K
    return {'arm': label, 'pass': npass, 'pass_rate': npass / n, 'b': b, 'c': c,
            'delta': (c - b) / n, 'p_raw': mcnemar_exact(b, c),
            'cohens_g': (c - b) / (b + c) if b + c else 0.0}

rows = [compare(full, 'full_prefix(#33)')]
for arm in ARMS:
    rows.append(compare(ckpt[arm], arm))
# Holm correction over the 4 NEW arms only (full is confirmatory, pre-existing)
new = sorted(rows[1:], key=lambda r: r['p_raw'])
m_ = len(new)
prev = 0.0
for i, r in enumerate(new):
    adj = min(1.0, max(prev, (m_ - i) * r['p_raw']))
    r['p_holm'] = adj
    prev = adj
base_pass = sum(sum(e['is_pass'] for e in base[tid]) for tid in EVAL_IDS)
summary = {'base_pass': base_pass, 'base_rate': base_pass / (len(EVAL_IDS) * K), 'arms': rows}
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
