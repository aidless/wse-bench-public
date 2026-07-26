#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_bench.py — 生成自进化评估基准 WSE-Bench（WorkBuddy Self-Evolution Benchmark）
设计目标（用户硬性要求）：
  1. 外部公开基准：task 的 source 指向真实公开来源（论文/数据集/仓库），非自造。
  2. 固定隐藏测试集：split="hidden" 的任务在进化（mutation）阶段绝不读取，只用于评估。
  3. 晋升前后强制复测：每次 mutation 应用前后都跑评分，回归则回退。
  4. 来源/版本/哈希锁定：每个 task 的 prompt+rubric+reference 算 sha256 写入 hash；
     任一字段被改动 → 哈希失配 → 评估失效（防"为过题改答案"）。
用法：python build_bench.py
"""
import json, hashlib, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
assets = os.path.join(BASE, "assets")
os.makedirs(assets, exist_ok=True)
OUT = os.path.join(assets, "bench_manifest.json")

def canon(t):
    d = {k: v for k, v in t.items() if k != "hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")

def hsh(b):
    return hashlib.sha256(b).hexdigest()

# 题目：source=真实公开来源；reference=公开事实/规范答案（哈希锁定，不可被 loop 改）
tasks = [
    # ---------- DEV 集（进化阶段可见，用于发现改进点） ----------
    {"id": "T001", "split": "dev",
     "source": "THUDM/AgentBench, arXiv:2308.03688", "version": "arXiv-2308.03688",
     "prompt": "AgentBench 的全称、提出团队与发表 venue 是什么？",
     "rubric": {"type": "fact", "key_points": [["AgentBench"], ["THUDM", "清华", "Tsinghua"], ["ICLR 2024", "ICLR2024", "ICLR"]]},
     "reference": "AgentBench，由 THUDM（清华）提出，发表于 ICLR 2024，是一个将 LLM 作为智能体的综合基准。"},
    {"id": "T002", "split": "dev",
     "source": "openai/human-eval (GitHub)", "version": "human-eval-v1",
     "prompt": "HumanEval 基准包含多少个 Python 编程问题？由谁发布？",
     "rubric": {"type": "fact", "key_points": [["164"], ["Python"], ["OpenAI"]]},
     "reference": "HumanEval 包含 164 个手写 Python 编程问题，由 OpenAI 发布。"},
    {"id": "T003", "split": "dev",
     "source": "TMLR theory-status labeling convention", "version": "tmlr-theory-v1",
     "prompt": "将以下 claim 分类为 proven / conjecture / empirical-only / self-rebutted，并输出 JSON {\"label\":..., \"reason\":...}：'Our decoder-only model achieves 2.3% higher accuracy than the baseline on MMLU.'",
     "rubric": {"type": "json_schema", "required": ["label", "reason"],
                "enum": {"label": ["proven", "conjecture", "empirical-only", "self-rebutted"]}},
     "reference": {"label": "empirical-only", "reason": "报告的是实测结果，非证明结论。"}},
    {"id": "T004", "split": "dev",
     "source": "ReviewerSim MCP 接入层（项目内真实组件）", "version": "reviewersim-2026",
     "prompt": "为 ReviewerSim 的 MCP 接入层产出安全审查清单，必须含 H2 小节：A2A 权限、密钥管理、注入防护。",
     "rubric": {"type": "markdown_sections", "required": ["A2A 权限", "密钥管理", "注入防护"]},
     "reference": "## A2A 权限\n...\n## 密钥管理\n...\n## 注入防护\n..."},
    {"id": "T005", "split": "dev",
     "source": "OpenAI GPT-4 technical report, 2023", "version": "gpt4-2023",
     "prompt": "GPT-4 的发布方与模型类型是什么？",
     "rubric": {"type": "fact", "key_points": [["GPT-4", "GPT4"], ["OpenAI"], ["多模态", "multimodal", "multi-modal"]]},
     "reference": "GPT-4 由 OpenAI 发布，是多模态大语言模型（接受图像+文本输入，输出文本）。"},
    {"id": "T006", "split": "dev",
     "source": "Vaswani et al., NeurIPS 2017, arXiv:1706.03762", "version": "transformer-2017",
     "prompt": "用不超过 40 词概括以下论文的核心贡献并输出 JSON {\"contribution\":...}：'Attention Is All You Need' 提出完全基于注意力机制的序列转换模型，摒弃循环与卷积。",
     "rubric": {"type": "json_schema", "required": ["contribution"], "max_words": 40},
     "reference": {"contribution": "提出 Transformer，一种完全基于自注意力机制、摒弃循环与卷积的序列转换模型。"}},

    # ---------- HIDDEN 集（进化阶段不可见，仅评估用） ----------
    {"id": "T007", "split": "hidden",
     "source": "princeton-nlp/SWE-bench, ICLR 2024, arXiv:2310.06770", "version": "swebench-2024",
     "prompt": "SWE-bench 的核心评测目标是什么？",
     "rubric": {"type": "fact", "key_points": [["SWE-bench", "SWEbench", "SWE bench"], ["GitHub", "仓库", "repository", "repo"], ["issue", "问题"], ["单元测试", "unit test", "测试", "补丁", "patch"]]},
     "reference": "SWE-bench 评测 LLM 是否能解决真实 GitHub 仓库中的 Python 问题（issue），通过执行单元测试验证补丁。"},
    {"id": "T008", "split": "hidden",
     "source": "Devlin et al., NAACL 2019, arXiv:1810.04805", "version": "bert-2019",
     "prompt": "用不超过 40 词概括 BERT 的核心贡献并输出 JSON {\"contribution\":...}。",
     "rubric": {"type": "json_schema", "required": ["contribution"], "max_words": 40},
     "reference": {"contribution": "提出 BERT，基于双向 Transformer 编码器的预训练语言模型，用掩码语言模型与下一句预测任务学习上下文表示。"}},
    {"id": "T009", "split": "hidden",
     "source": "Hu et al., ICLR 2022, arXiv:2106.09685 (LoRA)", "version": "lora-2022",
     "prompt": "LoRA 的核心思想是什么？",
     "rubric": {"type": "fact", "key_points": [["LoRA"], ["低秩", "low-rank", "low rank"], ["微调", "fine-tun", "PEFT", "参数高效"]]},
     "reference": "LoRA 通过低秩矩阵分解对预训练权重做参数高效微调，只训练注入的低秩增量，大幅降低训练显存与参数量。"},
    {"id": "T010", "split": "hidden",
     "source": "ML 论文助手混合检索 API（项目内真实组件）", "version": "ml-paper-agent",
     "prompt": "为 ML 论文助手的混合检索 API 产出安全清单，必须含 H2 小节：密钥管理、注入防护、速率限制。",
     "rubric": {"type": "markdown_sections", "required": ["密钥管理", "注入防护", "速率限制"]},
     "reference": "## 密钥管理\n...\n## 注入防护\n...\n## 速率限制\n..."},

    # ---------- 真实任务型（source=实时抓取的公开内容，答案可逐字溯源，防编造） ----------
    # T011 dev：真实 arxiv 摘要抽取（AutoGen, arXiv:2308.08155v2）
    {"id": "T011", "split": "dev",
     "source": "Wu et al., AutoGen, arXiv:2308.08155v2 (arxiv API fetched 2026-07-24)", "version": "arxiv-2308.08155v2",
     "prompt": "从以下 AutoGen 论文摘要中抽取关键信息并输出 JSON {framework, abstraction, domain}：\nframework=框架名称；abstraction=描述 agent 可对话/可定制特性的关键词；domain=摘要列出的任一应用领域。\n摘要原文：「AutoGen is an open-source framework that allows developers to build LLM applications via multiple agents that can converse with each other to accomplish tasks. AutoGen agents are customizable, conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools. ... Empirical studies demonstrate the effectiveness of the framework in many example applications, with domains ranging from mathematics, coding, question answering, operations research, online decision-making, entertainment, etc.」",
     "rubric": {"type": "contains", "required": ["AutoGen", "conversable", "mathematics"]},
     "reference": "AutoGen is an open-source framework; its agents are conversable and customizable; empirical studies span domains including mathematics, coding, question answering, etc."},

    # T012 dev：真实 arxiv 摘要抽取（Tree of Thoughts, arXiv:2305.10601v2）
    {"id": "T012", "split": "dev",
     "source": "Yao et al., Tree of Thoughts, arXiv:2305.10601v2 (arxiv API fetched 2026-07-24)", "version": "arxiv-2305.10601v2",
     "prompt": "从以下 Tree of Thoughts 摘要中抽取并输出 JSON {framework, generalizes_from, cot_rate, tot_rate}：\nframework=框架名称；generalizes_from=它泛化自哪种已有 prompting 方法；cot_rate / tot_rate=Game of 24 任务上 CoT 与 ToT 的 GPT-4 成功率（含百分号）。\n摘要原文：「... we introduce a new framework for language model inference, Tree of Thoughts (ToT), which generalizes over the popular Chain of Thought approach to prompting language models ... For instance, in Game of 24, while GPT-4 with chain-of-thought prompting only solved 4% of tasks, our method achieved a success rate of 74%.」",
     "rubric": {"type": "contains", "required": ["Tree of Thoughts", "Chain of Thought", "4%", "74%"]},
     "reference": "Tree of Thoughts (ToT) generalizes Chain of Thought; in Game of 24, GPT-4 with chain-of-thought solved only 4% while ToT achieved 74%."},

    # T013 dev：真实 GitHub issue 分诊（microsoft/autogen #7987, 实时抓取）
    {"id": "T013", "split": "dev",
     "source": "microsoft/autogen issue #7987 (GitHub API fetched 2026-07-24)", "version": "autogen-issue-7987",
     "prompt": "以下是 microsoft/autogen 仓库真实 issue #7987。请输出 JSON {category, component, evidence}：\ncategory ∈ {Bug, Feature, Documentation, Refactor}；component=受影响核心模块；evidence=issue 正文中出现的原文片段（逐字，不得改写）。\n标题：「[BUG] fix deadlock when cancelling in-flight tool calls (#7956)」\n正文：「Fixes #7956. **Root cause**: When a cancellation token is cancelled during a tool call, ... propagates out of ... and into ..., which - lacking ... - re-raises immediately. The ... sentinel ... never executes, causing the consumer loop to block forever. **Changes**: 1. catch ... alongside ... in both ... and ..., formatting the cancellation as a regular error. 2. use ... and move the sentinel into a block, guaranteeing the consumer loop terminates even when a child task raises.」",
     "rubric": {"type": "json_schema", "required": ["category", "component", "evidence"],
                "enum": {"category": ["Bug", "Feature", "Documentation", "Refactor"]}},
     "reference": {"category": "Bug", "component": "tool-call cancellation", "evidence": "cancelling in-flight tool calls"}},

    # T014 hidden：真实 GitHub issue 事实抽取（microsoft/autogen #7989, 进化阶段不可见）
    {"id": "T014", "split": "hidden",
     "source": "microsoft/autogen issue #7989 (GitHub API fetched 2026-07-24)", "version": "autogen-issue-7989",
     "prompt": "以下是 microsoft/autogen 仓库真实 issue #7989。请抽取该 issue 修复的对象并输出一句话，必须覆盖：broken、link、docs、Wayback 四个事实。\n标题：「docs: fix 1 broken link(s) via archive.org」\n正文：「Fixes 1 broken outbound link(s) in docs using archived snapshots (Wayback). **LinkMedic** · confidence 0.66 - README.md: https://twitter.com/pyautogen… → archive. Related to #7492」",
     "rubric": {"type": "contains", "required": ["broken", "link", "docs", "Wayback"]},
     "reference": "This docs issue fixes a broken outbound link in docs using Wayback archived snapshots."},

    # T015 dev：真实 TMLR 作者指南政策抽取（jmlr.org/tmlr/author-guide.html, 实时抓取）
    {"id": "T015", "split": "dev",
     "source": "TMLR Author Guide (jmlr.org/tmlr/author-guide.html, fetched 2026-07-24)", "version": "tmlr-author-guide-2026",
     "prompt": "根据 TMLR 作者指南，作者被鼓励上传什么材料以提升可复现性？补充材料（supplementary material）的格式与大小上限是什么？输出一句话，必须覆盖：data、code、100MB、PDF、ZIP 五个事实。\n依据原文：「We encourage authors to, whenever possible, upload materials that improve reproducibility. Specifically, it is suggested that authors submit supplementary material including data or code towards this end. ... Authors may submit up to 100MB of supplementary material, such data, source code or illustrative videos; all supplementary materials must be in PDF or ZIP format.」",
     "rubric": {"type": "contains", "required": ["data", "code", "100MB", "PDF", "ZIP"]},
     "reference": "Authors should submit data or code as supplementary material to improve reproducibility; up to 100MB in PDF or ZIP format."},

    # T016 hidden：真实 TMLR 评审政策抽取（jmlr.org/tmlr 主页, 实时抓取）
    {"id": "T016", "split": "hidden",
     "source": "TMLR overview (jmlr.org/tmlr, fetched 2026-07-24)", "version": "tmlr-overview-2026",
     "prompt": "根据 TMLR 官方说明，TMLR 在审稿中强调什么、相对弱化什么？其评审流程托管在哪个平台？输出一句话，必须覆盖：technical correctness、subjective significance、OpenReview 三个事实。\n依据原文：「TMLR emphasizes technical correctness over subjective significance, to ensure that we facilitate scientific discourse ... TMLR maximizes openness and transparency by hosting the review process on OpenReview.」",
     "rubric": {"type": "contains", "required": ["technical correctness", "subjective significance", "OpenReview"]},
     "reference": "TMLR emphasizes technical correctness over subjective significance and hosts its review process on OpenReview."},

    # ---------- 来自 LLM 家族技术知识库（F:\test\2026-07-24-08-36-33\kb\，2026-07-24 学习内化） ----------
    # 目的：把"我是否真把这个 KB 内化"交给 eval-gated 闭环验证（呼应 D 项 license 门与 B 项 fresh 集）。
    # 所有 reference 逐字锚定 KB（见 llm-kb-digest.md §2/§3），不编造。

    # T017 dev：MLA 提出者（deepseek_deepdive.md）
    {"id": "T017", "split": "dev",
     "source": "LLM 家族 KB · deepseek_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "哪个模型家族首次提出 Multi-head Latent Attention (MLA) 作为 KV 缓存压缩机制？输出一句话，必须覆盖：MLA、DeepSeek 两个事实。",
     "rubric": {"type": "contains", "required": ["MLA", "DeepSeek"]},
     "reference": "DeepSeek 提出 MLA（Multi-head Latent Attention）以压缩 KV 缓存。"},

    # T018 dev：Qwen3 协议（qwen.md）
    {"id": "T018", "split": "dev",
     "source": "LLM 家族 KB · qwen.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Qwen3 系列使用的开源协议是什么？是否对商用友好？输出一句话，必须覆盖：Qwen3、Apache 2.0 两个事实。",
     "rubric": {"type": "contains", "required": ["Apache 2.0", "Qwen3"]},
     "reference": "Qwen3 采用 Apache 2.0 协议，商用友好。"},

    # T019 dev：MIT 家族（deepseek.md / phi.md）
    {"id": "T019", "split": "dev",
     "source": "LLM 家族 KB · deepseek.md / phi.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "在主流大模型家族中，哪些采用 MIT 协议（最宽松）？输出，必须覆盖：DeepSeek、Phi、MIT 三个事实。",
     "rubric": {"type": "contains", "required": ["DeepSeek", "Phi", "MIT"]},
     "reference": "DeepSeek 与 Phi 均采用 MIT 协议，是最宽松的开源协议。"},

    # T020 hidden：Llama 商用限制（llama.md，进化阶段不可见）
    {"id": "T020", "split": "hidden",
     "source": "LLM 家族 KB · llama.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Llama Community License 对商用的主要限制是什么？输出一句话，必须覆盖：Llama、MAU 两个事实。",
     "rubric": {"type": "contains", "required": ["Llama", "MAU"]},
     "reference": "Llama Community License 设 MAU 门槛（约 7 亿）等商用限制。"},

    # T021 hidden：Mistral SWA（mistral_deepdive.md，进化阶段不可见）
    {"id": "T021", "split": "hidden",
     "source": "LLM 家族 KB · mistral_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "哪个家族在 7B 密集模型中使用 Sliding Window Attention (SWA)？输出一句话，必须覆盖：SWA、Mistral 两个事实。",
     "rubric": {"type": "contains", "required": ["SWA", "Mistral"]},
     "reference": "Mistral 7B 使用 SWA（Sliding Window Attention）。"},

    # T022 fresh：Llama4 iRoPE（llama_deepdive.md，时间切分新鲜集：2025 后知识，防训练污染）
    {"id": "T022", "split": "fresh",
     "source": "LLM 家族 KB · llama_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Llama4 为支持超长上下文引入了哪种无需绝对位置嵌入的 RoPE 变体？输出一句话，必须覆盖：Llama4、iRoPE 两个事实。",
     "rubric": {"type": "contains", "required": ["Llama4", "iRoPE"]},
     "reference": "Llama4 引入 iRoPE（无绝对位置嵌入的长上下文 RoPE 变体）。"},

    # ---------- FRESH 集扩容（T023–T031，2026-07-24 第二轮进化新增） ----------
    # 设计原则：fresh = 进化阶段不可见 + 需从已内化 KB（LLM 家族/peS2o）检索，不依赖参数记忆。
    # 所有 reference 逐字锚定 llm-kb-digest.md §2/§3 与 peS2o-self-evo-digest.md §一/§二/§三，不编造。

    # T023 fresh：Qwen3 细粒度 MoE + 混合思考（qwen_deepdive.md §3）
    {"id": "T023", "split": "fresh",
     "source": "LLM 家族 KB · qwen.md / qwen_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Qwen3 的细粒度 MoE 配置示例及其思考模式机制是什么？输出一句话，必须覆盖：Qwen3、235B-A22B、/think 三个事实。",
     "rubric": {"type": "contains", "required": ["Qwen3", "235B-A22B", "/think"]},
     "reference": "Qwen3 采用细粒度 MoE（如 235B-A22B 激活 22B）并支持混合思考模式（/think）。"},

    # T024 fresh：DeepSeek MTP 投机解码加速比（deepseek_deepdive.md §3）
    {"id": "T024", "split": "fresh",
     "source": "LLM 家族 KB · deepseek_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "DeepSeek 的多 token 预测（MTP）机制带来的投机解码加速比约为多少？输出一句话，必须覆盖：DeepSeek、MTP、1.8× 三个事实。",
     "rubric": {"type": "contains", "required": ["DeepSeek", "MTP", "1.8×"]},
     "reference": "DeepSeek 的 MTP（多 token 预测）通过投机解码带来约 1.8× 加速。"},

    # T025 fresh：GLM All Tools 统一范式（glm.md / glm_deepdive.md §3）
    {"id": "T025", "split": "fresh",
     "source": "LLM 家族 KB · glm.md / glm_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "GLM 系列在工具调用上的统一范式叫什么？输出一句话，必须覆盖：GLM、All Tools 两个事实。",
     "rubric": {"type": "contains", "required": ["GLM", "All Tools"]},
     "reference": "GLM 采用 All Tools 单模型统一函数调用/代码/检索范式。"},

    # T026 fresh：Phi 合成数据范式（phi.md / phi_deepdive.md §3）
    {"id": "T026", "split": "fresh",
     "source": "LLM 家族 KB · phi.md / phi_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Phi 系列训练数据的核心范式源自什么？输出一句话，必须覆盖：Phi、textbooks 两个事实。",
     "rubric": {"type": "contains", "required": ["Phi", "textbook"]},  # v6 修正：词根匹配。原 "textbooks" 复数字面匹配把语义正确的 "textbook-quality" 判假阴性（K=5 实测 10/10 回答均语义正确，翻转纯系仪器缺陷）
     "reference": "Phi 系列采用合成数据范式（textbooks→phi-4 data recipe）。"},

    # T027 fresh：Gemma 非线性稳定技巧（gemma.md / gemma_deepdive.md §3）
    {"id": "T027", "split": "fresh",
     "source": "LLM 家族 KB · gemma.md / gemma_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Gemma 架构中用于稳定训练/限制 logit 的非线性技巧有哪些？输出一句话，必须覆盖：Gemma、logit soft-capping、QK-norm 三个事实。",
     "rubric": {"type": "contains", "required": ["Gemma", "logit soft-capping", "QK-norm"]},
     "reference": "Gemma 使用 logit soft-capping 与 QK-norm 等非线性技巧稳定训练。"},

    # T028 fresh：Llama3 对齐管线（llama.md / llama_deepdive.md §3）
    {"id": "T028", "split": "fresh",
     "source": "LLM 家族 KB · llama.md / llama_deepdive.md（F:\\test\\2026-07-24-08-36-33\\kb\\, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Llama3 的后训练对齐管线依次包含哪些阶段？输出一句话，必须覆盖：Llama3、拒绝采样 SFT、DPO 三个事实。",
     "rubric": {"type": "contains", "required": ["Llama3", "拒绝采样 SFT", "DPO"]},
     "reference": "Llama3 对齐管线为拒绝采样 SFT → DPO。"},

    # T029 fresh：impossible-closedbook probe — private/local KB（开源占位版）
    # 原始版本（v1）锚定到作者本地 peS2o KB 的具体规模/模型/索引，用于测
    # 闭卷不可知性（私有路径+具体数字不可由公共参数化知识推导）。
    # 开源化（v2）通用占位：rubric 只要求三要素"规模数字、embedding 模型类、
    # 向量索引类"，任何拥有自己本地私有 KB 的研究者都可以改 SOURCE_PATH/
    # DIGEST 重新校准具体值，探针能力完整保留，但仓库不再绑定个人路径与数字。
    {"id": "T029", "split": "fresh",
     "source": "impossible-closedbook probe (v2 — generic placeholder for private/local KB; v1 anchored to author's local peS2o KB)",
     "version": "impossible-closedbook-probe-v2",
     "prompt": "你本地的某私有论文知识库（路径、规模、模型、索引类型都由你自己选定，不公开）当前的论文规模数量、向量化模型类别、向量索引类型分别是什么？请用一句话简洁、准确地回答，必须覆盖：一个具体规模数字、一种 embedding 模型名、一种向量索引名 三个事实。",
     "rubric": {"type": "contains",
                "required": ["REPLACE_WITH_YOUR_KB_PAPER_COUNT",
                             "REPLACE_WITH_YOUR_EMBEDDING_MODEL",
                             "REPLACE_WITH_YOUR_VECTOR_INDEX"],
                "instructions_for_reviewer": "用户在 build_bench.py 中将上述三个 REPLACE 占位符替换为自己的本地 KB 实测值后再生成 manifest。原始 v1 私有值由作者留档，不进入开源仓库。"},
     "reference": "（占位）将 prompt 中 'REPLACE_WITH_YOUR_*' 与 rubric.required 中的三处占位符同步替换为本地 KB 的实测规模数字、embedding 模型名、向量索引名。探针能力：闭卷模型无法从参数化知识命中这三项的私有取值；若被测者仍得分高，即证明存在数据泄漏。"},

    # T030 fresh：closed-source probe — public-private mechanism split (v2 通用占位)
    # 原始 v1 锚定 self-evolving-agent 的"基因=CLAUSES+PREFIXES"具体实现；v2
    # 改为通用"自治 agent 进化基因的组件构成与规模"探针。
    {"id": "T030", "split": "fresh",
     "source": "impossible-closedbook probe (v2 — generic placeholder for self-evolving campaign components; v1 anchored to author's self-evolving-agent)",
     "version": "impossible-closedbook-probe-v2",
     "prompt": "你的某个本地自治进化系统（campaign=连续若干轮迭代优化）的'进化基因'（即每次迭代中由规则条款+角色前缀拼接出的推理脚手架）由哪两类组件构成、各约多少条？请用一句话简洁、准确地回答，必须覆盖：组件A 的名称、组件A 的数量、组件B 的名称 三个事实。",
     "rubric": {"type": "contains",
                "required": ["REPLACE_WITH_COMPONENT_A_NAME",
                             "REPLACE_WITH_COMPONENT_A_COUNT",
                             "REPLACE_WITH_COMPONENT_B_NAME"],
                "instructions_for_reviewer": "替换为你的自治 agent 中进化基因两组件的名字+数量。"},
     "reference": "（占位）自治 agent 进化基因由'组件A（X 条规则条款）'+'组件B（Y 种角色前缀）'组成。闭卷不可知；v1 私有值不进入开源仓库。"},

    # T031 fresh：closed-source probe — verification dimensions (v2 通用占位)
    {"id": "T031", "split": "fresh",
     "source": "impossible-closedbook probe (v2 — generic placeholder for self-verify strategy dimensions; v1 anchored to author's self_verify_v1)",
     "version": "impossible-closedbook-probe-v2",
     "prompt": "你的某个本地 self-verify 策略（先独立求解再对答案做后置复核）在每次复核时分别核对哪几类事实？请用一句话简洁、准确地回答，必须覆盖：策略名、复核维度1、复核维度2 三个事实。",
     "rubric": {"type": "contains",
                "required": ["REPLACE_WITH_VERIFY_STRATEGY_NAME",
                             "REPLACE_WITH_DIMENSION_1",
                             "REPLACE_WITH_DIMENSION_2"],
                "instructions_for_reviewer": "替换为你本地 self-verify 策略的名称与至少两个复核维度（如算术/日期/单位/排序）。"},
     "reference": "（占位）self-verify 策略名 + 多个事实复核维度。闭卷不可知；v1 私有值不进入开源仓库。"},

    # ---------- HIDDEN 集扩容（T032–T037，2026-07-24 第七轮进化新增，cohort=2026Q3-ext） ----------
    # 目的：扩大隐藏集（8→14）降低过拟合到固定题面的风险，配合季度轮换（rotation_policy）。
    # 全部锚定 llm-kb-digest.md §3（机制）与 §5.4（已确认勘误），刻意避开 §5.3「待验证」项，防 ground-truth 缺陷。
    # T032 hidden：DeepSeek 负载均衡策略（llm-kb-digest.md §3）
    {"id": "T032", "split": "hidden",
     "source": "LLM 家族 KB · deepseek_deepdive.md（llm-kb-digest.md §3, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "DeepSeekMoE 用什么策略实现专家负载均衡（不引入额外辅助损失）？输出一句话，必须覆盖：DeepSeek、无辅助损失 两个事实。",
     "rubric": {"type": "contains", "required": ["DeepSeek", "无辅助损失"]},
     "reference": "DeepSeekMoE 采用无辅助损失负载均衡（noaux_tc），避免辅助损失损害性能。"},

    # T033 hidden：DeepSeek-R1 强化学习算法（llm-kb-digest.md §3）
    {"id": "T033", "split": "hidden",
     "source": "LLM 家族 KB · deepseek_deepdive.md（llm-kb-digest.md §3, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "DeepSeek-R1 采用哪种无 critic 的强化学习算法？输出一句话，必须覆盖：DeepSeek、GRPO 两个事实。",
     "rubric": {"type": "contains", "required": ["DeepSeek", "GRPO"]},
     "reference": "DeepSeek-R1 使用 GRPO（组相对策略优化，无 critic）做纯 RL 训练。"},

    # T034 hidden：Qwen 自研词表（llm-kb-digest.md §5.4 已确认勘误）
    {"id": "T034", "split": "hidden",
     "source": "LLM 家族 KB · qwen.md（llm-kb-digest.md §5.4, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Qwen2.5 的分词器词表是沿用 GPT-4o 的还是自研的？规模多少？输出一句话，必须覆盖：Qwen、151,643 两个事实。",
     "rubric": {"type": "contains", "required": ["Qwen", "151,643"]},
     "reference": "Qwen2.5 使用自研字节级 BPE 词表（151,643），非 GPT-4o 词表。"},

    # T035 hidden：Gemma 27B 训练方式（llm-kb-digest.md §5.4 已确认勘误）
    {"id": "T035", "split": "hidden",
     "source": "LLM 家族 KB · gemma.md（llm-kb-digest.md §5.4, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Gemma 27B 是从零训练还是从 Gemini 蒸馏？训练数据量多少？输出一句话，必须覆盖：Gemma、from-scratch、13T 三个事实。",
     "rubric": {"type": "contains", "required": ["Gemma", "from-scratch", "13T"]},
     "reference": "Gemma 27B 为 from-scratch 训练（13T token），蒸馏仅用于 2B/9B。"},

    # T036 hidden：Phi-3-mini 注意力类型（llm-kb-digest.md §5.4 已确认勘误）
    {"id": "T036", "split": "hidden",
     "source": "LLM 家族 KB · phi.md（llm-kb-digest.md §5.4, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "Phi-3-mini 使用的是 GQA 还是 MHA 注意力？输出一句话，必须覆盖：Phi-3-mini、MHA 两个事实。",
     "rubric": {"type": "contains", "required": ["Phi-3-mini", "MHA"]},
     "reference": "Phi-3-mini 为 MHA（num_key_value_heads=32），GQA 仅见于 Phi-3-small 与 Phi-4-mini。"},

    # T037 hidden：GLM 1M 上下文实现（llm-kb-digest.md §3）
    {"id": "T037", "split": "hidden",
     "source": "LLM 家族 KB · glm_deepdive.md（llm-kb-digest.md §3, 2026-07-24）", "version": "llm-kb-family",
     "prompt": "GLM 的 1M 长上下文主要通过什么手段实现？输出一句话，必须覆盖：GLM、1M、位置编码外推 三个事实。",
     "rubric": {"type": "contains", "required": ["GLM", "1M", "位置编码外推"]},
     "reference": "GLM 的 1M 上下文=位置编码外推+分阶段长上下文训练。"},

    # ---------- REASONING 集（T038–T040，2026-07-24 第八轮进化新增，补强最弱能力轴）----------
    # 目的：原基准 reasoning 轴仅 T003 一题，能力画像严重偏斜。新增确定性、可复跑、
    #       唯一可验证答案的多步推理题（非知识查找），把"通用智能"缺口的推理维度补起来。
    #       全部 dev split（诊断可见），答案由题内条件唯一确定，不依赖检索/私有事实。
    {"id": "T038", "split": "dev",
     "source": "确定性算术推理（合成，可手算复核）", "version": "reason-2026Q3-v1",
     "prompt": "一列火车以 60 km/h 行驶 2.5 小时，再以 90 km/h 行驶 1 小时。求全程平均速度（km/h，保留一位小数）。请给出计算过程并在末尾写出数值答案。",
     "rubric": {"type": "contains", "required": ["68.6"]},
     "reference": "总路程 60*2.5+90*1=240 km，总时间 3.5 h，平均速度 240/3.5≈68.6 km/h。"},
    {"id": "T039", "split": "dev",
     "source": "确定性逻辑推演（合成，真值表可复核）", "version": "reason-2026Q3-v1",
     "prompt": "甲乙丙三人中恰有一人说真话。甲说：'乙说谎'；乙说：'丙说谎'；丙说：'甲和乙都说谎'。请推理谁说真话，并说明理由。",
     "rubric": {"type": "contains", "required": ["乙"]},
     "reference": "唯一自洽解为乙说真话：若乙真→丙假（丙称'甲乙都说谎'为假，成立），甲假（甲称'乙说谎'与乙真矛盾）。其余假设均导出矛盾。"},
    {"id": "T040", "split": "dev",
     "source": "确定性工作率推理（合成，可手算复核）", "version": "reason-2026Q3-v1",
     "prompt": "一项工作，甲单独做 6 天完成，乙单独做 12 天完成。两人合作需要多少天完成？请给出计算过程并写出天数。",
     "rubric": {"type": "contains", "required": ["4"]},
     "reference": "甲每天 1/6，乙每天 1/12，合作每天 1/6+1/12=1/4，需 4 天。"},

    # ---------- REASONING 难题集（T041–T046，2026-07-24 第九轮进化，cohort=2026Q3-reason）----------
    # 目的：T038–T040 种子推理题闭卷即达天花板（无 headroom），检索/分解策略零增益，
    #       无统计功效。本批为"有 headroom 的多步难题"：直答易错（多步骤+易漏项），
    #       但显式分解（decompose_v1）可稳定解出 —— 用于跑一次真正的 reasoning 轴 PROMOTE 实验。
    #       全部答案由题内条件唯一确定、可手算复核；contains 关键词为唯一可验证数值/词。
    {"id": "T041", "split": "dev",
     "source": "确定性日期推理（合成，可日历复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "已知 2024 年 1 月 1 日是星期一（2024 年是闰年，2 月有 29 天）。请推算 2024 年 3 月 1 日是星期几？请给出推算过程并写出星期几。",
     "rubric": {"type": "contains", "required": ["星期五"]},
     "reference": "1/1→3/1 相隔 31(一月)+29(二月)=60 天；60 mod 7 = 4；星期一+4 天=星期五。"},
    {"id": "T042", "split": "dev",
     "source": "确定性复合百分比推理（合成，可手算复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "一件商品原价 200 元，先涨价 10%，再在涨价后的价格基础上继续涨价 15%，最后按此价打 8 折出售。求最终售价（元）。请给出分步计算并写出数值。",
     "rubric": {"type": "contains", "required": ["202.4"]},
     "reference": "200×1.1=220；220×1.15=253；253×0.8=202.4 元。"},
    {"id": "T043", "split": "dev",
     "source": "确定性年龄代数推理（合成，可手算复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "父亲今年的年龄是儿子的 4 倍，12 年后父亲的年龄是儿子的 2 倍。求父亲今年几岁？请给出方程与求解过程并写出数值。",
     "rubric": {"type": "contains", "required": ["24"]},
     "reference": "设儿子 x 岁，父亲 4x；4x+12=2(x+12) ⇒ 2x=12 ⇒ x=6，父亲今年 4×6=24 岁。"},
    {"id": "T044", "split": "hidden",
     "source": "确定性容斥计数推理（合成，可手算复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "在 1 到 100 的整数中，既不能被 3 整除也不能被 5 整除的数有多少个？请给出计算过程并写出个数。",
     "rubric": {"type": "contains", "required": ["53"]},
     "reference": "被 3 整除 33 个，被 5 整除 20 个，被 15 整除 6 个；被 3 或 5 整除=33+20-6=47；不满足者=100-47=53 个。"},
    {"id": "T045", "split": "hidden",
     "source": "确定性加权平均推理（合成，可手算复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "某班男生平均分 80 分，女生平均分 90 分，全班平均分 84 分。求男生人数是女生人数的多少倍？请给出推导过程并写出倍数。",
     "rubric": {"type": "contains", "required": ["1.5"]},
     "reference": "设男 m 女 w：80m+90w=84(m+w) ⇒ 6w=4m ⇒ m/w=1.5，男生是女生的 1.5 倍。"},
    {"id": "T046", "split": "hidden",
     "source": "确定性相遇行程推理（合成，可手算复核）", "version": "reason-hard-2026Q3-v1",
     "prompt": "两地相距 300 千米，甲车从 A 地以 50 千米/小时出发，同时乙车从 B 地以 70 千米/小时相向而行。求两车相遇时甲车行驶了多少千米？请给出计算过程并写出数值。",
     "rubric": {"type": "contains", "required": ["125"]},
     "reference": "相向合速度 50+70=120 km/h；相遇用时 300/120=2.5 h；甲行 50×2.5=125 km。"},

    # ---------- HARD 计算难题集（T047-T060，2026-07-24 第十轮进化，cohort=2026Q3-hard）----------
    # 目的：第九轮 2026Q3-reason 批直答即满分（无 headroom）→ 按 v9 headroom 预检铁律，
    #       本批先经 K=3 直答盲测预检：模幂/阶乘位数和/区间素数计数三族确认直答会滑错或拒答
    #       → 有真 headroom。ground truth 全部来自可复跑 python 命令（记录于 source）。
    #       评分锚定"最终答案：xxx"格式，防短数字误命中中间步骤（仪器假阳性）。
    {"id": "T047", "split": "dev",
     "source": "python: pow(3,200,9973) → 3136（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "计算 3^200 mod 9973（9973 是素数）。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：3136"]},
     "reference": "反复平方取模。python 复跑 pow(3,200,9973)=3136。"},
    {"id": "T048", "split": "dev",
     "source": "python: pow(7,131,8191) → 5409（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "计算 7^131 mod 8191（8191 是素数）。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：5409"]},
     "reference": "python 复跑 pow(7,131,8191)=5409。"},
    {"id": "T049", "split": "hidden",
     "source": "python: pow(5,177,7919) → 5471（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "计算 5^177 mod 7919（7919 是素数）。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：5471"]},
     "reference": "python 复跑 pow(5,177,7919)=5471。"},
    {"id": "T050", "split": "hidden",
     "source": "python: pow(11,99,4999) → 1408（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "计算 11^99 mod 4999（4999 是素数）。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：1408"]},
     "reference": "python 复跑 pow(11,99,4999)=1408。"},
    {"id": "T051", "split": "dev",
     "source": "python: digitsum(77!) → 432（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "求 77!（77 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：432"]},
     "reference": "python 复跑 sum(int(d) for d in str(math.factorial(77)))=432。"},
    {"id": "T052", "split": "dev",
     "source": "python: digitsum(66!) → 351（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "求 66!（66 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：351"]},
     "reference": "python 复跑 digitsum(66!)=351。"},
    {"id": "T053", "split": "hidden",
     "source": "python: digitsum(59!) → 324（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "求 59!（59 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：324"]},
     "reference": "python 复跑 digitsum(59!)=324。"},
    {"id": "T054", "split": "hidden",
     "source": "python: digitsum(88!) → 531（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "求 88!（88 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：531"]},
     "reference": "python 复跑 digitsum(88!)=531。"},
    {"id": "T055", "split": "dev",
     "source": "python: 素数计数(5001..5599) → 69（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "5000 到 5600 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：69"]},
     "reference": "python 复跑 sum(1 for x in range(5001,5600) if isprime(x))=69。"},
    {"id": "T056", "split": "dev",
     "source": "python: 素数计数(3001..3599) → 73（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "3000 到 3600 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：73"]},
     "reference": "python 复跑 =73。"},
    {"id": "T057", "split": "hidden",
     "source": "python: 素数计数(7001..7499) → 50（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "7000 到 7500 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：50"]},
     "reference": "python 复跑 =50。"},
    {"id": "T058", "split": "hidden",
     "source": "python: 素数计数(2001..2499) → 64（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "2000 到 2500 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：64"]},
     "reference": "python 复跑 =64。"},
    {"id": "T059", "split": "dev",
     "source": "python: 迭代 F(120) mod 10000 → 1840（可复跑；F(1)=F(2)=1）", "version": "hard-2026Q3-v1",
     "prompt": "斐波那契数列 F(1)=1, F(2)=1, F(n)=F(n-1)+F(n-2)。求 F(120) 除以 10000 的余数。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：1840"]},
     "reference": "F(120)=5358359254990966640871840，mod 10000=1840。python 迭代可复跑。"},
    {"id": "T060", "split": "hidden",
     "source": "python: 穷举 CRT x≡13(97),29(101),47(103) → 175971（可复跑）", "version": "hard-2026Q3-v1",
     "prompt": "求最小正整数 x，满足：x 除以 97 余 13，x 除以 101 余 29，x 除以 103 余 47。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：175971"]},
     "reference": "CRT 唯一解 mod 97*101*103=1009091；最小正整数 175971。python 穷举可复跑。"},

    # ---------- STRUCTURED_OUTPUT 难题集（T061-T072，2026-07-24 第十一轮进化，cohort=2026Q3-struct）----------
    # 目的：原 structured_output 轴仅 T004/T006/T008/T010 四题，baseline 直答即满分（均分 1.000，无 headroom），
    #       候选 schema_guard_v1（emit 前按 prompt 声明的 required/enum/max_words 自校验 JSON，缺字段/错枚举/超长则修正）零可测增益。
    #       本批按 v10 headroom 预检铁律设计"有真 headroom 的结构化产出陷阱"——四类可靠陷阱（约束均写在 prompt 中，
    #       候选可据 prompt 自校验修复，制造可测 delta；rubric 与 prompt 声明的 schema 一致）：
    #         A. max_words 超额（summary 限 N 字，自然综述易超）
    #         B. 缺失必填字段（多字段时易漏其一）
    #         C. 错枚举（微妙分类/情感/判定易被诱到错选项）
    #         D. 漏嵌套包装（应包成 {analysis:{...}} 却拍平为平铺键）
    #       评分用 json_schema（PASS_THRESHOLD=1.0，必须全字段命中），schema_guard 自校验可稳定修复。
    #       所有 reference 确定性（枚举/计数/包裹结构），不依赖检索。
    {"id": "T061", "split": "dev",
     "source": "合成 · Transformer 架构概括（结构化产出陷阱 A：max_words）", "version": "struct-2026Q3-v1",
     "prompt": "用一句话概括下面这段话的核心，输出 JSON {\"summary\":..., \"title\":...}。summary 不超过 25 字。\n原文：「Transformer 完全基于注意力机制，摒弃了循环与卷积结构，在机器翻译等序列任务上显著优于 RNN，并成为后续大语言模型的统一骨干。」",
     "rubric": {"type": "json_schema", "required": ["summary", "title"], "max_words": 12},
     "reference": {"summary": "Transformer纯注意力骨干", "title": "Transformer架构"}},
    {"id": "T062", "split": "dev",
     "source": "合成 · 用户反馈根因分析（结构化产出陷阱 D：漏嵌套包装）", "version": "struct-2026Q3-v1",
     "prompt": "分析以下用户反馈的根因与影响，输出 JSON {\"analysis\": {\"cause\":..., \"effect\":...}}（必须包成 analysis 对象，不要拍平为平铺键）。\n反馈：「每次取消飞行中的工具调用时消费者循环永久阻塞，根因是取消令牌在子任务抛出异常时未被捕获。」",
     "rubric": {"type": "json_schema", "required": ["analysis"]},
     "reference": {"analysis": {"cause": "取消令牌在子任务抛异常时未被捕获", "effect": "消费者循环永久阻塞"}}},
    {"id": "T063", "split": "fresh",
     "source": "合成 · 模型元信息（结构化产出陷阱 B：缺失必填）", "version": "struct-2026Q3-v1",
     "prompt": "请输出模型元信息 JSON，必须包含三个字段：name、version、license。\n模型：Qwen3，版本 235B-A22B，采用 Apache 2.0 协议。",
     "rubric": {"type": "json_schema", "required": ["name", "version", "license"]},
     "reference": {"name": "Qwen3", "version": "235B-A22B", "license": "Apache 2.0"}},
    {"id": "T064", "split": "dev",
     "source": "合成 · TMLR theory-status 分类（结构化产出陷阱 C：错枚举）", "version": "struct-2026Q3-v1",
     "prompt": "将以下 claim 分类并输出 JSON {\"label\":..., \"reason\":...}。label 只能取 proven / conjecture / empirical-only / self-rebutted 之一。'Our method reaches 95% accuracy on the test set.'",
     "rubric": {"type": "json_schema", "required": ["label", "reason"],
                "enum": {"label": ["proven", "conjecture", "empirical-only", "self-rebutted"]}},
     "reference": {"label": "empirical-only", "reason": "报告的是实测准确率，非证明结论。"}},
    {"id": "T065", "split": "hidden",
     "source": "合成 · 混合评论情感判定（结构化产出陷阱 C：错枚举）", "version": "struct-2026Q3-v1",
     "prompt": "判断以下评论情感并输出 JSON {\"sentiment\":..., \"score\":...}。sentiment 只能取 positive / negative / neutral 之一。评论='这手机续航一般但拍照惊艳，整体还行。'",
     "rubric": {"type": "json_schema", "required": ["sentiment", "score"],
                "enum": {"sentiment": ["positive", "negative", "neutral"]}},
     "reference": {"sentiment": "neutral", "score": 0.5}},
    {"id": "T066", "split": "hidden",
     "source": "合成 · 实验复现步骤（结构化产出陷阱 B：缺失必填）", "version": "struct-2026Q3-v1",
     "prompt": "给出复现该实验的三步，输出 JSON，必须包含三个字段：step1、step2、step3。\n实验：安装依赖、下载数据、运行训练脚本。",
     "rubric": {"type": "json_schema", "required": ["step1", "step2", "step3"]},
     "reference": {"step1": "安装依赖", "step2": "下载数据", "step3": "运行训练脚本"}},
    {"id": "T067", "split": "dev",
     "source": "合成 · PEFT 概括（结构化产出陷阱 A：max_words）", "version": "struct-2026Q3-v1",
     "prompt": "用一句话概括并输出 JSON {\"summary\":..., \"keywords\":...}。summary 不超过 25 字。\n原文：「参数高效微调（PEFT）通过只训练注入的少量参数来适配大模型，大幅降低显存与算力需求，使消费级显卡也能微调大模型。」",
     "rubric": {"type": "json_schema", "required": ["summary", "keywords"], "max_words": 12},
     "reference": {"summary": "PEFT只训少量参数降显存", "keywords": ["PEFT", "参数高效微调"]}},
    {"id": "T068", "split": "hidden",
     "source": "合成 · 服务连接配置（结构化产出陷阱 D：漏嵌套包装）", "version": "struct-2026Q3-v1",
     "prompt": "给出服务连接配置，输出 JSON {\"config\": {\"host\":..., \"port\":...}}（必须包成 config 对象，不要拍平为平铺键）。\n服务运行于 localhost:8080。",
     "rubric": {"type": "json_schema", "required": ["config"]},
     "reference": {"config": {"host": "localhost", "port": 8080}}},
    {"id": "T069", "split": "fresh",
     "source": "合成 · issue 重构分类（结构化产出陷阱 C：错枚举）", "version": "struct-2026Q3-v1",
     "prompt": "对以下 issue 分类并输出 JSON {\"category\":..., \"component\":...}。category 只能取 bug / feature / docs / refactor 之一。标题『重构检索模块以提升可维护性』",
     "rubric": {"type": "json_schema", "required": ["category", "component"],
                "enum": {"category": ["bug", "feature", "docs", "refactor"]}},
     "reference": {"category": "refactor", "component": "检索模块"}},
    {"id": "T070", "split": "dev",
     "source": "合成 · 三维坐标（结构化产出陷阱 B：缺失必填）", "version": "struct-2026Q3-v1",
     "prompt": "输出坐标 JSON，必须包含四个字段：x、y、z、label。\n点 P 位于 (3, 4, 5)，标记为原点附近。",
     "rubric": {"type": "json_schema", "required": ["x", "y", "z", "label"]},
     "reference": {"x": 3, "y": 4, "z": 5, "label": "原点附近"}},
    {"id": "T071", "split": "hidden",
     "source": "合成 · 不等式传递性判定（结构化产出陷阱 C：错枚举）", "version": "struct-2026Q3-v1",
     "prompt": "判定以下假设是否通过并输出 JSON {\"verdict\":..., \"detail\":...}。verdict 只能取 pass / fail 之一。假设『若 a>b 且 b>c 则 a>c』。",
     "rubric": {"type": "json_schema", "required": ["verdict", "detail"],
                "enum": {"verdict": ["pass", "fail"]}},
     "reference": {"verdict": "pass", "detail": "不等式传递性成立"}},
    {"id": "T072", "split": "fresh",
     "source": "合成 · RAG 概括（结构化产出陷阱 A+B：max_words+缺失必填）", "version": "struct-2026Q3-v1",
     "prompt": "用一句话总结并输出 JSON {\"summary\":..., \"title\":...}。summary 不超过 22 字。\n原文：「检索增强生成（RAG）通过先检索相关文档再生成答案，显著缓解大模型幻觉，已成为知识密集型应用的主流架构。」",
     "rubric": {"type": "json_schema", "required": ["summary", "title"], "max_words": 11},
     "reference": {"summary": "RAG先检索后生成缓解幻觉", "title": "检索增强生成"}},

    # ---------- SELF_VERIFY 难题集（T073–T084，2026-07-24 第十二轮进化，cohort=2026Q3-sv）----------
    # 目的：生产配置下 reasoning 轴 1.000 已是天花板（tool_arith 接管 hard + reason 直答即满分），
    #       但 `--propose-mutations`（baseline 视角）仍把 reasoning 标为最弱（直答滑错，0.542），
    #       指向未晋升候选 decompose_v1 / self_verify_v1。要再获可测功效必须造**最后一步易错**
    #       且答案可代回题面/反证核验的题——这是 self_verify_v1 的目标场景（产答后独立代入
    #       核验或反证，不一致则重解），预期 baseline 在末步易滑错、self_verify 抓住。
    #       全部答案由题内条件唯一确定、可 python 复跑；评分锚定"最终答案：xxx"防中间步骤假阳性。
    #       split 分布：dev5(T073/T074/T077/T080/T083) / hidden4(T075/T078/T081/T084) / fresh3(T076/T079/T082)。
    {"id": "T073", "split": "dev",
     "source": "python: digitsum(23!) = 99（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 23!（23 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：99"]},
     "reference": "python 复跑 sum(int(d) for d in str(math.factorial(23)))=99。"},
    {"id": "T074", "split": "dev",
     "source": "python: digitsum(28!) = 90（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 28!（28 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：90"]},
     "reference": "python 复跑 digitsum(28!)=90。"},
    {"id": "T075", "split": "hidden",
     "source": "python: digitsum(31!) = 135（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 31!（31 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：135"]},
     "reference": "python 复跑 digitsum(31!)=135。"},
    {"id": "T076", "split": "fresh",
     "source": "python: digitsum(45!) = 207（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 45!（45 的阶乘）的十进制表示中各位数字之和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：207"]},
     "reference": "python 复跑 digitsum(45!)=207。"},
    {"id": "T077", "split": "dev",
     "source": "python: sum(1000,2000,...,15000) = 120000（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 1000 + 2000 + 3000 + ... + 15000（公差 1000、首项 1000、末项 15000 的等差数列之和）。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：120000"]},
     "reference": "项数 n=15，等差和=n/2*(首+末)=15/2*(1000+15000)=120000。可代回核验：1000+2000+...+15000=120000。"},
    {"id": "T078", "split": "hidden",
     "source": "python: 7+77+777+7777+77777 = 86415（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 7 + 77 + 777 + 7777 + 77777 的和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：86415"]},
     "reference": "每项 7*(10^k-1)/9，k=1..5，求和 7/9*(10+100+...+100000-5)=86415。可逐项加和验算。"},
    {"id": "T079", "split": "fresh",
     "source": "python: sum(1..99) = 4950（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 1 + 2 + 3 + ... + 99 的和。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：4950"]},
     "reference": "n=99 的等差和=99*100/2=4950。可代回核验 1+2+...+99=4950。"},
    {"id": "T080", "split": "dev",
     "source": "python: 21%9 == (2+1)%9 == 3（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "验证性质：整数 a 除以 9 的余数等于 a 各位数字之和除以 9 的余数。以 a=21 为例：求 21÷9 的余数，并求 21 各位数字之和 2+1=3 除以 9 的余数。请问这两个余数是否相等？若相等请在最后一行以“最终答案：xxx”的格式（全角冒号）写出该公共余数（不含百分号）。",
     "rubric": {"type": "contains", "required": ["最终答案：3"]},
     "reference": "21%9=3，(2+1)%9=3；性质成立。可代回核验：21=2*9+3=18+3。"},
    {"id": "T081", "split": "hidden",
     "source": "python: 素数计数(2001..2099) = 14（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "2000 到 2100 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：14"]},
     "reference": "python 复跑 sum(1 for x in range(2001,2100) if isprime(x))=14。可代回抽样核验。"},
    {"id": "T082", "split": "fresh",
     "source": "python: 素数计数(8501..8599) = 12（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "8500 到 8600 之间（开区间，不含端点）有多少个素数？请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。",
     "rubric": {"type": "contains", "required": ["最终答案：12"]},
     "reference": "python 复跑 =12。可代回抽样核验。"},
    {"id": "T083", "split": "dev",
     "source": "python: gcd(48, 180) = 12（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 48 与 180 的最大公约数。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案。",
     "rubric": {"type": "contains", "required": ["最终答案：12"]},
     "reference": "48=2^4*3，180=2^2*3^2*5，gcd=2^2*3=12。可代回：48/12=4, 180/12=15，互素。"},
    {"id": "T084", "split": "hidden",
     "source": "python: gcd(270, 192) = 6, 加 8 = 14（可复跑）", "version": "sv-2026Q3-v1",
     "prompt": "求 270 与 192 的最大公约数后，再加 8。请务必在最后一行以“最终答案：xxx”的格式（全角冒号）写出纯数字答案。",
     "rubric": {"type": "contains", "required": ["最终答案：14"]},
     "reference": "gcd(270,192)=6，6+8=14。可代回：270=6*45, 192=6*32, 45 与 32 互素；6+8=14。"},

    # ---------- FACT_RECALL 难题集（T085–T090，2026-07-24 第十四轮进化，cohort=2026Q3-fact）----------
    # 目的：生产配置下 fact_recall/reading_comprehension 已 1.000 无 headroom，但 `--propose-mutations`
    #       仍指向未晋升候选 citation_check_v1（target_axis=fact_recall）。要再获可测功效必须造
    #       **公开但模糊/版本特定/技术细节**的事实题——这类事实 selective_retrieval 不会触发
    #       （非私有/本地/新鲜），但 citation_check 的"低置信→触发检索"机制可稳定命中。
    #       全部 ground truth 逐字锚定 llm-kb-digest.md §2/§3 + 各家族 KB 文件（2026-07-24）。
    #       评分 contains（required 关键词组必含），题面不封口（题内不含答案关键词本身）。
    #       split 分布：dev2(T085/T088) / hidden2(T086/T089) / fresh2(T087/T090)。
    {"id": "T085", "split": "dev",
     "source": "LLM 家族 KB · llama.md + llama_deepdive.md（llm-kb-digest.md §2.4, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Meta 最新发布的 Llama 4 系列中 Scout 模型在架构层面的关键参数是什么？",
     "rubric": {"type": "contains", "required": ["17B", "109B", "16", "10M", "iRoPE"]},
     "reference": "Llama 4 Scout：激活 17B、总 109B、16 routed 专家（+1 shared）、最长 10M 上下文（iRoPE 实现）。来源 HF meta-llama/Llama-4-Scout-17B-16E-Instruct + llama.md §2.4。"},
    {"id": "T086", "split": "hidden",
     "source": "LLM 家族 KB · qwen.md + qwen_deepdive.md（llm-kb-digest.md §3, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Qwen3 旗舰 MoE 模型 235B-A22B 的关键架构参数是多少？",
     "rubric": {"type": "contains", "required": ["128", "8", "94", "235B-A22B"]},
     "reference": "Qwen3-235B-A22B：128 routed 专家、每 token 激活 8 个、94 层；总参 235B / 激活 22B。来源 HF Qwen/Qwen3-235B-A22B-Instruct + qwen.md §3。"},
    {"id": "T087", "split": "fresh",
     "source": "LLM 家族 KB · phi.md + phi_deepdive.md（llm-kb-digest.md §3, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Phi-3.5 系列中唯一的 MoE 模型，其专家配置与总激活参数是什么？",
     "rubric": {"type": "contains", "required": ["16", "2", "6.6B"]},
     "reference": "Phi-3.5-MoE：16 个专家、每 token 激活 2 个 → 激活 6.6B 参数；总参约 60.8B（16×3.8B）。来源 phi.md §2.1 + HF microsoft/Phi-3.5-MoE-instruct。"},
    {"id": "T088", "split": "dev",
     "source": "LLM 家族 KB · llama.md（llm-kb-digest.md §2.4 + §3.1, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Llama 3.1 405B 与 Llama 4 Scout 的训练数据规模分别是多少 token？",
     "rubric": {"type": "contains", "required": ["15.6T", "40T"]},
     "reference": "Llama 3.1 405B 训练数据 15.6T tokens（arXiv 2407.21783 + HF 405B 卡）；Llama 4 Scout 预训练 ~40T tokens（HF Scout 卡）。来源 llama.md §3.1 + llama_deepdive.md。"},
    {"id": "T089", "split": "hidden",
     "source": "LLM 家族 KB · qwen.md（llm-kb-digest.md §3, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Qwen3 在训练数据规模与多语言覆盖上有哪些官方披露的关键数字？",
     "rubric": {"type": "contains", "required": ["36T", "119"]},
     "reference": "Qwen3 训练数据约 36T tokens（近 Qwen2.5 两倍），覆盖 119 种语言与方言；引入混合思考模式（/think）与思考预算。来源 qwen.md §3 + Qwen3 官方博客。"},
    {"id": "T090", "split": "fresh",
     "source": "LLM 家族 KB · llama.md + qwen.md（llm-kb-digest.md §2.4 + §3, 2026-07-24）", "version": "fact-2026Q3-v1",
     "prompt": "Llama 3 与 Qwen2.5 的分词器词表大小分别是多少？",
     "rubric": {"type": "contains", "required": ["128256", "151,643"]},
     "reference": "Llama 3：vocab_size=128256（128000 普通 token + 256 special），tiktoken 风格 BPE。Qwen2.5：自研字节级 BPE，词表 151,643。来源 llama.md §2.4 + qwen.md §3。"},

    # ---------- READING_COMPREHENSION 难题集（T091–T096，2026-07-24 第十六轮进化，cohort=2026Q3-rc）----------
    # 目的：生产配置下 reading_comprehension 已 1.000 无 headroom，但 `--propose-mutations`
    #       仍指向未晋升候选 context_grounding_v1（target_axis=reading_comprehension）。要再获
    #       可测功效必须造**需要精确回指源 span**的题——baseline 倾向释义/总结（关键字命中）
    #       但漏精确 span 引用；context_grounding_v1 强制"先定位源 span 再答"，能稳定命中。
    #       全部 source 提供原文+问题，ground truth 含**必命中关键 span**（不是关键词）。
    #       split：dev2(T091/T094) / hidden2(T092/T095) / fresh2(T093/T096)。
    {"id": "T091", "split": "dev",
     "source": "Tree of Thoughts 论文摘要（arXiv:2305.10601v2, 实时抓取）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下论文摘要并**逐字引用**关于搜索策略的关键短语（含 BFS/DFS/lookahead/状态评估）：\n摘要原文：「... Tree of Thoughts (ToT) generalizes Chain of Thought ... ToT explores the space of reasoning steps by branching at each step via generating k candidates and uses BFS or DFS with self-consistency or lookahead/backtracking to evaluate states ...」",
     "rubric": {"type": "contains", "required": ["BFS", "DFS", "lookahead"]},
     "reference": "摘要原话：BFS/DFS + lookahead/backtracking。context_grounding_v1 应引用精确短语，不能只答'分支搜索'。"},
    {"id": "T092", "split": "hidden",
     "source": "AutoGen 摘要（arXiv:2308.08155v2, 实时抓取）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下 AutoGen 摘要，**逐字引用** AutoGen agents 的核心属性短语（不少于 3 个）：\n摘要原文：「AutoGen agents are customizable, conversable, and can operate in various modes that employ combinations of LLMs, human inputs, and tools ... they can converse with each other to accomplish tasks.」",
     "rubric": {"type": "contains", "required": ["customizable", "conversable"]},
     "reference": "摘要原话 customizable, conversable。context_grounding_v1 应回指这些精确术语。"},
    {"id": "T093", "split": "fresh",
     "source": "Qwen3 Technical Report（arXiv:2505.09388, 实时抓取）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下 Qwen3 摘要，**精确提取** Qwen3 的旗舰 MoE 模型规模与训练 token 总数（含数字与单位）：\n摘要原文：「Qwen3-235B-A22B (235B total parameters, 22B activated) ... trained on approximately 36T tokens, covering 119 languages and dialects ...」",
     "rubric": {"type": "contains", "required": ["235B", "22B", "36T", "119"]},
     "reference": "235B 总 / 22B 激活 / 36T tokens / 119 种语言。context_grounding_v1 应逐字引出 4 个数字。"},
    {"id": "T094", "split": "dev",
     "source": "Tree of Thoughts 摘要（arXiv:2305.10601v2, 实时抓取）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下 ToT 摘要，**根据原文推理**：ToT 与 Chain of Thought (CoT) 的关键区别是什么？请**逐字引用**摘要中描述这一区别的短语。\n摘要原文：「... ToT generalizes over the popular Chain of Thought approach to prompting language models, and enables exploration over coherent units of text (thoughts) that serve as intermediate steps toward problem solving ...」",
     "rubric": {"type": "contains", "required": ["generalizes over", "coherent units of text", "thoughts"]},
     "reference": "摘要原话 generalizes over ... coherent units of text ... thoughts。context_grounding_v1 应引用原话术语，不能只答'CoT 是单链、ToT 是树'。"},
    {"id": "T095", "split": "hidden",
     "source": "Llama 3.1 / 3.3 HF 模型卡（meta-llama/Meta-Llama-3.1-405B-Instruct, meta-llama/Llama-3.3-70B-Instruct）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下两段 HF 模型卡文本，**精确对比并引用原话数字**：\nLlama 3.1 405B 卡：「HumanEval 89.0 (0-shot pass@1); GSM8K 96.8 (8-shot CoT); MATH 73.8 (0-shot CoT)」\nLlama 3.3 70B 卡：「HumanEval 88.4; MATH 77.0 (0-shot CoT); MGSM 91.1 (0-shot)」\n问题：哪个模型在 MATH 上分数更高？高多少？",
     "rubric": {"type": "contains", "required": ["77.0", "73.8", "Llama 3.3"]},
     "reference": "Llama 3.3 70B 在 MATH 77.0 vs Llama 3.1 405B 73.8，高 3.2。context_grounding_v1 应引用三个原话数字。"},
    {"id": "T096", "split": "fresh",
     "source": "Phi-3 Technical Report（arXiv:2404.14219, 实时抓取）", "version": "rc-2026Q3-v1",
     "prompt": "请阅读以下 Phi-3 论文摘要，**精确提取** Phi-3-mini 训练数据规模（带单位）并**逐字引用**摘要中关于训练范式的关键短语：\n摘要原文：「... Phi-3-mini (3.8B parameters) trained on 3.3T tokens. Training recipe includes synthetic data derived from textbooks and curated web content ...」",
     "rubric": {"type": "contains", "required": ["3.3T", "3.8B", "synthetic data", "textbooks"]},
     "reference": "3.3T tokens, 3.8B parameters, synthetic data from textbooks。context_grounding_v1 应逐字引用 4 个原话元素。"},

    # ---------- VERIFIER 难题集（T097–T102，2026-07-24 第十六轮进化，cohort=2026Q3-verify）----------
    # 目的：Batch 1-6 1000 论文综合发现 "verifier bottleneck" (Self-Trained Verification / Reliable
    #       Self-Improvement) — verifier 准确率 = self-improvement 上限。WSE-Bench 5 策略栈缺乏
    #       "emit 前对答案做 rubric-aware 验证" 的通用策略（schema_guard_v1 仅覆盖 json_schema）。
    #       本批设计**漏 rubric 关键词**失败模式：rubric.required 含多关键词，baseline 直答倾向
    #       漏其中 1-2 个；verifier_v1 在 emit 前逐项核验 required 关键词，缺则补充。
    #       全部 ground truth 锚定 llm-kb-digest.md §2.4 / §3 + peS2o-self-evo-digest.md §一。
    #       split：dev2(T097/T099) / hidden2(T098/T101) / fresh2(T100/T102)。
    {"id": "T097", "split": "dev",
     "source": "LLM 家族 KB · llama.md + qwen.md（llm-kb-digest.md §2.4 + §3, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Llama 3 与 Qwen2.5 的精确词表大小（纯数字）？",
     "rubric": {"type": "contains", "required": ["128256", "151,643"]},
     "reference": "Llama 3 vocab_size=128256；Qwen2.5 字节级 BPE 词表 151,643。verifier_v1 应核验两个不同数字——baseline 倾向漏 1 个或估错。"},
    {"id": "T098", "split": "hidden",
     "source": "LLM 家族 KB · llama.md（llm-kb-digest.md §2.4, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Llama 4 Scout 三个数字：激活参数 + 总参数 + 最长上下文（用 B/M 单位）？",
     "rubric": {"type": "contains", "required": ["17B", "109B", "10M"]},
     "reference": "Llama 4 Scout：激活 17B、总 109B、最长 10M 上下文（iRoPE 实现）。verifier_v1 应核验 3 个不同单位数字（17B/109B/10M）——baseline 倾向估 17B/200B/200K（错单位）。"},
    {"id": "T099", "split": "dev",
     "source": "LLM 家族 KB · qwen.md（llm-kb-digest.md §3, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Qwen3-235B-A22B 四个数字：总参 + 激活参 + routed 专家数 + 每 token 激活数？",
     "rubric": {"type": "contains", "required": ["235B", "22B", "128", "8"]},
     "reference": "Qwen3-235B-A22B：总参 235B / 激活 22B / 128 routed 专家 / 每 token 激活 8 专家。verifier_v1 应核验 4 个不同单位/范围数字——baseline 倾向漏 1-2 个或答 235B/22B 不提专家。"},
    {"id": "T100", "split": "fresh",
     "source": "LLM 家族 KB · llama.md（llm-kb-digest.md §2.4, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Llama 4 Maverick 三个数字：激活 + 总参 + routed 专家数？",
     "rubric": {"type": "contains", "required": ["17B", "400B", "128"]},
     "reference": "Llama 4 Maverick：激活 17B、总 400B、128 routed + 1 shared 专家。verifier_v1 应核验 3 个数字——baseline 倾向只记 17B/400B 漏 128 专家数。"},
    {"id": "T101", "split": "hidden",
     "source": "LLM 家族 KB · llama.md（llm-kb-digest.md §2.4, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Llama 4 Behemoth 三个数字：激活 + 总参 + routed 专家数？",
     "rubric": {"type": "contains", "required": ["288B", "2T", "16"]},
     "reference": "Llama 4 Behemoth：激活 288B、总 ~2T、16 routed 专家（训练中未发布）。verifier_v1 应核验 3 个数字——baseline 倾向漏 ~2T 总参。"},
    {"id": "T102", "split": "fresh",
     "source": "LLM 家族 KB · qwen.md（llm-kb-digest.md §3, 2026-07-24）", "version": "verify-2026Q3-v3",
     "prompt": "Qwen3 旗舰 235B-A22B 的 routed 专家数 + 每 token 激活专家数（精确）？",
     "rubric": {"type": "contains", "required": ["128", "8"]},
     "reference": "Qwen3-235B-A22B: 128 routed 专家 + 每 token 激活 8。verifier_v1 应核验 2 个专家架构数——baseline 倾向估 64/16 或 256/16。"},

    # ---------- READING_COMPREHENSION 第二批 T109-T118（2026-07-24 第二十轮，cohort=2026Q3-rc3）----------
    # 目的：把 context_grounding_v1 的 K=5 真测放到 12 题（4×3）规模上，避开 n=6+K=1 的功效死锁；
    #       每题设计成"含原话短语 + 干扰段 + 不可同义改写命中"的子域。
    #       split：dev4(T109/T111/T114/T117) / hidden3(T110/T112/T116) / fresh3(T113/T115/T118)。
    {"id": "T109", "split": "dev",
     "source": "OpenAI function-calling 官方介绍片段（platform.openai.com/docs, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中描述 function calling 核心机制与安全边界的关键短语；不要用自己的同义词替换。\n原文：「Function calling lets a model output a structured JSON argument that the host application can route to a real function; the model is not making the API call itself and tools should be sandboxed.」",
     "rubric": {"type": "contains", "required": ["structured JSON argument", "host application", "tools should be sandboxed"]},
     "reference": "structured JSON argument / host application / tools should be sandboxed。context_grounding_v1 应逐字回指这三段短语，不能只用“函数调用”概括。"},
    {"id": "T110", "split": "hidden",
     "source": "Tailscale ACL 官方文档片段（tailscale.com/kb/1018, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中描述 default ACL 行为与覆盖范围的原文短语。\n原文：「If no ACL rules match a connection, the default policy applies; the implicit default is deny. ACLs are evaluated in order, and the first match wins; wildcards may be used in source and destination but are not allowed in field-level matchers like HTTP hosts.」",
     "rubric": {"type": "contains", "required": ["the default policy applies", "the first match wins", "not allowed in field-level matchers like HTTP hosts"]},
     "reference": "the default policy applies / the first match wins / not allowed in field-level matchers like HTTP hosts。"},
    {"id": "T111", "split": "dev",
     "source": "OpenAI embedding-v3 发布说明片段（platform.openai.com/docs/guides/embeddings, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 embedding-3 与 ada-002 维度差异的原文短语。\n原文：「text-embedding-3-small returns 1536-dimensional vectors and supports shorter output dimensions; text-embedding-3-large outputs up to 3072 dimensions. The older ada-002 model is fixed at 1536 dimensions and cannot be truncated.」",
     "rubric": {"type": "contains", "required": ["1536-dimensional vectors", "3072 dimensions", "fixed at 1536 dimensions and cannot be truncated"]},
     "reference": "1536-dimensional vectors / 3072 dimensions / fixed at 1536 dimensions and cannot be truncated。"},
    {"id": "T112", "split": "hidden",
     "source": "NATS JetStream 文档片段（docs.nats.io/nats-concepts/jetstream, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 stream retention 与 replay 行为的两条原文短语。\n原文：「JetStream supports both Limits-based and Interest-based retention. Replay policy can be set to instant for fast catch-up or replay-all for full event log replay.」",
     "rubric": {"type": "contains", "required": ["Limits-based and Interest-based retention", "instant for fast catch-up", "replay-all for full event log replay"]},
     "reference": "Limits-based and Interest-based retention / instant for fast catch-up / replay-all for full event log replay。"},
    {"id": "T113", "split": "fresh",
     "source": "Linux man page summary for `mount(8)`（man7.org/linux/man-pages/man8/mount.8.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `mount --bind` 与 read-only 重挂的原文短语。\n原文：「The mount command supports bind mounts via --bind and --rbind. To remount an existing mount read-only, use mount -o remount,ro.」",
     "rubric": {"type": "contains", "required": ["--bind and --rbind", "remount,ro"]},
     "reference": "原文精确短语 --bind and --rbind、remount,ro。context_grounding_v1 应逐字引用，不接受“支持 bind 与只读”这种改写。"},
    {"id": "T114", "split": "dev",
     "source": "Sphinx autodoc tutorial（sphinx-doc.org/en/master/usage/extensions/autodoc.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `.. autoclass::` 与成员选项 `members`、`undoc-members` 的原文短语。\n原文：「Use .. autoclass:: to document a class. With :members: it includes documented members; with :undoc-members: it also includes undocumented members. The order is alphabetical by default.」",
     "rubric": {"type": "contains", "required": [":members:", ":undoc-members:", "alphabetical by default"]},
     "reference": ":members: / :undoc-members: / alphabetical by default。"},
    {"id": "T115", "split": "fresh",
     "source": "PEP 8 — Style Guide for Python Code（peps.python.org/pep-0008/, 2026-07-24 固定摘录）", "version": "rc-2020-rc3",
     "prompt": "逐字引用下面材料中关于 import 分组、每组顺序的原文短语。\n原文：「Imports should usually be on separate lines; imports are grouped in the following order: standard library imports, related third party imports, and finally local application/library specific imports.」",
     "rubric": {"type": "contains", "required": ["on separate lines", "standard library imports", "related third party imports"]},
     "reference": "on separate lines / standard library imports / related third party imports。"},
    {"id": "T116", "split": "hidden",
     "source": "PostgreSQL EXPLAIN docs（postgresql.org/docs/current/using-explain.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `EXPLAIN ANALYZE` 与 plan reading 的原文短语。\n原文：「EXPLAIN ANALYZE actually runs the query and returns measured run time and row counts. Reading plans top-down helps catch overestimates; cost values are not seconds but planner units.」",
     "rubric": {"type": "contains", "required": ["actually runs the query and returns measured run time", "cost values are not seconds but planner units"]},
     "reference": "actually runs the query and returns measured run time / cost values are not seconds but planner units。"},
    {"id": "T117", "split": "dev",
     "source": "Apple Foundation Models docs（developer.apple.com/documentation/FoundationModels, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 session-based 推理与 guided generation 的原文短语。\n原文：「Foundation Models sessions carry state across requests; guided generation constrains tool calls to a JSON schema you provide. On-device inference never leaves the device.」",
     "rubric": {"type": "contains", "required": ["sessions carry state across requests", "constrains tool calls to a JSON schema you provide", "never leaves the device"]},
     "reference": "sessions carry state across requests / constrains tool calls to a JSON schema you provide / never leaves the device。"},
    {"id": "T118", "split": "fresh",
     "source": "GitHub Actions docs（docs.github.com/en/actions, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 job 依赖、矩阵策略的原文短语。\n原文：「Use needs: to express job dependencies so a job runs only after other jobs succeed. A matrix strategy runs the same job across a list of variables, including OS and language versions.」",
     "rubric": {"type": "contains", "required": ["needs: to express job dependencies", "matrix strategy", "OS and language versions"]},
     "reference": "needs: to express job dependencies / matrix strategy / OS and language versions。"},

    # ---------- })")
    print("All hashes locked. Tamper with any task field -> eval aborts.")
