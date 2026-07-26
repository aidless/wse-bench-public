import json

a = {}
a["T001"] = "AgentBench 全称 AgentBench: Evaluating LLMs as Agents，由清华大学 THUDM 团队（Xiao Liu 等）提出，发表于 ICLR 2024。"
a["T002"] = "HumanEval 包含 164 个 Python 编程问题，由 OpenAI（Mark Chen 等）发布。"
a["T003"] = json.dumps({"label":"empirical-only","reason":"该 claim 是模型在 MMLU 基准上的实测经验性结果，既非数学证明（proven），也非未验证假设（conjecture），属经验性陈述，需通过评测复现验证。"}, ensure_ascii=False)
a["T004"] = """## A2A 权限
- 仅允许经显式注册的 agent 身份建立 Agent-to-Agent 会话，拒绝匿名/未声明来源的连接。
- 每次跨 agent 调用强制携带最小权限的 scoped token，按任务而非全局授权，调用后即失效。
- 在 MCP 接入层做来源白名单与意图校验，禁止 agent 越权调用彼此的工具或读写对方的上下文。

## 密钥管理
- 所有 API key / LLM token 存于受保护环境变量或密钥管理服务，禁止硬编码、禁止写入日志与仓库。
- 密钥按租户隔离并定期轮换，接入层仅持短期凭据，长生命周期密钥不得直接进入 MCP 进程内存常驻。
- 对密钥做最小暴露面审计，任何第三方工具调用前先做脱敏，防止密钥随工具参数外泄。

## 注入防护
- 对来自其他 agent / 外部文档的每条消息做指令边界隔离（系统指令不可被载荷覆盖），禁止工具回显内容被当作指令执行。
- 对检索结果、工具输出做结构化解析与沙箱渲染，必要时加 prompt 护栏，阻断“忽略前述指令”类越权指令。
- 在 MCP 工具调用入口做输入校验与高危操作确认，防止通过构造载荷触发未授权写/删/外发。"""
a["T005"] = "GPT-4 由 OpenAI 发布，是一种多模态大语言模型（基于 decoder-only Transformer，支持文本与图像输入的生成式基础模型）。"
a["T006"] = json.dumps({"contribution":"提出 Transformer：完全基于自注意力机制、彻底摒弃循环与卷积的序列转换架构，以更高并行度与更强长程依赖建模成为后续大模型基石。"}, ensure_ascii=False)
a["T007"] = "SWE-bench 的核心评测目标是：给定真实 GitHub 仓库的 issue，评估 LLM 自动生成代码补丁并使其通过仓库既有测试套件、从而解决实际软件工程问题的能力。"
a["T008"] = json.dumps({"contribution":"提出基于 Transformer 编码器的深层双向预训练语言模型 BERT，以掩码语言建模(MLM)与下一句预测(NSP)捕捉双向上下文，大幅提升下游任务表现。"}, ensure_ascii=False)
a["T009"] = "LoRA 的核心思想是冻结预训练权重，仅向网络注入可训练的低秩分解矩阵（A、B）来近似权重增量，以极小可训练参数量实现高效参数微调。"
a["T010"] = """## 密钥管理
- LLM/检索后端的 API key 仅存于密钥管理服务或加密环境变量，严禁硬编码、严禁落日志。
- 按调用方签发短期、最小权限的访问令牌，混合检索 API 对外仅暴露网关端点，密钥不触达前端。
- 定期轮换密钥并审计调用方白名单，异常高频调用触发密钥吊销。

## 注入防护
- 对用户查询与召回文档做指令边界隔离，外部文本一律视为数据而非指令，禁止覆写系统提示。
- 工具/检索结果经结构化解析与沙箱渲染，阻断“忽略前述指令”类越权提示与跨站脚本注入。
- 对写入型操作（建索引、删文档）做二次确认与权限校验，防止经检索链路触发未授权变更。

## 速率限制
- 按 API key / 租户维度设令牌桶限流（QPS 与日额度双限），防止滥用与成本失控。
- 对嵌入与重排序等重计算环节做并发上限与排队，保护向量库与 GPU 资源。
- 返回 429 时携带 Retry-After，并区分鉴权失败(401)与限流(429)，便于调用方正确处理。"""
a["T011"] = json.dumps({"framework":"AutoGen","abstraction":"conversable and customizable agents","domain":"mathematics"}, ensure_ascii=False)
a["T012"] = json.dumps({"framework":"Tree of Thoughts (ToT)","generalizes_from":"Chain of Thought (CoT)","cot_rate":"4%","tot_rate":"74%"}, ensure_ascii=False)
a["T013"] = json.dumps({"category":"Bug","component":"tool-call cancellation handler / consumer loop","evidence":"causing the consumer loop to block forever."}, ensure_ascii=False)
a["T014"] = "该 issue 修复了 docs 中 1 个 broken outbound link，使用 Wayback（archive.org）存档快照替换失效链接。"
a["T015"] = "TMLR 鼓励作者上传 data 或 code 等补充材料以提升可复现性，补充材料上限为 100MB，且必须采用 PDF 或 ZIP 格式。"
a["T016"] = "TMLR 在审稿中强调 technical correctness 而非 subjective significance，并将整个评审流程托管于 OpenReview 平台。"
a["T017"] = "Multi-head Latent Attention (MLA) 作为 KV 缓存压缩机制，由 DeepSeek 家族（DeepSeek-V2）首次提出。"
a["T018"] = "Qwen3 系列采用 Apache 2.0 开源协议，对商用友好（允许自由商用、修改与再分发）。"
a["T019"] = "在主流大模型家族中，DeepSeek 与 Phi 系列采用最宽松的 MIT 协议。"
a["T020"] = "Llama Community License 对商用的核心限制是设月活跃用户门槛（约 7 亿），超限需单独商业许可，并要求署名、不得使用 Llama 名义进行品牌化。"
a["T021"] = "Mistral 7B 在 7B 密集模型中率先采用 Sliding Window Attention (SWA) 限制注意力跨度。"
a["T022"] = "Llama4 为支持超长上下文引入了 iRoPE（交错 RoPE，去除绝对位置嵌入）这一无需绝对位置编码的 RoPE 变体。"
a["T023"] = "Qwen3 采用如 235B-A22B（激活 22B）的细粒度 MoE 配置，并提供/think 混合思考模式（可调 thinking budget，思考/非思考切换）。"
a["T024"] = "DeepSeek 的多 token 预测（MTP）机制带来的投机解码加速比约为 1.8×（约 1.8 倍）。"
a["T025"] = "GLM 系列在工具调用上的统一范式称为 All Tools（单一模型统一处理 function calling、代码执行与检索）。"
a["T026"] = "Phi 系列训练数据的核心范式源自高质量合成数据（textbook-quality 合成数据 / text-to-data 配方）。"
a["T027"] = "Gemma 架构中用于稳定训练/限制 logit 的非线性技巧包括 logit soft-capping（限制 logit 幅度）与 QK-norm（Query/Key 层归一化）。"
a["T028"] = "Llama3 的后训练对齐管线依次包含：拒绝采样监督微调（Rejection-sampled SFT）→ 直接偏好优化（DPO）。"
# T029/T030/T031: open-source placeholder probes. Replace REPLACE_* with your own
# private/local KB values to instantiate the closed-book probe on your machine.
# The author's v1 private values remain in their private archive, not the repo.
a["T029"] = "REPLACE_WITH_YOUR_KB_PAPER_COUNT 篇论文，embedding=REPLACE_WITH_YOUR_EMBEDDING_MODEL，索引=REPLACE_WITH_YOUR_VECTOR_INDEX。"
a["T030"] = "自治 agent 进化基因=组件 A(REPLACE_WITH_COMPONENT_A_NAME, REPLACE_WITH_COMPONENT_A_COUNT 条规则) + 组件 B(REPLACE_WITH_COMPONENT_B_NAME)。"
a["T031"] = "REPLACE_WITH_VERIFY_STRATEGY_NAME 在求解后独立复核 REPLACE_WITH_DIMENSION_1、REPLACE_WITH_DIMENSION_2 等维度。"

with open("__WSE_REPO_ROOT__/submissions_candidate_selective.json","w",encoding="utf-8") as f:
    json.dump(a, f, ensure_ascii=False, indent=2)
print("WROTE", len(a), "entries")
