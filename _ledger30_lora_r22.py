import json
from datetime import datetime
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
result_path = root / "results_qwen3b_lora_r22_v128.json"
ledger_path = root / "assets" / "evolution_ledger.json"
result = json.loads(result_path.read_text(encoding="utf-8"))
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if not any(e.get("round") == 22 and e.get("type") == "PATH_A_R22_LORA_FINAL" for e in ledger):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "round": 22,
        "type": "PATH_A_R22_LORA_FINAL",
        "decision": result["decision"],
        "model": result.get("model", "Qwen2.5-3B-Instruct + PATH A r22 LoRA (r=8, 78 dev records, 2 epochs)"),
        "K": 1,
        "n": result.get("n_tasks", 128),
        "baseline_pass": result["base_pass"],
        "candidate_pass": result["cand_pass"],
        "delta_overall": result["delta_overall"],
        "p_value": result["mcnemar_p"],
        "ci_low": result["bootstrap_ci95_overall_delta"][0],
        "ci_high": result["bootstrap_ci95_overall_delta"][1],
        "per_split": result["per_split"],
        "paired_t_p": result["paired_t_p"],
        "method_honesty": "PATH A r22 重试：dev-only 78 records（不含 hidden/fresh），r=8/lr=2e-5/2 epochs 训练 138s。K=1 greedy 256 max_new_tokens 同 base 同 generation v128 全跑 84min。",
        "note": "v128 评估：base 32/128 → cand 30/128，Δ-0.012，McNemar p=0.75，paired t p=0.53 → **HOLD（路径 A 仍负，dev pass 15→13 过拟合，hidden/fresh 持平）**。机制层：dev pass 退 2 题（dev 训练集过拟合），hidden 9→9 但 mean 0.335→0.351 微升，fresh 8→8 mean 持平。**78 dev records + 2 epochs 不足以泛化到 76 hidden/fresh 题**；路径 A 仍未完成真正权重级 PROMOTE。账本 #29 v24 alt-test gate PROMOTE 仍是 context_grounding_v1 唯一进入 production 的 RC 路径。",
        "artifact": "results_qwen3b_lora_r22_v128.json",
    }
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"appended PATH_A_R22_LORA_FINAL as ledger entry #{len(ledger)} decision={entry['decision']}")
else:
    print("ledger already contains round 22 PATH A lora final entry; skipping")
