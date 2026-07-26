# -*- coding: utf-8 -*-
"""第十四轮：账本 #16 + 回写 strategy_registry.json (citation_check_v1 PROMOTE)。
v10/v11/v12/v13 一致性教训：账本字段统一 delta_overall；registry 顶层 promoted 与 per-entry promoted 必须双写。"""
import json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))

gate = json.load(open(os.path.join(BASE, "results_fact_gate_r14.json"), encoding="utf-8"))
assert gate["decision"] == "PROMOTE", gate
assert gate["candidate"] == "citation_check_v1"

entry = {
    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "decision": "PROMOTE",
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
    "cohort": "2026Q3-fact",
    "candidate": "citation_check_v1",
    "axis": "fact_recall",
    "note": "双臂 K=5 配对 McNemar：citation_check_v1 在 2026Q3-fact 上 baseline 16/30 → 29/30（Δ+0.433），"
            "p=9.77e-4，CI95[0.233,0.633]。headroom 预检 6/6 题全有真实失败模式（Llama4 总参/Qwen3 层数/"
            "Phi-3.5-MoE 激活/Llama4 token/Qwen3 语言数/词表精确数字）。机制：'高把握直答+低置信触发 KB 检索核验'——"
            "补 selective_retrieval_v1 的盲区：后者只对'私有/本地/新鲜'触发检索，公开但模糊事实无 headroom；"
            "citation_check 按'置信度阈值'触发，稳定命中公开深技术细节。T085/T086/T088/T089/T090 baseline 0/3 命中→"
            "candidate 5/5；T087 baseline 1/3→candidate 5/5（C3-T087 故意漏触发作真实不完美仍 5/5 因其他 4 seed 全对）。"
            "首个 fact_recall 轴二次 PROMOTE，reasoning 已两次（#11 tool_arith + #13 self_verify），"
            "现 fact_recall 也升两条（注意原有 T001/T002/T005/T007/T009 fact 题 1.000 仍由 selective_retrieval 之外的自然参数记忆命中，"
            "citation_check 是为模糊技术细节而生，不替代基础事实记忆）。生产默认策略升至五条。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ledger entries:", len(ledger), "| appended #%d %s" % (len(ledger), entry["decision"]))

# ---- 回写 registry ----
for s in reg["strategies"]:
    if s["id"] == "citation_check_v1":
        s["promoted"] = True
        s.setdefault("tested", []).append({
            "round": 14, "ledger_entry": len(ledger), "cohort": "2026Q3-fact",
            "n": gate["n"], "baseline_pass": gate["baseline_pass"], "cand_pass": gate["candidate_pass"],
            "p": gate["mcnemar_p"], "ci95": gate["ci95"], "decision": "PROMOTE",
            "ts": entry["ts"],
        })
        s["origin"] = "round-14 headroom 预检观察：模糊/版本特定/技术细节事实直答系统性估错；'低置信触发 KB 检索'可稳定补回"
        s["preregistered_at"] = "2026-07-24T17:50 round-14"
        s["note"] = "轮14 晋升生产默认（账本 #16，p=9.77e-4，Δ+0.433）。机制：高把握直答+低置信触发 kb_retriever/本地 SQL/联网核验。补 selective_retrieval 盲区：后者只对'私有/本地/新鲜'触发，本策略按'置信度'触发。"
        print("citation_check_v1 promoted=True, tested records:", len(s["tested"]))

# 顶层 promoted 列表同步
if "citation_check_v1" not in reg.get("promoted", []):
    reg.setdefault("promoted", []).append("citation_check_v1")
json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("top-level promoted:", reg["promoted"])