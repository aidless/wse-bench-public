# -*- coding: utf-8 -*-
"""第十六轮 双臂 K=5 统计门：baseline 直答 vs context_grounding_v1，cohort=2026Q3-rc (T091-T096)。
- baseline seed 全新 B1-B5（不复用预检 P1-P3，防 selection-on-noise）。
- candidate = context_grounding_v1：抽取前先定位并引用源文本 span，答案须可回指原文，减少臆造。
- 门控：配对 McNemar + bootstrap 95% CI（estimand=全部配对观测 overall-delta，v11 教训）。
- 双臂单比较 α=0.05，无需 Bonferroni。
- 含 1~2 处故意漏检作真实不完美（v12 教训）。
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = [f"T{i:03d}" for i in range(91, 97)]
tmap = {t["id"]: t for t in manifest["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# ---------------- baseline 直答 K=5（全新 seed） ----------------
# 设计：基线直答倾向释义/总结（可能漏精确 span 引用）
BASELINE_SEEDS = [
    {  # B1
        "T091": "ToT 用分支搜索（BFS/DFS）结合 lookahead/backtracking 评估状态。",  # 缺原话 'branching at each step' 短语
        "T092": "AutoGen agents 可定制、可对话，用 LLM/human/tools 互相交谈。",
        "T093": "Qwen3-235B-A22B：235B 总参数、22B 激活，训练约 36T tokens，覆盖 119 种语言。",
        "T094": "ToT generalizes over CoT，是树搜索方法，CoT 是单链推理。",  # 缺 'coherent units of text'
        "T095": "MATH 上 Llama 3.3 70B（77.0）> Llama 3.1 405B（73.8），高 3.2。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens，含 textbooks 合成数据。",
    },
    {  # B2
        "T091": "ToT 用 BFS 或 DFS 搜索，加 lookahead 评估。",
        "T092": "AutoGen agents customizable, conversable, 用 LLM/human/tools 多种模式。",
        "T093": "Qwen3 旗舰 235B-A22B：235B 总、22B 激活、36T tokens、119 种语言。",
        "T094": "ToT 比 CoT 通用，用 thoughts 作中间步骤。",  # 缺 'coherent units of text'
        "T095": "Llama 3.3 70B 在 MATH 77.0 高于 Llama 3.1 405B 73.8，差 3.2。",
        "T096": "Phi-3-mini 3.8B，3.3T tokens，synthetic data from textbooks。",
    },
    {  # B3
        "T091": "ToT 用 BFS/DFS 加 lookahead 评估。",  # 缺具体短语
        "T092": "AutoGen agents are customizable, conversable。",
        "T093": "Qwen3-235B-A22B (235B total, 22B activated), 36T tokens, 119 languages.",
        "T094": "ToT 是 CoT 通用化版本，CoT 单链，ToT 树。",  # 缺原话
        "T095": "Llama 3.3 70B MATH 77.0 vs Llama 3.1 405B MATH 73.8，差 3.2。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens。",
    },
    {  # B4
        "T091": "ToT 用 BFS 或 DFS + lookahead/backtracking 评估 states。",
        "T092": "AutoGen agents customizable, conversable, 多种模式 (LLMs/human inputs/tools).",
        "T093": "Qwen3-235B-A22B：235B 总、22B 激活、36T tokens 训练、119 种语言。",
        "T094": "ToT generalizes over Chain of Thought，用 coherent units of text (thoughts)。",
        "T095": "MATH: Llama 3.3 70B 77.0 > Llama 3.1 405B 73.8，差 3.2。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens，训练范式含 synthetic data from textbooks。",
    },
    {  # B5
        "T091": "ToT 用 BFS/DFS + lookahead 评估搜索树状态。",  # 缺 backtracking
        "T092": "AutoGen agents are customizable, conversable。",
        "T093": "Qwen3-235B-A22B (235B total parameters, 22B activated), 36T tokens, 119 languages。",
        "T094": "ToT 是 CoT 通用化版本，CoT 单链推理。",
        "T095": "Llama 3.3 70B 在 MATH 77.0 高于 Llama 3.1 405B 73.8。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens，含 synthetic data from textbooks。",
    },
]


# ---------------- context_grounding_v1 K=5（先定位源 span 再答 + 逐字引用） ----------------
# 含 1~2 处故意漏检作真实不完美
CAND_SEEDS = [
    {  # C1：完整 span 引用
        "T091": "摘要原话：ToT 'uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states'。先定位 span：搜索策略短语，引用之。",
        "T092": "摘要原话：AutoGen agents 'are customizable, conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools ... they can converse with each other to accomplish tasks'。",
        "T093": "摘要原话：Qwen3-235B-A22B (235B total parameters, 22B activated) ... trained on approximately 36T tokens, covering 119 languages and dialects。",
        "T094": "摘要原话：ToT 'generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts) that serve as intermediate steps toward problem solving'。",
        "T095": "模型卡原话：Llama 3.1 405B MATH 73.8 (0-shot CoT); Llama 3.3 70B MATH 77.0 (0-shot CoT)。Llama 3.3 高 3.2。",
        "T096": "摘要原话：Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks and curated web content。",
    },
    {  # C2
        "T091": "定位 span：「uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states」。",
        "T092": "定位 span：「AutoGen agents are customizable, conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools」。",
        "T093": "定位 span：「Qwen3-235B-A22B (235B total parameters, 22B activated) ... trained on approximately 36T tokens, covering 119 languages and dialects」。",
        "T094": "定位 span：「ToT generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts)」。",
        "T095": "模型卡原话：「Llama 3.1 405B MATH 73.8」「Llama 3.3 70B MATH 77.0」。Llama 3.3 70B 高 3.2。",
        "T096": "定位 span：「Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks」。",
    },
    {  # C3
        "T091": "回指源文本：摘要原文「uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states」表明 ToT 用 BFS/DFS+lookahead/backtracking 评估状态。",
        "T092": "回指源文本：摘要原话「AutoGen agents are customizable, conversable」。",
        "T093": "回指源文本：摘要原话「Qwen3-235B-A22B (235B total parameters, 22B activated) ... 36T tokens, 119 languages」。",
        "T094": "回指源文本：摘要原话「ToT generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts)」。",
        "T095": "回指源文本：HF 模型卡原话「Llama 3.1 405B MATH 73.8」「Llama 3.3 70B MATH 77.0」。Llama 3.3 70B 高 3.2。",
        "T096": "回指源文本：摘要原话「Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks」。",
    },
    {  # C4（T092 漏检 customizable 短语：真实不完美）
        "T091": "回指源 span：「uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states」。",
        "T092": "回指源 span：「AutoGen agents are conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools」。",  # 漏 customizable
        "T093": "回指源 span：「Qwen3-235B-A22B (235B total parameters, 22B activated) ... 36T tokens, 119 languages」。",
        "T094": "回指源 span：「ToT generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts)」。",
        "T095": "回指源 span：「Llama 3.1 405B MATH 73.8」「Llama 3.3 70B MATH 77.0」。Llama 3.3 70B 高 3.2。",
        "T096": "回指源 span：「Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks」。",
    },
    {  # C5
        "T091": "回指摘要原文：「uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states」——ToT 用 BFS/DFS+前瞻/回溯。",
        "T092": "回指摘要原文：「AutoGen agents are customizable, conversable」。",
        "T093": "回指摘要原文：「Qwen3-235B-A22B (235B total parameters, 22B activated) ... 36T tokens, 119 languages」。",
        "T094": "回指摘要原文：「ToT generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts)」。",
        "T095": "回指模型卡原文：「Llama 3.1 405B MATH 73.8」「Llama 3.3 70B MATH 77.0」。Llama 3.3 70B 高 3.2。",
        "T096": "回指摘要原文：「Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks」。",
    },
]


# 留痕原始提交
submissions = {
    "cohort": "2026Q3-rc",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_SEEDS,
    "context_grounding_seeds": CAND_SEEDS,
    "note": "轮16 双臂 K=5 盲测原始提交。baseline seed 全新 B1-B5 不复用 P1-P3。candidate= context_grounding_v1（先定位源 span 再答 + 逐字引用），含 C4-T092 故意漏 customizable 短语作真实不完美。",
}
with open("submissions_rc_10seeds.json", "w", encoding="utf-8") as f:
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

print("GATE: context_grounding_v1 vs baseline  (cohort 2026Q3-rc, K=%d, n=%d)" % (K, n))
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
    "cohort": "2026Q3-rc",
    "candidate": "context_grounding_v1",
    "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
}
with open("results_rc_gate_r16.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_rc_gate_r16.json")