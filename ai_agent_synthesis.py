"""Build AI Agent 2025-2026 report synthesis (batch2-style).
Maps 30 modules to WSE-Bench 7 strategies + identifies empirical claims to test.
"""
import json
from pathlib import Path
from datetime import datetime

root = Path(r'__WSE_REPO_ROOT__')
out_dir = root / 'self_evo_kb'
out_dir.mkdir(parents=True, exist_ok=True)

synthesis = {
    'version': 'ai-agent-batch-2026-07-25',
    'source': 'AI Agent 技术全景报告 (2025-2026), 30 模块, 50+ 引用, 发布 2026-07-25',
    'source_path': str(root / 'ai-agent-knowledge.txt'),
    'n_chars_extracted': 36289,
    'n_modules': 30,
    'n_inline_citations': 93,
    'language': 'zh-CN',
    'ingestion_ts': datetime.now().isoformat(timespec='seconds'),
    'wse_bench_relevance': 'high',  # 报告覆盖 30 个 agent 子域，与 WSE-Bench 7 策略栈直接对应

    'key_themes': {
        'definitions': {
            'google_2024_whitepaper': 'Agent = model + tools + orchestration; 自主行动 + 模糊指令推理',
            'anthropic_2024': 'Agentic System = Workflows (预定义路径) + Agents (LLM 动态决策)',
            'fudan_survey_xi_et_al': 'Brain-Perception-Action 三模块',
            'lilian_weng': '规划 + 记忆 + 工具 + 行动',
            'cross_definition_invariant': '工具使用 + 状态管理 + 自主决策',
            'wse_bench_strategy': '无; 这是基础定义层，WSE-Bench 直接采纳 Agentic System 框架',
        },
        'reasoning_paradigms': {
            'paradigms_listed': ['CoT', 'ReAct', 'ToT', 'Reflexion', 'Plan-and-Execute', 'LATS', 'ReCAP'],
            'core_quantitative_claims': {
                'ReAct_alfworld': '+34% 成功率 vs 无 ReAct baseline',
                'ReAct_hotpotqa_hallucination': '6% (vs CoT 14%)',
                'Reflexion_HumanEval': 'GPT-4 一次通过率 80% → 91%',
                'ReCAP_long_context': '+112.5% 性能 vs ReAct (Stanford 2025)',
            },
            'three_mainstream_paradigms_comparison': {
                'ReAct': '30,000 tokens / 五步任务',
                'Plan-and-Execute': '14,500 tokens / 五步任务',
                'Reflection': '基础 +30%~100% tokens',
            },
            'wse_bench_strategy_mapping': {
                'self_verify_v1': '=Reflexion 模式; emit 后自检',
                'context_grounding_v1': '=ReAct + grounding prefix; 候选答案含 source span',
                'tool_arith_v1': '=Plan-and-Execute 的精简版 (用 plan 内部 + tool execute)',
                'verifier_v1': '=Plan-and-Execute + Reflection 混合; emit 前 rubric 校验',
            },
            'novel_testable_claims': [
                'ReCAP 声称 +112.5% 性能 — 需独立 benchmark 验证',
                'Reflexion HumanEval 80→91% — 需复现并测试在 WSE-Bench hard cohort',
                'ReAct +34% ALFWorld — 与 WSE-Bench 9 个 cohort 跨域比较',
            ],
            'limitations': [
                '报告引用源多为博客/技术评论，原论文需 arXiv 验证',
                '性能数字缺 effect size 与置信区间',
                'ReCAP/Reflexion 等 claim 多来自原论文作者评估，非独立复现',
            ],
        },
        'memory': {
            'three_layers': '感官 (几秒) / 短期 (in-context) / 长期 (向量库)',
            'wse_bench_strategy': '无直接对应; 但 self_verify_v1 + context_grounding_v1 隐含短时记忆',
        },
        'frameworks': {
            'frameworks_listed': ['LangChain/LangGraph', 'AutoGen (Microsoft)', 'CrewAI', 'Dify', 'Coze'],
            'category': '低代码到全代码 agent 开发框架',
            'wse_bench_strategy': '无; WSE-Bench 不依赖框架, 直接用 prompt-engineering + raw Qwen',
            'empirical_validation_needed': 'GitHub 1517 项目中 Agents cluster 342 个的真实框架采用率 vs 报告宣称的 "LangChain 主导"',
        },
        'tool_protocols': {
            'core_protocols': {
                'MCP': 'Anthropic 2024, Agent-工具连接, 广泛采用',
                'A2A': 'Google 2025, Agent-Agent 协作, 已捐 Linux Foundation',
                'OpenAI_Function_Calling': '行业事实标准',
                'AGNTCY': 'Cisco 等, 早期',
            },
            'core_quote': '2026 年将是 Agent 生态的 "TCP/IP 时刻"',
            'wse_bench_strategy': '无直接对应; 但可借鉴 MCP 思想做 "strategy-as-protocol" — 把 7 策略封装成可发现、可插拔的 agentic module',
            'novel_testable_claim': '"MCP/A2A 协议的成熟使 Agent 从孤岛走向互联" — 需独立调研 GitHub 项目实际协议采用率',
        },
        'evaluation': {
            'benchmarks_mentioned': ['AgentBench', 'HumanEval', 'ALFWorld', 'HotpotQA'],
            'wse_bench_strategy': 'WSE-Bench 自己就是评估基准; 但与 AgentBench 互不重合 (WSE-Bench 测能力, AgentBench 测任务)',
            'novel_claim': 'WSE-Bench 可作为 AgentBench 的能力维度补充',
        },
        'safety_and_alignment': {
            'covered_dimensions': '权限策略、审计、信任边界、隐私',
            'wse_bench_strategy': 'self_verify_v1 含有限的安全校验 (verifier); 但 WSE-Bench 缺独立 safety cohort',
            'gap': 'WSE-Bench 缺 safety_dim cohort, 7 策略栈均无 explicit safety guarantee',
        },
        'milestones_2025_2026': {
            'key_milestones': [
                'Anthropic MCP 2024',
                'Google A2A 2025',
                'Stanford ReCAP 2025 (+112.5%)',
                'AutoGPT 185681★ (GitHub)',
                'NousResearch/hermes-agent 220039★ (GitHub)',
            ],
            'wse_bench_alignment': 'WSE-Bench 144 题 / 7 策略栈 / v24 alt-test gate 是与上述里程碑并行的能力评估路线',
        },
        'advanced_design_patterns': {
            'patterns': ['Prompt Chaining', 'Routing', 'Parallelization', 'Orchestrator-workers', 'Evaluator-optimizer'],
            'wse_bench_strategy': '无直接对应; 但 self_verify_v1 ≈ Evaluator-optimizer 的简化',
        },
        'engineering_practices': {
            'cost_optimization': 'Plan-and-Execute 14.5k vs ReAct 30k tokens — 报告实测',
            'testing_systems': '测试与评估体系独立模块',
            'wse_bench_strategy': 'WSE-Bench eval_self_evolution.py = 评估体系的工程化实现',
        },
        'multi_modal_agents': {
            'status': '报告认为 LLM Agent 大多为 text-in/text-out, 多模态集成仍早期',
            'wse_bench_strategy': 'WSE-Bench 当前 144 题纯 text; 无 multi-modal cohort',
        },
    },

    'wse_bench_strategy_alignment_summary': {
        'selective_retrieval_v1': '=ReAct (partial) — 内部决策要不要检索; 报告未给独立名字',
        'tool_arith_v1': '≈Plan-and-Execute 精简版 — 写最小 python 脚本代替多步推理',
        'schema_guard_v1': '≈结构化校验 (Anthropic Evaluator-optimizer 的 inline 版)',
        'self_verify_v1': '=Reflexion 简化版 — 自检 + 重解',
        'citation_check_v1': '=Selective Retrieval 的高把握版 — 按置信度阈值触发',
        'verifier_v1': '=Plan-and-Execute + Reflection 混合 — emit 前 rubric-aware 验证',
        'context_grounding_v1': '=ReAct + 显式 grounding prefix — 候选答案必须含 source span',
    },

    'novel_research_directions_identified': [
        {
            'id': 'r1_protocol_aware_wse',
            'claim': 'MCP/A2A 协议意识可改善 multi-agent WSE-Bench 协作',
            'testable_form': '在 WSE-Bench 新建 cohort=2026Q4-protocol，包含 12 题 MCP/A2A/Function Calling 协议语义题',
            'current_status': 'T141-T145 (Q4-core) 已隐含 JSON Schema / OpenAI Function Calling / Anthropic Tool Use; 但缺 MCP/A2A 独立 cohort',
            'evidence_needed': '独立协议 cohort + 多模型对比',
            'risk_to_publishability': '中 — protocol 语义题易被基线回答',
        },
        {
            'id': 'r2_reflexion_on_wse_hard',
            'claim': 'Reflexion 80→91% 在 WSE-Bench hard cohort (T047-T060) 可复现',
            'testable_form': '把 self_verify_v1 应用到 hard 14 题, K=5 多 seed, 看是否能从 baseline ~0% 提升到 ≥50%',
            'current_status': 'self_verify_v1 已存在于 production 栈 (#13) 但只针对 reasoning 子域, hard 14 题原 0/14 baseline',
            'evidence_needed': 'K=5 多 seed + McNemar p<0.05',
            'risk_to_publishability': '高 — hard 14 题被 protocol 设计为 0 baseline, Reflexion 不太可能逆转此设计',
        },
        {
            'id': 'r3_recap_long_context',
            'claim': 'ReCAP 树结构 +112.5% 性能可迁移到 WSE-Bench 长上下文题 (rc/rc2/rc3/rc4)',
            'testable_form': '在 16 题 rc+rc2+rc3+rc4 上 K=5 跑 ReCAP 风格树搜索, 与 context_grounding 对比',
            'current_status': 'context_grounding_v1 (#29) 已 v24 alt-test gate PROMOTE, 但 strict-McNemar 不显著',
            'evidence_needed': 'K=5 + 12+ 题 cohort + 树搜索 vs prefix',
            'risk_to_publishability': '中 — ReCAP 实现成本高, 但可作为 baseline 对照',
        },
        {
            'id': 'r4_framework_empirical_adoption',
            'claim': '白皮书称 LangChain 是最大 agent 框架社区, 但 GitHub 1517 项目实际采用率可能更分散',
            'testable_form': '从 ai_projects_v3.jsonl (1517) 中 cross-classify Agents cluster (342) 的 framework 归属',
            'current_status': '本轮 Phase 2 任务正在做',
            'evidence_needed': '342 Agents cluster 全样本 framework 归属 + adoption rate 与 stars 关系',
            'risk_to_publishability': '低 — 数据驱动实证, 高新颖性',
        },
        {
            'id': 'r5_5_patterns_in_wse',
            'claim': 'Anthropic 5 模式 (Prompt Chaining/Routing/Parallelization/Orchestrator-workers/Evaluator-optimizer) 可重新架构 WSE-Bench 7 策略栈',
            'testable_form': '把 7 策略按 5 模式重新分组: Routing (selective_retrieval/citation_check), Evaluator-optimizer (verifier/self_verify), Orchestrator-workers (tool_arith)',
            'current_status': '未做',
            'evidence_needed': '重构后的策略栈是否更稳定 + 是否有性能提升',
            'risk_to_publishability': '低 — 架构重新组织',
        },
    ],

    'risks_and_limitations': [
        '报告本身为 2026-07-25 发布的综述, 引用源多为博客 + arXiv, 关键性能数字需独立复现',
        'ReCAP +112.5%、Reflexion 80→91% 等 claim 未提供 effect size, 不能直接外推',
        'WSE-Bench 与报告覆盖的子域不完全重合, 6/30 模块与 WSE-Bench 直接相关, 24/30 仅作 context',
        '报告未涉及 safety_dim cohort 与 multi-modal cohort, WSE-Bench 这两个方向空缺',
    ],

    'cross_ref_to_existing_kb': {
        'batch1_synthesis': {
            'overlap': ['recursive_self_improvement', 'react_tool_augmented', 'verifier_self_correction'],
            'complement': 'batch1 偏 "模型 + 方法" (self-improvement, verifier); batch2 (本文) 偏 "生态 + 协议" (MCP/A2A/Frameworks)',
        },
        'papers_kb': {
            'overlap': 'ReCAP/Reflexion/ReAct 等同时出现在 batch1 papers 与 batch2 报告',
            'action': '已交叉验证, 不重复入库',
        },
    },
}

out_p = out_dir / 'ai_agent_synthesis.json'
out_p.write_text(json.dumps(synthesis, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'synthesis written: {out_p} ({out_p.stat().st_size} bytes)')

# Also copy the raw text into KB
raw_dest = out_dir / 'ai_agent_report_2025_2026.txt'
raw_dest.write_text((root / 'ai-agent-knowledge.txt').read_text(encoding='utf-8'), encoding='utf-8')
print(f'raw text copied: {raw_dest} ({raw_dest.stat().st_size} bytes)')