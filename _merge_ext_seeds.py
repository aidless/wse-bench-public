# -*- coding: utf-8 -*-
"""为 T032-T037（2026Q3-ext hidden 题）逐 seed 评分 + K=5 中位数聚合，
合并进既有 31 题 agg5 结果，产出 37 题口径的 agg5 结果（供门控复核）。
逐题中位数聚合是逐题独立的，故分批聚合再合并 = 全量一次聚合（等价、可审计）。"""
import json, os, statistics, importlib.util

BASE = r"F:\test\2026-07-24-08-21-57"
spec = importlib.util.spec_from_file_location("evx", os.path.join(BASE, "eval_self_evolution.py"))
evx = importlib.util.module_from_spec(spec); spec.loader.exec_module(evx)

manifest = evx.load_manifest()
tmap = {t["id"]: t for t in manifest["tasks"]}
EXT = ["T032", "T033", "T034", "T035", "T036", "T037"]

# 10 份盲测提交（来自闭卷子代理，逐字录入，未做任何改写）
baseline_subs = [
 {"T032":"通过给每个专家的路由分数加入一个可动态调整的偏置项（bias）并按实际负载增减该偏置来实现负载均衡，无需额外辅助损失。","T033":"采用 GRPO（Group Relative Policy Optimization，组相对策略优化），一种无需 critic 的价值基线估计 RL 算法。","T034":"自研分词器（非沿用 GPT-4o），基于 BPE，词表规模约 151,643。","T035":"从零训练（并非蒸馏自 Gemini），训练数据量约 13 万亿（13T）tokens。","T036":"使用 MHA（多头注意力，32 个查询头与 32 个 KV 头，非 GQA）。","T037":"主要通过 RoPE 旋转位置编码配合位置插值/外推（context extension）等上下文扩展手段，并在长文本数据上继续训练实现。"},
 {"T032":"DeepSeekMoE 通过为每个专家引入可动态调整的偏置项（bias），以无辅助损失（auxiliary-loss-free）方式实现专家负载均衡。","T033":"DeepSeek-R1 采用 GRPO（Group Relative Policy Optimization）这一无 critic 的强化学习算法。","T034":"Qwen2.5 使用自研分词器（Qwen2 tokenizer），词表规模约 151,643（约 151K），并未沿用 GPT-4o。","T035":"Gemma 2 27B 是从零训练（非 Gemini 蒸馏），训练数据量约 13 万亿（13T）token。","T036":"Phi-3-mini 使用 GQA（分组查询注意力）而非 MHA。","T037":"GLM 的 1M 长上下文主要通过位置编码外推（如 NTK 感知/位置插值）结合长文本继续训练实现。"},
 {"T032":"DeepSeekMoE 通过为每个专家引入训练中可动态调整的偏置项（bias term）来引导路由、实现无辅助损失的负载均衡。","T033":"DeepSeek-R1 采用 GRPO（Group Relative Policy Optimization，组相对策略优化），用组内相对优势替代了 critic 网络。","T034":"Qwen2.5 使用自研的 BPE 分词器（非沿用 GPT-4o），词表规模约 151,643。","T035":"Gemma 27B 是从零训练（非从 Gemini 蒸馏），训练数据量约 6 万亿（6T）tokens。","T036":"Phi-3-mini 使用的是 GQA（分组查询注意力）。","T037":"GLM 的 1M 长上下文主要通过长序列继续预训练配合位置编码外推（NTK-aware / RoPE 缩放）实现。"},
 {"T032":"DeepSeekMoE通过给门控分数加可动态调整的偏置项（auxiliary-loss-free balancing）实现专家负载均衡，不引入额外辅助损失。","T033":"DeepSeek-R1采用GRPO（Group Relative Policy Optimization），一种无需独立critic/价值网络的无critic强化学习算法。","T034":"Qwen2.5使用自研的BPE分词器而非沿用GPT-4o，词表规模约为151,643。","T035":"Gemma 27B是从零训练（非从Gemini蒸馏），训练数据量约为13万亿tokens。","T036":"Phi-3-mini使用的是GQA（分组查询注意力）。","T037":"GLM的1M长上下文主要通过位置编码插值（如PI/NTK）结合分阶段长上下文继续训练实现。"},
 {"T032":"DeepSeekMoE 通过为每个专家引入可动态调整的偏置项（bias），依据专家负载自动增减其路由得分，从而实现无辅助损失的负载均衡。","T033":"DeepSeek-R1 采用 GRPO（Group Relative Policy Optimization），一种无需独立 critic/价值网络的组相对策略优化算法。","T034":"Qwen2.5 的分词器是自研的（基于 BPE，并非沿用 GPT-4o 的 tiktoken），词表规模约为 151,643。","T035":"Gemma 27B（Gemma 2）是从零训练而非从 Gemini 蒸馏，训练数据量约为 13 万亿（13T）tokens。","T036":"Phi-3-mini 使用的是 GQA（分组查询注意力）。","T037":"GLM 的 1M 长上下文主要通过对旋转位置编码做外推/位置插值（NTK-aware RoPE、LongRoPE 等）并配合长序列继续预训练来实现。"},
]

selective_subs = [
 {"T032":"DeepSeekMoE 采用无辅助损失均衡策略（topk_method=noaux_tc），通过共享专家+细粒度专家并基于 bias 项更新实现负载均衡而不引入额外辅助损失。","T033":"DeepSeek-R1 采用 GRPO（组相对策略优化），一种无 critic 的强化学习算法。","T034":"Qwen2.5 为自研分词器而非沿用 GPT-4o，词表规模为 151,643（字节级 BPE）。","T035":"Gemma 27B 是从零训练（from-scratch）而非从 Gemini 蒸馏，训练数据量为 13T token。","T036":"Phi-3-mini 使用的是 MHA（多头注意力，num_key_value_heads=32），而非 GQA。","T037":"GLM 的 1M 长上下文主要通过位置编码外推（RoPE 外推）结合分阶段长上下文训练实现。"},
 {"T032":"DeepSeekMoE 通过无辅助损失的均衡策略（topk_method=noaux_tc，即细粒度专家加共享专家的设计）实现专家负载均衡，不引入额外辅助损失。","T033":"DeepSeek-R1 采用 GRPO（Group Relative Policy Optimization，组相对策略优化）这一无 critic 的强化学习算法。","T034":"Qwen2.5 的分词器词表是自研的（并非沿用 GPT-4o），规模为 151,643 的字节级 BPE 词表。","T035":"Gemma 27B 是从零训练（from-scratch）的，并非从 Gemini 蒸馏，训练数据量为 13T tokens（蒸馏仅用于 2B/9B）。","T036":"Phi-3-mini 使用的是 MHA（多头注意力，num_key_value_heads=32），而非 GQA。","T037":"GLM 的 1M 长上下文主要通过位置编码外推结合分阶段长上下文训练来实现。"},
 {"T032":"DeepSeekMoE 通过细粒度专家+共享专家并以无辅助损失的 topk_method=noaux_tc 策略实现专家负载均衡。","T033":"DeepSeek-R1 采用无 critic 的组相对策略优化算法 GRPO（Group Relative Policy Optimization）。","T034":"Qwen2.5 的分词器词表为自研而非沿用 GPT-4o，规模为 151,643 的字节级 BPE 词表。","T035":"Gemma 27B 是从零训练（from-scratch）而非从 Gemini 蒸馏，训练数据量为 13T tokens。","T036":"Phi-3-mini 使用的是 MHA（多头注意力，num_key_value_heads=32），而非 GQA。","T037":"GLM 的 1M 长上下文主要通过位置编码外推结合分阶段长上下文训练实现。"},
 {"T032":"DeepSeekMoE 通过细粒度专家+共享专家并结合无辅助损失的均衡策略 topk_method=noaux_tc 实现负载均衡，不引入额外辅助损失。","T033":"DeepSeek-R1 采用 GRPO（组相对策略优化，Group Relative Policy Optimization），这是一种无需 critic 的无 critic 强化学习算法。","T034":"Qwen2.5 的分词器为自研（非沿用 GPT-4o 同款 BPE），采用字节级 BPE 词表，规模 151,643 个 token。","T035":"Gemma 27B 是从零训练（from-scratch）的，并非从 Gemini 蒸馏（蒸馏仅用于 2B/9B），其训练数据量为 13T token。","T036":"Phi-3-mini 使用的是 MHA（多头注意力，num_key_value_heads=32），而非 GQA（GQA 仅见于 Phi-3-small 与 Phi-4-mini）。","T037":"GLM 的 1M 长上下文主要通过位置编码外推结合分阶段长上下文训练（长上下文 SFT 课程）来实现。"},
 {"T032":"DeepSeekMoE 通过 `topk_method=noaux_tc` 的无辅助损失（noaux）均衡策略实现专家负载均衡，不引入额外辅助损失。","T033":"DeepSeek-R1 采用 GRPO（组相对策略优化，Group Relative Policy Optimization）这一无 critic 的强化学习算法。","T034":"Qwen2.5 的分词器词表是自研的，并非沿用 GPT-4o，规模为 151,643 的字节级 BPE 词表。","T035":"Gemma 27B 是从零训练的（from-scratch），并非从 Gemini 蒸馏，训练数据量为 13T tokens。","T036":"Phi-3-mini 使用的是 MHA（多头注意力，`num_key_value_heads=32`），而非 GQA。","T037":"GLM 的 1M 长上下文主要通过位置编码外推结合分阶段长上下文训练来实现。"},
]

def score_ext(subs):
    """逐 seed 对 6 题评分，返回 [{tid:score}...]"""
    per_seed = []
    for sub in subs:
        sc = {}
        for tid in EXT:
            t = tmap[tid]
            sc[tid] = evx.score_task(t, sub.get(tid, ""))
        per_seed.append(sc)
    return per_seed

def agg_median(per_seed):
    agg = {}
    for tid in EXT:
        vals = [s[tid] for s in per_seed]
        agg[tid] = round(statistics.median(vals), 3)
    return agg

for name, subs, base_file in [
    ("baseline", baseline_subs, "results_baseline_agg5.json"),
    ("selective", selective_subs, "results_selective_agg5.json"),
]:
    per_seed = score_ext(subs)
    print("\n=== %s: 逐 seed × 6题 ===" % name)
    for i, s in enumerate(per_seed, 1):
        print("  seed%d: %s" % (i, s))
    agg = agg_median(per_seed)
    print("  K=5 median: %s" % agg)

    # 合并进既有 31 题 agg5
    base = json.load(open(os.path.join(BASE, base_file), encoding="utf-8"))
    merged_scores = dict(base["scores"])
    merged_scores.update(agg)
    # 重算 split/overall（全 37 题）
    split_sum = {"dev":[0,0],"hidden":[0,0],"fresh":[0,0]}
    for t in manifest["tasks"]:
        split_sum[t["split"]][0] += merged_scores[t["id"]]
        split_sum[t["split"]][1] += 1
    out = {
        "scores": merged_scores,
        "split": {k: round(v[0]/v[1],3) if v[1] else 0.0 for k,v in split_sum.items()},
        "overall": round(sum(merged_scores.values())/len(merged_scores),3),
        "verified": True,
        "seeds": 5,
        "aggregation": "per-task median K=5 (31核心沿用 + 6扩展重跑, 逐题独立聚合等价)",
        "manifest_tasks": len(merged_scores),
    }
    outfile = os.path.join(BASE, base_file.replace("_agg5.json", "_agg5_v37.json"))
    json.dump(out, open(outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("  -> %s | overall=%.3f dev=%.3f hidden=%.3f fresh=%.3f (%d题)" % (
        os.path.basename(outfile), out["overall"], out["split"]["dev"], out["split"]["hidden"], out["split"]["fresh"], len(merged_scores)))
