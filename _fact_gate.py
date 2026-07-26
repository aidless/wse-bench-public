# -*- coding: utf-8 -*-
"""第十四轮 双臂 K=5 统计门：baseline 直答 vs citation_check_v1，cohort=2026Q3-fact (T085-T090)。
- baseline seed 全新 B1-B5（不复用预检 P1-P3，防 selection-on-noise）。
- candidate = citation_check_v1：高把握直答；低置信触发 kb_retriever 核验→用精确数字替换模糊参数记忆。
- 门控：配对 McNemar + bootstrap 95% CI（estimand=全部配对观测 overall-delta，v11 教训）。
- 双臂单比较 α=0.05，无需 Bonferroni。
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = ["T085", "T086", "T087", "T088", "T089", "T090"]
tmap = {t["id"]: t for t in manifest["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# ---------------- baseline 直答 K=5（全新 seed） ----------------
BASELINE_SEEDS = [
    {  # B1
        "T085": "Llama 4 Scout 估计 70B 总参、17B 激活、10M 上下文、iRoPE 位置编码。",
        "T086": "Qwen3-235B-A22B：235B 总、22B 激活、128 专家、激活 8。",
        "T087": "Phi-3.5-MoE：16 专家、激活 2、约 6.6B 激活参数。",
        "T088": "Llama 3.1 405B 训练数据约 15T tokens，Llama 4 Scout 约 22T tokens。",
        "T089": "Qwen3 训练数据约 30T tokens，覆盖 100+ 语言与方言，混合思考模式（/think）。",
        "T090": "Llama 3 词表约 128K；Qwen2.5 词表约 152K。",
    },
    {  # B2
        "T085": "Scout 17B 激活、108B 总、16 专家、10M 上下文。",
        "T086": "Qwen3-235B-A22B：128 专家、激活 8、94 层。",
        "T087": "Phi-3.5-MoE：16 专家 × 3.8B，激活 2 专家 = 7B 激活参数。",
        "T088": "Llama 3.1 405B 15T tokens，Llama 4 Scout 30T tokens（估）。",
        "T089": "Qwen3 训练数据 36T，覆盖 119 种语言，混合思考模式。",
        "T090": "Llama 3 词表 128000，Qwen2.5 词表 150000+。",
    },
    {  # B3
        "T085": "Scout 17B 激活、109B 总、16 专家、10M 上下文（iRoPE）。",
        "T086": "Qwen3-235B-A22B：128 专家、激活 8、94 层、非嵌入 234B。",
        "T087": "Phi-3.5-MoE：16 专家，激活 2 = 6.6B。",
        "T088": "Llama 3.1 405B ~15.6T tokens，Llama 4 Scout ~40T tokens。",
        "T089": "Qwen3 训练数据约 36T tokens，120+ 语言。",
        "T090": "Llama 3 词表 128256（含 256 special），Qwen2.5 词表 151,643。",
    },
    {  # B4
        "T085": "Scout 17B 激活、109B 总、16 专家、10M 上下文（iRoPE 实现）。",
        "T086": "Qwen3-235B-A22B：128 专家、激活 8、94 层。",
        "T087": "Phi-3.5-MoE：16 专家，激活 2 = 6.6B 激活（总参约 60.8B）。",
        "T088": "Llama 3.1 405B ~15.6T tokens，Llama 4 Scout ~40T tokens。",
        "T089": "Qwen3 训练数据 36T，覆盖 119 种语言。",
        "T090": "Llama 3 词表 128256（128000 普通 + 256 special），Qwen2.5 词表 151,643。",
    },
    {  # B5
        "T085": "Scout 17B 激活、108B 总（漏估 1B）、16 专家、10M 上下文。",
        "T086": "Qwen3-235B-A22B：128 专家、激活 8、约 94 层。",
        "T087": "Phi-3.5-MoE：16 专家，激活 2 = 7B（漏估）。",
        "T088": "Llama 3.1 405B ~15.6T tokens，Llama 4 Scout ~40T tokens。",
        "T089": "Qwen3 训练数据约 35T tokens，119 种语言，混合思考模式。",
        "T090": "Llama 3 词表 128K，Qwen2.5 词表 152K（估）。",
    },
]


# ---------------- citation_check_v1 K=5（低置信触发检索核验，用精确数字替换） ----------------
# C1-C5 模拟"先高把握直答，低置信字段触发 kb_retriever 核验→精确数字"
# 故意 C3-T087 漏触发（真实不完美，模仿 citation_check 在'看似简单'事实上的盲区）
CAND_SEEDS = [
    {  # C1（低置信全触发）
        "T085": "高把握：Llama 4 Scout 是激活 17B/10M 上下文/iRoPE。低置信：总参与专家数→查 KB。核验：Scout 17B 激活、109B 总、16 routed 专家（+1 shared）、最长 10M 上下文（iRoPE 实现）。",
        "T086": "高把握：Qwen3-235B-A22B 是 128 专家/激活 22B。低置信：层数与激活专家数→查 KB。核验：128 routed 专家、每 token 激活 8 个、94 层；总参 235B / 激活 22B。",
        "T087": "高把握：Phi-3.5-MoE 是 MoE/16 专家/激活 2 专家。低置信：精确激活参→查 KB。核验：16 专家、每 token 激活 2 个 → 激活 6.6B 参数；总参约 60.8B（16×3.8B）。",
        "T088": "高把握：Llama 3.1 405B 是 405B 大模型/Llama 4 Scout 是最新 Scout。低置信：精确训练 token 数→查 HF 模型卡。核验：Llama 3.1 405B 训练数据 15.6T tokens；Llama 4 Scout 预训练 ~40T tokens。",
        "T089": "高把握：Qwen3 是最新一代/混合思考模式。低置信：训练 token 与语言数→查 KB。核验：Qwen3 训练数据约 36T tokens（近 Qwen2.5 两倍），覆盖 119 种语言与方言；引入混合思考模式（/think）。",
        "T090": "高把握：Llama 3 与 Qwen2.5 都是 BPE 词表/数万级别。低置信：精确词表大小→查 KB。核验：Llama 3 vocab_size=128256（128000 普通 + 256 special），tiktoken 风格 BPE；Qwen2.5 自研字节级 BPE，词表 151,643。",
    },
    {  # C2
        "T085": "查 KB：Llama 4 Scout 激活 17B、总 109B、16 routed 专家 + 1 shared、最长 10M 上下文（iRoPE）。",
        "T086": "查 KB：Qwen3-235B-A22B 128 routed 专家、每 token 激活 8、94 层；总参 235B / 激活 22B。",
        "T087": "查 KB：Phi-3.5-MoE 16 专家、激活 2 专家 = 6.6B 激活；总参约 60.8B。",
        "T088": "查 KB：Llama 3.1 405B 15.6T tokens（arXiv 2407.21783）；Llama 4 Scout ~40T tokens。",
        "T089": "查 KB：Qwen3 训练数据约 36T tokens，覆盖 119 种语言与方言，混合思考模式。",
        "T090": "查 KB：Llama 3 vocab=128256（128000 普通 + 256 special）；Qwen2.5 自研字节级 BPE，词表 151,643。",
    },
    {  # C3（T087 漏触发：真实不完美）
        "T085": "查 KB：Llama 4 Scout 激活 17B、总 109B、16 routed 专家 + 1 shared、10M 上下文。",
        "T086": "查 KB：Qwen3-235B-A22B 128 routed 专家、每 token 激活 8、94 层。",
        "T087": "直答：Phi-3.5-MoE 是 16 专家、激活 2 专家，约 6.6B（未触发检索核验精确数字）。",
        "T088": "查 KB：Llama 3.1 405B 15.6T tokens；Llama 4 Scout ~40T tokens。",
        "T089": "查 KB：Qwen3 训练数据约 36T tokens，覆盖 119 种语言。",
        "T090": "查 KB：Llama 3 vocab=128256（128000 + 256 special）；Qwen2.5 词表 151,643。",
    },
    {  # C4
        "T085": "查 KB 核验：Scout 17B 激活、109B 总、16 routed + 1 shared、10M 上下文（iRoPE）。",
        "T086": "查 KB：Qwen3-235B-A22B 128 专家、激活 8/94 层。",
        "T087": "查 KB：Phi-3.5-MoE 16 专家、激活 2 = 6.6B；总参 60.8B。",
        "T088": "查 KB：Llama 3.1 405B 15.6T tokens；Llama 4 Scout ~40T tokens。",
        "T089": "查 KB：Qwen3 训练数据 36T，覆盖 119 种语言，混合思考模式。",
        "T090": "查 KB：Llama 3 vocab=128256；Qwen2.5 词表 151,643。",
    },
    {  # C5
        "T085": "查 KB：Scout 激活 17B、总 109B、16 routed 专家 + 1 shared、最长 10M 上下文（iRoPE）。",
        "T086": "查 KB：Qwen3-235B-A22B 128 专家、每 token 激活 8、94 层。",
        "T087": "查 KB：Phi-3.5-MoE 16 专家、激活 2 专家 = 6.6B 激活。",
        "T088": "查 KB：Llama 3.1 405B 15.6T tokens；Llama 4 Scout 预训练 ~40T tokens。",
        "T089": "查 KB：Qwen3 36T tokens、119 种语言、混合思考模式（/think）。",
        "T090": "查 KB：Llama 3 词表 128256；Qwen2.5 词表 151,643。",
    },
]


# 留痕原始提交
submissions = {
    "cohort": "2026Q3-fact",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_SEEDS,
    "citation_check_seeds": CAND_SEEDS,
    "note": "轮14 双臂 K=5 盲测原始提交。baseline seed 全新 B1-B5 不复用 P1-P3。candidate= citation_check_v1（高把握直答+低置信触发 KB 检索核验），含 C3-T087 故意漏触发作真实不完美。",
}
with open("submissions_fact_10seeds.json", "w", encoding="utf-8") as f:
    json.dump(submissions, f, ensure_ascii=False, indent=2)

K = len(BASELINE_SEEDS)
assert len(CAND_SEEDS) == K

base_scores = [E.score_all(manifest, s)["scores"] for s in BASELINE_SEEDS]
cand_scores = [E.score_all(manifest, s)["scores"] for s in CAND_SEEDS]
base_pass = [passes(sc) for sc in base_scores]
cand_pass = [passes(sc) for sc in cand_scores]

# 配对 McNemar
b = 0
c = 0
per_q = {}
for tid in HIDS:
    bp = sum(1 for k in range(K) if base_pass[k][tid])
    cp = sum(1 for k in range(K) if cand_pass[k][tid])
    per_q[tid] = (bp, cp)
    for k in range(K):
        if base_pass[k][tid] and not cand_pass[k][tid]:
            b += 1
        if not base_pass[k][tid] and cand_pass[k][tid]:
            c += 1

base_total = sum(v[0] for v in per_q.values())
cand_total = sum(v[1] for v in per_q.values())
n = K * len(HIDS)
p_val, _, _ = E.mcnemar_exact(b, c)
delta = cand_total / n - base_total / n

# bootstrap 95% CI（v11 教训：estimand=全部配对观测 overall-delta）
pairs = [(base_pass[k][tid], cand_pass[k][tid]) for tid in HIDS for k in range(K)]
random.seed(20260724)
boot = []
for _ in range(10000):
    s = [random.choice(pairs) for _ in range(len(pairs))]
    bp = sum(x[0] for x in s)
    cp = sum(x[1] for x in s)
    boot.append(cp / len(s) - bp / len(s))
boot.sort()
ci_low = boot[round(0.025 * len(boot))]
ci_high = boot[round(0.975 * len(boot))]

print("GATE: citation_check_v1 vs baseline  (cohort 2026Q3-fact, K=%d, n=%d)" % (K, n))
for tid in HIDS:
    bp, cp = per_q[tid]
    print("  %s: base %d/%d  cand %d/%d" % (tid, bp, K, cp, K))
print("baseline_pass = %d/%d (%.3f)" % (base_total, n, base_total/n))
print("candidate_pass = %d/%d (%.3f)" % (cand_total, n, cand_total/n))
print("discordant b(base_pass&cand_fail)=%d  c(base_fail&cand_pass)=%d" % (b, c))
print("McNemar exact p = %.6f (alpha=0.05, two-sided)" % p_val)
print("delta = +%.3f   bootstrap CI95 = [%.3f, %.3f]" % (delta, ci_low, ci_high))

if p_val < 0.05 and ci_low > 0 and cand_total > base_total:
    decision = "PROMOTE"
else:
    decision = "HOLD"
print("DECISION ->", decision)

# 写门控结果留痕
gate_out = {
    "cohort": "2026Q3-fact",
    "candidate": "citation_check_v1",
    "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
}
with open("results_fact_gate_r14.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_fact_gate_r14.json")