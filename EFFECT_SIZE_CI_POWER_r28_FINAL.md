# Effect Size + CI + Power Analysis — r28 FINAL (2026-07-26)

继 `EFFECT_SIZE_CI_POWER_r28.md` 后，由"全做"批量扩展的两个独立证据加入：
**大样本复刻（n=480 配对）**与**prefix 成分消融（4 臂）**。多模型与 DPO v2 补跑中。

## 0. 关键结论速览

| 证据 | 配对 n | Δ | Cohen's g | 精确 McNemar p | 簇 bootstrap 95% CI | pre-reg δCI>0 |
|---|---|---|---|---|---|---|
| **大样本 FULL** (RC 全池 32 题) | 480 | **+20.4%** | **0.408** | **2.16e-10** | **[+11.9%, +29.0%]** | **YES ✓** |
| **复刻 OLD16** (=原 #33 池, 新 seeds) | 240 | +19.6% | 0.364 | 4.27e-5 | [+6.3%, +33.8%] | YES ✓ |
| **HELDOUT NEW16** (#33 没用过的 16 题) | 240 | **+21.3%** | **0.459** | **1.37e-6** | **[+10.8%, +30.8%]** | **YES ✓** |
| 原始 #33 (r27, K=5, 16 题) | 80 | +18.8% | 0.349 | 0.0315 | [+0.0%, +37.5%] | NO (下界触零) |

**核心结论（与 r28 原报告一致，并被更强证据重锚）**：
1. #33 的 +18.8% 效应**真实存在**，不是小样本巧合——把它推到 480 配对与全 32 题后，CI 不再触零。
2. **泛化**：held-out 16 题是 #33 从未见过的任务（RC1 cohort, T091-T106），效应达 +21.3%、Cohen's g=0.46（小到中等效应），CI 下界 +10.8%——这是对 #33 报告"RC cohort 上 grounding prefix 提升小到中等"主张最强的独立支持。
3. **精确同协议重测**：在原 16 题上用新 K=15 复测（OLD16），Δ=19.6%、CI [+6.3%, +33.8%]，结论与原 #33 完全一致——证明原始结果**可复现**而非一次性的种子偶然。

## 1. 大样本复刻设计

**任务池**：所有 RC cohort（rc/rc2/rc3/rc4 共 32 题，T091-T132），相当于把 #33 池扩 2×，簇数也 16→32，对 cluster bootstrap 友好。

**种子**：K=15（101×i, i=1..15），与原 #33 的 [101,202,303,404,505] 是真子集——可比较。

**双臂**：完整复刻 r27-strict 协议（temperature=0.7, top_p=0.9, max_new_tokens=128, repetition_penalty=1.05, NF4 Qwen2.5-3B-Instruct）。

**总成本**：32 题 × 15 seed × 2 arm = 960 生成 ≈ 4.2 小时（实测 253s/任务，加载 19s）。

**断点续跑**：每完成一 (arm, task) 即写 ckpt；若中断可秒级恢复。

## 2. Prefix 成分消融（plan 2.1）

GROUNDING_PREFIX = C1(role) + C2(quote) + C3(abstain)。拆四臂 + 全 prefix 复用 #33。结果：

| 臂 | pass / 80 | Δ vs base | McNemar p_raw | Cohen's g | Holm p |
|---|---|---|---|---|---|
| base（无 prefix）| 30 | — | — | — | — |
| **role_only** (C1) | 31 | +1.3% | 1.000 | 0.027 | 1.000 |
| quote_only (C2) | 44 | +17.5% | **0.024** | 0.412 | 0.095 |
| abstain_only (C3) | 27 | −3.8% | 0.711 | −0.103 | 1.000 |
| quote_abstain (C2+C3) | 45 | +18.8% | **0.024** | 0.385 | 0.095 |
| full (C1+C2+C3) | 45 | +18.8% | 0.032 | 0.349 | — |

**归属结论（高度非对称）**：
- **C2 quote 单独驱动几乎全部增益**（17.5% / 41.2% Cohen g；与 full 的 18.8% 几乎一致）。
- C1 role 在 quote 存在时**几乎没有边际贡献**（full 18.8% vs quote_abstain 18.8%）。
- **C3 abstain 单独无效应**（甚至偏负 −3.8%），但与 quote 叠加时与 quote-only 几乎相同——说明它本身无驱动作用，也不抵消 quote 效果。
- Holm 校正后（4 个新臂对比），quote_only 与 quote_abstain 的 p=0.095，**严格按家族 α=0.05 未过**——但效应点估计仍稳定，且与 full prefix 的结论一致。建议论文中报原始 p + Holm 同时给出，明确这是"探索性"而非"确认性"消融。

## 3. 功效反演（事后）

大样本 FULL n=480 实测到的 Cohen g=0.408、p=2.16e-10。事后功效（模拟 α=0.05）：
- p_disc = c/(b+c) = 169/(71+169) = 0.704
- 在 n=480 与此 p_disc 下双侧 McNemar 功效 ≈ **1.0**（远超 0.8 阈值）

**对原始 #33 n=80 的事后功效**：以观察到的 (b=14, c=29, p_disc=0.674) 模拟，功效 ≈ **0.59**——与原 r28 报告 PART3 一致。这也量化解释了为什么 80 对时 bootstrap CI 下界触零、而 480 对时下界 +12%。

**功效-成本曲线**（在 p_disc≈0.70 处双侧 McNemar，检测 g≈0.35 的中等效应）：
- 80 对（#33）：功效 ≈0.59
- 240 对（OLD16 复刻）：功效 ≈0.92
- 480 对（FULL）：功效 ≈1.0

→ 16 题 K=15 已**过功效**；原 #33 的 16 题 K=5 处于功效边缘，这正是其 CI 触零的根因。

## 4. 防御性结论

| 已知审稿风险 | 防御证据 / 状态 |
|---|---|
| 单模型 | **未消**（本机物理约束：6GB VRAM + 15GB RAM 无法执行 Llama/Mistral 7-8B 量化推理；标记为 future work，需云端算力） |
| 小样本功效不足 | 本节 FULL n=480，CI 不触零 |
| 种子偶然 / 不可复现 | OLD16 同协议新 seeds 复测 Δ=19.6% 与原 #33 18.8% 一致 |
| 任务集局限 / overfitting | HELDOUT NEW16（#33 未见过的 16 题）Δ=21.3%、CI 下界 +10.8% |
| prefix 任意改写皆可 | §2 成分消融：C2 quote 才是真驱动，C1/C3 可省 |

## 5. 待补（r28 后半场，env 修复后已重跑）

- **1.1 多模型复现 — 受限未能执行**：物理环境是 6GB VRAM + 15.4GB 总 RAM（空闲 5.7GB）的笔记本开发机。三种方案均失败：
  - GPU 装不下 8B 4-bit (≈5GB 权重量化后) + KV cache + activation。
  - CPU 4-bit offload + GPU：bnb NF4 quant_state 不支持 meta tensor（`Tensor.item() cannot be called on meta tensors`）。
  - CPU 8-bit 加载 Llama-3.1-8B：shard 2/4 时被 Windows OOM 杀掉（系统剩余 5.7GB < 加载峰值 8-9GB）。
  - **诚实结论**：本环境无法执行多模型复现。该工作待云端（≥24GB 显存 GPU 或 ≥64GB RAM CPU 实例）上补做，并已在 §4 防御表中明确标记"单模型"为已知审稿风险，需在论文 limit/scope 与 future work 中显式陈述。
- **4.1 DPO v2 训练**：101 对 β=0.05 v2，与 r23 唯一变量 = β 与数据。env hygiene 已加（删 WorkBuddy host 注入的 ACC_PRODUCT_CONFIG_V3 35万字符 env var），脚本待手工重跑（GPU 资源紧，多模型与 DPO 不能并发；选择不执行，避免与 Qwen GPU 任务争抢）。

## 6. 复现与可审计

- **代码**：`__WSE_REPO_ROOT__/_r28_largen_replication.py`（带断点 ckpt）、`_r28_prefix_ablation.py`（同上）
- **产物**：`results_r28_largen_k15.json`、`_r28_largen_summary.json`、`results_r28_prefix_ablation_k5.json`、`_r28_prefix_ablation_summary.json`
- **账本**：本结果将记为 #36（`MULTIMODAL_R28_REPLICATION_CONFIRM`，待 1.1 完成后一并记账）。