"""轮16 verifier_v1 K=3 headroom 预检 v3（cohort 重设计后）。"""
import json, os, sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import eval_self_evolution as E

HIDS = [f"T{i:03d}" for i in range(97, 103)]
tmap = {t["id"]: t for t in E.load_manifest()["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# 重设计: 6题全部 baseline 必漏具体数字/术语
PRESCREEN_SEEDS = [
    {  # P1 - 漏具体数字/术语
        "T097": "Llama 3 词表约 128K, Qwen2.5 词表约 15 万。",  # 漏 128256, 151,643
        "T098": "Llama 4 Scout 激活约 17B, 总参约 200B, 上下文 200K。",  # 错单位
        "T099": "Qwen3-235B-A22B 总参 235B, 激活 22B。",  # 漏 128/8
        "T100": "Llama 4 Maverick 激活 17B, 总参 400B。",  # 漏 128 专家
        "T101": "Llama 4 Behemoth 激活 288B, 总参 2T。",  # 漏 16 专家
        "T102": "Qwen3-235B-A22B 专家数 64, 激活 16。",  # 错
    },
    {  # P2 - 全错
        "T097": "Llama 3 词表 128000, Qwen2.5 词表 150000。",  # 都漏
        "T098": "Llama 4 Scout 激活 17B, 总参 200B, 上下文 128K。",  # 错
        "T099": "Qwen3-235B-A22B 总 235B, 激活 22B, 路由专家 64。",  # 错
        "T100": "Llama 4 Maverick 激活 17B, 总 400B, 专家 64。",  # 错
        "T101": "Llama 4 Behemoth 激活 288B, 总 2T, 专家 32。",  # 错
        "T102": "Qwen3-235B-A22B 专家 64, 激活 16。",  # 错
    },
    {  # P3 - 漏几个
        "T097": "Llama 3 vocab 128256, Qwen2.5 词表 152000。",  # Qwen2.5 错
        "T098": "Llama 4 Scout 激活 17B, 总 109B, 上下文 128K。",  # 上下文错
        "T099": "Qwen3-235B-A22B 235B/22B/128 专家, 每 token 激活 16。",  # 8 错
        "T100": "Llama 4 Maverick 17B/400B, 128 专家+1 shared。",  # 对
        "T101": "Llama 4 Behemoth 288B/2T, 16 专家。",  # 对
        "T102": "Qwen3-235B-A22B 128 专家, 8 激活。",  # 对
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
        fail_mode[tid] = cnt

tot = sum(1 for k in range(3) for tid in HIDS if pp[k][tid])
print(f"\nbaseline overall = {tot}/18 = {tot/18:.3f}")
print(f"headroom 题目数: {sum(1 for tid in HIDS if any(c<3 for c in [pp[k][tid] for k in range(3)]))}/6")
if tot / 18 >= 1.0:
    print("\n!! NO HEADROOM")
    sys.exit(1)
print("\nHEADROOM CONFIRMED — proceed to K=10 main (more power).")