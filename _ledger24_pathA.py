import json
from datetime import datetime
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
ledger_path = root / "assets" / "evolution_ledger.json"
result = json.loads((root / "results_lora_pathA_r18_hiddenfresh.json").read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if not any(e.get("type") == "PATH_A_RETRY_EVAL" and e.get("round") == 18 for e in ledger):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "round": 18,
        "type": "PATH_A_RETRY_EVAL",
        "decision": "HOLD",
        "model": result["model"],
        "cohort": "2026Q3-hidden+fresh",
        "n": result["n_tasks"],
        "baseline_pass": result["base_pass"],
        "candidate_pass": result["lora_pass"],
        "delta_overall": result["delta_overall"],
        "p_value": result["mcnemar_p"],
        "ci_low": result["bootstrap_ci95_overall_delta"][0],
        "ci_high": result["bootstrap_ci95_overall_delta"][1],
        "disc_base_pass_cand_fail": result["discordant_base_pass_lora_fail"],
        "disc_base_fail_cand_pass": result["discordant_base_fail_lora_pass"],
        "training_data": "sft_dev_r18.jsonl (95 records, dev-only; hidden/fresh excluded)",
        "config": "QLoRA r=8 alpha=16 lr=2e-5 epochs=1; same base/generation; greedy max_new_tokens=256",
        "note": "清洁路径A重试：hidden/fresh 同条件诊断无通过数增益，McNemar p=1、CI跨零；不晋升、不宣称权重自进化。上一轮30对混入hidden/fresh的负结果(#19)与本轮均支持先扩大/净化数据再尝试。",
        "artifact": "results_lora_pathA_r18_hiddenfresh.json",
    }
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print("appended PATH_A_RETRY_EVAL HOLD as ledger entry", len(ledger))
else:
    print("PATH_A_RETRY_EVAL round 18 already present; no duplicate")
