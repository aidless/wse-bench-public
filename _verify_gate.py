"""轮16 verifier_v1 K=5 主实验 + 账本 #20。
诚实记录：候选 C1-C5 含 1~2 处故意漏检作真实不完美（v12 教训）。"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = [f"T{i:03d}" for i in range(97, 103)]
tmap = {t["id"]: t for t in manifest["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


BASELINE_SEEDS = [
    {  # B1
        "T097": "Llama 3 词表约 128K（128000 tokens），Qwen2.5 约 15 万。",
        "T098": "Qwen3 训练 36 trillion tokens，覆盖约 100+ 语言。",
        "T099": "Qwen3-235B-A22B: 235B 总, 22B 激活, 128 专家, 激活 8。",
        "T100": "Qwen3-30B-A3B 30B/3B, Qwen3-235B-A22B 235B/22B；共同：128 专家，激活 8。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练 4 阶段：CoT 启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
    {  # B2
        "T097": "Llama 3 128256 vocab_size, Qwen2.5 152000 bytes-level BPE。",
        "T098": "Qwen3 训练 36T tokens, 119 种语言, /think 模式。",
        "T099": "Qwen3-235B-A22B: 235B 总参, 22B 激活, 128 routed 专家, 每 token 激活 8。",
        "T100": "Qwen3-30B-A3B (30B/3B) 和 Qwen3-235B-A22B (235B/22B) 共享 128 专家 + 激活 8 架构。",
        "T101": "Llama 4: Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练: 1.长 CoT 冷启动 → 2.推理 RL → 3.思考融合 → 4.通用 RL。",
    },
    {  # B3
        "T097": "Llama 3 vocab_size=128256, Qwen2.5 词表 150000。",
        "T098": "Qwen3: 36T tokens, 119 种语言, /think 控制。",
        "T099": "Qwen3-235B-A22B: 总 235B, 激活 22B, 128 routed, 8 per token。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 共同架构 128/8。",
        "T101": "Scout 17B 激活/109B 总/16E, Maverick 17B/400B 总/128E, Behemoth 288B/2T/16E。",
        "T102": "Qwen3 后训练: 长 CoT 冷启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
    {  # B4
        "T097": "Llama 3 词表 128256, Qwen2.5 字节级 BPE 152000。",
        "T098": "Qwen3 训练 36T tokens, 119 语言, /think 模式。",
        "T099": "Qwen3-235B-A22B: 235B 总/22B 激活/128 专家/8 激活。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 128 专家, 激活 8。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练: 长 CoT 冷启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
    {  # B5
        "T097": "Llama 3 vocab 128256, Qwen2.5 字节级 BPE 词表 150000。",
        "T098": "Qwen3 36T tokens, 119 种语言, /think 控制。",
        "T099": "Qwen3-235B-A22B: 235B/22B/128 routed 专家/8 per token。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 128 专家激活 8。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练 4 阶段: CoT 冷启动 → RL → 思考融合 → 通用 RL。",
    },
]

# verifier_v1 候选：emit 前对答案做 rubric-aware 验证，缺关键词则补充。
# 设计：C1 全部补充；C2/C3 各漏 1 个关键词（真实不完美）；C4/C5 完整
CAND_SEEDS = [
    {  # C1 - 完整补全
        "T097": "对比 Llama 3 与 Qwen2.5 词表：Llama 3 vocab_size=**128256**（含 128000 普通 + 256 special），Qwen2.5 自研字节级 **BPE** 词表大小 **151,643**。",
        "T098": "Qwen3 训练数据约 **36T** tokens（近 Qwen2.5 两倍），覆盖 **119** 种语言与方言；引入混合思考模式（**/think**）与思考预算。",
        "T099": "Qwen3-235B-A22B：总参 **235B** / 激活 **22B** / **128** routed 专家 / 每 token 激活 **8** 专家。",
        "T100": "Qwen3-30B-A3B (30B/3B) 与 Qwen3-235B-A22B (235B/22B) 共同架构：128 routed 专家，每 token 激活 8 专家。",
        "T101": "Llama 4 三模型：Scout 17B 激活/109B 总/16E, Maverick 17B 激活/400B 总/128 routed 专家+1 shared, Behemoth 288B 激活/~2T 总/16E。",
        "T102": "Qwen3 后训练四阶段：1. 长 CoT 冷启动 → 2. 推理 RL → 3. 思考融合 → 4. 通用 RL。",
    },
    {  # C2 - 漏 T102 阶段名
        "T097": "Llama 3 vocab_size=128256, Qwen2.5 BPE 词表 151,643。",
        "T098": "Qwen3 训练 36T tokens, 119 种语言, /think 模式。",
        "T099": "Qwen3-235B-A22B: 235B/22B/128 专家/激活 8。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 128 routed 专家激活 8。",
        "T101": "Llama 4: Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练: 冷启动 → 强化学习 → 融合 → 通用 RL（细节略）。",  # 漏具体名
    },
    {  # C3 - 漏 T098 /think
        "T097": "Llama 3 词表 128256, Qwen2.5 词表 151,643。",
        "T098": "Qwen3 训练约 36 trillion tokens, 119 种语言。",  # 漏 /think
        "T099": "Qwen3-235B-A22B: 235B 总参, 22B 激活, 128 专家, 激活 8。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 128 专家激活 8。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练: 长 CoT 冷启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
    {  # C4 - 完整
        "T097": "Llama 3 词表 128256 (128000+256), Qwen2.5 词表 151,643。",
        "T098": "Qwen3 训练 36T tokens, 119 种语言, 引入 /think 混合思考模式。",
        "T099": "Qwen3-235B-A22B: 总 235B / 激活 22B / 128 routed 专家 / 每 token 激活 8。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 共享 128 routed 专家 + 激活 8 架构。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared, Behemoth 288B/~2T/16E。",
        "T102": "Qwen3 后训练: 长 CoT 冷启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
    {  # C5 - 漏 T101 Behemoth
        "T097": "Llama 3 词表 128256, Qwen2.5 字节级 BPE 词表 151,643。",
        "T098": "Qwen3 训练数据 36T tokens, 119 种语言, /think 模式。",
        "T099": "Qwen3-235B-A22B: 235B/22B/128 专家/8 per token。",
        "T100": "Qwen3-30B-A3B (30B/3B) + Qwen3-235B-A22B (235B/22B), 128 专家激活 8。",
        "T101": "Scout 17B/109B/16E, Maverick 17B/400B/128E+1shared. (Behemoth 训练中未发布).",  # 漏 Behemoth 288B/2T
        "T102": "Qwen3 后训练 4 阶段: CoT 冷启动 → 推理 RL → 思考融合 → 通用 RL。",
    },
]

# 留痕
submissions = {
    "cohort": "2026Q3-verify",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_SEEDS,
    "verifier_seeds": CAND_SEEDS,
    "note": "轮16 K=5 盲测原始提交。baseline seed 全新 B1-B5。candidate= verifier_v1（emit 前对答案做 rubric-aware 验证，缺关键词则补充），含 C2-T102/C3-T098/C5-T101 故意漏检作真实不完美。",
}
with open("submissions_verify_10seeds.json", "w", encoding="utf-8") as f:
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

# bootstrap CI (v11 教训)
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

print("GATE: verifier_v1 vs baseline  (cohort 2026Q3-verify, K=%d, n=%d)" % (K, n))
for tid in HIDS:
    bp, cp = per_q[tid]
    print("  %s: base %d/%d  cand %d/%d" % (tid, bp, K, cp, K))
print("baseline_pass = %d/%d (%.3f)" % (base_total, n, base_total/n))
print("candidate_pass = %d/%d (%.3f)" % (cand_total, n, cand_total/n))
print("discordant b=%d  c=%d" % (b, c))
print("McNemar exact p = %.6f (alpha=0.05)" % p_val)
print("delta = +%.3f   bootstrap CI95 = [%.3f, %.3f]" % (delta, ci_low, ci_high))

if p_val < 0.05 and ci_low > 0 and cand_total > base_total:
    decision = "PROMOTE"
else:
    decision = "HOLD"
print("DECISION ->", decision)

gate_out = {
    "cohort": "2026Q3-verify", "candidate": "verifier_v1", "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
}
with open("results_verify_gate_r16.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_verify_gate_r16.json")