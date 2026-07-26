import json
from datetime import datetime
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
result_path = root / "results_context_grounding_r20_real.json"
ledger_path = root / "assets" / "evolution_ledger.json"
result = json.loads(result_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if not any(e.get("round") == 20 and e.get("type") == "CONTEXT_GROUNDING_RC2_RC3_K5_REAL" for e in ledger):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "round": 20,
        "type": "CONTEXT_GROUNDING_RC2_RC3_K5_REAL",
        "decision": result["decision"],
        "model": result["model"],
        "K": result["K"],
        "seeds": result["seeds"],
        "n": result["n_tasks"],
        "task_ids": result["task_ids"],
        "cohort": "2026Q3-rc2+rc3",
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
        "method_honesty": "K=5 独立 seed (temperature=0.7, top_p=0.9) 同 base 同 generation；per-task pass = 5 seeds 中 ≥3 通过。诚实为模型层 K=5 真测。",
        "note": "第二十轮 K=5 真测：12 题 (T103-T112) 同一 Qwen2.5-3B-Instruct，5 不同 seed。",
        "artifact": "results_context_grounding_r20_real.json",
    }
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"appended CONTEXT_GROUNDING_RC2_RC3_K5_REAL as ledger entry #{len(ledger)}")
else:
    print("ledger already contains round 20 RC K=5 entry; skipping")
