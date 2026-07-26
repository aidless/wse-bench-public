# LLM 家族技术知识库 · 学习笔记（WorkBuddy 内化版）

> 源目录：`F:\test\2026-07-24-08-36-33\kb\`（24 文件，~532KB，构建于 2026-07-24）
> 用途：作为模型选型 / 架构对比 / 论文基线引用的**可信参考资产**。
> 维护准则（源自原库 index.md，须遵守）：所有数字标注来源与评测协议；无法确认的标「待验证」，不编造；协议以官方 LICENSE 原文为准。
> 诚实边界：本笔记是**二级提炼**，关键数字/协议须回查源文件与原始出处后再用于论文或对外承诺。

---

## 1. 资产结构（速记）

- 入口：`index.md`（横向对比总表 + 选型建议 + 勘误汇总）
- 7 家族条目：`llama / qwen / deepseek / mistral / gemma / glm / phi .md`（四维度：架构训练/能力评测/微调部署/Agent 特性）
- 7 篇 deepdive：`deepdive/*_deepdive.md`（机制推导 + 管线图）
- 5 篇国内：`domestic/{baichuan,yi,minimax,step,kimi}.md`
- 数据：`benchmarks.csv`(155 行：Family,Model,Benchmark,Score,EvalProtocol,Source,Notes)、`family_comparison.csv`(9 字段)、`comparison.xlsx`(双 sheet)

---

## 2. 7 主流家族速查表（决策用）

| 家族 | 架构主线 | 开源协议（商用边界） | 原生工具调用 | RTX 3060 6GB 最小可跑 |
|---|---|---|---|---|
| Llama | 3.x Dense / 4 MoE(iRoPE) | Llama Community License（**非 OSI，7 亿 MAU 门槛+署名**） | 3.1+ 原生；Llama4 待验证 | 8B Q4≈4.7GB / 3B Q4≈2GB |
| Qwen | 2.5 Dense / 3 Dense+MoE(混合思考) | Qwen3 全 Apache 2.0；2.5 部分 Qwen License | 原生 tool_call token | 7B 4-bit≈4.5GB；0.5/1.5B 全参 |
| DeepSeek | MoE(MLA+DeepSeekMoE) | **MIT**（最宽松） | V3.1+ 支持；R1 原版无 | R1-Distill-Qwen-1.5/7B 4-bit(1–4.8GB) |
| Mistral | 7B Dense(SWA+GQA) / Mixtral MoE | 混合（Apache 2.0 + MRL/MNPL 限制） | 多数原生 | 仅 7B Q4≈4.2GB（短上下文） |
| Gemma | Dense（交替注意力+GeGLU） | Gemma Terms（**非 OSI，月活/用途限制**） | 否（需微调） | 3 1B/4B Q4、3n E2B/E4B |
| GLM | Dense（1M 上下文, All Tools） | GLM-4 License（自定义，商用需免费登记+署名） | 原生（BFCL 81.00） | 9B 4-bit≈5.5–6GB（临界） |
| Phi | Dense（3.5-MoE 为 MoE） | **MIT** | 原生（部分） | 3.8B Q4≈2.2GB 很轻松；14B 超限 |

**协议陷阱（对外/商用前必查 LICENSE 原文）**：Llama(MAU 门槛)、Gemma(用途/月活限制)、GLM(登记+署名)、Mistral(部分 MRL/MNPL)。

---

## 3. 关键机制（deepdive 要点，引用前核对公式）

- **DeepSeek**：MLA（KV 压至低维潜变量，`kv_lora_rank`；文中量级 576 浮点 / KV 压缩 56×）→ DeepSeekMoE（细粒度专家+共享专家，无辅助损失均衡 `topk_method=noaux_tc`）→ GRPO（无 critic 组相对策略优化，R1 纯 RL）→ MTP（多 token 预测，投机解码≈1.8×）→ FP8 混合精度训练。
- **Qwen3**：混合思考（`/think` + thinking budget）→ QK-Norm（稳定大规模训练）→ 细粒度 MoE（如 235B-A22B 激活 22B，base 32K+YaRN→128K）。
- **Llama4**：iRoPE（无绝对位置嵌入的长上下文 RoPE）+ early exit + MoE（Scout 16 专家 / Maverick 128 专家）；Llama3 对齐管线 = 拒绝采样 SFT → DPO。
- **Mistral**：SWA（滑动窗口）+ Mixtral Top-K 路由；**训练透明度最低**（token 数/语料从未公开）。
- **Gemma**：交替注意力 + GeGLU + logit soft-capping + QK-norm；SigLIP 多模态；3n MatFormer 端侧可裁剪。
- **GLM**：All Tools 单模型统一 function calling/代码/检索；1M 上下文=位置编码外推+分阶段长上下文训练。
- **Phi**：合成数据范式（textbooks→phi-4 data recipe）+ PTS 后训练（教师模型提示式缩放）。

---

## 4. Agent OS / Agentic AI 主线选型建议（源自 index.md §2）

- 中文 + 原生工具调用 + 长上下文：**Qwen3**（Apache 2.0 商用友好）或 **GLM-4-9B**（中文/1M 强，需登记）；强推理+中文+MIT 选 **DeepSeek-R1 蒸馏小模型**。
- 端侧 / 6GB 本地实验（LoRA、Agent 原型）：**Phi-3/4-mini（MIT, Q4≈2.2GB）**、**Gemma 3 1B/4B**、**Qwen2.5-0.5/1.5/3B**、**Llama 3.2-3B**。
- 最大开放权重 + 生态成熟：**Llama 3.1/4**（工具链全），但协议非 OSI、Llama4 训练披露有限。
- 可复现推理研究：**DeepSeek-R1**（Nature 同行评审、方法论透明）是优质开放对象。
- **不推荐作中文 Agent 基座**：Mistral / Llama / Phi（英文-centric，需额外 SFT）。

---

## 5. 诚实边界（TMLR 视角最关键）

### 5.1 来源可信度偏差（跨家族横比第一陷阱）
`benchmarks.csv` 中 **DeepSeek-R1** 的 MMLU-Pro/AIME/MATH-500/GPQA 均标 `official (DeepSeek README)`；而 **Qwen3-235B-A22B (thinking)** 同等指标标 `third-party (pass@1, T=0.6)`。两者分数量级相近（MATH-500 97.3 vs 97.5），但**一为官方自报、一为第三方复测**。index 总表与 family_comparison.csv 的 Highlight 列**未区分来源**——直接横比需注意来源偏差，论文中引用须显式标注 official/third-party。

### 5.2 库内不一致（已自标注，引用前须复核）
- **index §5 滞后于 domestic 条目**：Step 已更正为「Step 3/3.5/3.7 Flash = Apache 2.0 开放权重」，Kimi 已更正为「K2 = Modified MIT」；总览仍写「多为 API / 待核实」。
- **MiniMax RoPE base 冲突**：技术报告正文 10,000 vs HF 文档 10,000,000（§7 待核实）。
- **Kimi 6GB 可行性**：题设「4-bit 可跑」被更正为「4-bit 全量≈8GB > 6GB，需 Q3/CPU offload」。
- **Step 题设更正**：「Step-2 300B+ 激活更少」实为 Step 3（321B/38B）。
- **小数/百分制混用**：index 写 MMLU-Pro 0.831，CSV 写 83.1（同值，表示不同，易误读）。

### 5.3 全部「待验证」高信号项（引用前一律回查）
- Llama4：arXiv 编号（2504.07524 实为 DGOcc，非 Llama4）、原生 function calling、训练细节(FP8/early exit)、共享专家数。
- Qwen：与 GPT-4o 同款 BPE（**不成立**，自研 151,643 词表）、各尺寸精确许可、官方 A2A 协议。
- DeepSeek：V3 训练成本「557.6 万美元」为估算；MTP「规划能力」学术存疑；蒸馏模型许可边界（MIT 但基座受 Qwen/Llama 约束）。
- Mistral：7B/Mixtral 预训练 token 数与语料构成（**从未公开**）；独立 Agent 基准缺失。
- Gemma：「29 种语言」实为 140+；「27B 从 Gemini 蒸馏」不成立（from-scratch 13T）；商用月活阈值待逐字核实。
- GLM：旗舰是否 MoE 未公开；OpenRAIL-M/200 万美元门槛说法官方无此文字；1M 大海捞针仅定性。
- Phi：Phi-3-mini 注意力为 MHA（非 GQA）；训练 tokens 论文 3.3T vs HF 4.9T 冲突；中文/多语无官方数字。
- 国内：Yi-VL 为 `yi-license`（非 Apache）；MiniMax/Kimi 许可与 6GB 可行性多处待核；Step 早期仅 API。

### 5.4 已确认的勘误（直接采用）
- Qwen2.5 ≠ GPT-4o 词表（自研 151,643 字节级 BPE）。
- Gemma 27B 为 from-scratch（13T），蒸馏仅 2B/9B。
- Phi-3-mini 为 MHA（`num_key_value_heads=32`），GQA 仅 Phi-3-small 与 Phi-4-mini。

---

## 6. 我的使用约定（WorkBuddy 内部）

1. 被问「选哪个基座 / 某家族架构 / 某协议边界」时，先查本笔记 §2–§4；涉及具体数字或对外/论文用途，回 `benchmarks.csv` 并核对 EvalProtocol/Source 列与 official/third-party。
2. 涉及「待验证」项（§5.3），**明确告知用户尚未确认**，不当作事实陈述。
3. 横比基准须显式标注来源类型（official vs third-party），不混用小数/百分制。
4. 商用部署前提示协议陷阱（§2 末行），建议核对 LICENSE 原文。
5. 库位置为临时 test 路径，正式复用前应迁移至 `F:\Research`（用户已声明研究知识库根）。
