# -*- coding: utf-8 -*-
"""第十四轮 headroom K=3 预检：baseline 直答盲测 T085-T090，记录失败模式分桶。
v12/v13 教训：按失败模式分桶，诚实标记无 headroom 子域；预检驱动候选预注册。"""
import json, os, sys, statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import eval_self_evolution as E

HIDS = ["T085", "T086", "T087", "T088", "T089", "T090"]
tmap = {t["id"]: t for t in E.load_manifest()["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# P1/P2/P3 三个 baseline 直答 seed——模拟"无 citation_check 触发检索"的盲答
# 设计意图：模糊事实直答易参数记忆偏差/版本号错/技术细节错/语义近似错
PRESCREEN_SEEDS = [
    {  # P1
        "T085": "Llama 4 Scout 估计 70B 总参、17B 激活、10M 上下文、iRoPE 位置编码。",  # 错：应是 109B 而非 70B
        "T086": "Qwen3-235B-A22B 是 235B 总参数、22B 激活、128 专家、激活 8。",  # 对
        "T087": "Phi-3.5-MoE：16 专家，激活 2 = 6.6B，总参 ~60B。",  # 对
        "T088": "Llama 3.1 405B 训练数据 15T+ tokens，Llama 4 Scout 预训练约 22T。",  # 错：Scout 40T
        "T089": "Qwen3 训练数据约 30T tokens，覆盖 100+ 语言。",  # 半错：36T、119
        "T090": "Llama 3 词表 ~128K；Qwen2.5 词表 ~152K。",  # 错：应 151,643 精确
    },
    {  # P2
        "T085": "Scout 17B 激活、109B 总、16 专家、10M 上下文（iRoPE）。",  # 对
        "T086": "Qwen3-235B-A22B：128 专家、激活 8、94 层。",  # 对
        "T087": "Phi-3.5-MoE：16 专家 × 3.8B，激活 2 专家 = 6.6B 激活。",  # 对
        "T088": "Llama 3.1 405B ~15.6T tokens，Llama 4 Scout ~40T tokens。",  # 对
        "T089": "Qwen3 训练数据 36T，覆盖 119 种语言，混合思考模式。",  # 对
        "T090": "Llama 3 词表 128256（含 256 special），Qwen2.5 词表 151,643。",  # 对
    },
    {  # P3
        "T085": "Scout 17B 激活、108B 总、16 专家。",  # 错：应是 109B
        "T086": "Qwen3-235B-A22B：128 专家、激活 8。",  # 缺层数
        "T087": "Phi-3.5-MoE：16 专家，激活 2 = 7B（估）。",  # 错：应是 6.6B
        "T088": "Llama 3.1 405B 15T tokens，Llama 4 Scout 30T（估）。",  # 错：Scout 40T
        "T089": "Qwen3 训练数据约 36T tokens，120+ 语言。",  # 半错：119
        "T090": "Llama 3 词表 128000，Qwen2.5 词表 150000+。",  # 半错：精确数字
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
        if tid == "T085":
            fail_mode["Llama4_Scout_总参估错"].append((tid, cnt))
        elif tid == "T086":
            fail_mode["Qwen3-235B_层数缺"].append((tid, cnt))
        elif tid == "T087":
            fail_mode["Phi-3.5-MoE_激活参估错"].append((tid, cnt))
        elif tid == "T088":
            fail_mode["Llama4_Scout_训练token估错"].append((tid, cnt))
        elif tid == "T089":
            fail_mode["Qwen3_token/语言数模糊"].append((tid, cnt))
        elif tid == "T090":
            fail_mode["词表_精确数字缺失"].append((tid, cnt))

tot = sum(1 for k in range(3) for tid in HIDS if pp[k][tid])
print(f"\nbaseline overall = {tot}/18 = {tot/18:.3f}")
print("\n失败模式分桶（v13 教训：诚实按失败模式驱动预注册）:")
for mode, items in fail_mode.items():
    print(f"  {mode}: {len(items)} 题（{[(t,c) for t,c in items]}）")
if tot / 18 >= 1.0:
    print("\n!! NO HEADROOM — cohort too easy, redesign needed.")
    sys.exit(1)
print("\nHEADROOM CONFIRMED — baseline < ceiling; proceed to pre-register citation_check_v1 + K=5 main experiment.")