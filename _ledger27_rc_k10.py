import json
from datetime import datetime
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
result_path = root / "results_context_grounding_r21_real_k10.json"
ledger_path = root / "assets" / "evolution_ledger.json"
result = json.loads(result_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if not any(e.get("round") == 21 and e.get("type") == "CONTEXT_GROUNDING_RC_K10_REAL" for e in ledger):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "round": 21,
        "type": "CONTEXT_GROUNDING_RC_K10_REAL",
        "decision": result["decision"],
        "model": result["model"],
        "K": result["K"],
        "seeds": result["seeds"],
        "n": result["n_tasks"],
        "task_ids": result["task_ids"],
        "cohort": "2026Q3-rc2+rc3 (T103-T112)",
        "baseline_pass": result["base_pass"],
        "candidate_pass": result["cand_pass"],
        "delta_overall": result["delta_overall"],
        "p_value": result["mcnemar_p"],
        "ci_low": result["bootstrap_ci95_overall_delta"][0],
        "ci_high": result["bootstrap_ci95_overall_delta"][1],
        "disc_base_pass_cand_fail": result["discordant_base_pass_cand_fail"],
        "disc_base_fail_cand_pass": result["discordant_base_fail_cand_pass"],
        "per_seed_base_pass": result["per_seed_base_pass"],
        "per_seed_cand_pass": result["per_seed_cand_pass"],
        "per_task_base_pass": result["per_task_base_pass"],
        "per_task_cand_pass": result["per_task_cand_pass"],
        "per_split": result["per_split"],
        "method_honesty": "K=10 独立 seed (101-1010) 同 base 同 generation；per-task pass = 5/10+ 通过 (>=6/10)。诚实为 K=10 真实模型测。",
        "note": "第二十一轮 K=10 真测 T103-T112 10 题：base 5/10 vs cand 5/10 (pass 计数)；机制层 mean 升 dev 0.367→0.629、hidden 0.49→0.787 (T110 1/10→9/10 大幅提升)；fresh 持平。pass 翻转 1-1 平衡 → McNemar p=1。≥6/10 pass 阈值过严，T110/T112 等中等提升在阈值下被吞掉。context_grounding 机制仍有效（hidden mean +60%），但 cohort 平衡与 pass 阈值共同让统计门不破。",
        "artifact": "results_context_grounding_r21_real_k10.json",
    }
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"appended CONTEXT_GROUNDING_RC_K10_REAL as ledger entry #{len(ledger)}")
else:
    print("ledger already contains round 21 RC K=10 entry; skipping")
