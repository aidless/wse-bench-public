# WSE-Bench 周度自进化闭环 · Evolution Note (r28 / 2026-07-25 周六)

> 协议: eval-gated 周度闭环 (WSE-Bench 多 seed + 能力画像 + headroom 预检 + 预注册 + STRATEGY_AUDIT)
> 最高律令: 反 Goodhart — 绝不为过题改题面/答案; 哈希失配立即中止; 宁 HOLD/FAILED 不凑 PROMOTE; 所有审计结论须有原始数据支撑。

## 本周决策: STEADY_STATE / 无新 PROMOTE (账本 #36)

诚实结论: **本周无候选具备合法的新 headroom, 因此不运行任何模型层实验, 记 STEADY_STATE。** 这是反 Goodhart 的正确行为, 而非停滞。

---

## 1. 完整性门 (强制, 通过)
| 门 | 结果 |
|---|---|
| `--verify` | **HASH LOCK: OK** (无失配, 不中止) |
| `--selfcheck` | overall=**0.782**, **verified=True** |

直答零分项全部符合设计预期, 无异常:
- hard `T047-T060` (14题) 直答全 0 — 预期 (headroom 设计)
- sv `T073-T084` (12题) 直答全 0 — 预期
- rc4 `T124/T126-T132` 直答 0 = headroom 设计 (该 cohort base 4/10)
- 声明校验通过: rc `T091-T096` / rc2 `T103-T108` / rc3 `T109-T118` 直答均 1.0

## 2. 分片 (`--cohort-report`)
- **156 题 / 14 cohort**, 13 active + 1 archived (`2026Q3-core` 34题按季度轮换归档, 仍锁 hash 不计门)
- active: ext / reason / hard / struct / sv / fact / rc / verify / rc2 / rc3 / rc4 / Q4-core / Q4-protocol
- 轮换策略: quarterly, window=4季度

## 3. 能力画像 (`--capability-report`) + 自提议 (`--propose-mutations`)
生产栈 v102 (5轴):
| 轴 | 覆盖 | 生产均分 | baseline 均分 |
|---|---|---|---|
| fact_recall | 85% | 1.000 | 0.577 |
| selective_retrieval | 100% | **0.964** (最弱) | 0.688 |
| reasoning | 82% | 1.000 | 0.583 |
| structured_output | 76% | 1.000 | 0.813 |
| reading_comprehension | **28%** | 1.000 | 0.933 |

- **最弱轴 = reading_comprehension, 判据=欠测量 (覆盖28%)**: v102 结果文件是第16轮(102题)生成, 滞后于当前156题; rc2/rc3/rc4/Q4 新题未纳入。这是**测量缺口, 非表现缺口**。
- 自提议: 步骤0 提示下轮须对 `T103-T132` 做 K=5 盲测重建生产/baseline 聚合; **无对口未晋升候选** (context_grounding_v1 已晋升)。

## 4-9. 实验决策 (为何本周不跑)
| 方向 | 状态 | 本周动作 | 依据铁律 |
|---|---|---|---|
| decompose_v1 (唯一未晋升候选) | #10 HOLD, 零 headroom | **跳过** | 已 HOLD 候选无新 headroom 不重跑 |
| 路径 A (权重级) | 5 轮全 HOLD/FAILED | **跳过** | 无 ≥500 独立数据, 不重复相同配置 |
| context_grounding_v1 | **已 PROMOTE** (#29) + strict 确认 (#32/#33) | 见风险栏 | — |
| STRATEGY_AUDIT | 7 策略栈全 NECESSARY (V1-V4) | 无新策略, 不重跑 | 新增策略后才重跑全栈 |

> **重要修正**: 自动化 prompt 文本 (称"118题/11 cohort/六策略/context_grounding 未晋升") 为**滞后描述**。实际状态: 156题 / 14 cohort / **7 策略生产栈** / context_grounding_v1 已于第22轮 #29 PROMOTE、第27轮 #32/#33 strict 确认 NECESSARY。本 note 以实际状态为准。

## 生产栈 (7 策略, 全 promoted + audited NECESSARY)
`selective_retrieval_v1` · `tool_arith_v1` · `schema_guard_v1` · `self_verify_v1` · `citation_check_v1` · `verifier_v1` · `context_grounding_v1`

## 一致性审计 (步骤6 铁律, 全绿)
- 账本 `delta_overall` 字段统一: **OK**
- registry 顶层 promoted (7) == per-entry promoted=True (7): **OK**
- audit key `_v1` 后缀: **OK**

## 首要未解决风险 (下季度优先项)
1. **context_grounding_v1 严格稳健性 (接账本 #35)**: PROMOTE 走的是 v24 替代统计量门 (#29 strict-McNemar p=0.125) + 后续 strict 确认 (#32 p=0.039 / #33 p=0.032)。但 #35 效应量分析 (从原始 (task,seed) 配对重算, b=14/c=29/p=0.031539 与账本一致) 揭示: **cluster-bootstrap CI 下界触 0、事后功效仅 0.59、Bonferroni α=0.025 下两门均不单独过**。→ 严格预注册 delta-CI 规则**未完全满足**。达 80% 功效需 ~470 配对 (~94题@K=5)。**不得据现有证据用"机制正确"为由强化 claim**。
2. **单模型验证**: 全部证据来自 Qwen2.5-3B 单 base, 多模型验证是 P1。
3. **路径 A 根本数据约束**: 权重级自进化仍未成功, 卡在 ≥500 独立训练对 (0/1 rubric 使 DPO pair 数受限, 需 arxiv benchmark 训练子集)。

## 已消解
- **P0 (Q4-protocol T149-T160 出处风险)**: 已于账本 #34 `REANCHOR_VERIFIED` 处理 (见 `PILLAR_B_VERIFICATION_r28.md`)。

## 硬边界遵守声明
未改任何论文 claim/数字/TMLR/业务代码; 未删任何文件; 未改 bench_manifest 题面/答案 (仅 append 账本 #36); ground-truth 全部可复跑; GitHub 项目实测 1517 个 (非未完成目标写成已完成)。
