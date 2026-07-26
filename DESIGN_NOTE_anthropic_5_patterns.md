# Design Note: Anthropic 5 Patterns Refactor of WSE-Bench 7-Strategy Stack

**Date**: 2026-07-25
**Author**: WorkBuddy Self-Evolution Team
**Status**: r25 design note (column E)

## Motivation

The 30-module AI Agent technical report (2026-07-25) explicitly lists Anthropic's 5 design patterns for `Agentic System`s (Workflows + Agents, Anthropic 2024):

1. **Prompt Chaining** — 多步确定性处理链
2. **Routing** — 决策 + 分流
3. **Parallelization** — 并行执行多分支
4. **Orchestrator-workers** — 中央调度 + 多个 worker
5. **Evaluator-optimizer** — 生成器 + 评估器 + 优化循环

WSE-Bench's 7-strategy production stack (`selective_retrieval_v1`, `tool_arith_v1`, `schema_guard_v1`, `self_verify_v1`, `citation_check_v1`, `verifier_v1`, `context_grounding_v1`) has been incrementally added across 23 rounds of self-evolution. The question: **does mapping to Anthropic's 5 patterns clarify the architectural landscape, or reveal a missing pattern (Parallelization)?**

## Mapping Result

| Strategy | Anthropic Pattern | Mechanism Summary |
|---|---|---|
| `selective_retrieval_v1` | **Routing** | 通用知识走参数记忆，私有/本地/新鲜事实走检索（按领域路由） |
| `citation_check_v1` | **Routing** | 高把握直答，低置信触发检索（按置信度阈值路由） |
| `tool_arith_v1` | **Orchestrator-workers** | 主 LM 编排，python 脚本作为 worker 执行多步算术 |
| `schema_guard_v1` | **Prompt Chaining** | 输入→结构化核验→输出（不合规修正）→emit |
| `self_verify_v1` | **Evaluator-optimizer** | 生成→自检→不一致重解 |
| `verifier_v1` | **Evaluator-optimizer** | emit 前 rubric-aware 跨 rubric 验证 |
| `context_grounding_v1` | **Prompt Chaining** | 输入→定位源 span→逐字引用→emit |

## Coverage

| Pattern | Count | Strategies |
|---|---|---|
| Routing | 2 | selective_retrieval_v1, citation_check_v1 |
| Orchestrator-workers | 1 | tool_arith_v1 |
| Evaluator-optimizer | 2 | self_verify_v1, verifier_v1 |
| Prompt Chaining | 2 | schema_guard_v1, context_grounding_v1 |
| **Parallelization** | **0** | — gap |

## Key Observation: Parallelization Gap

WSE-Bench's 7-strategy stack has **zero coverage of the Parallelization pattern** (multiple branches run in parallel, then aggregated). Examples that could be designed:

- `parallel_synthesis_v1`: emit K=5 candidate answers in parallel, then aggregate via majority vote / rank aggregation
- `ensemble_verifier_v1`: run N verifier instances, only pass if ≥M agree on the rubric check
- `multi_strategy_router_v1`: run 3 strategies in parallel, pick the one with highest verifier score

## Novelty Assessment

- **Low novelty in mapping**: The mapping is largely taxonomic — it doesn't generate new strategies, only relabels existing ones.
- **Higher novelty in gap identification**: Identifying "no Parallelization" is a *falsifiable claim* (the 7-strategy stack has no parallel branches). This is empirically testable in WSE-Bench by asking: "does any strategy generate K=5 candidates and aggregate?"
- **Highest novelty in cross-stack consistency**: Showing that `selective_retrieval_v1` and `citation_check_v1` are both "Routing but on different signals" reveals an architectural pattern (decision-then-action) that wasn't explicit before.

## Limitations

1. The 5-pattern taxonomy is itself from an industry whitepaper, not a peer-reviewed source. Reviewers may question its authority.
2. Mapping is subjective — `schema_guard_v1` could be Routing (route to schema-validate or skip) rather than Prompt Chaining. Different mappers may disagree.
3. The mapping does not change runtime behavior, only documentation. It is a refactor, not an enhancement.
4. We did not run new WSE-Bench experiments; this design note is purely architectural.

## Next Step

If Parallelization is genuinely needed for the next WSE-Bench capability (e.g., to reduce hard-cohort pass rate variance), the natural experiment is:
1. Design `parallel_synthesis_v1` (K=5 candidates, majority vote)
2. K=5 pre-screen on hard 14 题 (T047-T060) for headroom
3. K=5 main experiment vs base
4. If p<0.05 + CI>0 → STRATEGY_AUDIT_V4 candidate

## Conclusion

The 5-pattern mapping is a useful architectural lens but not a publishable result on its own. The genuine finding is the **Parallelization gap** in the 7-strategy stack — a testable claim that motivates a future strategy candidate. We do not PROMOTE the 5-pattern mapping as a strategy; we record it as a metadata refactor with `anthropic_pattern` fields.
