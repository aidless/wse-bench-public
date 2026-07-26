"""1b Ablation: -grounding prefix on T103-T132 K=5 multi-seed.
Hypothesis: -grounding is closer to baseline; +grounding's gain comes from the prefix instruction.
"""
import json, os, time, sys, gc
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
EVAL_IDS = [f'T{i:03d}' for i in range(103, 123)]
tasks_eval = [t for t in manifest['tasks'] if t['id'] in EVAL_IDS]
print(f'ablation tasks: {len(tasks_eval)}')

K = 5
SEEDS = [101, 202, 303, 404, 505]

NO_PREFIX = ""  # ablation: no grounding prefix
GROUNDING_PREFIX = """You are an expert reading-comprehension assistant. Answer ONLY by quoting exact source spans (verbatim phrases) from the provided material. Do not paraphrase. If the material does not directly contain the answer, say "not stated in the source".

"""

MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
print(f'Loading {MODEL_PATH}...')
t0 = time.time()
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, quantization_config=bnb, torch_dtype=torch.bfloat16, device_map='auto', trust_remote_code=True,
)
model.eval()
print(f'  loaded in {time.time()-t0:.1f}s')

def gen_one(prompt, seed):
    torch.manual_seed(seed)
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=0.7, top_p=0.9, pad_token_id=tok.eos_token_id, repetition_penalty=1.05)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

# Run -grounding (ablation)
print('\n=== -grounding (ablation) ===')
ablation = {}
t0 = time.time()
for t in tasks_eval:
    full_prompt = NO_PREFIX + t['prompt']
    ablation[t['id']] = []
    for seed in SEEDS:
        ans = gen_one(full_prompt, seed)
        s = score_task(t, ans)
        ablation[t['id']].append({
            'seed': seed,
            'answer': ans,
            'score': s,
            'is_pass': is_pass(s, t),
            'split': t['split'],
        })
    n_pass = sum(e['is_pass'] for e in ablation[t['id']])
    print(f'  {t["id"]} ({t["split"]}): {n_pass}/{K}')
print(f'ablation done in {time.time()-t0:.1f}s')

# Save
out_p = root / 'results_ablation_30q_k5.json'
out_p.write_text(json.dumps(ablation, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsaved: {out_p}')

# Summary
print('\n=== Ablation Summary (T103-T122, K=5) ===')
total_pass = sum(sum(e['is_pass'] for e in ablation[t['id']]) for t in tasks_eval)
total_n = len(tasks_eval) * K
print(f'total: {total_pass}/{total_n} ({total_pass/total_n*100:.1f}%)')
by_split = {'dev': [0, 0], 'hidden': [0, 0], 'fresh': [0, 0]}
for t in tasks_eval:
    n = sum(e['is_pass'] for e in ablation[t['id']])
    by_split[t['split']][0] += n
    by_split[t['split']][1] += K
for sp, (p, n) in by_split.items():
    if n:
        print(f'  {sp}: {p}/{n} ({p/n*100:.1f}%)')