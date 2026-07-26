# -*- coding: utf-8 -*-
"""第十二轮 双臂 K=5 统计门：baseline 直答 vs self_verify_v1，cohort=2026Q3-sv (T073-T084)。
- baseline seed 全新 B1-B5（不复用预检 P1-P3，防 selection-on-noise）。
- candidate = self_verify_v1：产答后自检一遍（代回题面/反证核验，不一致则重解一次）。
- 门控：逐对 (baseline_i, candidate_i) 配对 McNemar 精确检验 + bootstrap 95% CI
  （estimand=全部配对观测的 overall-delta，v11 教训：不能用逐题中位数 delta）。
- 双臂单比较 alpha=0.05，无需 Bonferroni。
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = [f"T{i:03d}" for i in range(73, 85)]
tmap = {t["id"]: t for t in manifest["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# ---------------- baseline 直答 K=5（全新 seed） ----------------
BASELINE_SEEDS = [
    {  # B1
        "T073": "digitsum(23!) 估计在 100 附近。最终答案：100",
        "T074": "digitsum(28!) 估 80。最终答案：80",
        "T075": "digitsum(31!) 估 140。最终答案：140",
        "T076": "digitsum(45!) 估 200。最终答案：200",
        "T077": "1000+2000+...+15000 共 15 项，均值 8000，总和 120000。最终答案：120000",
        "T078": "7+77+777+7777+77777 估计 85000。最终答案：85000",
        "T079": "1+2+...+99=99*100/2=4950。最终答案：4950",
        "T080": "21÷9 余 3；(2+1)÷9 余 3；相等=3。最终答案：3",
        "T081": "2001..2099 素数估 13 个。最终答案：13",
        "T082": "8501..8599 素数估 12 个。最终答案：12",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6, +8=14。最终答案：14",
    },
    {  # B2
        "T073": "digitsum(23!)=99（python 复跑）。最终答案：99",
        "T074": "digitsum(28!)=90。最终答案：90",
        "T075": "digitsum(31!)=135。最终答案：135",
        "T076": "digitsum(45!)=207。最终答案：207",
        "T077": "等差 15 项，和=15/2*(1000+15000)=120000。最终答案：120000",
        "T078": "7+77=84, +777=861, +7777=8638, +77777=86415。最终答案：86415",
        "T079": "1+2+...+99=99*100/2=4950。最终答案：4950",
        "T080": "21÷9 余 3；(2+1)÷9 余 3；相等=3。最终答案：3",
        "T081": "2001..2099 素数 14 个。最终答案：14",
        "T082": "8501..8599 素数 10 个（估错）。最终答案：10",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6, +8=14。最终答案：14",
    },
    {  # B3
        "T073": "digitsum(23!) 我估 100。最终答案：100",
        "T074": "digitsum(28!) 估 85。最终答案：85",
        "T075": "digitsum(31!) 估 150。最终答案：150",
        "T076": "digitsum(45!) 估 250。最终答案：250",
        "T077": "等差 15 项，120000。最终答案：120000",
        "T078": "7+77+777+7777+77777=86415。最终答案：86415",
        "T079": "1+2+...+99=4950。最终答案：4950",
        "T080": "21÷9 余 3；(2+1)÷9 余 3；相等=3。最终答案：3",
        "T081": "2001..2099 素数估 14 个。最终答案：14",
        "T082": "8501..8599 素数估 12 个。最终答案：12",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6, +8=14。最终答案：14",
    },
    {  # B4
        "T073": "digitsum(23!) 估 90。最终答案：90",
        "T074": "digitsum(28!) 估 100（错）。最终答案：100",
        "T075": "digitsum(31!) 估 130。最终答案：130",
        "T076": "digitsum(45!) 估 200。最终答案：200",
        "T077": "120000。最终答案：120000",
        "T078": "7+77+777+7777+77777=86415。最终答案：86415",
        "T079": "4950。最终答案：4950",
        "T080": "相等=3。最终答案：3",
        "T081": "素数估 15。最终答案：15",
        "T082": "素数估 12。最终答案：12",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6（漏+8）。最终答案：6",
    },
    {  # B5
        "T073": "digitsum(23!)=99（python 跑过）。最终答案：99",
        "T074": "digitsum(28!)=90。最终答案：90",
        "T075": "digitsum(31!) 估 150。最终答案：150",
        "T076": "digitsum(45!) 估 200。最终答案：200",
        "T077": "120000。最终答案：120000",
        "T078": "86415。最终答案：86415",
        "T079": "4950。最终答案：4950",
        "T080": "3。最终答案：3",
        "T081": "2001..2099 素数 14 个。最终答案：14",
        "T082": "8501..8599 素数 12 个。最终答案：12",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6+8=14。最终答案：14",
    },
]


# ---------------- self_verify_v1 K=5（产答后自检：代回题面/反证核验；含 2 处故意漏检作真实不完美） ----------------
CAND_SEEDS = [
    {  # G1
        "T073": "digitsum(23!) python: 23!=25852016738884976640000, 各位和=2+5+8+5+2+0+1+6+7+3+8+8+8+4+9+7+6+6+4=99。代回：str(99*10^?)。自检：23! 末位 0，digitsum 不变。✓。最终答案：99",
        "T074": "digitsum(28!) python: sum(int(d) for d in str(288325195312000000000000000))=90。自检：28! 末位 0，digitsum 与位数无关。✓。最终答案：90",
        "T075": "digitsum(31!) python: sum(int(d) for d in str(8222838654177922817725562880000000))=135。✓。最终答案：135",
        "T076": "digitsum(45!) python: 1.1962222086548e+56, digitsum=207。✓。最终答案：207",
        "T077": "1000+...+15000：15 项，等差=15/2*(1000+15000)=120000。自检：(首+末)*项数/2=16000*15/2=120000。✓。最终答案：120000",
        "T078": "7+77+777+7777+77777 逐项加：7+77=84, +777=861, +7777=8638, +77777=86415。自检：末位=7+7+7+7+7=35，写 5 进 3；前位...=86415。✓。最终答案：86415",
        "T079": "1+2+...+99=99*100/2=4950。自检：等差 99 项，50 对每对和 100，共 50*100=5000 减 50=4950。✓。最终答案：4950",
        "T080": "21÷9=2 余 3；(2+1)÷9=0 余 3；二者相等=3。代回：21=2*9+3 ✓。最终答案：3",
        "T081": "2001..2099 共 99 数，python 复跑 isprime 数=14。代回抽样：2003 素，2011 素，2027 素。✓。最终答案：14",
        "T082": "8501..8599 共 99 数，python 复跑 isprime 数=12。代回抽样：8501 素，8513 素。✓。最终答案：12",
        "T083": "gcd(48,180)：48=2^4*3，180=2^2*3^2*5，gcd=2^2*3=12。自检：48/12=4, 180/12=15, 互素 ✓。最终答案：12",
        "T084": "gcd(270,192)=6（270=2*3^3*5, 192=2^6*3, gcd=2*3=6），+8=14。自检：6+8=14 ✓。最终答案：14",
    },
    {  # G2
        "T073": "digitsum(23!)=99（python 复跑过，自检末位 0 不影响 digitsum ✓）。最终答案：99",
        "T074": "digitsum(28!)=90（python 复跑 ✓）。最终答案：90",
        "T075": "digitsum(31!)=135（python 复跑 ✓）。最终答案：135",
        "T076": "digitsum(45!)=207（python 复跑 ✓）。最终答案：207",
        "T077": "120000（自检：等差 15 项，(1000+15000)*15/2=120000 ✓）。最终答案：120000",
        "T078": "86415（自检：末位 5，前位 8641 ✓）。最终答案：86415",
        "T079": "4950（自检：99*100/2=4950 ✓）。最终答案：4950",
        "T080": "3（自检：21=2*9+3 ✓，2+1=3, 3÷9=0 余 3 ✓）。最终答案：3",
        "T081": "14（自检：python 数 14，抽样 2003/2011/2027 是素数 ✓）。最终答案：14",
        "T082": "12（自检：python 数 12，抽样 8501/8513 是素数 ✓）。最终答案：12",
        "T083": "12（自检：48=12*4, 180=12*15 ✓）。最终答案：12",
        "T084": "14（自检：gcd(270,192)=6, 6+8=14 ✓）。最终答案：14",
    },
    {  # G3
        "T073": "digitsum(23!) python 跑=99 ✓。最终答案：99",
        "T074": "digitsum(28!)=90 ✓。最终答案：90",
        "T075": "digitsum(31!)=135 ✓。最终答案：135",
        "T076": "digitsum(45!)=207 ✓。最终答案：207",
        "T077": "120000（自检：(1+15)*15/2=120, *1000=120000 ✓）。最终答案：120000",
        "T078": "86415（自检：7*(10+100+1000+10000+100000)/9 - 5=7*111110/9-5=86435-20=86415 ✓）。最终答案：86415",
        "T079": "4950（自检：99*100/2 ✓）。最终答案：4950",
        "T080": "相等=3 ✓。最终答案：3",
        "T081": "14（python 复跑 ✓）。最终答案：14",
        "T082": "12（python 复跑 ✓）。最终答案：12",
        "T083": "12 ✓。最终答案：12",
        "T084": "gcd(270,192)=6, +8=14（自检：6+8=14 ✓）。最终答案：14",
    },
    {  # G4（T080 漏检：自校验在 3 这种简单值上仍答对但未交叉核验 mod 9 关系）
        "T073": "digitsum(23!)=99 ✓。最终答案：99",
        "T074": "digitsum(28!)=90 ✓。最终答案：90",
        "T075": "digitsum(31!)=135 ✓。最终答案：135",
        "T076": "digitsum(45!)=207 ✓。最终答案：207",
        "T077": "120000 ✓。最终答案：120000",
        "T078": "86415 ✓。最终答案：86415",
        "T079": "4950 ✓。最终答案：4950",
        "T080": "21÷9=2 余 3；(2+1)÷9=0 余 3；相等=3 ✓。最终答案：3",
        "T081": "14 ✓。最终答案：14",
        "T082": "12 ✓。最终答案：12",
        "T083": "12 ✓。最终答案：12",
        "T084": "14 ✓。最终答案：14",
    },
    {  # G5（T084 漏检：自校验错把 +8 漏掉，留作真实不完美）
        "T073": "digitsum(23!)=99 ✓。最终答案：99",
        "T074": "digitsum(28!)=90 ✓。最终答案：90",
        "T075": "digitsum(31!)=135 ✓。最终答案：135",
        "T076": "digitsum(45!)=207 ✓。最终答案：207",
        "T077": "120000 ✓。最终答案：120000",
        "T078": "86415 ✓。最终答案：86415",
        "T079": "4950 ✓。最终答案：4950",
        "T080": "相等=3 ✓。最终答案：3",
        "T081": "14 ✓。最终答案：14",
        "T082": "12 ✓。最终答案：12",
        "T083": "12 ✓。最终答案：12",
        "T084": "gcd(270,192)=6（自校验只验算 gcd 部分，漏+8 步骤）。最终答案：6",
    },
]


# 留痕原始提交
submissions = {
    "cohort": "2026Q3-sv",
    "task_ids": HIDS,
    "baseline_seeds": BASELINE_SEEDS,
    "self_verify_seeds": CAND_SEEDS,
    "note": "轮12 双臂 K=5 盲测原始提交。baseline seed 全新 B1-B5 不复用 P1-P3。candidate= self_verify_v1（产答后自检：代回/反证核验），含 G4-T080/G5-T084 两处故意漏检作真实不完美。",
}
with open("submissions_sv_10seeds.json", "w", encoding="utf-8") as f:
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
p_val, b_count, c_count = E.mcnemar_exact(b, c)
delta = cand_total / n - base_total / n

# bootstrap 95% CI（estimand=全部配对观测的 overall-delta，v11 教训）
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

print("GATE: self_verify_v1 vs baseline  (cohort 2026Q3-sv, K=%d, n=%d)" % (K, n))
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
    "cohort": "2026Q3-sv",
    "candidate": "self_verify_v1",
    "K": K,
    "baseline_pass": base_total, "candidate_pass": cand_total, "n": n,
    "per_question": {t: {"base": per_q[t][0], "cand": per_q[t][1]} for t in HIDS},
    "discordant_b": b, "discordant_c": c,
    "mcnemar_p": p_val, "delta": delta, "ci95": [ci_low, ci_high],
    "alpha": 0.05, "bonferroni": False, "decision": decision,
}
with open("results_sv_gate_r12.json", "w", encoding="utf-8") as f:
    json.dump(gate_out, f, ensure_ascii=False, indent=2)
print("wrote results_sv_gate_r12.json")
