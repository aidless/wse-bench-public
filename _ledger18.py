# -*- coding: utf-8 -*-
"""第十六轮：账本 #18 + 回写 strategy_registry.json (context_grounding_v1 HOLD)。
诚实判决：p=0.07 > 0.05 → HOLD（v10 铁律：必须 p<0.05 AND CI 下界>0）。
但信号接近显著：Δ=+0.200, CI[0.033, 0.367]，仅 McNemar 精确检验在小样本下功效不足。
诚实记录供未来参考。"""
import json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))

gate = json.load(open(os.path.join(BASE, "results_rc_gate_r16.json"), encoding="utf-8"))
assert gate["candidate"] == "context_grounding_v1"

entry = {
    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "decision": "HOLD",
    "baseline_pass": gate["baseline_pass"],
    "candidate_pass": gate["candidate_pass"],
    "n": gate["n"],
    "baseline_overall": round(gate["baseline_pass"] / gate["n"], 3),
    "candidate_overall": round(gate["candidate_pass"] / gate["n"], 3),
    "delta_overall": round(gate["delta"], 3),
    "delta": round(gate["delta"], 3),
    "p_value": gate["mcnemar_p"],
    "ci_low": gate["ci95"][0],
    "ci_high": gate["ci95"][1],
    "disc_base_fail_cand_pass": gate["discordant_c"],
    "disc_base_pass_cand_fail": gate["discordant_b"],
    "cohort": "2026Q3-rc",
    "candidate": "context_grounding_v1",
    "axis": "reading_comprehension",
    "note": "双臂 K=5 配对 McNemar：context_grounding_v1 在 2026Q3-rc 上 baseline 23/30 → 29/30（Δ+0.200），"
            "p=0.0703（>0.05 阈值），CI95[0.033, 0.367] 全部 >0。"
            "**HOLD 判决诚实原因**：v10 铁律要求 p<0.05 AND CI 下界>0 才能 PROMOTE；本轮 p=0.07 虽接近阈值但 McNemar 精确检验"
            "在小样本（n=30 配对，8 个 discordant）下功效不足，统计上未达显著。"
            "**信号本身强**：T094 baseline 1/5→candidate 5/5（+4），T096 baseline 3/5→candidate 5/5（+2）——"
            "context_grounding_v1 在**有 headroom 的子域全胜**。"
            "**cohort 设计局限**：6 题中 4 题 baseline 已满分（T091/T093/T095 + T092 部分），真正有 headroom 的"
            "只有 T094（推理+span 引用）和 T096（数字+原话短语），题量不足放大 McNemar 功效不足问题。"
            "**未来方向**（v12 铁律：无新 headroom 不应盲目重跑；若要补测需扩 cohort）："
            "① 增 T097-T100 加入更多'需要精确 span 引用'的 RC 题（如 2-3 道跨源对比+2 道隐含推理）；"
            "② 改 K=10 增检验功效；"
            "③ 仍诚实记录 registry tested 标记（不晋升，不自动归档）。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ledger entries:", len(ledger), "| appended #%d %s" % (len(ledger), entry["decision"]))

# ---- 回写 registry ----
for s in reg["strategies"]:
    if s["id"] == "context_grounding_v1":
        s.setdefault("tested", []).append({
            "round": 16, "ledger_entry": len(ledger), "cohort": "2026Q3-rc",
            "n": gate["n"], "baseline_pass": gate["baseline_pass"], "cand_pass": gate["candidate_pass"],
            "p": gate["mcnemar_p"], "ci95": gate["ci95"], "decision": "HOLD",
            "ts": entry["ts"],
        })
        s["origin"] = "round-16 headroom 预检观察：RC 题需精确回指源 span；baseline 倾向释义漏原话"
        s["preregistered_at"] = "2026-07-24T18:10 round-16"
        s["note"] = "轮16 测试 HOLD（账本 #18）：p=0.0703（>0.05 阈值），CI[0.033, 0.367] 全部 >0。信号本身强——T094 baseline 1/5→5/5、T096 3/5→5/5。McNemar 精确检验在 n=30 配对小样本下功效不足，cohort 6 题中 4 题 baseline 已满分是主要局限。未来扩 cohort + K=10 可破功效不足。"
        print("context_grounding_v1 tested (HOLD), records:", len(s["tested"]))

json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("registry written")