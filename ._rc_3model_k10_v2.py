"""Pillar A: 3-base-model K=10 context_grounding evaluation.
Models: Qwen2.5-3B-Instruct (already done), Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3
Cohort: T103-T122 (20题) for max power
K=10 independent seeds (101-1010)
Ablation: with grounding prefix vs without

If only Qwen is locally available, run only Qwen (3rd model run will be skipped).
"""
import json, os, sys, time, gc
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass, PASS_THRESHOLD

os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

# Eval cohort: T103-T122 (RC2+RC3, 20题 context-grounding design)
EVAL_IDS = []
for tid in range(103, 123):
    EVAL_IDS.append(f'T{tid:03d}')
EVAL_IDS = [t for t in EVAL_IDS if any(task['id'] == t for task in manifest['tasks'])]
print('eval tasks:', len(EVAL_IDS), EVAL_IDS)

tasks_eval = [t for t in manifest['tasks'] if t['id'] in EVAL_IDS]

CONTEXT_GROUNDING_PREFIX = """You are an expert reading-comprehension assistant. Answer ONLY by quoting exact source spans (verbatim phrases) from the provided material. Do not paraphrase. If the material does not directly contain the answer, say "not stated in the source".

"""

NO_PREFIX = ""  # ablation: no grounding prefix

K = 10
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]

MODELS = [
    {
        'name': 'Qwen2.5-3B-Instruct',
        'path': r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master',
        'available': True,
    },
    {
        'name': 'Llama-3.1-8B-Instruct',
        'path': r'F:/hf_cache/models/meta-llama--Llama-3.1-8B-Instruct',
        'available': False,  # not downloaded
    },
    {
        'name': 'Mistral-7B-Instruct-v0.3',
        'path': r'F:/hf_cache/models/mistralai--Mistral-7B-Instruct-v0.3',
        'available': False,  # not downloaded
    },
]

def load_model(model_path):
    print(f'Loading {model_path}...')
    t0 = time.time()
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path, quantization_config=bnb, torch_dtype=torch.bfloat16,
        device_map='auto', trust_remote_code=True,
    )
    model.eval()
    print(f'  loaded in {time.time()-t0:.1f}s')
    return model, tok

def gen_one(model, tok, prompt, seed):
    torch.manual_seed(seed)
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=128, do_sample=True, temperature=0.7, top_p=0.9,
            pad_token_id=tok.eos_token_id, repetition_penalty=1.05,
        )
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

def score_arm(model, tok, prefix, label):
    results = {}
    for t in tasks_eval:
        full_prompt = prefix + t['prompt']
        for seed in SEEDS:
            ans = gen_one(model, tok, full_prompt, seed)
            s = score_task(t, ans)
            results[f"{t['id']}_seed{seed}"] = {
                'task_id': t['id'],
                'seed': seed,
                'answer': ans[:200],
                'score': s,
                'is_pass': is_pass(s, t),
                'split': t['split'],
            }
    return results

# Run per available model
all_results = {}
for m in MODELS:
    if not m['available']:
        print(f"\n=== {m['name']} NOT AVAILABLE locally — skipping ===")
        continue
    print(f"\n=== {m['name']} ===")
    t0 = time.time()
    model, tok = load_model(m['path'])
    # With grounding
    print('  with grounding:')
    cand = score_arm(model, tok, CONTEXT_GROUNDING_PREFIX, 'cand')
    # Without grounding (ablation)
    print('  without grounding (ablation):')
    base = score_arm(model, tok, NO_PREFIX, 'base')
    all_results[m['name']] = {'cand': cand, 'base': base, 'duration': time.time() - t0}
    # Cleanup
    del model, tok
    gc.collect()
    torch.cuda.empty_cache()

# Save partial result
out_p = root / 'results_3model_k10_partial.json'
out_p.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')

# Quick per-model summary
for mname, mdata in all_results.items():
    base_pass = sum(1 for r in mdata['base'].values() if r['is_pass'])
    cand_pass = sum(1 for r in mdata['cand'].values() if r['is_pass'])
    n = len(mdata['base'])
    delta = (cand_pass - base_pass) / n
    print(f'{mname}: base {base_pass}/{n} → cand {cand_pass}/{n} (Δ {delta:+.3f}) in {mdata["duration"]:.0f}s')