# -*- coding: utf-8 -*-
"""路径 A 启动：从 5 策略栈 K=5 原始提交抽取 SFT 数据。
源：submissions_*.json (production candidate 答) + baseline_5 seeds (baseline 答)。
筛选：仅保留 is_pass(answer) == True 的对 (prompt, answer)。
目标：蒸馏 5 策略栈到一个端到端小模型（QLoRA Qwen2.5-1.5B）。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import eval_self_evolution as E

manifest = E.load_manifest()
tmap = {t["id"]: t for t in manifest["tasks"]}

# 加载所有 5 策略栈 K=5 原始提交
SOURCES = [
    ("hard",        "submissions_hard_15seeds.json",  "tool_arith_seeds",     "tool_arith_v1"),
    ("struct",      "submissions_struct_10seeds.json", "schema_guard_seeds",   "schema_guard_v1"),
    ("self_verify", "submissions_sv_10seeds.json",     "self_verify_seeds",    "self_verify_v1"),
    ("fact",        "submissions_fact_10seeds.json",   "citation_check_seeds", "citation_check_v1"),
]

# 收集所有 candidate 答（5 策略栈 K=5 真跑结果）
sft_pairs = []  # list of {task_id, axis, source, prompt, answer, score, seed_idx}
excluded = []  # 不通过的样本（用于诚实记录）

for src_name, filename, cand_field, cand_label in SOURCES:
    path = os.path.join(ROOT, filename)
    if not os.path.exists(path):
        print(f"  skip {src_name}: {filename} not found")
        continue
    with open(path, encoding="utf-8") as f:
        sub = json.load(f)
    task_ids = sub["task_ids"]
    cand_seeds = sub.get(cand_field)
    if cand_seeds is None:
        print(f"  {src_name}: no field {cand_field}")
        continue

    K = len(cand_seeds)
    axis = manifest["cohorts" if False else "tasks"]  # placeholder
    # 实际：每个 task 的 capability 是其轴
    for k_idx, seed in enumerate(cand_seeds):
        for tid in task_ids:
            ans = seed.get(tid, "")
            t = tmap[tid]
            score = E.score_task(t, ans)
            passed = E.is_pass(score, t)
            if passed:
                sft_pairs.append({
                    "task_id": tid,
                    "axis": t.get("capability", "unknown"),
                    "source_strategy": cand_label,
                    "source_file": filename,
                    "seed_idx": k_idx,
                    "prompt": t["prompt"],
                    "answer": ans,
                    "score": score,
                })
            else:
                excluded.append({
                    "task_id": tid,
                    "source_strategy": cand_label,
                    "seed_idx": k_idx,
                    "score": score,
                    "answer_preview": ans[:60],
                })

# 也从 baseline K=5 收集（适用于 baseline 已通过的题——给模型"普通答"基线）
# baseline 来源：results_*.json 中 scores 字典的 1.0 那些
# 但 baseline 答题文本本身不存储在 scores 字典里（只有分数）。要从原始 baseline seed 拉。
# 简化：本轮只从 production candidate 收集 SFT 数据——baseline 数据用于未来 RFT/DPO。

# 去重：保留每个 (task_id, source_strategy) 的前 1 个 seed（避免过拟合到同一 seed）
seen = set()
unique_sft = []
for p in sft_pairs:
    key = (p["task_id"], p["source_strategy"])
    if key in seen:
        continue
    seen.add(key)
    unique_sft.append(p)

# 按 capability 分组统计
from collections import defaultdict
by_axis = defaultdict(int)
for p in unique_sft:
    by_axis[p["axis"]] += 1

print(f"Total candidate seeds: {len(sft_pairs)}")
print(f"  passed: {len(sft_pairs)}")
print(f"  excluded: {len(excluded)}")
print(f"Unique (task, strategy) pairs: {len(unique_sft)}")
print()
print("By axis (unique pairs):")
for ax, cnt in sorted(by_axis.items()):
    print(f"  {ax}: {cnt}")

# 写 JSONL for SFT
out_jsonl = os.path.join(ROOT, "sft_v90_5strat.jsonl")
with open(out_jsonl, "w", encoding="utf-8") as f:
    for p in unique_sft:
        # 训练格式：{"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]}
        f.write(json.dumps({
            "messages": [
                {"role": "user", "content": p["prompt"]},
                {"role": "assistant", "content": p["answer"]},
            ],
            "task_id": p["task_id"],
            "axis": p["axis"],
            "source_strategy": p["source_strategy"],
        }, ensure_ascii=False) + "\n")

# 写 manifest 摘要
out_manifest = {
    "version": "v90-5strat-sft-v1",
    "created": "2026-07-24",
    "round": 16,
    "n_pairs": len(unique_sft),
    "n_total_candidate_seeds": len(sft_pairs),
    "n_excluded": len(excluded),
    "by_axis": dict(by_axis),
    "source_files": [s[1] for s in SOURCES],
    "strategies": ["selective_retrieval_v1", "tool_arith_v1", "schema_guard_v1", "self_verify_v1", "citation_check_v1"],
    "filter": "is_pass(answer) == True, dedup by (task_id, source_strategy)",
    "jsonl_path": "sft_v90_5strat.jsonl",
    "note": "路径 A 启动数据：从 5 策略 K=5 真跑 candidate 答中抽取 production-quality 答案作为 SFT 目标。蒸馏 5 策略栈到一个端到端小模型。",
}
with open(os.path.join(ROOT, "sft_v90_5strat_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(out_manifest, f, ensure_ascii=False, indent=2)
    f.write("\n")

print()
print(f"wrote {out_jsonl} ({len(unique_sft)} pairs)")
print(f"wrote sft_v90_5strat_manifest.json")