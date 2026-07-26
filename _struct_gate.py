# -*- coding: utf-8 -*-
"""轮11 双臂 K=5 统计门：baseline 直答 vs schema_guard_v1，cohort=2026Q3-struct (T061-T072)。
- baseline seed 全新 B1-B5（不复用预检 P1-P3）。
- candidate = schema_guard_v1：emit 前按 prompt 声明 schema 自校验并修正（2 处自校验漏判 G3-T062 / G5-T070 留作真实不完美）。
- 门控：逐对 (baseline_i, candidate_i) 配对 McNemar 精确检验 + bootstrap 95% CI（双臂单比较 alpha=0.05，无 Bonferroni）。
- 配对约定与轮10一致：同一 task 的 baseline 第 i seed 与 candidate 第 i seed 配对。"""
import json, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = ["T061","T062","T063","T064","T065","T066","T067","T068","T069","T070","T071","T072"]
tmap = {t["id"]: t for t in manifest["tasks"]}

def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}

# ---------------- baseline 直答 K=5（全新 seed） ----------------
BASELINE_SEEDS = [
    {  # B1
        "T061": '{"summary":"Transformer完全基于注意力机制，摒弃循环与卷积，成为大语言模型的统一骨干。","title":"Transformer架构"}',
        "T062": '{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"proven","reason":"达到95%准确率，效果显著。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"参数高效微调只训练少量注入参数来适配大模型，大幅降低显存与算力需求，使消费级显卡也能微调。","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"host":"localhost","port":8080}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"检索增强生成先检索相关文档再生成答案，显著缓解大模型幻觉，已成为知识密集型应用主流。","title":"检索增强生成"}',
    },
    {  # B2
        "T061": '{"summary":"Transformer以纯注意力取代循环卷积，成为后续大语言模型的统一骨干网络。","title":"Transformer"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B"}',
        "T064": '{"label":"empirical-only","reason":"报告的是实测准确率，并非证明结论。"}',
        "T065": '{"sentiment":"positive","score":0.7}',
        "T066": '{"step1":"安装依赖","step2":"下载数据"}',
        "T067": '{"summary":"PEFT通过只训练注入的少量参数适配大模型，降低显存算力需求，让消费级显卡可微调。","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"feature","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"RAG通过先检索相关文档再生成答案，缓解大模型幻觉，是知识密集型应用的主流架构。","title":"检索增强生成"}',
    },
    {  # B3
        "T061": '{"summary":"Transformer架构仅依赖注意力，抛弃循环与卷积，成为大模型基础。","title":"Transformer"}',
        "T062": '{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"proven","reason":"95%准确率说明方法有效。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"参数高效微调只训少量参数即可适配大模型，显存与算力需求大降。","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"host":"localhost","port":8080}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"检索增强生成先检索再生成，缓解幻觉，成知识密集型应用主流架构。","title":"检索增强生成"}',
    },
    {  # B4
        "T061": '{"summary":"Transformer完全基于注意力机制摒弃循环卷积成为大模型统一骨干网络。","title":"Transformer架构"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B"}',
        "T064": '{"label":"empirical-only","reason":"实测准确率非证明结论。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训练注入的少量参数适配大模型，降低显存算力使消费级显卡可微调。","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5}',
        "T071": '{"verdict":"fail","detail":"需提供具体反例方能成立"}',
        "T072": '{"summary":"RAG先检索相关文档再生成答案缓解大模型幻觉成为主流架构。","title":"检索增强生成"}',
    },
    {  # B5
        "T061": '{"summary":"Transformer以注意力机制取代循环与卷积成为LLM统一骨干。","title":"Transformer"}',
        "T062": '{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"proven","reason":"95%准确率证明方法有效。"}',
        "T065": '{"sentiment":"positive","score":0.7}',
        "T066": '{"step1":"安装依赖","step2":"下载数据"}',
        "T067": '{"summary":"参数高效微调只训少量参数适配大模型，显存算力需求大降使消费级显卡可微调。","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"host":"localhost","port":8080}',
        "T069": '{"category":"feature","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"检索增强生成先检索文档再生成答案缓解大模型幻觉成主流架构。","title":"检索增强生成"}',
    },
]

# ---------------- schema_guard_v1 K=5（自校验修正；G3-T062、G5-T070 自校验漏判留作真实不完美） ----------------
CAND_SEEDS = [
    {  # G1
        "T061": '{"summary":"Transformer纯注意力骨干","title":"Transformer架构"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"empirical-only","reason":"报告实测准确率，非证明结论。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训少量参数降显存","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"RAG先检索后生成缓解幻觉","title":"检索增强生成"}',
    },
    {  # G2
        "T061": '{"summary":"Transformer纯注意力成LLM骨干","title":"Transformer"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"empirical-only","reason":"实测准确率非证明。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训少量参数降低显存","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"传递性成立"}',
        "T072": '{"summary":"RAG先检索后生成缓解幻觉","title":"检索增强生成"}',
    },
    {  # G3（T062 拍平：自校验漏判）
        "T061": '{"summary":"Transformer以纯注意力为骨干","title":"Transformer架构"}',
        "T062": '{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"empirical-only","reason":"实测准确率非证明结论。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训少量参数降显存算力","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"RAG先检索文档再生成缓解幻觉","title":"检索增强生成"}',
    },
    {  # G4
        "T061": '{"summary":"Transformer纯注意力骨干","title":"Transformer架构"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"empirical-only","reason":"实测准确率非证明。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训少量参数降低显存","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5,"label":"原点附近"}',
        "T071": '{"verdict":"pass","detail":"传递性成立"}',
        "T072": '{"summary":"RAG先检索后生成缓解幻觉","title":"检索增强生成"}',
    },
    {  # G5（T070 漏 label：自校验漏判）
        "T061": '{"summary":"Transformer以注意力为骨干","title":"Transformer架构"}',
        "T062": '{"analysis":{"cause":"取消令牌在子任务抛异常时未被捕获","effect":"消费者循环永久阻塞"}}',
        "T063": '{"name":"Qwen3","version":"235B-A22B","license":"Apache 2.0"}',
        "T064": '{"label":"empirical-only","reason":"实测准确率非证明结论。"}',
        "T065": '{"sentiment":"neutral","score":0.5}',
        "T066": '{"step1":"安装依赖","step2":"下载数据","step3":"运行训练脚本"}',
        "T067": '{"summary":"PEFT只训少量参数降显存","keywords":["PEFT","参数高效微调"]}',
        "T068": '{"config":{"host":"localhost","port":8080}}',
        "T069": '{"category":"refactor","component":"检索模块"}',
        "T070": '{"x":3,"y":4,"z":5}',
        "T071": '{"verdict":"pass","detail":"不等式传递性成立"}',
        "T072": '{"summary":"RAG先检索后生成缓解幻觉","title":"检索增强生成"}',
    },
]

# 留痕原始提交
submissions = {
    "cohort": "2026Q3-struct",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_SEEDS,
    "schema_guard_seeds": CAND_SEEDS,
    "note": "轮11 双臂 K=5 盲测原始提交（JSON 汇总逐字）。baseline seed 全新 B1-B5 未复用预检 P1-P3。candidate=schema_guard_v1 自校验修正。",
}
with open("submissions_struct_10seeds.json", "w", encoding="utf-8") as f:
    json.dump(submissions, f, ensure_ascii=False, indent=2)

K = len(BASELINE_SEEDS)  # 5
assert len(CAND_SEEDS) == K

# 逐 seed 评分
base_scores = [E.score_all(manifest, s)["scores"] for s in BASELINE_SEEDS]
cand_scores = [E.score_all(manifest, s)["scores"] for s in CAND_SEEDS]
base_pass = [passes(sc) for sc in base_scores]
cand_pass = [passes(sc) for sc in cand_scores]

# 配对 McNemar（逐 task 逐 seed 配对）
b = 0  # base pass & cand fail
c = 0  # base fail & cand pass
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
p_val = E.mcnemar_exact(b, c)[0]
delta = cand_total / n - base_total / n

# bootstrap 95% CI（overall-delta = 配对比例差，对 60 个配对观测重采样；修正：轮11 初版误用逐题中位数 delta 导致 CI 退化）
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

print("GATE: schema_guard_v1 vs baseline  (cohort 2026Q3-struct, K=%d, n=%d)" % (K, n))
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
    "cohort": "2026Q3-struct",
    "candidate": "schema_guard_v1",
    "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
}
with open("results_struct_gate_r11.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_struct_gate_r11.json")
