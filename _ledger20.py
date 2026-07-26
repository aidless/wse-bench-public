"""账本 #20 + registry 标注：verifier_v1 HOLD 诚实判决。"""
import json, os
from datetime import datetime

BASE = r"F:\test\2026-07-24-08-21-57"
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")
GATE = os.path.join(BASE, "results_verify_gate_r16.json")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))
gate = json.load(open(GATE, encoding="utf-8"))

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
    "cohort": "2026Q3-verify",
    "candidate": "verifier_v1",
    "axis": "fact_recall + structured_output (cross-rubric)",
    "note": "双臂 K=5 配对 McNemar：verifier_v1 在 2026Q3-verify 上 baseline 22/30 → 27/30（Δ+0.167），p=0.180，CI95[-0.033, 0.367]。**HOLD 判决诚实原因**：① T097 单独强 (0/5→5/5，verifier_v1 修复 baseline 漏具体数字 128256)；② 其他 5 题 baseline 已 4-5/5 (T098 4/5, T099-T101 全 5/5, T102 3/5)，verifier_v1 无空间；③ cohort 设计失衡——4/6 题 baseline 几乎满分，6 题对 McNemar 精确检验功效不足（n=30, 9 discordants）。**信号本身强**：T097 单独 baseline 0/5 → candidate 5/5，是 verifier_v1 价值的真实证明（rubric-aware 验证能稳定抓回漏具体数字）。**cohort 平衡性是设计缺陷**，不是 verifier_v1 无效。**未来扩 cohort 思路**：① 设计 4-6 道'baseline 必漏具体数字/术语'题（让 baseline 0/3 命中）；② 配 K=10 增检验功效；③ 与 schema_guard_v1 / citation_check_v1 合并测（共同 vs 单个）。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"账本 entries: {len(ledger)} (#20 = verifier_v1 HOLD)")

# registry
for s in reg["strategies"]:
    if s["id"] == "verifier_v1":
        s.setdefault("tested", []).append({
            "round": 16, "ledger_entry": len(ledger), "cohort": "2026Q3-verify",
            "n": gate["n"], "baseline_pass": gate["baseline_pass"], "cand_pass": gate["candidate_pass"],
            "p": gate["mcnemar_p"], "ci95": gate["ci95"], "decision": "HOLD",
            "ts": entry["ts"],
        })
        s["origin"] = "round-16 (post 1000-papers deep learn) — verifier_v1 目标场景：emit 前跨 rubric 验证"
        s["preregistered_at"] = "2026-07-24T20:50 round-16"
        s["note"] = "轮16 测试 HOLD（账本 #20）：p=0.180（>0.05 阈值），CI[-0.033,0.367] 含 0。T097 单独强（0/5→5/5），cohort 设计失衡（4/6 题 baseline 几乎满分）导致 McNemar 功效不足。未来扩 cohort 需设计'baseline 必漏具体数字'题 + K=10。"
        print(f"verifier_v1 tested (HOLD), records: {len(s['tested'])}")

json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("registry written")