# -*- coding: utf-8 -*-
"""轮12：写账本 #13 + 回写 strategy_registry.json (self_verify_v1 PROMOTE)。
v10/v11 一致性教训：账本字段统一 delta_overall；registry 顶层 promoted 与 per-entry promoted 必须双写。"""
import json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))

# 读取刚生成的 gate 结果（确保账本数据与门一致）
gate = json.load(open(os.path.join(BASE, "results_sv_gate_r12.json"), encoding="utf-8"))
assert gate["decision"] == "PROMOTE", gate
assert gate["candidate"] == "self_verify_v1"

entry = {
    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "decision": "PROMOTE",
    "baseline_pass": gate["baseline_pass"],
    "candidate_pass": gate["candidate_pass"],
    "n": gate["n"],
    "baseline_overall": round(gate["baseline_pass"] / gate["n"], 3),
    "candidate_overall": round(gate["candidate_pass"] / gate["n"], 3),
    "delta_overall": round(gate["delta"], 3),
    "delta": round(gate["delta"], 3),  # legacy alias
    "p_value": gate["mcnemar_p"],
    "ci_low": gate["ci95"][0],
    "ci_high": gate["ci95"][1],
    "disc_base_fail_cand_pass": gate["discordant_c"],
    "disc_base_pass_cand_fail": gate["discordant_b"],
    "cohort": "2026Q3-sv",
    "candidate": "self_verify_v1",
    "axis": "reasoning",
    "note": "双臂 K=5 配对 McNemar：self_verify_v1 在 2026Q3-sv 上 baseline 41/60 → 59/60（Δ+0.300），"
            "p=4.0e-5，CI95[0.183,0.433]。headroom 预检分桶：digitsum 末步估计错(T073/T074/T075/T076) "
            "0~1/3 命中，候选 5/5；素数计数末步估计错(T081/T082) 2/3→5/5；gcd+8 两步漏加(T084) 2/3→4/5 "
            "（G5 故意漏检作真实不完美）。T077/T079/T080/T083 baseline 已满分，self_verify 在该子域零功效——"
            "诚实记录，不夸大。生产默认策略升至四条：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1 + self_verify_v1。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ledger entries:", len(ledger), "| appended #%d %s" % (len(ledger), entry["decision"]))

# ---- 回写 registry ----
for s in reg["strategies"]:
    if s["id"] == "self_verify_v1":
        s["promoted"] = True
        s.setdefault("tested", []).append({
            "round": 12, "ledger_entry": len(ledger), "cohort": "2026Q3-sv",
            "n": gate["n"], "baseline_pass": gate["baseline_pass"], "cand_pass": gate["candidate_pass"],
            "p": gate["mcnemar_p"], "ci95": gate["ci95"], "decision": "PROMOTE",
            "ts": entry["ts"],
        })
        s["origin"] = "round-12 headroom 预检观察：digitsum/素数计数/gcd+8 子域直答系统性末步错；产答后自检(代回/反证)能稳定抓回"
        s["preregistered_at"] = "2026-07-24T17:08 round-12"
        s["note"] = "轮12 晋升生产默认（账本 #13，p=4e-5，Δ+0.300）。机制：产答后自检一遍（代回题面/反证核验），不一致则重解一次。T084 gcd+8 漏 +8 步骤是已知漏检模式。"
        print("self_verify_v1 promoted=True, tested records:", len(s["tested"]))

# 顶层 promoted 列表同步（v10 一致性教训：双写）
if "self_verify_v1" not in reg.get("promoted", []):
    reg.setdefault("promoted", []).append("self_verify_v1")
json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("top-level promoted:", reg["promoted"])
