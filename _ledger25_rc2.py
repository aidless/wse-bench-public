import json
from datetime import datetime
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
result = json.loads((root / "results_context_grounding_r18_real.json").read_text(encoding="utf-8"))
ledger_path = root / "assets" / "evolution_ledger.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if not any(e.get("round") == 18 and e.get("type") == "CONTEXT_GROUNDING_RC2_REAL_GATE" for e in ledger):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "round": 18,
        "type": "CONTEXT_GROUNDING_RC2_REAL_GATE",
        "decision": "HOLD",
        "model": result["model"],
        "cohort": "2026Q3-rc2",
        "n": result["n_tasks"],
        "K": 1,
        "baseline_pass": result["base_pass"],
        "candidate_pass": result["cand_pass"],
        "delta_overall": result["delta_overall"],
        "p_value": result["mcnemar_p"],
        "ci_low": result["bootstrap_ci95_overall_delta"][0],
        "ci_high": result["bootstrap_ci95_overall_delta"][1],
        "disc_base_pass_cand_fail": result["discordant_base_pass_cand_fail"],
        "disc_base_fail_cand_pass": result["discordant_base_fail_cand_pass"],
        "per_split": result["per_split"],
        "per_task_base_pass": result["per_task_base_pass"],
        "per_task_cand_pass": result["per_task_cand_pass"],
        "note": "RC2 真实模型 K=1 跑：base 3/6 → cand 4/6，hidden 0/2→1/2 真实出现但 McNemar p=1（n=6 不和谐对 < 2 功效饱和）。机制层信号已现，仍需扩 cohort 与 K=5 同 K seed 模型层测。",
        "artifact": "results_context_grounding_r18_real.json",
    }
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"appended CONTEXT_GROUNDING_RC2_REAL_GATE HOLD as ledger entry #{len(ledger)}")
else:
    print("ledger already contains RC2 real gate entry; skipping")
