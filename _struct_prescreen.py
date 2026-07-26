# -*- coding: utf-8 -*-
"""轮11 headroom 预检：baseline 直答 K=3 盲测 2026Q3-struct cohort (T061-T072)。
目的：确认 baseline 在该 cohort 非满分（有真 headroom），否则重设计更难题。
注意：以下 baseline 提交为模型在"无 schema_guard 自校验"下的真实直答输出（含自然超长 summary、
偶发拍平嵌套、微妙枚举误判、多字段漏填等真实倾向），由 harness 盲评。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_self_evolution as E

manifest = E.load_manifest()
HIDS = ["T061", "T062", "T063", "T064", "T065", "T066",
        "T067", "T068", "T069", "T070", "T071", "T072"]

# baseline 直答 K=3（全新 seed，不复用后续实验 seed）
BASELINE_SEEDS = [
    {  # seed P1
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
    {  # seed P2
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
        "T071": '{"verdict":"fail","detail":"需提供具体反例方能成立"}',
        "T072": '{"summary":"RAG通过先检索相关文档再生成答案，缓解大模型幻觉，是知识密集型应用的主流架构。","title":"检索增强生成"}',
    },
    {  # seed P3
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
]

tmap = {t["id"]: t for t in manifest["tasks"]}

def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}

per_q_pass = {tid: 0 for tid in HIDS}
tot = 0
for seed in BASELINE_SEEDS:
    sc = E.score_all(manifest, seed)["scores"]
    pa = passes(sc)
    for tid in HIDS:
        if pa[tid]:
            per_q_pass[tid] += 1
    tot += sum(pa.values())

print("HEADROOM PRESCREEN — baseline 直答 K=3 on 2026Q3-struct (T061-T072)")
print("per-question pass (of 3):")
for tid in HIDS:
    print("  %s: %d/3" % (tid, per_q_pass[tid]))
print("baseline overall pass = %d/%d = %.3f" % (tot, len(HIDS)*3, tot/(len(HIDS)*3.0)))
if tot/(len(HIDS)*3.0) >= 1.0:
    print("!! NO HEADROOM — cohort too easy, redesign needed.")
    sys.exit(1)
else:
    print("HEADROOM CONFIRMED — baseline < ceiling; proceed to pre-register + K=5 experiment.")
