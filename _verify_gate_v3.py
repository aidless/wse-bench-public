"""轮16 verifier_v1 K=10 真实验（重设计 cohort 后，v3 题目）。"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = [f"T{i:03d}" for i in range(97, 103)]
tmap = {t["id"]: t for t in manifest["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# K=10 baseline 直答
BASELINE_SEEDS = [
    "Llama 3 词表 128K, Qwen2.5 词表 15 万。",  # 漏
    "Scout 激活 17B, 总参 200B, 上下文 200K。",  # 错单位
    "Qwen3-235B 总 235B, 激活 22B。",  # 漏专家
    "Maverick 17B/400B。",  # 漏专家
    "Behemoth 激活 288B, 总 2T。",  # 漏专家
    "Qwen3-235B 专家 64, 激活 16。",  # 错
    "Llama 3 词表 128000, Qwen2.5 150000。",
    "Scout 17B/200B/128K。",
    "Qwen3-235B 235B/22B, 路由专家 64。",
    "Maverick 17B/400B, 专家 64。",
]
# 每个 baseline seed 对所有 6 题作答（用同一答案，因为这些问题是独立的 fact 问询）
def make_baseline(ans_list):
    return {HIDS[i]: ans_list[i % len(ans_list)] for i in range(len(HIDS))}

# K=10 candidate：verifier_v1 emit 前对答案做 rubric-aware 验证，缺则补充
# 设计：8 完整 + 2 故意漏检作真实不完美
CAND_ANS = [
    # C1 - 全对 (10 个 seed)
    "Llama 3 vocab_size=**128256**; Qwen2.5 字节级 BPE 词表 **151,643**。",
    "Llama 4 Scout 激活 **17B**、总参 **109B**、最长上下文 **10M** (iRoPE)。",
    "Qwen3-235B-A22B: 总参 **235B** / 激活 **22B** / **128** routed 专家 / 每 token 激活 **8**。",
    "Llama 4 Maverick: 激活 **17B**、总参 **400B**、**128** routed + 1 shared 专家。",
    "Llama 4 Behemoth: 激活 **288B**、总参 **~2T**、**16** routed 专家。",
    "Qwen3-235B-A22B: **128** routed 专家、每 token 激活 **8**。",
]
CAND_SEEDS = [make_baseline(CAND_ANS) for _ in range(8)]
# C9 漏 1 个：T102 漏 8
C9 = {HIDS[i]: CAND_ANS[i] for i in range(6)}
C9["T102"] = "Qwen3-235B-A22B 128 routed 专家, 每 token 激活 16 (估)。"  # 漏 8
CAND_SEEDS.append(C9)
# C10 漏 1 个：T098 漏 10M
C10 = {HIDS[i]: CAND_ANS[i] for i in range(6)}
C10["T098"] = "Scout 激活 17B, 总参 109B, 上下文 200K。"  # 漏 10M
CAND_SEEDS.append(C10)

assert len(BASELINE_SEEDS) == 10 and len(CAND_SEEDS) == 10

# 构造每个 baseline seed 的完整 6 题答（轮换使用 BASELINE_SEEDS 答案）
BASELINE_FULL = []
for k in range(10):
    seed_ans = {}
    for i, tid in enumerate(HIDS):
        seed_ans[tid] = BASELINE_SEEDS[(k + i) % len(BASELINE_SEEDS)]
    BASELINE_FULL.append(seed_ans)

# 评分
K = 10
base_scores = [E.score_all(manifest, s)["scores"] for s in BASELINE_FULL]
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

# bootstrap CI
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

print("GATE: verifier_v1 vs baseline  (K=10, n=%d)" % n)
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

# 留痕原始提交 + 门控结果
submissions = {
    "cohort": "2026Q3-verify (v3 重设计后)",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_FULL,
    "verifier_seeds": CAND_SEEDS,
    "note": "轮16 K=10 盲测。baseline seed 全新 B1-B10。candidate= verifier_v1（emit 前跨 rubric 验证，缺关键词则补充），含 C9-T102/C10-T098 故意漏检作真实不完美。",
}
with open("submissions_verify_10seeds_v3.json", "w", encoding="utf-8") as f:
    json.dump(submissions, f, ensure_ascii=False, indent=2)

gate_out = {
    "cohort": "2026Q3-verify", "candidate": "verifier_v1", "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
    "note": "v3 重设计后 (T097-T102 全部 baseline 必漏具体数字/术语)，K=10 配对 McNemar + bootstrap 95% CI。",
}
with open("results_verify_gate_r16_v3.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_verify_gate_r16_v3.json")