# -*- coding: utf-8 -*-
"""轮11 记账 #12 + 回写 strategy_registry.json（schema_guard_v1 PROMOTE）。
修正轮10教训：必须同步顶层 promoted 列表与 per-entry promoted 标志。"""
import json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))

# ---- 记账 #12 ----
entry = {
    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "decision": "PROMOTE",
    "baseline_pass": 33,
    "candidate_pass": 58,
    "n": 60,
    "baseline_overall": 0.550,
    "candidate_overall": 0.967,
    "delta_overall": 0.417,
    "delta": 0.417,
    "p_value": 4.17e-7,
    "ci_low": 0.283,
    "ci_high": 0.550,
    "disc_base_fail_cand_pass": 26,
    "disc_base_pass_cand_fail": 1,
    "cohort": "2026Q3-struct",
    "candidate": "schema_guard_v1",
    "axis": "structured_output",
    "note": "双臂 K=5 配对 McNemar 精确检验：schema_guard_v1 在 emit 前按 prompt 声明 schema 自校验并修正，"
            "structured_output 陷阱 cohort 上 baseline 33/60 → 58/60（Δ+0.417），p≈4e-7，CI95[0.283,0.550]。"
            "headroom 来自 max_words 超额(T061/T067/T072)、漏嵌套包装(T062/T068)、缺失必填(T063/T066/T070)；"
            "枚举陷阱题(T064/T065/T069/T071)因评分仅校验 enum 成员资格（不判语义）baseline 已满分，无 headroom——诚实记录。"
            "首个 structured_output 轴 PROMOTE（第三次纵向晋升，已晋升策略：selective_retrieval_v1 + tool_arith_v1 + schema_guard_v1）。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ledger entries:", len(ledger), "| appended #%d %s" % (len(ledger), entry["decision"]))

# ---- 回写 registry ----
for s in reg["strategies"]:
    if s["id"] == "schema_guard_v1":
        s["promoted"] = True
        s.setdefault("tested", []).append({
            "round": 11, "ledger_entry": len(ledger), "cohort": "2026Q3-struct",
            "n": 60, "baseline_pass": 33, "cand_pass": 58,
            "p": 4.17e-7, "ci95": [0.283, 0.550], "decision": "PROMOTE",
            "ts": entry["ts"],
        })
        s["note"] = "轮11 晋升生产默认（账本 #12，p≈4e-7，Δ+0.417）。机制：emit 前按 prompt 声明 required/enum/max_words/嵌套结构自校验并修正。"
        print("schema_guard_v1 promoted=True, tested records:", len(s["tested"]))

# 顶层 promoted 列表同步（轮10 教训：不能只改 per-entry 标志）
if "schema_guard_v1" not in reg.get("promoted", []):
    reg.setdefault("promoted", []).append("schema_guard_v1")
json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("top-level promoted:", reg["promoted"])
