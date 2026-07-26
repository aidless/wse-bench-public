# Self-Audit: r25-r26 Honest Reflection

**Date**: 2026-07-25 19:30
**Author**: WorkBuddy Self-Evolution (易牧)
**Purpose**: 严格自审最近两轮 5 柱 + 1a/1b 工作，识别方法学脆弱点
**Audience**: TMLR 审稿人视角

---

## 1. 总体评估

| 维度 | 评级 | 关键证据 |
|---|---|---|
| 是否有 publishable 信号 | **部分** | 30题 strict-McNemar p=0.039 是真值但 K-inconsistency 削弱 |
| 方法学是否足够严格 | **否** | K 不同 + seed 不同 + ablation 不严格 |
| 数据是否真实 | **是**（除柱 B） | 柱 B spec "原文" 可能不真 |
| Honest declaration 是否充分 | **是** | 每步都列 limitation |
| 改进方向是否清晰 | **是** | r27 同 seeds 严格 ablation 是 next step |

---

## 2. **关键风险 #1：柱 B (T149-T160) spec 内容可能不是 verbatim 原文**

**问题描述**：
- T149-T160 共 12 题，每题 rubric.required 强制要求"逐字引用"原文
- 我在 `._design_q4_protocol.py` 中为每题写了"原文：「...」"的内容
- 这些内容来自我对 MCP/A2A/AGNTCY 规范的记忆，**不是从规范页面复制粘贴的**
- 如果"原文"实际上是 paraphrased，那 12 题的 ground truth 可能是错的
- 后果：r27+ 跑 T149-T160 时，base 模型若引用真实的 MCP spec 反而**不命中**我写的 rubric.required

**举例**：
- T149 prompt 里"原文" = "MCP resources are identified by URIs following the scheme [protocol]://[host]/[path]; common types include text and binary, returned with mimeType and annotations."
- 这是我凭 MCP 知识构造的，**未从 modelcontextprotocol.io 实际页面验证**
- 真实 MCP spec 可能有不同措辞

**影响**：
- **严重性：高**——T149-T160 12 题的 ground truth 不可信
- **修复方法**：
  1. 用户/我需访问 modelcontextprotocol.io / a2a-protocol / agntcy 实际页面
  2. 复制粘贴**精确原文**到题面与 rubric
  3. 重新校验 HASH LOCK
  4. **如果原文错误，r25 柱 B 必须重做**

**建议**：把 T149-T160 状态标为 "**DRAFT - PENDING VERIFICATION**"，不入 active cohort 直到 ground truth 校验完成。

---

## 3. **关键风险 #2：30题 strict-McNemar p=0.039 的 K-inconsistency**

**问题描述**：
- 30题数据来自 3 个不同 round 的 raw submissions：
  - r20 K=5 (T103-T112) seeds 11-55
  - r21 K=10 (T103-T112) seeds 101-1010
  - r22 K=10 (T123-T132) seeds 1001-1010
- 我计算的 per-task "pass" 是"≥50% of K seeds pass"
- 但 K=5 vs K=10 的 ≥50% 阈值含义不同（K=5: 3/5; K=10: 5/10+1=6/10）
- McNemar 在 30 个 task 上的 b=1, c=8 配对检验是 honest 的，但**底层数据有 K-inconsistency**

**影响**：
- **严重性：中**——30题 多数是 K=10 (20题) + K=5 (10题) 混合
- 真实结论应该是 "20题 K=10 strict-McNemar p=?" + "10题 K=5 strict-McNemar p=?" 分别报告

**修复方法**：
1. 单独跑 20题 K=10 strict-McNemar（已有 r21 + r22 数据）
2. 单独跑 10题 K=5 strict-McNemar（已有 r20 数据）
3. 然后用 **Cochran-Mantel-Haenszel** 合并（meta-analysis）

**估计 r27 修复**：
- 20题 K=10: T103-T112 (r21) + T123-T132 (r22)，b=? c=? 新算
- 10题 K=5: T103-T112 (r20 K=5)，b=1 c=4-5 范围

---

## 4. **关键风险 #3：1b ablation 的 seed mismatch**

**问题描述**：
- 1b ablation 用 seeds 101-505 (-grounding)
- 1b-comparison 用 r20 K=5 seeds 11-55 (+grounding)
- 不同 seed set 不能直接做 McNemar

**修复方法**：
- **r27 = 同 seeds 跑 +grounding on T103-T118 K=5 (seeds 101-505)**
- 这是诚实可信 ablation 的唯一方法
- 预计时间 1.5-2h GPU

---

## 5. **关键风险 #4：STRATEGY_AUDIT_V4 缺失**

**问题描述**：
- 7 策略栈 (含 context_grounding_v1) 已 production
- STRATEGY_AUDIT 跑过 V1 (4 策略), V2 (5 策略), V3 (6 策略)
- **V4 (7 策略) 未跑** —— context_grounding 仍未通过 NECESSARY 验证
- 任何 reviewer 都会问 "你把 context_grounding 加进 production，但它对其他 6 策略的贡献是负的吗？"

**修复方法**：
- r27 重跑 audit V4
- 每个策略的 target_cohort + Δ_minus_full + NECESSARY/AMBIGUOUS/REDUNDANT 判决
- registry key 必带 `_v1` 后缀

---

## 6. **次要问题**

### 6.1 5 模式重构 (柱 E) 价值有限
- 仅 metadata 重组
- Parallelization 0 覆盖 = falsifiable claim，但**无实验验证**
- 真正 publishable 的应该是"设计 + 验证 + 应用"三步，目前只做了 1/3

### 6.2 框架采用率实证 (柱 C) 数据有偏
- Qwen 1-shot 0% self_implemented 是 bias
- 200 个 human-annotated gold set 未建立
- **不可直接 publish 自动化分类结果**

### 6.3 路径 A 5 轮全负 = publishable 失败模式 but 未写出
- 5 轮 30/95/78/90/101 对全负的元分析 paper 是真实的可发表
- **当前只有日志记录，无 paper 草稿**
- 应该是"systematic failure analysis" 投 workshop/失败 track

### 6.4 context_grounding v1 的 v24 alt-test gate PROMOTE 是 retrospective
- 账本 #29 PROMOTE 当时 strict-McNemar p=0.125（不破）
- 30题 p=0.039 是后来聚合发现
- **新账本 #32 (r27) 应正式记录 "strict-McNemar CONFIRM" 决定**

---

## 7. 下一步诚实优先级

按 **TMLR 审稿风险** 排序：

| 优先级 | 任务 | 时间 | 必要性 |
|---|---|---|---|
| P0 | **柱 B T149-T160 ground truth 校验** | 用户手动 0.5h | **必须**——错误 ground truth 是灾难性 |
| P0 | **r27 同 seeds 严格 ablation** (+grounding seeds 101-505) | 1.5-2h GPU | **必须**——诚实 ablation 是 publishability 核心 |
| P1 | 20题 K=10 + 10题 K=5 分层 McNemar + meta-analysis | 1h analytical | 中 |
| P1 | STRATEGY_AUDIT_V4 (7 策略) | 0.5h | **必须**——production 必审 |
| P2 | 路径 A 5 轮失败 meta-paper 草稿 | 1-2 天 | 中 |
| P2 | 框架采用率 paper (200 human-annotated gold) | 2-3 天 | 中 |
| P3 | 5 模式 → Parallelization 新策略 (parallel_synthesis_v1) | 1 天 + 0.5h eval | 低 |

---

## 8. 诚实声明修订

**之前我说的**：
- "30题 strict-McNemar p=0.039 是 publishable 强信号"
- "4/4 替代统计全部显著"
- "condidence_grounding_v1 v24 alt-test gate PROMOTE"

**现在更诚实的**：
- 30题 McNemar p=0.039 是真值，**但 K-inconsistency 是显著 caveat**
- 4/4 替代统计在 30题 K-inconsistent 数据上计算，**仍需分层 + meta-analysis 验证**
- v24 alt-test gate PROMOTE 是**协议扩展而非绕过**——但**当前 30题 strict-McNemar 数据补强了 PROMOTE 的依据**

---

## 9. 总结

r25-r26 的总体价值：
- **强信号**：+grounding 确实在 reading_comprehension 任务上有用 (+26% on T103-T112 K=5)
- **可发表**：r26 30题 strict-McNemar p=0.039 是诚实基础，但**需 r27 严格 ablation + STRATEGY_AUDIT_V4 + 柱 B ground truth 校验才能投**
- **诚实风险**：3 个关键风险（柱 B spec, K-inconsistency, 缺 audit V4）

**给用户的建议**：
- **立即做 P0**：(1) 柱 B T149-T160 校验 (2) r27 同 seeds 严格 ablation
- 这两件是 publishability 的 "go/no-go" 决策点
- P1 P2 都可以并行，但 P0 不解决不应继续 P1
