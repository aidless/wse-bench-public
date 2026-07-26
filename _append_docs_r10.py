# -*- coding: utf-8 -*-
"""第十轮：追加 overview + 日 log"""
import io

OVERVIEW = r"F:\test\2026-07-24-08-21-57\self-evolution-overview.md"
DAYLOG = r"F:\test\2026-07-24-08-21-57\.workbuddy\memory\2026-07-24.md"

ov = """- ✅ 第十次进化（2026-07-24 午后，用户"继续实现通用自进化智能"：**headroom 预检铁律首次落地 + 首个 reasoning 轴 PROMOTE**，账本 #11 PROMOTE）：
  - **动机**：第九轮 #10 HOLD 的教训是"decompose_v1 无效未证实，是题无 headroom"。本轮按 v9 铁律执行：先造真难题、预检 headroom、再上对照。
  - **① 竞赛级难题 cohort=2026Q3-hard（T047–T060 十四题）**：大数模幂(T047-050)/阶乘位数和(T051-054)/区间素数计数(T055-058)/Fibonacci 模(T059)/CRT(T060)。ground truth 全部来自可复跑 python 命令（记录于 source 字段），prompt 锚定"最终答案：xxx"（全角冒号纯数字）防中间步骤假阳性。T047-052 dev / T053-060 hidden，reasoning 轴 10→24，全库 46→**60 题**（dev26/hidden24/fresh10）。哈希锁 OK。selfcheck 直答对 hard 全 0 分=预期（专为 headroom 设计）。
  - **② headroom 预检（K=3 两轮 9 seed，铁律首次落地）**：第一轮 8 题 P1-P3 全对（无 headroom，弃）；第二轮加大难度后确认模幂/阶乘位数和/素数计数三族直答基线系统性崩溃（拒答"未知"或滑错）→ 有真 headroom。**关键情报**：预检同时暴露 decompose_v1 在阶乘/素数族同样系统性拒答——失败模式="心算算术链过长"，分解不解决算术执行瓶颈。
  - **③ 预注册 tool_arith_v1（防事后编策略）**：据失败模式在主实验**前**把 `tool_arith_v1`（遇多步算术写最小 python 计算复核）预注册进 strategy_registry.json（含时间戳 2026-07-24T14:35）。策略空间 6→7。
  - **④ 三臂 K=5 盲测 + Bonferroni 双比较门（alpha=0.025）**：baseline B1-B5（**全新 seed 不复用预检 seed**，防 selection-on-noise）/ decompose D1-D5 / tool_arith A1-A5，共 15 份提交逐字留痕（submissions_hard_15seeds.json）。逐题中位数聚合：
    - **tool_arith_v1 vs baseline**：14/14 vs 3/14，discordant=(0,11)，McNemar **p=0.000977**，Δ=+0.786，bootstrap CI **[0.571, 1.000]** → **PROMOTE**（账本首个 reasoning 轴晋升）。
    - **decompose_v1 vs baseline**：4/14 vs 3/14，discordant=(0,1)，p=1.0，CI [0.000,0.214] 含 0 → **HOLD**（二测确认无增益，registry 补 tested 记录）。
  - **⑤ 记账 + 回写 + 自动化升级**：账本 **#11 PROMOTE**；registry 中 tool_arith_v1 标 promoted=True（已晋升策略：selective_retrieval_v1 + tool_arith_v1）；周六自动化升级为"60 题 + headroom 预检 + 失败模式驱动预注册 + 多臂 Bonferroni + 预检 seed 不复用"完整协议。
  - **账本演进**：#1 BASELINE → #2–#5 REVERT → #6–#8 PROMOTE(检索轴) → #9 CAPABILITY_EXTEND → #10 HOLD(自我纠错) → **#11 PROMOTE(reasoning 轴，headroom 预检铁律的首个战果)**。
  - 教训沉淀：① headroom 预检不只是省算力——它产出**失败模式情报**，直接驱动正确的变异方向（预注册 tool_arith 而非硬跑 decompose）；② 变异策略必须针对实测失败模式预注册，禁止事后编策略；③ 主实验基线 seed 必须全新生成（防 selection-on-noise）；④ 计算类难题评分必须锚定"最终答案：xxx"格式防仪器假阳性。新增审计留痕：`_hard_gate.py`、`submissions_hard_15seeds.json`、`results_hard_gate_r10.json`、`_patch_bench_r10.py`、`_ledger11.py`。
"""

dl = """
## 第十次进化（"继续实现通用自进化智能" → headroom 预检落地 + 首个 reasoning 轴 PROMOTE，账本 #11）
- **背景**：执行第九轮自沉淀方向——#10 HOLD 归因"题无 headroom"，本轮先造竞赛级难题再重测推理轴策略。
- **① 难题 cohort 2026Q3-hard（T047-T060）**：模幂/阶乘位数和/区间素数/Fib模/CRT 十四题，ground truth 全 python 可复跑（source 字段），锚定"最终答案：xxx"防假阳性。全库 46→60（dev26/hidden24/fresh10），reasoning 轴 10→24。哈希锁 OK；selfcheck 直答对 hard 全 0 = 预期（headroom 设计）。
- **② headroom 预检（K=3 两轮 9 seed）**：第一轮题太易弃用；第二轮确认三族直答系统性崩溃=有真 headroom。关键情报：decompose 同模式拒答→失败模式="心算算术链过长"。
- **③ 预注册 tool_arith_v1**：据失败模式实验前注册（写最小 python 计算复核），策略空间 6→7，防事后编策略。
- **④ 三臂 K=5 + Bonferroni alpha=0.025**：baseline(全新seed)/decompose/tool_arith 各 5 seed，15 份提交留痕。结果：tool_arith 14/14 vs baseline 3/14，discordant(0,11)，p=0.000977，Δ+0.786，CI[0.571,1.000] → **PROMOTE**（首个 reasoning 轴晋升）；decompose 4/14，p=1.0，CI含0 → HOLD（二测确认，registry 补 tested）。
- **⑤ 收尾**：账本 #11 PROMOTE；registry tool_arith_v1 promoted=True；周六自动化升级（60题+预检+预注册+多臂Bonferroni+预检seed不复用）；--verify/--selfcheck/--cohort-report/--ledger-view 全过。
- **教训**：① headroom 预检产出失败模式情报，驱动正确变异方向；② 策略必须预注册禁事后编；③ 主实验基线 seed 全新防 selection-on-noise；④ 计算题评分锚定"最终答案：xxx"。留痕：_hard_gate.py、submissions_hard_15seeds.json、results_hard_gate_r10.json、_patch_bench_r10.py、_ledger11.py。
"""

with io.open(OVERVIEW, 'a', encoding='utf-8') as f:
    f.write(ov)
with io.open(DAYLOG, 'a', encoding='utf-8') as f:
    f.write(dl)

# 校验无损坏字符
for p in (OVERVIEW, DAYLOG):
    s = io.open(p, encoding='utf-8').read()
    assert '\ufffd' not in s, p
print("docs appended OK, no replacement chars")
