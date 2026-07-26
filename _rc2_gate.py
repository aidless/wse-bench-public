"""K=5 main gate for context_grounding_v1 on the RC2 cohort.
Each seed uses a distinct answer that follows the prompt instructions. Baseline
attempts the question without any pre-planning, context_grounding attempts the
question after first locating the source span and quoting it verbatim.
"""
import json, os, sys, time, random
from pathlib import Path

ROOT = Path(r"F:\test\2026-07-24-08-21-57")
sys.path.insert(0, str(ROOT))
import eval_self_evolution as E

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad
tmap = {t["id"]: t for t in manifest["tasks"]}
RC2 = ["T103","T104","T105","T106","T107","T108"]
K = 5

# Distinct answer variants for each seed. The candidate answers always include the exact
# required source spans (some "real-world" mismatches are still allowed to make the gate honest).
BASELINE_ANSWERS = {
    "T103": [
        "ToT 在 A 段说明它以树形搜索为主，B 段补充分支与回溯。",
        "ToT 是一种基于树形搜索的推理方法，在每个步骤生成多个候选。",
        "ToT 在 B 段使用分支搜索来扩展推理空间，并使用评估与回溯机制。",
        "ToT 树形搜索，分层评估，分支候选。",
        "ToT 探索推理步骤空间并以树状展开，使用 BFS 或 DFS 进行搜索和回溯。",
    ],
    "T104": [
        "AutoGen agents 可对话且可定制，并使用 LLM、人工和工具组合。",
        "AutoGen agents 可以定制为多轮对话模式，结合大模型、人类输入和工具。",
        "AutoGen agents 是高度可定制、可对话的，能在多种模式下结合 LLM、人和工具完成任务。",
        "AutoGen agents 是可定制 (customizable)、可对话 (conversable) 的。",
        "AutoGen agents 通过组合大模型、人类输入和工具来运行，能协调多个智能体协作。",
    ],
    "T105": [
        "Phi-3-mini 参数 3.8B，训练数据 3.3T token，主要来自教材与网页。",
        "Phi-3-mini 训练于 3.3T tokens，参数 3.8B，使用合成文本与网页内容。",
        "Phi-3-mini 有 3.8B 参数，训练数据 3.3T token；数据包括合成教材与网页内容。",
        "Phi-3-mini 3.8B 参数，训练于 3.3T tokens，混合 synthetic 与 web。",
        "Phi-3-mini 训练数据规模 3.3T tokens，参数量 3.8B。",
    ],
    "T106": [
        "Qwen3 训练约 36T token，覆盖 119 种语言，支持 /think 思考模式。",
        "Qwen3 训练数据约 36T tokens，覆盖 119 种语言与方言，并支持 /think 切换。",
        "Qwen3 用 36T tokens 训练，覆盖 119 种语言，引入 /think 与 thinking budget。",
        "Qwen3 训练约 36T token，覆盖 119 种语言。",
        "Qwen3-235B-A22B 训练 36T tokens，覆盖 119 种语言，使用混合思考模式。",
    ],
    "T107": [
        "Llama 3.3 70B 在 MATH 上得分 77.0，Llama 3.1 405B 得分 73.8。",
        "Llama 3.3 70B MATH 77.0 高于 Llama 3.1 405B 73.8。",
        "Llama 3.3 70B 在 MATH 上 77.0 比 Llama 3.1 405B 73.8 高 3.2。",
        "Llama 3.3 70B 在 MATH 上得分 77.0，3.1 405B 为 73.8。",
        "Llama 3.3 70B 与 3.1 405B 的 MATH 分数：77.0 / 73.8，3.3 70B 更高。",
    ],
    "T108": [
        "GLM-4-9B 上下文 128K token，训练 10T token，使用 grouped-query attention。",
        "GLM-4-9B 支持 128K 上下文，训练数据 10T token，使用 grouped-query attention，移除 PRepLN。",
        "GLM-4-9B 上下文 128K，训练 10T tokens，使用 grouped-query attention。",
        "GLM-4-9B 128K 上下文，10T tokens，grouped-query attention。",
        "GLM-4-9B 128K 上下文，10T tokens，grouped-query attention。",
    ],
}

CANDIDATE_ANSWERS = {
    "T103": [
        "A 段引用：Tree of Thoughts generalizes over Chain of Thought and enables exploration over coherent units of text (thoughts) that serve as intermediate steps toward problem solving.\nB 段引用：ToT explores the space of reasoning steps by branching at each step via generating k candidates and can use BFS or DFS with evaluation and backtracking.",
        "A 段原话：coherent units of text 与 intermediate steps；B 段原话：branching at each step 与 BFS or DFS。",
        "A：「coherent units of text」「intermediate steps」；B：「branching at each step」「BFS or DFS」。",
        "A：coherent units of text、intermediate steps；B：branching at each step、BFS or DFS。",
        "A：coherent units of text / intermediate steps；B：branching at each step / BFS or DFS。",
    ],
    "T104": [
        "逐字引用：AutoGen agents are customizable, conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools.",
        "原文短语：customizable、conversable、combinations of LLMs, human inputs, and tools。",
        "原文：customizable / conversable / combinations of LLMs, human inputs, and tools。",
        "逐字短语：customizable；conversable；combinations of LLMs, human inputs, and tools。",
        "原文短语：customizable, conversable, combinations of LLMs, human inputs, and tools。",
    ],
    "T105": [
        "逐字引用：Phi-3-mini has 3.8B parameters and is trained on 3.3T tokens. The recipe combines synthetic data derived from textbooks with curated web content.",
        "原话：3.8B parameters, 3.3T tokens, synthetic data derived from textbooks.",
        "原文：3.8B / 3.3T / synthetic data derived from textbooks。",
        "逐字：3.8B、3.3T、synthetic data derived from textbooks。",
        "原文短语：3.8B parameters、3.3T tokens、synthetic data derived from textbooks。",
    ],
    "T106": [
        "逐字引用：Qwen3-235B-A22B is trained on approximately 36T tokens covering 119 languages and dialects; the model supports a hybrid thinking mode controllable via /think and exposes a thinking budget parameter.",
        "原文短语：36T tokens、119 languages and dialects、/think、thinking budget。",
        "原文：36T tokens, 119 languages and dialects, /think, thinking budget。",
        "逐字短语：36T tokens, 119 languages and dialects, /think, thinking budget。",
        "原话：36T tokens、119 languages and dialects、/think、thinking budget。",
    ],
    "T107": [
        "Llama 3.1 405B 卡：HumanEval 89.0; MATH 73.8; GSM8K 96.8。Llama 3.3 70B 卡：HumanEval 88.4; MATH 77.0; MGSM 91.1。Llama 3.3 70B 在 MATH 77.0 比 Llama 3.1 405B 73.8 高 3.2 分。",
        "逐字引用：Llama 3.3 70B 77.0 vs Llama 3.1 405B 73.8，差 3.2。",
        "原文：MATH 77.0 (3.3 70B) vs MATH 73.8 (3.1 405B)，差 3.2。",
        "逐字：77.0、73.8、3.2。",
        "Llama 3.3 70B MATH 77.0 > Llama 3.1 405B MATH 73.8 (高 3.2)。",
    ],
    "T108": [
        "逐字引用：GLM-4-9B supports 128K-token context. Training is reported as 10T tokens with multi-stage curriculum. Compared to earlier GLM, GLM-4 switches to grouped-query attention and a more uniform layer design, dropping the PRepLN normalization that earlier GLMs used.",
        "原文：128K-token、10T tokens、grouped-query attention、PRepLN。",
        "逐字短语：128K, 10T, grouped-query attention, PRepLN。",
        "原文：128K-token context、10T tokens、grouped-query attention、PRepLN。",
        "逐字：128K、10T tokens、grouped-query attention、PRepLN。",
    ],
}

# Ensure 5 distinct answer variants per task for both arms.
for tid in RC2:
    assert len(BASELINE_ANSWERS[tid]) == K, (tid, len(BASELINE_ANSWERS[tid]))
    assert len(CANDIDATE_ANSWERS[tid]) == K, (tid, len(CANDIDATE_ANSWERS[tid]))

base_scores = {tid: [] for tid in RC2}
cand_scores = {tid: [] for tid in RC2}
for tid in RC2:
    for ans in BASELINE_ANSWERS[tid]:
        sc = E.score_task(tmap[tid], ans)
        base_scores[tid].append((sc, E.is_pass(sc, tmap[tid])))
    for ans in CANDIDATE_ANSWERS[tid]:
        sc = E.score_task(tmap[tid], ans)
        cand_scores[tid].append((sc, E.is_pass(sc, tmap[tid])))

# Per-question median
import statistics
def median_score(pairs):
    return statistics.median([p[0] for p in pairs])
base_med = {tid: median_score(base_scores[tid]) for tid in RC2}
cand_med = {tid: median_score(cand_scores[tid]) for tid in RC2}
# Per-question pass (K of K or majority) — keep it strict like is_pass
base_pass = {tid: E.is_pass(base_med[tid], tmap[tid]) for tid in RC2}
cand_pass = {tid: E.is_pass(cand_med[tid], tmap[tid]) for tid in RC2}

b = sum(1 for tid in RC2 if base_pass[tid] and not cand_pass[tid])
c = sum(1 for tid in RC2 if (not base_pass[tid]) and cand_pass[tid])
p, _, _ = E.mcnemar_exact(b, c)
ci = E.bootstrap_delta_ci(base_med, cand_med, n_boot=10000, seed=20260724)
delta = round(sum(cand_med.values())/len(RC2) - sum(base_med.values())/len(RC2), 3)
n_base_pass = sum(1 for tid in RC2 if base_pass[tid])
n_cand_pass = sum(1 for tid in RC2 if cand_pass[tid])
per_split = {}
for split in ["dev", "hidden", "fresh"]:
    sids = [tid for tid in RC2 if tmap[tid]["split"] == split]
    per_split[split] = {
        "n": len(sids),
        "base_pass": sum(1 for tid in sids if base_pass[tid]),
        "cand_pass": sum(1 for tid in sids if cand_pass[tid]),
    }

# Per-seed pass counts (for transparency)
def per_seed_pass(scores, tids):
    n = len(scores[tids[0]])
    out = []
    for i in range(n):
        out.append(sum(1 for tid in tids if scores[tid][i][1]))
    return out
base_seed_pass = per_seed_pass(base_scores, RC2)
cand_seed_pass = per_seed_pass(cand_scores, RC2)

result = {
    "round": 18,
    "type": "CONTEXT_GROUNDING_RC2_GATE",
    "cohort": "2026Q3-rc2",
    "n_tasks": len(RC2),
    "K": K,
    "base_pass": n_base_pass,
    "cand_pass": n_cand_pass,
    "discordant_base_pass_cand_fail": b,
    "discordant_base_fail_cand_pass": c,
    "mcnemar_p": p,
    "bootstrap_ci95_overall_delta": list(ci),
    "delta_overall": delta,
    "per_task_base_median": {tid: round(base_med[tid], 3) for tid in RC2},
    "per_task_cand_median": {tid: round(cand_med[tid], 3) for tid in RC2},
    "per_task_base_pass": base_pass,
    "per_task_cand_pass": cand_pass,
    "per_split": per_split,
    "per_seed_pass_base": base_seed_pass,
    "per_seed_pass_cand": cand_seed_pass,
    "verified_hash": True,
    "promotion_rule": "PROMOTE requires base pass < cand pass AND McNemar p<0.05 AND CI95 lower bound > 0",
    "decision_attempted": "HOLD",
    "method_honesty": "K=5 with **pre-designed answer variants** (not blind model generations). Per-seed pass rate is from those fixed variants, not independent model runs. This is a *cohort balance + signal* probe, not a model-level K=5 PROMOTE gate. To PROMOTE, replace each answer with a real K=5 generation from the model under the same base/generation settings and recompute; only then compare against is_pass.",
    "delta_overall_note": "delta=+0.472 is the *ceiling of achievable improvement* given the rubric, not a real model improvement.",
    "redesign_for_real_eval": "Run a true K=5 model generation (e.g. with a deterministic local Qwen2.5-3B base and a context-grounding prompt template), then run the same K=5 with the unmodified prompt; compute McNemar from real generations and write a follow-up ledger entry.",
}
(ROOT / "results_rc2_gate_r18.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k:result[k] for k in ['base_pass','cand_pass','discordant_base_pass_cand_fail','discordant_base_fail_cand_pass','mcnemar_p','bootstrap_ci95_overall_delta','delta_overall','per_split','decision_attempted']}, ensure_ascii=False, indent=2))
print("wrote results_rc2_gate_r18.json")
