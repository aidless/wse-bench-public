"""r28 large-n replication of ledger #33 (plan: push power to ~0.8).

Design (2026-07-25):
- Task pool: ALL RC cohorts (2026Q3-rc/rc2/rc3/rc4) = 32 tasks (T091-T132),
  double the clusters of #33 (16) -> better for cluster bootstrap.
- K=15 seeds (101*i, i=1..15), superset convention of #33's 101-505.
- Both arms regenerated fresh (also a sanity reproduction of #33's 16 tasks).
- Pairs: 32*15 = 480 >= 470 target => expected power ~0.8 at half-effect,
  >0.95 at #33's observed effect.
- Checkpoint per (arm, task) to _r28_largen_ckpt.json; safe to re-run.
- Final: paired McNemar (exact), Cohen's g, cluster bootstrap CI (B=20000),
  separate report for held-out 16 tasks never used in #33.
Protocol identical to ._r27_strict_ablation.py (Qwen2.5-3B-Instruct NF4,
temp=0.7, top_p=0.9, max_new_tokens=128, rep_pen=1.05, manual_seed per call).
"""
import json, os, time, sys, math, random
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

root = Path(os.environ.get('WSE_REPO_ROOT', r'__WSE_REPO_ROOT__'))
sys.path.insert(0, str(root))
from eval_self_evolution import score_task, is_pass

os.environ['HF_HOME'] = r'F:/hf_cache/hf_home'
os.environ['BITSANDBYTES_NOWELCOME'] = '1'

manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
tasks_eval = [t for t in manifest['tasks'] if t.get('cohort', '').startswith('2026Q3-rc')]
tasks_eval.sort(key=lambda t: t['id'])
OLD_IDS = {f'T{i:03d}' for i in range(103, 119)}  # #33 original 16
print(f'r28 large-n tasks: {len(tasks_eval)} ({tasks_eval[0]["id"]}..{tasks_eval[-1]["id"]})')

K = 15
SEEDS = [101 * i for i in range(1, K + 1)]

GROUNDING_PREFIX = """You are an expert reading-comprehension assistant. Answer ONLY by quoting exact source spans (verbatim phrases) from the provided material. Do not paraphrase. If the material does not directly contain the answer, say "not stated in the source".

"""

CKPT = root / '_r28_largen_ckpt.json'
OUT = root / 'results_r28_largen_k15.json'
SUMMARY = root / '_r28_largen_summary.json'

ckpt = json.loads(CKPT.read_text(encoding='utf-8')) if CKPT.exists() else {'base': {}, 'cand': {}}

MODEL_PATH = r'F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct/snapshots/master'
print(f'Loading {MODEL_PATH}...')
t0 = time.time()
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
tok = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, quantization_config=bnb,
                                             torch_dtype=torch.bfloat16, device_map='auto',
                                             trust_remote_code=True)
model.eval()
print(f'  loaded in {time.time()-t0:.1f}s')


def gen_one(prompt, seed):
    torch.manual_seed(seed)
    inputs = tok(prompt, return_tensors='pt', truncation=True, max_length=1024).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=0.7,
                             top_p=0.9, pad_token_id=tok.eos_token_id, repetition_penalty=1.05)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


def run_arm(arm_name, prefix):
    store = ckpt[arm_name]
    t_start = time.time()
    for idx, t in enumerate(tasks_eval):
        if t['id'] in store and len(store[t['id']]) == K:
            continue
        full_prompt = prefix + t['prompt']
        rows = []
        for seed in SEEDS:
            ans = gen_one(full_prompt, seed)
            s = score_task(t, ans)
            rows.append({'seed': seed, 'answer': ans, 'score': s,
                         'is_pass': bool(is_pass(s, t)), 'split': t['split']})
        store[t['id']] = rows
        CKPT.write_text(json.dumps(ckpt, ensure_ascii=False), encoding='utf-8')
        n_pass = sum(r['is_pass'] for r in rows)
        el = time.time() - t_start
        print(f'  [{arm_name}] {t["id"]} {n_pass}/{K}  ({idx+1}/{len(tasks_eval)}, {el:.0f}s elapsed)', flush=True)


print('\n=== arm: base (-grounding) ===')
run_arm('base', '')
print('\n=== arm: cand (+grounding) ===')
run_arm('cand', GROUNDING_PREFIX)

OUT.write_text(json.dumps(ckpt, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'saved: {OUT}')

# ---------------- analysis ----------------
def mcnemar_exact(b, c):
    k = b + c
    if k == 0:
        return 1.0
    from math import comb
    lo = min(b, c)
    p = sum(comb(k, i) for i in range(0, lo + 1)) / 2 ** k * 2
    return min(1.0, p)


def analyze(ids, label):
    b = c = a = d = 0
    per_task = {}
    for tid in ids:
        tb = tc = 0
        for rb, rc_ in zip(ckpt['base'][tid], ckpt['cand'][tid]):
            assert rb['seed'] == rc_['seed']
            bp, cp = rb['is_pass'], rc_['is_pass']
            if bp and not cp: b += 1; tb += 1
            elif cp and not bp: c += 1; tc += 1
            elif bp and cp: a += 1
            else: d += 1
        per_task[tid] = {'b': tb, 'c': tc}
    n = len(ids) * K
    p = mcnemar_exact(b, c)
    g = (c - b) / (b + c) if (b + c) else 0.0
    delta = (c - b) / n
    # cluster bootstrap over tasks
    rng = random.Random(20260725)
    B = 20000
    boots = []
    idlist = list(ids)
    for _ in range(B):
        s_b = s_c = 0
        for _ in idlist:
            tid = rng.choice(idlist)
            s_b += per_task[tid]['b']; s_c += per_task[tid]['c']
        boots.append((s_c - s_b) / n)
    boots.sort()
    lo95, hi95 = boots[int(0.025 * B)], boots[int(0.975 * B)]
    frac_le0 = sum(1 for x in boots if x <= 0) / B
    res = {'label': label, 'n_tasks': len(ids), 'n_pairs': n, 'a': a, 'b': b, 'c': c, 'd': d,
           'mcnemar_p': p, 'cohens_g': g, 'delta': delta,
           'boot_ci95': [lo95, hi95], 'boot_p_one_sided': frac_le0,
           'prereg_rule_pass': bool(lo95 > 0)}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res

all_ids = [t['id'] for t in tasks_eval]
old_ids = sorted(OLD_IDS & set(all_ids))
new_ids = sorted(set(all_ids) - OLD_IDS)
summary = {
    'design': {'K': K, 'seeds': SEEDS, 'n_tasks': len(all_ids), 'protocol': 'r27-strict-identical'},
    'full': analyze(all_ids, 'FULL 32 tasks x K=15'),
    'replication_old16': analyze(old_ids, 'OLD 16 tasks (=#33 pool, new seeds)'),
    'heldout_new16': analyze(new_ids, 'HELD-OUT 16 tasks (never used in #33)'),
}
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nsummary saved: {SUMMARY}')
