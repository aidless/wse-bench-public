"""全 batch 综合：1004 papers + GitHub 扩展 + 新候选策略。"""
import json
import os
import re

BASE = r"F:\test\2026-07-24-08-21-57"
GITHUB_FILE = os.path.join(BASE, "github-top100-for-you.md")
OUT_SYNTH = os.path.join(BASE, "self_evo_kb", "full_synthesis.json")
OUT_KB = os.path.join(BASE, "self_evo_kb", "papers_kb.json")
os.makedirs(os.path.dirname(OUT_SYNTH), exist_ok=True)

# 加载所有 batch
all_papers = {}
all_topics = set()
for i in range(1, 7):
    p = os.path.join(BASE, f"papers_batch{i}.json")
    d = json.load(open(p, encoding="utf-8"))
    for pp in d.get("papers", []):
        if pp["paper_id"] not in all_papers:
            all_papers[pp["paper_id"]] = pp
        for t in pp.get("topics", []):
            all_topics.add(t)
print(f"已加载 {len(all_papers)} unique papers across {len(all_topics)} topics")

# 按 year 分布
from collections import Counter
year_dist = Counter()
for p in all_papers.values():
    y = p.get("year", "?")
    if y and y not in ("?", ""):
        year_dist[y[:4]] += 1
print("\nYear 分布:")
for y, n in sorted(year_dist.items(), reverse=True):
    print(f"  {y}: {n}")

# 抽取 GitHub repos
with open(GITHUB_FILE, encoding="utf-8") as f:
    gh_md = f.read()
repos = re.findall(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", gh_md)
unique_repos = sorted(set((o, r) for o, r in repos if o and r))
print(f"\nGitHub projects from existing 100: {len(unique_repos)}")

# 从 paper 文本前缀提取 GitHub repos（公开提到的）
gh_paper = re.findall(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", " ".join(p.get("text_prefix", "") for p in all_papers.values()))
paper_repos = sorted(set((o, r) for o, r in gh_paper if o and r))
print(f"GitHub repos from papers: {len(paper_repos)}")
all_repos = sorted(set(unique_repos + paper_repos))
print(f"Combined unique GitHub repos: {len(all_repos)}")

# Write KB
out_papers = {
    "version": "all-batches-2026-07-24",
    "n_papers": len(all_papers),
    "n_topics": len(all_topics),
    "topics": sorted(all_topics),
    "year_distribution": dict(year_dist),
    "papers": sorted(all_papers.values(), key=lambda x: -x["score"]),
}
with open(OUT_KB, "w", encoding="utf-8") as f:
    json.dump(out_papers, f, ensure_ascii=False, indent=2)
print(f"\nwrote {OUT_KB} ({len(all_papers)} papers)")

# Full synthesis: themes + candidates
synth = {
    "version": "all-batches-2026-07-24",
    "n_papers": len(all_papers),
    "n_topics": len(all_topics),
    "year_distribution": dict(year_dist),
    "github_repos_total": len(all_repos),
    "github_repos_from_existing_list": len(unique_repos),
    "github_repos_from_papers": len(paper_repos),
    "candidate_strategies_extended": [
        {
            "id": "verifier_v1",
            "source_topic": "verifier_self_correction",
            "description": "rubric-aware 跨 rubric 验证 (json_schema/contains/markdown_sections)",
            "evidence": "Self-Trained Verification / Reliable Self-Improvement",
        },
        {
            "id": "ensemble_v1",
            "source_topic": "model_merging + self_consistency_cot",
            "description": "5 策略并行 K=5 + 加权合并（test-time ensemble of strategies）",
            "evidence": "Adaptive-Consistency + TIES + DARE",
        },
        {
            "id": "test_time_compute_v1",
            "source_topic": "test_time_compute + reasoning_math",
            "description": "对 hard 题（如 T047-T060）增加推理 token budget + self-consistency sampling；评估用 WSE-Bench 控制生成 token",
            "evidence": "o1-style reasoning / Self-Consistency",
        },
        {
            "id": "rubric_distill_v1",
            "source_topic": "verifier_self_correction + chain_of_thought",
            "description": "用 SFT 数据教模型'先 chain-of-thought 推理 rubric 约束再答'，跨题族（fact/struct/RC）通用",
            "evidence": "Beyond Output Critique: Self-Correction via Task Distillation (SELF-THOUGHT)",
        },
        {
            "id": "process_reward_v1",
            "source_topic": "verifier_self_correction + process_reward_model",
            "description": "对 reasoning 答案做 step-by-step 评分（每步核验），对 final 答案加权；WSE-Bench sv cohort 适配",
            "evidence": "Process Reward Models (PRM) / self-trained verification",
        },
    ],
    "self_evolution_takeaways": [
        "introspection threshold 理论 (DGM 系列): 真正的 self-improvement 需要 introspection + 外部 verifier feedback loop — WSE-Bench 5 策略栈已实现这两点",
        "verifier bottleneck 定理: 评估信号 is_pass() 准确率 = self-improvement 上限 — 我们用 deterministic is_pass 作为 ground truth 优势巨大",
        "46% PR reject 率 (AIDE² 实证): 盲信 benchmark 提升 = 反 Goodhart — WSE-Bench hash 锁 + K=5 + McNemar 防止",
        "model merging 思路 (TIES/DARE): 5 策略的'顺序叠加'未来可升级为'并行 ensemble + 加权合并'",
        "AIDE 实证与 WSE-Bench 差异: AIDE 评估 ML benchmark 表现 → 真实 PR 拒; 我们评估 rubric 严格满足度 → 测量可改进",
        "introspection 文档: 12 轮 K-5 评估/13 轮 STRATEGY_AUDIT/14 轮真 K-3 ablation 论证 evaluator 本身可被评估",
    ],
}
with open(OUT_SYNTH, "w", encoding="utf-8") as f:
    json.dump(synth, f, ensure_ascii=False, indent=2)
print(f"wrote {OUT_SYNTH}")