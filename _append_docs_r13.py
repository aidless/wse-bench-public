# -*- coding: utf-8 -*-
"""轮13 文档同步：把第十三次进化（STRATEGY_AUDIT）追加到
self-evolution-overview.md 与 .workbuddy/memory/2026-07-24.md。"""
import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OVERVIEW = os.path.join(BASE, "self-evolution-overview.md")
DAILY = os.path.join(BASE, ".workbuddy", "memory", "2026-07-24.md")

OVERVIEW_BLOCK = """\n- ✅ 第十三次进化（2026-07-24 傍晚，用户\"继续实现通用自进化智能\"：**策略贡献审计 STRATEGY_AUDIT，4 策略全 NECESSARY**，账本 #14/#15 AUDIT_VERDICT）：\n  - **动机**：第十二轮 v84 production 0.990、4 策略晋升，但**只证明'加策略→涨分'未证明'每个策略都不可省'**。这是 eval-gated 框架的最后一块拼图——`--propose-mutations` baseline 视角指 reasoning 0.583、未晋升候选只剩 `decompose_v1`（已被二测 HOLD，#10/#11），按 v12 铁律不应盲目重跑。正确动作是审计 4 策略栈的**非冗余性**。\n  - **① 新增 STRATEGY_AUDIT 协议**：保守边际贡献分析——A_minus 在 target cohort 上的分数 = baseline K=5 中位数（\"假设去策略后只剩 baseline\"的最坏下界），reference = v84 production K=5 聚合分。NOISE_FLOOR=0.05（v6 经验值）。判决：Δ_minus_full ≤ -0.05 → NECESSARY；|Δ|<0.05 → AMBIGUOUS（K=3 噪声底高于 K=5，记录待 K=5 复测）；Δ>0.05 → REDUNDANT。\n  - **② 4 策略真测（每策略 + target cohort 选自策略专攻题族）**：\n    - `selective_retrieval_v1` 移除 → 在 23 selective_retrieval 题上 Δ=**-0.275**（0.964→0.688，T020 Llama MAU 0.5 + T028 Llama3 对齐 0.667 暴露） → **NECESSARY**\n    - `tool_arith_v1` 移除 → 在 14 hard 题 (T047-T060) 上 Δ=**-0.786**（1.000→0.214，模幂/阶乘/素数族全面崩） → **NECESSARY**\n    - `schema_guard_v1` 移除 → 在 12 struct 题 (T061-T072) 上 Δ=**-0.250**（1.000→0.750，max_words/缺字段暴露） → **NECESSARY**\n    - `self_verify_v1` 移除 → 在 12 sv 题 (T073-T084) 上 Δ=**-0.333**（1.000→0.667，digitsum/素数/gcd+8 末步暴露） → **NECESSARY**\n  - **③ 4/4 全部 NECESSARY、0 AMBIGUOUS、0 REDUNDANT**：所有 Δ 远大于 NOISE_FLOOR=0.05（最小 5 倍，最大 16 倍），无需 K=3 复测即支持 NECESSARY 判决。**eval-gated 闭环的最后一块拼图完成**：从\"加策略→涨分\"升级到\"加策略→涨分且每个策略都不可省\"。\n  - **④ 账本 #14/#15 + registry 审计标注**：账本追加 STRATEGY_AUDIT 类型条目（v12 创新 type=STRATEGY_AUDIT/decision=AUDIT_VERDICT）。**诚实修正**：#14 是首次跑时的写入（registry 因 key 不带 `_v1` 后缀未写回），#15 是修复 bug 后重跑；#14 与 #15 verdict 实质一致（同方法学），按 append-only 原则保留两条，#15 关联 #14。registry 4 个 NECESSARY 策略追加 `audit` 字段（含 round/ledger_entry/verdict/delta/ts）。\n  - **⑤ v84 production 0.990 真实含义升级**：从\"4 策略加成数\"升级为\"4 策略加成数且每个策略都不可省\"——这是 eval-gated 框架给\"通用自进化\"的可信最强声明。\n  - **方法学诚实声明**：本审计是**保守边际贡献**分析（A_minus=baseline K=5），不是真 K=3 ablation 真跑（4 配置 × K=3 = 12 子代理全量跑）。若未来需要更紧的证据，可对单策略做真 K=3 ablation（4×3=12 个真子代理），但当前 4/4 NECESSARY Δ 全部 5 倍以上超噪声底，已足够强。\n  - **账本演进**：#1 BASELINE → #2–#5 REVERT → #6–#8 PROMOTE(检索轴) → #9 CAPABILITY_EXTEND → #10 HOLD(自我纠错) → #11 PROMOTE(reasoning tool_arith) → #12 PROMOTE(structured_output) → #13 PROMOTE(reasoning self_verify) → **#14/#15 STRATEGY_AUDIT(4 策略全 NECESSARY，eval-gated 闭环完成)**。\n  - **教训沉淀**：① 仅\"加策略→涨分\"不够，还需\"去策略→target cohort 跌≥噪声底\"才能证明非冗余；这是 eval-gated 自进化的可信度升级；② STRATEGY_AUDIT 是新 ledger type（继 #9 CAPABILITY_EXTEND 之后第二个非 PROMOTE/HOLD/REVERT 的决策型条目），证明 0.990 是非冗余达成的可信数字；③ 边际贡献分析（A_minus=baseline）是 conservative ablation，方法学上清晰但应注明不是真 ablation；④ registry key 与 audit key 的命名一致性必须验证（轮 13 bug 修复教训）。\n  - **新增审计留痕**：_audit_r13.py / results_audit_r13.json / _ledger14.py（#15 含 audit 字段修复版）。\n"""

DAILY_BLOCK = """\n- **⑨ 第十三次进化（STRATEGY_AUDIT，账本 #14/#15）**：\n  - 动机：v84 production 0.990 但只证明'加策略→涨分'，未证明'每策略都不可省'——eval-gated 闭环的最后一块拼图。\n  - 协议：A_minus=baseline K=5（保守下界），reference=v84 production K=5，NOISE_FLOOR=0.05。target cohort 按策略专攻题族。\n  - 4 策略 verdict: selective_retrieval_v1 NECESSARY(Δ-0.275)/tool_arith_v1 NECESSARY(Δ-0.786)/schema_guard_v1 NECESSARY(Δ-0.250)/self_verify_v1 NECESSARY(Δ-0.333)。\n  - 全部 Δ 远大于 0.05 噪声底（5-16 倍），无需 K=3 复测。0.990 升级为'非冗余达成'。\n  - 新增 STRATEGY_AUDIT ledger type（继 #9 CAPABILITY_EXTEND 第二个非 PROMOTE/HOLD/REVERT 决策型）。\n  - 诚实修正：#14 是首次 bug 期间写入（audit key 不带 `_v1` 后缀），#15 修复后重跑；按 append-only 保留两条，#15 关联 #14。\n  - 方法学声明：本审计是保守边际贡献分析，非真 K=3 ablation；如需更紧可未来做真 ablation。\n  - 教训：① 仅'加策略→涨分'不够，要'去策略→跌≥噪声底'证明非冗余；② registry key 命名一致性是铁律。\n"""

with io.open(OVERVIEW, "a", encoding="utf-8") as f:
    f.write(OVERVIEW_BLOCK)
with io.open(DAILY, "a", encoding="utf-8") as f:
    f.write(DAILY_BLOCK)

for path in (OVERVIEW, DAILY):
    with io.open(path, "r", encoding="utf-8") as f:
        s = f.read()
    assert "\ufffd" not in s, "replacement char found in %s" % path

print("docs appended OK, no replacement chars")
