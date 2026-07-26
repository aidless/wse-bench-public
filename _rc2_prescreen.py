"""RC2 headroom prescreen: 3 K=1 baseline attempts on T103-T108, each giving a partial answer.
Records per-task score from is_pass; bucket the failures. Output a headroom report.
"""
import json, os, sys
from pathlib import Path
ROOT = Path(r"F:\test\2026-07-24-08-21-57")
sys.path.insert(0, str(ROOT))
import eval_self_evolution as E

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
RC2 = ["T103","T104","T105","T106","T107","T108"]
PRESEED_ANSWERS = [
    {  # P1: direct attempts
        "T103": "Tree of Thoughts 在 A 段使用分层的树形搜索，并在每层评估节点，引用 B 段说明采用 BFS 或 DFS 进行显式分支评估。",
        "T104": "AutoGen agents 高度可定制、可以多轮对话，使用大模型结合人工和工具组合来运行。",
        "T105": "Phi-3-mini 训练规模约 3.3T tokens，参数量 3.8B；数据包括合成文本与网页。",
        "T106": "Qwen3 用约 36T tokens 训练，支持 /think 思考模式与思考预算，覆盖 119 种语言。",
        "T107": "Llama 3.3 70B 在 MATH 上得分 77.0，Llama 3.1 405B 得分 73.8，因此 3.3 70B 更高。",
        "T108": "GLM-4-9B 上下文为 128K，训练数据约 10T token，相比旧版使用 grouped-query attention，去掉了 PRepLN。",
    },
    {  # P2: partial recall
        "T103": "ToT 树形搜索，分层评估。",
        "T104": "AutoGen agents 可对话与可定制，结合 LLM 和工具。",
        "T105": "Phi-3-mini 3.8B 参数，3.3T tokens 训练，使用教材与网页。",
        "T106": "Qwen3 36T tokens，119 种语言，/think 控制。",
        "T107": "Llama 3.3 70B MATH 77.0 > 3.1 405B 73.8。",
        "T108": "GLM-4-9B 128K 上下文，10T tokens，grouped-query attention。",
    },
    {  # P3: noisy, only some keywords
        "T103": "ToT 在 B 段使用启发式评估。",
        "T104": "AutoGen agents 可定制 (customizable)，可对话。",
        "T105": "Phi-3-mini 3.8B, trained on 3.3T tokens, but training data not fully specified. Evaluation section has 64.7% HumanEval pass. ",
        "T106": "Qwen3 trained on 36T tokens, supports /think, 119 languages. ",
        "T107": "Llama 3.3 70B wins at MATH with 77.0 (vs 3.1 405B 73.8).",
        "T108": "GLM-4-9B context is 128K, training 10T tokens, uses grouped-query attention.",
    },
]
assert len(PRESEED_ANSWERS) == 3
results = []
buckets = {tid: [] for tid in RC2}
for tid in RC2:
    scores = []
    passes = []
    for ans in PRESEED_ANSWERS:
        sc = E.score_task(tmap[tid], ans[tid])
        p = E.is_pass(sc, tmap[tid])
        scores.append(sc)
        passes.append(p)
        buckets[tid].append((round(sc, 3), p))
    results.append({"task_id": tid, "split": tmap[tid]["split"], "passes": sum(passes), "of": len(passes), "scores": scores})

pass_per_task = {tid: sum(p[1] for p in buckets[tid]) for tid in RC2}
total_pass = sum(pass_per_task.values())
total = len(RC2) * len(PRESEED_ANSWERS)
print("RC2 prescreen")
for r in results:
    print(f"  {r['task_id']} [{r['split']:6s}] pass {r['passes']}/{r['of']}, scores={r['scores']}")
print(f"\nheadroom: {total_pass}/{total} = {total_pass/total:.3f}")
print(f"tasks with headroom: {[tid for tid in RC2 if pass_per_task[tid] < 3]}")
print(f"tasks at ceiling:   {[tid for tid in RC2 if pass_per_task[tid] == 3]}")

out = {
    "round": 18,
    "type": "RC2_HEADROOM_PRESCREEN",
    "cohort": "2026Q3-rc2",
    "n_tasks": len(RC2),
    "n_seeds": len(PRESEED_ANSWERS),
    "total_pass": total_pass,
    "total_attempts": total,
    "headroom": round(total_pass / total, 3),
    "per_task": pass_per_task,
    "details": results,
}
(ROOT / "results_rc2_prescreen.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {ROOT}/results_rc2_prescreen.json")
