"""路径 A step 3 收尾：LoRA eval 记账 #19 + 失败原因诚实分析。"""
import json, os
from datetime import datetime

BASE = r"F:\test\2026-07-24-08-21-57"
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")
REG = os.path.join(BASE, "assets", "strategy_registry.json")
EVAL_RESULTS = os.path.join(BASE, "results_qwen3b_lora_v96.json")
SFT_DATA = os.path.join(BASE, "sft_v90_5strat.jsonl")

ledger = json.load(open(LEDGER, encoding="utf-8"))
reg = json.load(open(REG, encoding="utf-8"))
r = json.load(open(EVAL_RESULTS, encoding="utf-8"))
n = sum(1 for line in open(SFT_DATA, encoding="utf-8"))

entry = {
    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "type": "PATH_A_STEP3_EVAL",
    "decision": "FAILED",
    "model": "Qwen2.5-3B-Instruct + LoRA r=16 alpha=32 on q/k/v/o/gate/up/down_proj",
    "training": {
        "n_sft_pairs": n,
        "epochs": 3,
        "batch": 1, "grad_accum": 8,
        "lr": 2e-4, "scheduler": "cosine",
        "warmup_ratio": 0.1,
        "train_runtime_s": 76,
        "gpu_peak_gb": 3.98,
    },
    "results": {
        "v90_baseline_k5":  {"n_pass_05": r["v90_baseline_comp"]["n_pass_05"], "n_pass_099": r["v90_baseline_comp"]["n_pass_099"]},
        "v90_prod_k5":      {"n_pass_05": r["v90_production_comp"]["n_pass_05"], "n_pass_099": r["v90_production_comp"]["n_pass_099"]},
        "lora_k1":          {"n_pass_05": r["lora_pass_05"], "n_pass_099": r["lora_pass_099"]},
        "sft_train_pass":   r["sft_train_pass"],
        "heldout_pass":     r["heldout_pass"],
    },
    "delta_vs_baseline": {
        "pass_05_lora - pass_05_baseline": r["lora_pass_05"] - r["v90_baseline_comp"]["n_pass_05"],
        "pass_099_lora - pass_099_baseline": r["lora_pass_099"] - r["v90_baseline_comp"]["n_pass_099"],
    },
    "diagnosis": [
        "30 对 SFT 太少（>2000 对才能 generalizable）。30 对含 12 fact/struct + 6 fact + 12 reasoning = 30 任务，96 题 benchmark 上严重过拟合到 SFT 任务风格。",
        "K=1 推理 vs v90 baseline K=5 → 5 seed aggregation 提供 noise floor baseline，K=1 单点估计方差大。",
        "max_new_tokens=256 截断长 answer（T020/T028 等 50+ 字符）。",
        "LoRA r=16 注入 29.9M 参数（0.96% 总参），训练数据不足导致对 base model 有 'catastrophic forgetting' 风险。",
        "SFT 数据是 5 策略 K=5 的 perfect answers——但 base model + LoRA 没有 5 策略能力，学到的只是表面的 text format。",
    ],
    "lesson": "SFT 蒸馏 5 策略栈需要：① 显著更多的 SFT 数据（>=500 对）；② 每个 task K=5 sample 给出多种 answer 变体；③ SFT 阶段就教推理策略（如 schema_guard emit 前自校验），不只是答案文本；④ 训练数据要 balance 各 cohort 不是 30 对集中在 3 个 topic。",
    "next_steps": [
        "扩大 SFT 数据：30 → 500-1000 对（用全部 v90 production candidate K=5 answers × 多 cohort）",
        "改用 0.5B-1.5B 模型作 SFT 起点（更小过拟合风险）",
        "改用 DPO/ORPO 训练（直接偏好对齐）代替 SFT",
        "作为 baseline 对比 v90 production：5 策略 K=5 = 0.978；LoRA K=1 = 0.189；差距 -0.789 → 路径 A 当前实现**远不如 prompt engineering + verifier 套件**——但提供了 eval-gated 闭环的完整模板",
    ],
    "note": "路径 A step 3 NEGATIVE result：30 对 SFT + QLoRA 微调 Qwen2.5-3B + 96 题 v96 benchmark K=1 推理 → pass_05=37/90 (0.411) / pass_099=17/90 (0.189)。远差于 v90 baseline K=5 (0.756/0.600) 和 v90 production K=5 (1.000/0.978)。诚实判定为 FAILED，**SFT 蒸馏 5 策略栈的'单模型+端到端'路径当前不可行**。未来需 500-1000 对数据 + DPO/ORPO 训练。**eval-gated 闭环本身的工程模板完成**：eval 5 策略 → SFT 30 对 → QLoRA 训练 1m16s → 推理 → v96 eval 全部跑通。",
}
ledger.append(entry)
json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"账本 entries: {len(ledger)}, #19 = PATH_A_STEP3_EVAL FAILED")