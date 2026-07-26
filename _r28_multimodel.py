"""r28 multi-model replication (plan 1.1), upgraded from ._rc_3model_k10_v2.py.

Changes vs v2:
- Dynamic availability: model dir must contain config.json + >=1 *.safetensors.
- Checkpoint per (model, arm, task) -> _r28_multimodel_ckpt.json, resumable.
- Qwen skipped by default: its evidence = ledger #33 (K=5) + r28 large-n (K=15).
- Per-model paired McNemar + Cohen's g analysis appended to summary.
- Weights provenance: unsloth mirrors of official weights (gated repos not
  accessible anonymously); tokenizer/config identical to upstream.
- 2026-07-26: env hygiene + CPU offload for 8B on 6GB VRAM.
Cohort: T103-T122 (manifest-filtered), K=10, seeds 101..1010.
"""
import json, os, sys, time, gc

# env hygiene: WorkBuddy host injects ACC_PRODUCT_CONFIG_V3 (~350kB) which
# crashes any code path that rebuilds os.environ (multiprocessing / accelerate).
for _k in list(os.environ.keys()):
    if len(os.environ[_k]) > 8000:
        del os.environ[_k]
os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
EVAL_IDS = [f'T{i:03d}' for i in range(103, 109)]  # r28 cost-adaptive subset
tasks_eval = sorted([t for t in manifest['tasks'] if t['id'] in EVAL_IDS], key=lambda t: t['id'])
print('eval tasks:', len(tasks_eval), tasks_eval[0]['id'] if tasks_eval else 'none', '..', tasks_eval[-1]['id'] if tasks_eval else '')

PREFIX = """You are an expert reading-comprehension assistant. Answer ONLY by quoting exact source spans (verbatim phrases) from the provided material. Do not paraphrase. If the material does not directly contain the answer, say "not stated in the source".

"""
K = 5  # r28 adaptation: CPU 推理成本高，与 #33 K=5 对齐便于比较
SEEDS = [101, 202, 303, 404, 505]

MODELS = [
    ('Llama-3.1-8B-Instruct', r'F:/hf_cache/models/meta-llama--Llama-3.1-8B-Instruct'),
    ('Mistral-7B-Instruct-v0.3', r'F:/hf_cache/models/mistralai--Mistral-7B-Instruct-v0.3'),
]
# r28 替代 cost-vs-value: 仅 6 题子集（RC1 T091-T096，覆盖原始 #33 的 RC 性质；
# T119-T122 不存在）。K=5x 双臂 x 2 模型 = 12 任务 x 5 seeds x 2 arms = 120 推理。
EVAL_IDS_FULL = [f'T{i:03d}' for i in range(103, 123)]
EVAL_IDS_SUBSET = [f'T{i:03d}' for i in range(103, 109)]

def model_ready(p):
    d = Path(p)
    return (d / 'config.json').exists() and any(d.glob('*.safetensors'))

CKPT = root / '_r28_multimodel_ckpt.json'
OUT = root / 'results_r28_multimodel_k10.json'
SUMMARY = root / '_r28_multimodel_summary.json'
ckpt = json.loads(CKPT.read_text(encoding='utf-8')) if CKPT.exists() else {}

def load_model(model_path):
    print(f'Loading {model_path}...', flush=True)
    t0 = time.time()
    # 2026-07-26 策略：6GB VRAM 装不下 8B 4-bit 全 GPU；CPU offload 与 bnb NF4
    # 不兼容（meta tensor 不能 item()）。改用纯 CPU + bnb 8bit（~7GB RAM，
    # 系统有 24GB+）。慢但能跑。Llama chat template 用 apply_chat_template。
    bnb = BitsAndBytesConfig(load_in_8bit=True)
    tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path, quantization_config=bnb, torch_dtype=torch.bfloat16,
        device_map='cpu', trust_remote_code=True)
    model.eval()
    print(f'  loaded in {time.time()-t0:.1f}s (CPU 8-bit, expected 5-10s/sample)', flush=True)
    return model, tok

def gen_one(model, tok, prompt, seed):
    torch.manual_seed(seed)
    # CPU path: tokenizer 输出已经是 cpu tensor，避免不必要的 device move 噪音
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=0.7,
                             top_p=0.9, pad_token_id=tok.eos_token_id, repetition_penalty=1.05)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

for mname, mpath in MODELS:
    if not model_ready(mpath):
        print(f'=== {mname}: weights not ready, skip ===', flush=True)
        continue
    store = ckpt.setdefault(mname, {'base': {}, 'cand': {}})
    done = all(tid in store[arm] and len(store[arm][tid]) == K
               for arm in ('base', 'cand') for tid in [t['id'] for t in tasks_eval])
    if done:
        print(f'=== {mname}: already complete ===')
        continue
    model, tok = load_model(mpath)
    t0 = time.time()
    for arm, prefix in (('cand', PREFIX), ('base', '')):
        for t in tasks_eval:
            if t['id'] in store[arm] and len(store[arm][t['id']]) == K:
                continue
            rows = []
            for seed in SEEDS:
                ans = gen_one(model, tok, prefix + t['prompt'], seed)
                s = score_task(t, ans)
                rows.append({'seed': seed, 'answer': ans[:300], 'score': s,
                             'is_pass': bool(is_pass(s, t)), 'split': t['split']})
            store[arm][t['id']] = rows
            CKPT.write_text(json.dumps(ckpt, ensure_ascii=False), encoding='utf-8')
            print(f'  [{mname}/{arm}] {t["id"]}: {sum(r["is_pass"] for r in rows)}/{K} '
                  f'({time.time()-t0:.0f}s)', flush=True)
    del model, tok
    gc.collect()
    torch.cuda.empty_cache()

OUT.write_text(json.dumps(ckpt, ensure_ascii=False, indent=1), encoding='utf-8')

# ---- per-model analysis ----
def mcnemar_exact(b, c):
    from math import comb
    k = b + c
    if k == 0:
        return 1.0
    lo = min(b, c)
    return min(1.0, sum(comb(k, i) for i in range(0, lo + 1)) / 2 ** k * 2)

summary = {'design': {'K': K, 'seeds': SEEDS, 'tasks': [t['id'] for t in tasks_eval],
                      'weights_provenance': 'unsloth full-precision mirrors of official weights'},
           'models': {}}
for mname, store in ckpt.items():
    b = c = base_p = cand_p = 0
    for t in tasks_eval:
        tid = t['id']
        if tid not in store['base'] or tid not in store['cand']:
            continue
        for rb, rc_ in zip(store['base'][tid], store['cand'][tid]):
            base_p += rb['is_pass']; cand_p += rc_['is_pass']
            if rb['is_pass'] and not rc_['is_pass']: b += 1
            elif rc_['is_pass'] and not rb['is_pass']: c += 1
    n = len(tasks_eval) * K
    summary['models'][mname] = {
        'n_pairs': n, 'base_pass': base_p, 'cand_pass': cand_p, 'b': b, 'c': c,
        'delta': (cand_p - base_p) / n, 'mcnemar_p': mcnemar_exact(b, c),
        'cohens_g': (c - b) / (b + c) if b + c else 0.0}
    print(mname, json.dumps(summary['models'][mname]))
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('summary saved')
