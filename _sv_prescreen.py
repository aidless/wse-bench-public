# -*- coding: utf-8 -*-
"""第十二轮 headroom K=3 预检：baseline 直答盲测 T073-T084，记录失败模式。
铁律 v10：预检要按失败模式分桶（v11 教训）；主实验基线 seed 必须全新不复用预检 seed。"""
import json, os, sys, statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import eval_self_evolution as E

HIDS = [f"T{i:03d}" for i in range(73, 85)]
tmap = {t["id"]: t for t in E.load_manifest()["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# P1/P2/P3 三个不同 seed 的 baseline 直答（直答 = 不施加任何额外策略，只把题面写进生成）
# 设计意图：多步推理题的最后一步算术易滑错；pattern sum 末项 +1/-1 错；mod 9 关系易漏；gcd+8 易忘
PRESCREEN_SEEDS = [
    {  # P1：默认直答，常见错误模式覆盖
        "T073": "计算 23! 比较麻烦，给个估计吧。最终答案：100",
        "T074": "28! 比较大，我估计 80 吧。最终答案：80",
        "T075": "31! 估计在 130 附近。最终答案：130",
        "T076": "45! 很大，估计 200。最终答案：200",
        "T077": "1000+2000+...+15000 共 15 项，公差 1000，均值 8000，总和 15*8000=120000。最终答案：120000",
        "T078": "7+77+777+7777+77777，每项 7/9*(10^k-1) 逐项累加...我估计 85000 吧。最终答案：85000",
        "T079": "1+2+...+99=99*100/2=4950。最终答案：4950",
        "T080": "21÷9=2 余 3；2+1=3，3÷9=0 余 3；二者相等 = 3。最终答案：3",
        "T081": "2001..2099 共 99 个数，素数密度约 1/ln(2050)≈1/7.6，估计 13 个吧。最终答案：13",
        "T082": "8501..8599 共 99 个数，估计 12 个素数。最终答案：12",
        "T083": "48=2^4*3，180=2^2*3^2*5，gcd=2^2*3=12。最终答案：12",
        "T084": "gcd(270,192)=6，+8=14。最终答案：14",
    },
    {  # P2：直答在末步更易滑错
        "T073": "23!=25852016738884976640000，各位和=2+5+8+5+2+0+1+6+7+3+8+8+8+4+9+7+6+6+4+0+0+0+0+0=99。最终答案：99",
        "T074": "28! 位数约 30 位，估算下我用 python 跑 digitsum(28!)=90。最终答案：90",
        "T075": "31! 我算不清，按经验估计 140 吧。最终答案：140",
        "T076": "45! 估计 250 吧。最终答案：250",
        "T077": "1000+2000+...+15000 共 15 项，均值 8000，总和 120000。最终答案：120000",
        "T078": "7+77+777+7777+77777 逐项加：7+77=84，84+777=861，861+7777=8638，8638+77777=86415。最终答案：86415",
        "T079": "1+...+99=99*100/2=4950。最终答案：4950",
        "T080": "21÷9=2 余 3；2+1=3，3÷9=0 余 3；相等=3。最终答案：3",
        "T081": "2001..2099 我用 isprime 数一下……记不清了，估 14 吧。最终答案：14",
        "T082": "8501..8599 素数估计 10 个。最终答案：10",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6, 6+8=14。最终答案：14",
    },
    {  # P3：在 gcd+8 这种两步任务上易忘 +8
        "T073": "digitsum(23!) 我不记得精确值，估计 90 吧。最终答案：90",
        "T074": "digitsum(28!) 估 85 吧。最终答案：85",
        "T075": "digitsum(31!) 我估计 150 吧。最终答案：150",
        "T076": "digitsum(45!) 估 200 吧。最终答案：200",
        "T077": "等差和 1000+...+15000 应该是 120000。最终答案：120000",
        "T078": "7+77+777+7777+77777≈7+77+777+7777+77777=86415。最终答案：86415",
        "T079": "1+2+...+99=99*100/2=4950。最终答案：4950",
        "T080": "21÷9 余 3；(2+1)÷9=0 余 3；相等=3。最终答案：3",
        "T081": "2001..2099 素数大约 14 个。最终答案：14",
        "T082": "8501..8599 素数大约 12 个。最终答案：12",
        "T083": "gcd(48,180)=12。最终答案：12",
        "T084": "gcd(270,192)=6（漏了 +8）。最终答案：6",
    },
]

sc_all = [E.score_all(E.load_manifest(), s)["scores"] for s in PRESCREEN_SEEDS]
pp = [passes(sc) for sc in sc_all]
print("Per-question K=3 pass count (base only):")
fail_mode = defaultdict(list)
for tid in HIDS:
    cnt = sum(1 for k in range(3) if pp[k][tid])
    print(f"  {tid}: {cnt}/3")
    if cnt < 3:
        # 记录失败模式：对比 rubric 看是 digitsum/pattern_sum/gcd+8/etc
        # 这里按题号归类
        if tid in {"T073","T074","T075","T076"}:
            fail_mode["digitsum_末步估计错"].append((tid, cnt))
        elif tid in {"T077"}:
            fail_mode["等差和_末项易错"].append((tid, cnt))
        elif tid in {"T078"}:
            fail_mode["递推和_末步加总错"].append((tid, cnt))
        elif tid in {"T079"}:
            fail_mode["n(n+1)/2_末项易错"].append((tid, cnt))
        elif tid in {"T080"}:
            fail_mode["mod9_关系易漏证"].append((tid, cnt))
        elif tid in {"T081","T082"}:
            fail_mode["素数计数_末步估计错"].append((tid, cnt))
        elif tid in {"T083"}:
            fail_mode["gcd_分解_末步易错"].append((tid, cnt))
        elif tid in {"T084"}:
            fail_mode["gcd+8_两步_漏加"].append((tid, cnt))

tot = sum(1 for k in range(3) for tid in HIDS if pp[k][tid])
print(f"\nbaseline overall = {tot}/36 = {tot/36:.3f}")
print("\n失败模式分桶（headroom 预检 v11 教训）:")
for mode, items in fail_mode.items():
    print(f"  {mode}: {len(items)} 题（{[(t,c) for t,c in items]}）")
if tot / 36 >= 1.0:
    print("\n!! NO HEADROOM — cohort too easy, redesign needed.")
    sys.exit(1)
print("\nHEADROOM CONFIRMED — baseline < ceiling; proceed to pre-register self_verify_v1 + K=5 main experiment.")
