# GitHub 上对你最有用的 100 个项目

> **筛选方法**：通过已连接的 GitHub 连接器，按你的身份（LLM 实证研究 / Agent OS·可信多智能体·治理 / 评估偏置·校准 / ReviewerSim·ML论文助手 / OPC 一人公司 / 考研 408 / 前端 Next.js·React）分 10 个领域检索，按 star 排序取头部、跨域去重，精选 100 个。
> **数据说明**：star 数为检索时快照（2026-07-24）；相关性由关键词匹配 + 人工归类得出，非普适排名。
> **诚实边界**：本列表基于 GitHub search API 的公开元数据，未逐一验证代码质量/活跃度；⭐ 高不代表适合你，请结合用途判断。

---

## A. LLM 评估与基准（偏置 / 校准 / 方法论）— 18

- [openai/evals](https://github.com/openai/evals) ⭐18995 — OpenAI 官方评估框架与开放基准注册表
- [open-compass/opencompass](https://github.com/open-compass/opencompass) ⭐7231 — 百模型·百数据集统一评估平台（你的偏置评估底座）
- [open-compass/VLMEvalKit](https://github.com/open-compass/VLMEvalKit) ⭐4298 — 多模态模型评估工具包
- [THUDM/AgentBench](https://github.com/THUDM/AgentBench) ⭐3597 — LLM 作为智能体的综合基准（ICLR'24）
- [modelscope/evalscope](https://github.com/modelscope/evalscope) ⭐3127 — 大模型高效评估与性能基准（兼实验追踪）
- [FreedomIntelligence/LLMZoo](https://github.com/FreedomIntelligence/LLMZoo) ⭐2939 — LLM 数据/模型/评估基准集合
- [beir-cellar/beir](https://github.com/beir-cellar/beir) ⭐2250 — 信息检索异构基准（RAG 评测基础）
- [Xnhyacinth/Awesome-LLM-Long-Context-Modeling](https://github.com/Xnhyacinth/Awesome-LLM-Long-Context-Modeling) ⭐2146 — 长上下文建模必读论文/博客
- [Barca0412/Introduction-to-Quantitative-Finance](https://github.com/Barca0412/Introduction-to-Quantitative-Finance) ⭐1577 — AI+金融量化（含 LLM/Agent/benchmark）
- [evalplus/evalplus](https://github.com/evalplus/evalplus) ⭐1783 — LLM 生成代码的严谨评估（NeurIPS'23）
- [MLGroupJLU/LLM-eval-survey](https://github.com/MLGroupJLU/LLM-eval-survey) ⭐1609 — LLM 评估综述官方页
- [OpenGenerativeAI/llm-colosseum](https://github.com/OpenGenerativeAI/llm-colosseum) ⭐1482 — 趣味对抗式 LLM 评估
- [pinchbench/skill](https://github.com/pinchbench/skill) ⭐1296 — OpenClaw 编程智能体基准（PinchBench）
- [ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench) ⭐1153 — LLM 写 GPU kernel 基准
- [carlini/yet-another-applied-llm-benchmark](https://github.com/carlini/yet-another-applied-llm-benchmark) ⭐1063 — 应用型 LLM 基准（安全视角）
- [suyoumo/ClawProBench](https://github.com/suyoumo/ClawProBench) ⭐817 — 智能体实时基准（确定性评分 + 重复试验可靠性）
- [The-FinAI/PIXIU](https://github.com/The-FinAI/PIXIU) ⭐878 — 金融 LLM 评估基准
- [MME-Benchmarks/Video-MME](https://github.com/MME-Benchmarks/Video-MME) ⭐787 — 视频多模态评估（CVPR'25）

## B. 多智能体框架（编排 / 治理）— 22

- [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) ⭐69491 — 多智能体「软件公司」框架
- [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) ⭐56036 — 角色扮演协作多智能体
- [openai/openai-agents-python](https://github.com/openai/openai-agents-python) ⭐28123 — OpenAI 轻量多智能体工作流框架
- [deepset-ai/haystack](https://github.com/deepset-ai/haystack) ⭐25991 — 生产级 LLM 编排（检索/Agent/RAG）
- [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) ⭐24717 — 生产级 LLM 软件 12 因素原则（治理参考）
- [openai/swarm](https://github.com/openai/swarm) ⭐21857 — OpenAI 轻量多智能体编排（教学）
- [microsoft/agent-framework](https://github.com/microsoft/agent-framework) ⭐12345 — 微软多智能体编排框架（Python/.NET）
- [raga-ai-hub/RagaAI-Catalyst](https://github.com/raga-ai-hub/RagaAI-Catalyst) ⭐16140 — 智能体观测/监控/评估
- [MervinPraison/PraisonAI](https://github.com/MervinPraison/PraisonAI) ⭐8509 — 低代码多智能体工作力
- [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) ⭐7684 — 元 harness + 策略/沙箱（agent-governance）
- [kyegomez/swarms](https://github.com/kyegomez/swarms) ⭐6979 — 企业级多智能体编排
- [InternLM/MindSearch](https://github.com/InternLM/MindSearch) ⭐6897 — 多智能体网页搜索引擎
- [open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent) ⭐6646 — 动态工作流编排（TS）
- [SolaceLabs/solace-agent-mesh](https://github.com/SolaceLabs/solace-agent-mesh) ⭐4968 — 事件驱动多智能体编排（A2A/MCP）
- [VRSEN/agency-swarm](https://github.com/VRSEN/agency-swarm) ⭐4495 — 可靠多智能体编排
- [LazyAGI/LazyLLM](https://github.com/LazyAGI/LazyLLM) ⭐3855 — 最简多智能体应用构建
- [agentuniverse-ai/agentUniverse](https://github.com/agentuniverse-ai/agentUniverse) ⭐2308 — 多智能体应用框架
- [trypromptly/LLMStack](https://github.com/trypromptly/LLMStack) ⭐2307 — 无代码多智能体
- [Kocoro-lab/Shannon](https://github.com/Kocoro-lab/Shannon) ⭐2134 — 生产级多智能体编排（Go）
- [trpc-group/trpc-agent-go](https://github.com/trpc-group/trpc-agent-go) ⭐1584 — Go 生产级 agent（A2A/AG-UI/MCP/评估/可观测）
- [ZHangZHengEric/Sage](https://github.com/ZHangZHengEric/Sage) ⭐1219 — 复杂任务多智能体
- [wanxingai/LightAgent](https://github.com/wanxingai/LightAgent) ⭐1184 — 轻量 OpenAI 兼容 agent（含 guardrails）

## C. 自主智能体 / Agent 应用 — 20

- [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) ⭐94309 — 多智能体金融交易框架
- [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) ⭐48921 — AI 生产力工作室（智能体/300+ 助手）
- [reworkd/AgentGPT](https://github.com/reworkd/AgentGPT) ⭐36286 — 浏览器内部署自主智能体
- [khoj-ai/khoj](https://github.com/khoj-ai/khoj) ⭐35953 — 自托管 AI 第二大脑（研究/智能体）
- [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) ⭐28591 — 自主深度研究智能体
- [Fosowl/agenticSeek](https://github.com/Fosowl/agenticSeek) ⭐26678 — 全本地 Manus 式自主智能体
- [Tencent/WeKnora](https://github.com/Tencent/WeKnora) ⭐18806 — 腾讯 LLM 知识平台（RAG+推理 agent+Wiki）
- [TransformerOptimus/SuperAGI](https://github.com/TransformerOptimus/SuperAGI) ⭐17635 — 开发者优先自主智能体框架
- [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) ⭐13776 — 自主 ML 研究技能（评审循环/实验自动化）
- [0x4m4/hexstrike-ai](https://github.com/0x4m4/hexstrike-ai) ⭐10458 — 自主网络安全 agent（MCP, 150+ 工具）
- [OpenBMB/XAgent](https://github.com/OpenBMB/XAgent) ⭐8524 — 复杂任务自主 LLM 智能体
- [osaurus-ai/osaurus](https://github.com/osaurus-ai/osaurus) ⭐7295 — macOS 原生 agent harness（持久记忆/加密身份）
- [BlockRunAI/ClawRouter](https://github.com/BlockRunAI/ClawRouter) ⭐6669 — agent-native LLM 路由（成本优化/x402 支付）
- [aiwaves-cn/agents](https://github.com/aiwaves-cn/agents) ⭐5955 — 数据驱动自进化自主语言智能体
- [kodu-ai/claude-coder](https://github.com/kodu-ai/claude-coder) ⭐5256 — IDE 内自主编程 agent
- [campfirein/byterover-cli](https://github.com/campfirein/byterover-cli) ⭐4925 — 自主编程 agent 的可移植记忆层
- [PurpleAILAB/Decepticon](https://github.com/PurpleAILAB/Decepticon) ⭐4891 — 红队自主黑客 agent
- [ruc-datalab/DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze) ⭐4391 — 自主数据分析科学家 agent
- [gptme/gptme](https://github.com/gptme/gptme) ⭐4369 — 终端内持久自主 agent
- [MemMachine/MemMachine](https://github.com/MemMachine/MemMachine) ⭐3341 — 通用 agent 记忆层

## D. 知识图谱 / GraphRAG / RAG — 10

- [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) ⭐94605 — 代码库转查询知识图谱（无向量库，AST 解析）
- [pingcap/autoflow](https://github.com/pingcap/autoflow) ⭐2959 — GraphRAG 对话知识库（TiDB 向量）
- [Azure-Samples/graphrag-accelerator](https://github.com/Azure-Samples/graphrag-accelerator) ⭐2411 — Azure 一键 GraphRAG
- [1517005260/graph-rag-agent](https://github.com/1517005260/graph-rag-agent) ⭐2287 — 融合 GraphRAG/LightRAG/Neo4j（含评估框架，贴合你的 ML论文助手）
- [raphaelmansuy/edgequake](https://github.com/raphaelmansuy/edgequake) ⭐2048 — Rust 高性能 GraphRAG（LightRAG 启发）
- [desplega-ai/agent-swarm](https://github.com/desplega-ai/agent-swarm) ⭐639 — 「你的公司智能体操作系统」（agentic OS）
- [codefuse-ai/CodeFuse-muAgent](https://github.com/codefuse-ai/CodeFuse-muAgent) ⭐774 — 知识图谱引擎驱动 agent 框架
- [LHRLAB/HyperGraphRAG](https://github.com/LHRLAB/HyperGraphRAG) ⭐431 — 超图结构 RAG（NeurIPS'25）
- [bibinprathap/VeritasGraph](https://github.com/bibinprathap/VeritasGraph) ⭐303 — 知识图谱&GraphRAG（多跳推理/可验证归因）
- [OriginTrail/dkg-engine](https://github.com/OriginTrail/dkg-engine) ⭐234 — 去中心化知识图谱网络节点

## E. 参数高效微调 / LoRA / 小模型 — 17

- [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) ⭐73472 — 100+ LLM/VLM 统一高效微调（ACL'24）
- [huggingface/peft](https://github.com/huggingface/peft) ⭐21442 — 参数高效微调 SOTA 库
- [predibase/lorax](https://github.com/predibase/lorax) ⭐3820 — 多 LoRA 推理服务（千级微调模型）
- [aiming-lab/MetaClaw](https://github.com/aiming-lab/MetaClaw) ⭐3472 — agent 持续学习/进化（微调/RL）
- [ashishpatel26/LLM-Finetuning](https://github.com/ashishpatel26/LLM-Finetuning) ⭐2965 — PEFT 微调合集
- [stochasticai/xTuring](https://github.com/stochasticai/xTuring) ⭐2670 — 个性化开源 LLM（预处理到微调）
- [ARahim3/mlx-tune](https://github.com/ARahim3/mlx-tune) ⭐1368 — Apple Silicon 上微调（MLX）
- [SakanaAI/text-to-lora](https://github.com/SakanaAI/text-to-lora) ⭐1294 — 超网络按文本描述适配 LLM
- [datawhalechina/base-llm](https://github.com/datawhalechina/base-llm) ⭐916 — 从 NLP 到 LLM 全栈教程（中文）
- [georgian-io/LLM-Finetuning-Toolkit](https://github.com/georgian-io/LLM-Finetuning-Toolkit) ⭐872 — 微调/消融/单测工具包
- [dvgodoy/FineTuningLLMs](https://github.com/dvgodoy/FineTuningLLMs) ⭐852 — 微调实战书配套代码
- [DaoyuanLi2816/can-i-finetune-this](https://github.com/DaoyuanLi2816/can-i-finetune-this) ⭐791 — **估算本地 GPU 能否微调（对你的 RTX 3060 6GB 直接有用）**
- [AutoArk/TinyEngram](https://github.com/AutoArk/TinyEngram) ⭐735 — Engram 架构研究（Qwen/SD）
- [arielnlee/Platypus](https://github.com/arielnlee/Platypus) ⭐625 — LoRA 微调 Platypus 系列
- [Leeroo-AI/mergoo](https://github.com/Leeroo-AI/mergoo) ⭐518 — 多 LLM 专家合并与训练
- [Joyce94/LLM-RLHF-Tuning](https://github.com/Joyce94/LLM-RLHF-Tuning) ⭐453 — PEFT 全流程（SFT+RM+PPO+DPO+LoRA）
- [wpydcr/LLM-Kit](https://github.com/wpydcr/LLM-Kit) ⭐552 — LLM 全流程 WebUI（含 LoRA/全参微调/知识库）

## F. 文献管理 / 论文工具 — 3

- [hans/obsidian-citation-plugin](https://github.com/hans/obsidian-citation-plugin) ⭐1333 — Obsidian 学术引用插件（你的文献笔记流）
- [vict0rsch/PaperMemory](https://github.com/vict0rsch/PaperMemory) ⭐573 — 浏览器文献管理器（ArXiv/OpenReview 自动识别+代码发现）
- [ResearchHelper/research-helper](https://github.com/ResearchHelper/research-helper) ⭐205 — 参考管理器（PDF 标注/Excalidraw 笔记）

## G. 实验追踪 / MLOps — 4

- [aimhubio/aim](https://github.com/aimhubio/aim) ⭐6201 — 易用且强大的开源实验追踪器
- [determined-ai/determined](https://github.com/determined-ai/determined) ⭐3224 — 分布式训练/超参搜索/实验追踪平台
- [neptune-ai/neptune-client](https://github.com/neptune-ai/neptune-client) ⭐623 — 基础模型训练实验追踪器
- [modelscope/evalscope](https://github.com/modelscope/evalscope) ⭐3127 — 评估兼性能基准（见 A 类，实验侧复用）

## H. 前端 / SaaS / 产品（OPC 可用）— 6

- [ixartz/SaaS-Boilerplate](https://github.com/ixartz/SaaS-Boilerplate) ⭐7305 — Next.js+Tailwind+Shadcn 全栈 SaaS 脚手架（OPC 起手）
- [medusajs/nextjs-starter-medusa](https://github.com/medusajs/nextjs-starter-medusa) ⭐2793 — Next.js 电商前端 starter
- [BCG-X-Official/agentkit](https://github.com/BCG-X-Official/agentkit) ⭐1947 — Next.js+FastAPI+LangChain 约束智能体 starter
- [NiGhTTraX/ts-monorepo](https://github.com/NiGhTTraX/ts-monorepo) ⭐1626 — TypeScript monorepo 模板（ReviewerSim/ML论文助手复用）
- [reliverse/relivator](https://github.com/reliverse/relivator) ⭐1558 — Next.js 15/React 19 电商模板（better-auth/polar）
- [Skolaczk/next-starter](https://github.com/Skolaczk/next-starter) ⭐995 — Next.js 起步模板（TS/Tailwind/Stripe/测试）

---

## 针对你身份的速读建议
- **评估偏置研究**：A 类是核心武器库；`opencompass` + `evalplus` + `beir` 可组成你的偏置/校准评测基线。
- **ReviewerSim / ML 论文助手**：B/C 的 `openai-agents-python`、`haystack`、`graphify`、`graph-rag-agent`（含评估框架）直接可借鉴；H 类模板加速前端。
- **本地算力（RTX 3060 6GB）**：E 类的 `can-i-finetune-this` 先算可行性，`LlamaFactory`+`peft` 做 ≤3B LoRA 验证。
- **OPC 一人公司**：H 类 SaaS 模板 + `agentkit` 是产品 MVP 起点；C 类 `gpt-researcher`/`khoj` 可作内容/研究杠杆。

## 未充分覆盖的方向（可再搜）
- **考研 408**：GitHub 上专门的 408 题库/笔记类项目较少且质量参差，未纳入上述 100（避免低相关噪音）。需要可再检索「408」「cs 考研」「王道/天勤 笔记」等。
- **Agent OS / 治理专项**：已通过 `omnigent`（agent-governance）、`12-factor-agents`、`humanlayer`、`desplega-ai/agent-swarm`（agentic OS）部分覆盖；若需更系统的「Agent OS 参考架构」类项目可再定向检索。
