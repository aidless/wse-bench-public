# -*- coding: utf-8 -*-
"""第十轮：bootstrap CI + 账本#11追加 + strategy_registry 回写"""
import json, random, datetime

R = json.load(open('results_hard_gate_r10.json', encoding='utf-8'))
HIDS = sorted(R['baseline_agg'].keys())
b = [R['baseline_agg'][t] for t in HIDS]
c = [R['tool_arith_agg'][t] for t in HIDS]
d = [ci - bi for bi, ci in zip(b, c)]

random.seed(20260724)
n = len(d)
boots = []
for _ in range(10000):
    s = [d[random.randrange(n)] for _ in range(n)]
    boots.append(sum(s) / n)
boots.sort()
ci_low, ci_high = boots[249], boots[9749]
print(f"bootstrap 95% CI for tool_arith delta: [{ci_low:.3f}, {ci_high:.3f}]")

# decompose CI
d2 = [R['decompose_agg'][t] - R['baseline_agg'][t] for t in HIDS]
boots2 = []
for _ in range(10000):
    s = [d2[random.randrange(n)] for _ in range(n)]
    boots2.append(sum(s) / n)
boots2.sort()
ci2 = (boots2[249], boots2[9749])
print(f"bootstrap 95% CI for decompose delta: [{ci2[0]:.3f}, {ci2[1]:.3f}]")

now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

# ---- 账本 #11（append-only）----
led = json.load(open('assets/evolution_ledger.json', encoding='utf-8'))
assert len(led) == 10
entry = {
    "ts": now,
    "baseline_overall": R['gate_tool_arith']['baseline_mean'],
    "candidate_overall": R['gate_tool_arith']['cand_mean'],
    "n": n,
    "baseline_pass": R['gate_tool_arith']['baseline_pass'],
    "candidate_pass": R['gate_tool_arith']['cand_pass'],
    "delta_overall": R['gate_tool_arith']['delta'],
    "p_value": R['gate_tool_arith']['p'],
    "ci_low": round(ci_low, 3),
    "ci_high": round(ci_high, 3),
    "disc_base_pass_cand_fail": R['gate_tool_arith']['b'],
    "disc_base_fail_cand_pass": R['gate_tool_arith']['c'],
    "decision": "PROMOTE",
    "license": None,
    "note": ("第十轮·headroom预检铁律首次落地+首个reasoning轴PROMOTE：新增竞赛级难题cohort=2026Q3-hard"
             "(T047-T060十四题:大数模幂/阶乘位数和/区间素数计数/Fibonacci模/CRT,答案全部python可复跑,"
             "评分锚定'最终答案：xxx'防中间步骤假阳性),全库46->60(dev26/hidden24/fresh10)。"
             "流程:①headroom预检(直答K=3两轮9seed)确认模幂/阶乘/素数三族基线系统性崩溃(有headroom),"
             "同时发现decompose_v1同模式拒答;②据失败模式('心算算术链过长')实验前预注册tool_arith_v1"
             "(写最小python计算复核);③三臂各K=5盲测(baseline seed全新生成不复用预检seed,防selection-on-noise),"
             "Bonferroni alpha=0.025双比较。结果:tool_arith_v1 14/14 vs baseline 3/14,discordant(0,11),"
             "McNemar p=0.000977,delta=+0.786,CI下界>0 -> PROMOTE(账本首个reasoning轴晋升)。"
             "decompose_v1 4/14,discordant(0,1),p=1.0 -> HOLD(二次测试确认无增益,失败模式与直答相同)。"
             "教训:变异方向应针对实测失败模式预注册,而非凭直觉硬跑旧候选;headroom预检既省K=5成本又提供失败模式情报。")
}
led.append(entry)
json.dump(led, open('assets/evolution_ledger.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"ledger appended: #{len(led)}")

# ---- registry 回写 ----
reg = json.load(open('assets/strategy_registry.json', encoding='utf-8'))
for s in reg['strategies']:
    if s['id'] == 'tool_arith_v1':
        s['promoted'] = True
        s.setdefault('tested', []).append({
            "round": 10, "ledger_entry": 11, "cohort": "2026Q3-hard", "n": n,
            "baseline_pass": 3, "cand_pass": 14, "p": 0.000977,
            "ci95": [round(ci_low, 3), round(ci_high, 3)],
            "decision": "PROMOTE", "ts": now})
    if s['id'] == 'decompose_v1':
        s.setdefault('tested', []).append({
            "round": 10, "ledger_entry": 11, "cohort": "2026Q3-hard", "n": n,
            "baseline_pass": 3, "cand_pass": 4, "p": 1.0,
            "ci95": [round(ci2[0], 3), round(ci2[1], 3)],
            "decision": "HOLD",
            "note": "二测确认：在真headroom难题上与直答同模式失效(心算链过长)，分解不解决算术执行瓶颈",
            "ts": now})
json.dump(reg, open('assets/strategy_registry.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
promoted = [s['id'] for s in reg['strategies'] if s.get('promoted')]
print("registry updated. promoted:", promoted)
