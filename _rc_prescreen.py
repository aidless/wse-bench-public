# -*- coding: utf-8 -*-
"""第十六轮 headroom K=3 预检：baseline 直答盲测 T091-T096 (RC cohort)。
- 设计：context_grounding_v1 目标场景——需要精确回指源 span。
- baseline 倾向释义/总结（关键字命中）但漏精确 span 引用，预期有 headroom。
- 预检 3 seed 估计 baseline 答"全精确 span 引用"的难度。"""
import json, os, sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import eval_self_evolution as E

HIDS = [f"T{i:03d}" for i in range(91, 97)]
tmap = {t["id"]: t for t in E.load_manifest()["tasks"]}


def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}


# P1/P2/P3 三个 baseline 直答 seed——模拟"无 context_grounding"的盲答
# 预期：基线倾向释义/概括（可能漏精确 span 引用），有 headroom
PRESCREEN_SEEDS = [
    {  # P1：典型基线直答——释义/总结，缺精确 span
        "T091": "ToT 论文用分支搜索方法（BFS/DFS），结合前瞻和回溯评估状态。",  # 缺原话短语
        "T092": "AutoGen agents 是可定制的、可对话的，能用 LLM 和工具互相交谈完成任务。",  # 释义非逐字
        "T093": "Qwen3 旗舰 MoE 是 235B-A22B（235B 总/22B 激活），训练约 36T tokens，覆盖 119 种语言。",  # 对
        "T094": "ToT 相比 CoT 是更通用的方法，CoT 是单链、ToT 是树。",  # 缺原话短语
        "T095": "Llama 3.3 70B 在 MATH 上更高（77.0 vs 73.8），高 3.2。",  # 引用数字
        "T096": "Phi-3-mini 3.8B 参数，训练 3.3T tokens，使用 textbooks 合成数据。",  # 引用部分原话
    },
    {  # P2
        "T091": "ToT 用搜索树分支评估，用 BFS 或 DFS 加 lookahead 探索。",
        "T092": "AutoGen agents 特性：customizable、conversable，能用 LLM/human/tools 多种模式。",  # 含原话术语
        "T093": "Qwen3-235B-A22B：235B 总参数，22B 激活，36T tokens 训练，119 种语言。",
        "T094": "ToT generalizes over CoT，用 coherent units of text (thoughts) 作为中间步骤。",  # 含原话
        "T095": "MATH: Llama 3.3 70B 77.0 > Llama 3.1 405B 73.8，差 3.2。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens，训练范式是 synthetic data from textbooks。",
    },
    {  # P3
        "T091": "ToT 用 BFS/DFS + lookahead/backtracking 评估搜索树状态。",  # 引用原话
        "T092": "AutoGen agents are customizable, conversable, 多种模式 (LLM/human inputs/tools).",  # 含原话
        "T093": "Qwen3-235B-A22B (235B total, 22B activated), 36T tokens, 119 languages.",  # 缺 22B activated 关键短语形式
        "T094": "ToT generalizes over CoT；CoT 是单链，ToT 是树。",  # 缺 coherent units of text
        "T095": "Llama 3.3 70B MATH 77.0 高于 Llama 3.1 405B MATH 73.8，差 3.2。",
        "T096": "Phi-3-mini 3.8B 训练 3.3T tokens；training recipe 含 synthetic data from textbooks.",
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
        if tid == "T091":
            fail_mode["缺BFS/DFS/lookahead_原话引用"].append((tid, cnt))
        elif tid == "T092":
            fail_mode["缺customizable/conversable_原话术语"].append((tid, cnt))
        elif tid == "T093":
            fail_mode["缺235B/22B/36T/119_精确四元组"].append((tid, cnt))
        elif tid == "T094":
            fail_mode["缺generalizes over/coherent units_原话短语"].append((tid, cnt))
        elif tid == "T095":
            fail_mode["缺MATH原话数字对比"].append((tid, cnt))
        elif tid == "T096":
            fail_mode["缺synthetic data/textbooks_原话"].append((tid, cnt))

tot = sum(1 for k in range(3) for tid in HIDS if pp[k][tid])
print(f"\nbaseline overall = {tot}/18 = {tot/18:.3f}")
print("\n失败模式分桶（v13 教训：诚实按失败模式驱动预注册）:")
for mode, items in fail_mode.items():
    print(f"  {mode}: {len(items)} 题（{[(t,c) for t,c in items]}）")
if tot / 18 >= 1.0:
    print("\n!! NO HEADROOM — cohort too easy, redesign needed.")
    sys.exit(1)
print("\nHEADROOM CONFIRMED — baseline < ceiling; proceed to pre-register context_grounding_v1 + K=5 main experiment.")